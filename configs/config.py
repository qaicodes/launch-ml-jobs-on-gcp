from dataclasses import dataclass, field

from hydra.core.config_store import ConfigStore

from configs.infrastructure.infrastructure_configs import InfrastructureConfig


@dataclass
class Config:
    infrastructure: InfrastructureConfig = field(default_factory=lambda: InfrastructureConfig())
    docker_image: str = "asd"


def setup_config() -> None:
    cs = ConfigStore.instance()
    cs.store(name="config", node=Config)