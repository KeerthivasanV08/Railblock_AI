"""
MDPS Model Evaluation Script.

Evaluates trained artifacts from ml/mdps/artifacts/ or backend/app/ml/models/ against the
mdps_training_labels dataset and prints metrics.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def main():
    from scripts.evaluate_ml import main as evaluate_main
    return evaluate_main()


if __name__ == "__main__":
    main()
