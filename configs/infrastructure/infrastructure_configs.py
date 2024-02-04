from omegaconf import SI
from dataclasses import dataclass, field
from typing import Optional
from configs.infrastructure.instance_group_creator_configs import InstanceGroupCreatorConfig

@dataclass
class MLFlowConfig:
    mlflow_external_tracking_uri: str = SI("${oc.env:MLFLOW_TRACKING_URI,localhost:6101}")
    mlflow_internal_tracking_uri: str = SI("${oc.env:MLFLOW_INTERNAL_TRACKING_URI,localhost:6101}")
    experiment_name: str = "Default"
    run_name: Optional[str] = None
    run_id: Optional[str] = None
    experiment_id: Optional[str] = None 
    experiment_url: str = SI(
        "${.mlflow_external_tracking_uri}/#/experiments/${.experiment_id}/runs/${.run_id}"
        )
    artifact_uri: Optional[str] = None


@dataclass
class InfrastructureConfig:
    project_id: str = "cybulde"
    zone: str = "europe-west4-a"
    instance_group_creator: InstanceGroupCreatorConfig = field(default_factory=lambda: InstanceGroupCreatorConfig())
    mlflow: MLFlowConfig = field(default_factory=lambda: MLFlowConfig() )