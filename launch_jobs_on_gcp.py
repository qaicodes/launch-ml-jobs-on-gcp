import hydra
from hydra.utils import instantiate
from utils import TrainingInfo
from omegaconf import DictConfig

from configs.config import setup_config

setup_config()


@hydra.main(config_path=".", config_name="config", version_base= None)
def run(config: DictConfig) -> None:
    instance_group_creator = instantiate(config.infrastructure.instance_group_creator)
    instance_ids = instance_group_creator.launch_instance_groups()
    training_info = TrainingInfo(
        instance_ids=instance_ids,
        project_id=config.infrastructure.project_id,
        zone=config.infrastructure.zone,
        instance_group_name=config.infrastructure.instance_group_creator.name,
        mlflow_experiment_url=config.infrastructure.mlflow.experiment_url,
    )
    training_info.print_job_info()

if __name__ == "__main__":
    run()