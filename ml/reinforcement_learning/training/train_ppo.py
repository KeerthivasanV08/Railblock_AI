"""
PPO Training Script — RailBlock AI Rescheduler (Self-Contained PyTorch Implementation)

Trains a lightweight PPO agent on RailwayDisruptionEnv to learn maintenance-block
rescheduling policies under operational disruptions.

Architecture
————————————
  Shared MLP backbone  →  Actor head (5-action softmax)
                       →  Critic head (scalar value estimate)

Outputs
───────
  ml/reinforcement_learning/artifacts/ppo_rescheduler_v1.pt   (policy weights)
  ml/reinforcement_learning/artifacts/training_metrics.json    (metrics history)
  backend/app/ml/models/ppo_rescheduler_v1.pt                 (runtime copy)

Safety notes
────────────
  The trained policy only PROPOSES rescheduling actions.
  All proposals must pass HardConstraintGuard and require explicit human approval.
  The policy is trained in offline simulation — NOT on live IR operational data.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

# Path bootstrap
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ml.reinforcement_learning.environment.railway_env import RailwayDisruptionEnv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PPO-TRAIN] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"
_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

_POLICY_PATH = _ARTIFACTS_DIR / "ppo_rescheduler_v1.pt"
_METRICS_PATH = _ARTIFACTS_DIR / "training_metrics.json"

_BACKEND_MODELS_DIR = _REPO_ROOT / "backend" / "app" / "ml" / "models"
_BACKEND_MODELS_DIR.mkdir(parents=True, exist_ok=True)
_RUNTIME_POLICY_PATH = _BACKEND_MODELS_DIR / "ppo_rescheduler_v1.pt"


class PPOConfig:
    N_ENVS: int = 8
    N_STEPS: int = 256
    TOTAL_TIMESTEPS: int = 200_000
    LEARNING_RATE: float = 3e-4
    N_EPOCHS: int = 8
    BATCH_SIZE: int = 64
    GAMMA: float = 0.99
    GAE_LAMBDA: float = 0.95
    CLIP_EPS: float = 0.2
    VF_COEF: float = 0.5
    ENT_COEF: float = 0.02
    MAX_GRAD_NORM: float = 0.5
    OBS_DIM: int = 12
    N_ACTIONS: int = 5
    HIDDEN: int = 128
    SEED: int = 42
    LOG_INTERVAL: int = 10


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int, n_actions: int, hidden: int):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(obs_dim, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
        )
        self.actor = nn.Linear(hidden, n_actions)
        self.critic = nn.Linear(hidden, 1)
        for layer in self.backbone:
            if isinstance(layer, nn.Linear):
                nn.init.orthogonal_(layer.weight, gain=np.sqrt(2))
                nn.init.zeros_(layer.bias)
        nn.init.orthogonal_(self.actor.weight, gain=0.01)
        nn.init.zeros_(self.actor.bias)
        nn.init.orthogonal_(self.critic.weight, gain=1.0)
        nn.init.zeros_(self.critic.bias)

    def forward(self, obs: torch.Tensor) -> Tuple[Categorical, torch.Tensor]:
        shared = self.backbone(obs)
        dist = Categorical(logits=self.actor(shared))
        value = self.critic(shared).squeeze(-1)
        return dist, value

    def get_value(self, obs: torch.Tensor) -> torch.Tensor:
        shared = self.backbone(obs)
        return self.critic(shared).squeeze(-1)


class VecEnv:
    def __init__(self, n_envs: int, seed: int = 42):
        self.envs = [RailwayDisruptionEnv(random_seed=seed + i) for i in range(n_envs)]
        self.n_envs = n_envs

    def reset(self) -> np.ndarray:
        return np.stack([env.reset()[0] for env in self.envs], axis=0)

    def step(self, actions: np.ndarray):
        obs_list, reward_list, done_list, info_list = [], [], [], []
        for i, env in enumerate(self.envs):
            obs, reward, terminated, truncated, info = env.step(int(actions[i]))
            done = terminated or truncated
            if done:
                obs, _ = env.reset()
            obs_list.append(obs)
            reward_list.append(reward)
            done_list.append(float(done))
            info_list.append(info)
        return (
            np.stack(obs_list, axis=0),
            np.array(reward_list, dtype=np.float32),
            np.array(done_list, dtype=np.float32),
            info_list,
        )


class RolloutBuffer:
    def __init__(self, n_steps: int, n_envs: int, obs_dim: int):
        self.n_steps = n_steps
        self.n_envs = n_envs
        self.obs = np.zeros((n_steps, n_envs, obs_dim), dtype=np.float32)
        self.actions = np.zeros((n_steps, n_envs), dtype=np.int64)
        self.log_probs = np.zeros((n_steps, n_envs), dtype=np.float32)
        self.rewards = np.zeros((n_steps, n_envs), dtype=np.float32)
        self.dones = np.zeros((n_steps, n_envs), dtype=np.float32)
        self.values = np.zeros((n_steps, n_envs), dtype=np.float32)
        self.ptr = 0

    def add(self, obs, action, log_prob, reward, done, value):
        self.obs[self.ptr] = obs
        self.actions[self.ptr] = action
        self.log_probs[self.ptr] = log_prob
        self.rewards[self.ptr] = reward
        self.dones[self.ptr] = done
        self.values[self.ptr] = value
        self.ptr = (self.ptr + 1) % self.n_steps

    def compute_advantages(self, last_values, gamma, gae_lambda):
        advantages = np.zeros_like(self.rewards)
        last_gae = np.zeros(self.n_envs, dtype=np.float32)
        for t in reversed(range(self.n_steps)):
            nnt = 1.0 - self.dones[t]
            next_vals = last_values if t == self.n_steps - 1 else self.values[t + 1]
            delta = self.rewards[t] + gamma * next_vals * nnt - self.values[t]
            last_gae = delta + gamma * gae_lambda * nnt * last_gae
            advantages[t] = last_gae
        return advantages, advantages + self.values

    def get_batches(self, batch_size, advantages, returns, device):
        flat_obs = self.obs.reshape(-1, self.obs.shape[-1])
        flat_acts = self.actions.flatten()
        flat_lps = self.log_probs.flatten()
        flat_adv = advantages.flatten()
        flat_ret = returns.flatten()
        n = len(flat_obs)
        idx = np.random.permutation(n)
        for start in range(0, n, batch_size):
            b = idx[start: start + batch_size]
            yield (
                torch.tensor(flat_obs[b], dtype=torch.float32).to(device),
                torch.tensor(flat_acts[b], dtype=torch.long).to(device),
                torch.tensor(flat_lps[b], dtype=torch.float32).to(device),
                torch.tensor(flat_adv[b], dtype=torch.float32).to(device),
                torch.tensor(flat_ret[b], dtype=torch.float32).to(device),
            )


def train_ppo_policy(
    total_timesteps: int = PPOConfig.TOTAL_TIMESTEPS,
    n_envs: int = PPOConfig.N_ENVS,
    n_steps: int = PPOConfig.N_STEPS,
    learning_rate: float = PPOConfig.LEARNING_RATE,
    n_epochs: int = PPOConfig.N_EPOCHS,
    batch_size: int = PPOConfig.BATCH_SIZE,
    gamma: float = PPOConfig.GAMMA,
    gae_lambda: float = PPOConfig.GAE_LAMBDA,
    clip_eps: float = PPOConfig.CLIP_EPS,
    vf_coef: float = PPOConfig.VF_COEF,
    ent_coef: float = PPOConfig.ENT_COEF,
    max_grad_norm: float = PPOConfig.MAX_GRAD_NORM,
    seed: int = PPOConfig.SEED,
    output_path: str = str(_POLICY_PATH),
) -> dict:
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s | Timesteps: %d | Envs: %d | Steps/update: %d",
                device, total_timesteps, n_envs, n_steps)

    vec_env = VecEnv(n_envs=n_envs, seed=seed)
    model = ActorCritic(PPOConfig.OBS_DIM, PPOConfig.N_ACTIONS, PPOConfig.HIDDEN).to(device)
    optimizer = optim.Adam(model.parameters(), lr=learning_rate, eps=1e-5)
    buffer = RolloutBuffer(n_steps=n_steps, n_envs=n_envs, obs_dim=PPOConfig.OBS_DIM)

    metrics_history: List[dict] = []
    episode_rewards: List[float] = []
    ep_reward_buf = np.zeros(n_envs, dtype=np.float32)

    obs = vec_env.reset()
    total_steps = 0
    n_updates = total_timesteps // (n_steps * n_envs)
    start_time = time.time()
    logger.info("Starting PPO — %d updates planned", n_updates)

    for update in range(1, n_updates + 1):
        model.eval()
        for _ in range(n_steps):
            with torch.no_grad():
                obs_t = torch.tensor(obs, dtype=torch.float32).to(device)
                dist, values = model(obs_t)
                actions = dist.sample()
                log_probs = dist.log_prob(actions)

            actions_np = actions.cpu().numpy()
            next_obs, rewards, dones, _ = vec_env.step(actions_np)
            buffer.add(obs, actions_np, log_probs.cpu().numpy(), rewards, dones, values.cpu().numpy())

            ep_reward_buf += rewards
            for i, done in enumerate(dones):
                if done > 0.5:
                    episode_rewards.append(float(ep_reward_buf[i]))
                    ep_reward_buf[i] = 0.0

            obs = next_obs
            total_steps += n_envs

        with torch.no_grad():
            last_vals = model.get_value(torch.tensor(obs, dtype=torch.float32).to(device)).cpu().numpy()

        advantages, returns = buffer.compute_advantages(last_vals, gamma, gae_lambda)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        model.train()
        pg_losses, vf_losses, ent_losses, clip_fracs = [], [], [], []
        for _ in range(n_epochs):
            for obs_b, act_b, old_lp_b, adv_b, ret_b in buffer.get_batches(batch_size, advantages, returns, device):
                dist, values_pred = model(obs_b)
                new_lp = dist.log_prob(act_b)
                entropy = dist.entropy().mean()
                ratio = torch.exp(new_lp - old_lp_b)
                clip_fracs.append(((ratio - 1.0).abs() > clip_eps).float().mean().item())
                pg_loss = -torch.min(ratio * adv_b, torch.clamp(ratio, 1 - clip_eps, 1 + clip_eps) * adv_b).mean()
                vf_loss = nn.functional.mse_loss(values_pred, ret_b)
                loss = pg_loss + vf_coef * vf_loss - ent_coef * entropy
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
                optimizer.step()
                pg_losses.append(pg_loss.item())
                vf_losses.append(vf_loss.item())
                ent_losses.append(entropy.item())

        if update % PPOConfig.LOG_INTERVAL == 0 or update == n_updates:
            recent = episode_rewards[-50:] if episode_rewards else [0.0]
            mean_rew = float(np.mean(recent))
            elapsed = time.time() - start_time
            logger.info(
                "Update %4d/%d | steps=%7d | mean_rew=%6.2f | pg=%.4f | vf=%.4f | ent=%.4f | clip=%.3f | fps=%d",
                update, n_updates, total_steps, mean_rew,
                np.mean(pg_losses), np.mean(vf_losses), np.mean(ent_losses),
                np.mean(clip_fracs), int(total_steps / elapsed),
            )
            metrics_history.append({
                "update": update,
                "total_steps": total_steps,
                "mean_ep_reward_last50": round(mean_rew, 4),
                "pg_loss": round(float(np.mean(pg_losses)), 6),
                "vf_loss": round(float(np.mean(vf_losses)), 6),
                "entropy": round(float(np.mean(ent_losses)), 6),
                "clip_fraction": round(float(np.mean(clip_fracs)), 4),
                "fps": int(total_steps / elapsed),
                "elapsed_s": round(elapsed, 1),
            })

    model.eval()
    final_mean_reward = float(np.mean(episode_rewards[-100:])) if episode_rewards else 0.0

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "config": {"obs_dim": PPOConfig.OBS_DIM, "n_actions": PPOConfig.N_ACTIONS, "hidden": PPOConfig.HIDDEN},
        "training_summary": {
            "total_timesteps": total_steps,
            "total_episodes": len(episode_rewards),
            "final_mean_reward_last100": round(final_mean_reward, 4),
            "training_duration_s": round(time.time() - start_time, 1),
            "model_version": "ppo_rescheduler_v1",
            "policy_type": "PPO_ACTOR_CRITIC_MLP",
            "environment": "RailwayDisruptionEnv",
            "corridor": "Chennai_Egmore_Thoothukudi",
            "data_note": (
                "Policy trained in offline simulation using structurally realistic disruption "
                "scenarios grounded in Chennai-Thoothukudi corridor topology. "
                "NOT trained on private Indian Railways live operational data."
            ),
            "safety_note": (
                "This policy only proposes rescheduling actions. "
                "All proposals pass HardConstraintGuard and require human approval."
            ),
        },
    }

    policy_path = Path(output_path)
    torch.save(checkpoint, policy_path)
    logger.info("Policy saved     -> %s", policy_path)
    shutil.copy2(policy_path, _RUNTIME_POLICY_PATH)
    logger.info("Runtime copy     -> %s", _RUNTIME_POLICY_PATH)

    full_metrics = {
        "training_config": {
            "total_timesteps": total_steps, "n_envs": n_envs, "n_steps": n_steps,
            "learning_rate": learning_rate, "n_epochs": n_epochs, "batch_size": batch_size,
            "gamma": gamma, "gae_lambda": gae_lambda, "clip_eps": clip_eps,
            "vf_coef": vf_coef, "ent_coef": ent_coef,
        },
        "training_summary": checkpoint["training_summary"],
        "metrics_history": metrics_history,
    }
    with open(_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(full_metrics, f, indent=2)
    logger.info("Metrics saved    -> %s", _METRICS_PATH)

    return {
        "status": "SUCCESS",
        "policy_path": str(policy_path),
        "runtime_path": str(_RUNTIME_POLICY_PATH),
        "metrics_path": str(_METRICS_PATH),
        "total_timesteps": total_steps,
        "total_episodes": len(episode_rewards),
        "final_mean_reward": round(final_mean_reward, 4),
        "training_duration_s": checkpoint["training_summary"]["training_duration_s"],
    }


if __name__ == "__main__":
    result = train_ppo_policy()
    print("\n=== PPO Training Summary ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
