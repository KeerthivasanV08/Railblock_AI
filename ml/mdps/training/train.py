"""
MDPS Training Script wrapper.

Delegates to the canonical preprocessing/mdps_dataset.py pipeline.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "data"))


def main():
    from data.preprocessing.mdps_dataset import train_mdps_model_and_score_tasks
    scored_df, metrics = train_mdps_model_and_score_tasks()
    print(f"Training complete. Metrics: {metrics}")
    return scored_df, metrics


if __name__ == "__main__":
    main()

