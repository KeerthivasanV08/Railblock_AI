"""
PPO RL Training Script — RailBlock AI

STATUS: SCAFFOLDING ONLY — training not yet implemented.

This script is the intended entry point for training a PPO policy
using Stable-Baselines3 once the RailwayEnv is implemented.
"""


def train_ppo_policy(
    total_timesteps: int = 1_000_000,
    n_envs: int = 4,
    learning_rate: float = 3e-4,
    n_steps: int = 2048,
    batch_size: int = 64,
    n_epochs: int = 10,
    gamma: float = 0.99,
    output_path: str = "ml/reinforcement_learning/artifacts/ppo_policy.zip",
) -> None:
    """
    Train PPO policy on RailwayEnv.

    NOT YET IMPLEMENTED.
    Prerequisites:
    1. Implement RailwayEnv in environment/railway_env.py (state/action/reward)
    2. Install stable-baselines3
    3. Define reward shaping constants in environment/actions.py
    4. Validate environment with environment/check_env.py

    Once trained, artifact will be saved to:
        ml/reinforcement_learning/artifacts/ppo_policy.zip
    AND copied to:
        backend/app/ml/models/rl_policy.zip
    """
    raise NotImplementedError(
        "PPO training is not yet implemented. "
        "Implement RailwayEnv first, then enable this training script."
    )


if __name__ == "__main__":
    train_ppo_policy()
