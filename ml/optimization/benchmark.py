"""
OR-Tools Solver Top-Level Benchmark Entry Point.

Delegates to ml/optimization/experiments/benchmark.py.
Run:
    python ml/optimization/benchmark.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.optimization.experiments.benchmark import run_benchmark

if __name__ == "__main__":
    results = run_benchmark()
    print(f"\nBenchmark complete. {len(results)} scenarios tested.")
