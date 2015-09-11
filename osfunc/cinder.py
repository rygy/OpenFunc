import images
import servers
import keypairs
import networks
import volumes

from neutronclient.v2_0 import client as neutron_client
from cinderclient.v1 import client as cinder_client
from novaclient.v1_1 import client as nova_client
from time import sleep


class CinderCheck:
    """
    Description - Basic work flow for Cinder script.

        List volumes
            volumes.list_volumes(self)
            volumes.list_volume_type(self)

        Create volume
            volumes.create_volume(self)
            volumes.check_available(self)

        Create server
            images.select_image(self)
            networks.select_network(self)
            keypairs.select_keypair(self)
            servers.create_volume_instance(self)
            servers.check_active(self)

        Attach & detach volume from server
            volumes.attach_volume(self)
            volumes.detach_volume(self)
            volumes.check_available(self)

        Delete volume and server
            volumes.delete_volume(self)
            servers.delete_instance(self)

        Create volume from image
            images.select_image(self)
            volumes.create_with_image(self)
            volumes.check_available(self)

        Create server from volume
            images.select_image(self)
            networks.select_network(self)
            keypairs.select_keypair(self)
            servers.create_instance_with_bdm(self)
            servers.check_active(self)

        Delete server and volume
            servers.delete_instance(self)
            volumes.delete_volume(self)
    """

    def __init__(self, logger, exec_time, **kwargs):
        self.cinder_client = cinder_client.Client(
            kwargs['os_username'],
            kwargs['os_password'],
            kwargs['os_tenant_name'],
            kwargs['os_auth_url'],
            region_name=kwargs['os_region'],
            service_type="volume"
        )

        self.nova_client = nova_client.Client(
            kwargs['os_username'],
            kwargs['os_password'],
            kwargs['os_tenant_name'],
            kwargs['os_auth_url'],
            region_name=kwargs['os_region']
        )

        self.neutron_client = neutron_client.Client(
            username=kwargs['os_username'],
            password=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            auth_url=kwargs['os_auth_url'],
            region_name=kwargs['os_region']
        )

        self.logger = logger
        self.exec_time = exec_time
        self.zone = kwargs['os_zone']
        self.region = kwargs['os_region']
        self.instance = None
        self.volume = None
        self.overall_success = True
        self.service = 'Block Storage'
        self.failure = None
        self.tenant_name = kwargs['os_tenant_name']

    def run(self):
        volumes.list_volumes(self)
        volumes.list_volume_type(self)
        volumes.create_volume(self)
        volumes.check_available(self)

        images.select_image(self)
        networks.select_network(self)
        keypairs.select_keypair(self)
        servers.create_volume_instance(self)
        servers.check_active(self)

        volumes.attach_volume(self)
        sleep(5)
        volumes.detach_volume(self)
        volumes.check_available(self)
        volumes.delete_volume(self)
        servers.delete_instance(self)

        images.select_image(self)
        volumes.create_with_image(self)
        volumes.check_available(self)

        images.select_image(self)
        networks.select_network(self)
        keypairs.select_keypair(self)
        servers.create_instance_with_bdm(self)
        servers.check_active(self)
        servers.delete_instance(self)
        volumes.delete_volume(self)

        if self.overall_success is True:
            exit(0)
        else:
            exit(1)
