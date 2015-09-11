import flavors
import images
import servers
import keypairs
import networks
import floating_ip

from novaclient.v1_1 import client as nova_client
from novaclient import exceptions as nova_exceptions
from neutronclient.v2_0 import client as neutron_client
from sys import exit
from time import sleep


class NovaCheck:
    """
        Description - Basic workflow for NOVA script.  Starting with the
                      create instance step each step builds on the prior
                      step and for the most part requires the previous
                      step to complete before executing the next step.

        Check security groups
            create_delete_security_group

        Check keypairs
            list_keypair
            create_keypair
            delete_keypair

        Check flavors
            list_flavors
            get_flavor

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

        Check Floating IP
            floating_ip.create_floating
            floating_ip.add_floating
            floating_ip.ssh_to_instance

        Check stop server
            get_server
            stop_server
            check_stopped

        Check start server
            get_server
            start_server
            check_active

        Check reboot server hard
            reboot_server_hard
            check_active

        Check reboot server soft
            reboot_server_soft
            check_active

        Check metadata
            set_server_metadata
            delete_server_metadata

        Cleanup routines
            delete_floating
            delete_instance
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
        self.zone = kwargs['os_zone']
        self.service = 'Compute'
        self.failure = None
        self.overall_success = True
        self.ssh_to_instance = kwargs['ssh_to_instance']
        self.region = kwargs['os_region']
        self.ssh_timeout = kwargs['ssh_timeout']
        self.tenant_name = kwargs['os_tenant_name']

    def run(self):

        # Add sec_group rule
        floating_ip.create_delete_security_group(self)

        # Keypair processing

        keypairs.list_keypair(self)
        keypairs.create_keypair(self)
        keypairs.delete_keypair(self)

        # Flavor processing
        flavors.list_flavors(self)
        flavors.get_flavor(self)

        # Create server
        images.select_image(self)
        keypairs.select_keypair(self)
        networks.select_network(self)

        servers.create_instance(self)
        servers.check_active(self)

        # floating IP
        floating_ip.create_floating(self)
        sleep(10)
        floating_ip.add_floating(self)

        # SSH to Instance
        if self.ssh_to_instance == 'True':
            floating_ip.ssh_to_instance(self)

        # Stop server
        servers.get_server(self)
        servers.stop_server(self)
        servers.check_stopped(self)

        # Start stopped server
        servers.get_server(self)
        servers.start_server(self)
        servers.check_active(self)

        # Reboot server Hard
        servers.reboot_server_hard(self)
        servers.check_active(self)

        # Set and delete server metadata
        servers.set_server_metadata(self)
        servers.delete_server_metadata(self)

        # Delete floating ip
        floating_ip.delete_floating(self)

        #Delete instance
        servers.delete_instance(self)

        sleep(5)

        if self.overall_success is True:
            exit(0)
        else:
            exit(1)
