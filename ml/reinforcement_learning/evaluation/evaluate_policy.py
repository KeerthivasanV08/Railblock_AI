"""
RL Policy Evaluation Script — RailBlock AI

STATUS: SCAFFOLDING ONLY — no trained policy artifact exists.
"""


def evaluate_policy(
    policy_path: str = "ml/reinforcement_learning/artifacts/ppo_policy.zip",
    n_eval_episodes: int = 100,
) -> None:
    """
    Evaluate a trained PPO policy on held-out disruption scenarios.

    NOT YET IMPLEMENTED — no policy artifact exists.

    Expected metrics:
    - Mean episodic reward
    - Success rate (maintenance completion)
    - Average train disruption penalty
    - Average resource utilization
    - Comparison with deterministic baseline (policy_engine.py)
    """
    raise NotImplementedError(
        "Policy evaluation requires a trained artifact at "
        f"'{policy_path}'. No trained artifact currently exists."
    )


if __name__ == "__main__":
    evaluate_policy()
