"""Runtime evaluation wrapper."""


def trigger_evaluation():
    from scripts.evaluate_ml import main
    return main()
