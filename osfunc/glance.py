import images
import servers
import keypairs
import networks

from sys import exit

from novaclient.v1_1 import client as nova_client
from neutronclient.v2_0 import client as neutron_client


class GlanceCheck:
    """

    Create instance
            select_image
            select_keypair
            select_network
            create_instance
            check_active

    Check images
            create_image
            check_active
            delete_image
            list_image
            get_image
    """

    def __init__(self, logger, exec_time, **kwargs):
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
        self.instance = None
        self.volume = None
        self.zone = None
        self.region = kwargs['os_region']
        self.service = 'Glance'
        self.failure = None
        self.overall_success = True
        self.tenant_name = kwargs['os_tenant_name']

    def run(self):

        # Create server
        images.select_image(self)
        keypairs.select_keypair(self)
        networks.select_network(self)

        servers.create_instance(self)
        servers.check_active(self)

        # Image processing
        images.create_image(self)

        images.check_image_status(self)
        images.list_images(self)
        images.get_image(self)
        images.delete_image(self)

        if self.overall_success is True:
            exit(0)
        else:
            exit(1)
