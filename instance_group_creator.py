from instance_template_creator import InstanceTemplateCreator
from utils import getLogger
from google.cloud import compute_v1
from utils import wait_for_extended_operation
import time

class InstanceGroupCreator:
    def __init__(
            self,
            instance_template_creator: InstanceTemplateCreator,
            name: str,
            node_count: int,
            project_id: str,
            zone: str,
    ) -> None:
        self.logger = getLogger(self.__class__.__name__)
        self.instance_template_creator = instance_template_creator
        self.name = name.lower() 
        self.node_count = node_count
        self.project_id = project_id
        self.zone = zone
    
    def launch_instance_groups(self) -> list[int]: 
        instance_group = self._create_instance_group()
        self.logger.debug(f"{instance_group=}")

        instance_group_instance_ids = self._get_instance_ids(self.name, self.node_count)
        return instance_group_instance_ids


    def _create_instance_group(self) -> compute_v1.InstanceGroupManager:
        self.logger.info(f"Creating instance group {self.name}")
        instance_template = self.instance_template_creator.create_template()

        instance_group_manager_resources = compute_v1.InstanceGroupManager(
            base_instance_name=self.name,
            instance_template=instance_template.self_link,
            target_size=self.node_count,
            name=self.name,
            target_size=self.node_count
        )
        instance_group_manager_client = compute_v1.InstanceGroupManagersClient()
        operation = instance_group_manager_client.insert(
            project=self.project_id, zone=self.zone, instance_group_manager_resources=instance_group_manager_resources   
        )
        wait_for_extended_operation(operation, "managed instance group creation")

        self.logger.info(f"Created instance group {self.name}")
        return instance_group_manager_client.get(project=self.project_id, zone=self.zone, instance_group_manager=self.name)

    def _get_instance_ids(self, name: str, node_count: int) -> list[int]:
        instance_ids = set()
        trials = 0
        max_trials = 10
        base_sleep_time = 1.5
        while trials <= max_trials:
            self.logger.info(f"Waiting for instances ({trials=})")
            pager = self.list_instances_in_group(name) 
            for instance in pager:
                if instance.id:
                    self.logger.info(f"Found instance {instance.id}")
                    instance_ids.add(instance.id)
            if len(instance_ids) >= node_count:
                break
            time.sleep(pow(base_sleep_time, max_trials))
            trials += 1
        return list(instance_ids)

            
    def list_instances_in_group(self, name: str) -> compute_v1.services.instance_group_managers.pagers.ListManagedInstancesPager:
        instance_group_manager_client = compute_v1.InstanceGroupManagersClient()
        pager = instance_group_manager_client.list_managed_instances(project=self.project_id, zone=self.zone, instance_group_manager=name)
        return pager