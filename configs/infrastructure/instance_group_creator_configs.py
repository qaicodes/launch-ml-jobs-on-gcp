from dataclasses import dataclass, field

from omegaconf import SI

from configs.infrastructure.instance_template_creator_configs import InstanceTemplateCreatorConfig


@dataclass
class InstanceGroupCreatorConfig:
    _target_: str = "instance_group_creator.InstanceGroupCreator"
    instance_template_creator: InstanceTemplateCreatorConfig = field(default_factory=lambda: InstanceTemplateCreatorConfig())
    name: str = SI("job-${now:%Y%m%d%H%M%S}")
    node_count: int = 1
    project_id: str = SI("${infrastructure.project_id}")
    zone: str = SI("${infrastructure.zone}")