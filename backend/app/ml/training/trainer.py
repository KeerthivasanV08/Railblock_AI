"""Runtime training trigger wrapper."""


def trigger_training():
    from data.preprocessing.mdps_dataset import train_mdps_model_and_score_tasks
    return train_mdps_model_and_score_tasks()

