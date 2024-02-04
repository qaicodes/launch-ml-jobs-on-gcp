from enum import Enum
from dataclasses import dataclass
from utils import getLogger, wait_for_extended_operation
from pathlib import Path


from google.cloud import compute_v1

class VMType(Enum):
    STANDARD = "STANDARD"
    SPOT = "SPOT"
    PREEMTIBLE = "PREEMTIBLE"


@dataclass
class BootDiskConfig:
    project_id: str
    name: str
    size_db: int
    labels: dict[str, str]

@dataclass
class VMConfig:
    machine_type: str
    accelerator_type: str
    accelaraotr_count: int
    vm_type: VMType
    disks: list[str]

@dataclass
class VMMetadataConfig:
    instance_group_name: str
    docker_image: str
    zone: str
    python_hash_seed: str
    mlflow_tracking_uri: str
    node_count: int
    disks: list[str]

class InstanceTemplateCreator:
    def __init__(
        self,
        scopes: list[str],
        network: str,
        subnetwork: str,
        startup_script_path: str,
        vm_config: VMConfig,
        boot_disk_config: BootDiskConfig,
        vm_metadata_config: VMMetadataConfig,
        template_name: str,
        project_id: str,
        labels: dict[str, str] = {},
    ) -> None:
        self.logger = getLogger(self.__class__.__name__)    
        self.scopes = scopes
        self.network = network
        self.subnetwork = subnetwork
        self.startup_script_path = startup_script_path
        self.vm_config = vm_config
        self.boot_disk_config = boot_disk_config
        self.vm_metadata_config = vm_metadata_config
        self.template_name = template_name.lower()
        self.project_id = project_id
        self.labels = labels

        self.template = compute_v1.InstanceTemplate()
        self.template.name = self.template_name

    def create_template(self) -> compute_v1.InstanceTemplate():
        self.logger.info(f"Creating instance template {self.template_name}...")
        self.logger.info(f"self.vm_metadata_config: {self.vm_metadata_config}")

        self._create_boot_disk()
        self._attach_disks()
        self._create_network_interface()
        self._create_machine_configuration()
        self._attach_metadata()
        self.logger.info("Creating Instance Template...")
        template_client = compute_v1.InstanceTemplate()
        operation = template_client.insert(project=self.project_id, instance_template_resource=self.template)
        wait_for_extended_operation(operation, "instance template creation")

        self.logger.info(f"Instance template {self.template_name} created successfully")

        return template_client.get(project=self.project_id, instance_template=self.template_name)


    def _create_boot_disk(self) -> None:
        boot_disk = compute_v1.AttachedDisk()
        boot_disk_initialize_params = compute_v1.AttachedDiskInitializeParams()
        boot_disk_image = self._get_disk_image(self.boot_disk_config.project_id, self.boot_disk_config.name)
        boot_disk_initialize_params.source_image = boot_disk_image.self_link
        boot_disk_initialize_params.disk_size_gb = self.boot_disk_config.size_db
        boot_disk_initialize_params.labels = self.boot_disk_config.labels
        boot_disk.initialize_params = boot_disk_initialize_params
        boot_disk.auto_delete = True
        boot_disk.boot = True
        boot_disk.device_name = self.boot_disk_config.name

        self.template.properties.disks = [boot_disk]

    def _get_disk_image(self, project_id: str, image_name: str) -> compute_v1.Image:
        image_client = compute_v1.ImagesClient()
        return image_client.get(project=project_id, image=image_name)
    
    def _attach_disks(self) -> None:
        disk_names = self.vm_config.disks
        for disk_name in disk_names: 
            disk = compute_v1.AttachedDisk(auto_delete=False, boot=False, mode="READ_ONLY", device_name=disk_name, source=disk_name) 
            self.template.properties.disks.append(disk)

        if len(disk_names) > 0:
            self.template.properties.metadata.items.append(compute_v1.Items(key="disks", value="\n".join(disk_names)))
    
    def _create_network_interface(self) -> None:
        network_interface = compute_v1.NetworkInterface()
        network_interface.name = "nic0"
        network_interface.subnetwork = self.subnetwork
        network_interface.network = self.network
        self.template.properties.network_interfaces = [network_interface]

    def _create_machine_configuration(self) -> None:
        self.template.properties.machine_type = self.vm_config.machine_type
        if self.vm_config.accelerator_count > 0:
            self.template.properties.guest_accelerators = [
                compute_v1.AcceleratorConfig(
                    accelerator_count=self.vm_config.accelerator_count,
                    accelerator_type=self.vm_config.accelerator_type,
                )
            ]
        self.template.properties.service_accounts = [compute_v1.ServiceAccount( email="default", scopes=self.scopes)]
        self.template.properties.labels = self.labels

        vm_type = self.vm_config.vm_type
        if vm_type == VMType.PREEMTIBLE:
            self.logger.info("Creating preemptible instance...")
            self.template.properties.scheduling = compute_v1.Scheduling(preemptible=True)
        elif vm_type == VMType.SPOT:
            self.logger.info("Creating spot instance...")
            self.template.properties.scheduling = compute_v1.Scheduling(provisioning_model= compute_v1.Scheduling.ProvisioningModel.SPOT.name,
                                                                        on_host_maintenance=compute_v1.Scheduling.OnHostMaintenance.TERMINATE.name,
                                                                   )
        elif vm_type == VMType.STANDARD:
            self.logger.info("Creating standard instance...")
            self.template.properties.scheduling = compute_v1.Scheduling(provisioning_model=compute_v1.Scheduling.ProvisioningModel.STANDARD.name,
                                                                        on_host_maintenance=compute_v1.Scheduling.OnHostMaintenance.TERMINATE.name)
        else:
            raise ValueError(f"Invalid VM type: {vm_type}")
    
    def _attach_metadata(self) -> None:
        startup_script = self.startup_script_path(self.startup_script_path)
        self.template.properties.metadata.items.append(compute_v1.Items(key="startup-script", value=startup_script))

        for meta_data_name, meta_data_value in self.vm_metadata_config.items():
            self.template.properties.metadata.items.append(compute_v1.Items(key=meta_data_name, value=meta_data_value))
        
    
    def _read_startup_script(self, startup_script_path) -> str:
        return Path(startup_script_path).read_text()
