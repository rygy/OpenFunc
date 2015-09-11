import networks
import subnets
import ports
import routers
import floating_ip

from novaclient.v1_1 import client as nova_client
from neutronclient.v2_0 import client as neutron_client


class NeutronCheck:
    """
    Description - Basic workflow for neutron script.  For the create
                  processes one routine builds off a prior routine. For
                  the delete process items need to be deleted in the
                  opposite order that they were created.

    Create
        create_network
        create_subnet
        create_router
        create_port
        create_floating

    List
        list_network
        list_subnet
        list_router
        list_port
        list_floating

    Update
        update_network
        update_subnet
        update_router
        update_port

    Delete
        delete_floating
        delete_port
        delete_router
        delete_subnet
        delete_network
    """
    def __init__(self, logger, exec_time, **kwargs):
        self.neutron_client = neutron_client.Client(
            username=kwargs['os_username'],
            password=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            auth_url=kwargs['os_auth_url'],
            region_name=kwargs['os_region']
        )
        self.nova_client = nova_client.Client(
            kwargs['os_username'],
            kwargs['os_password'],
            kwargs['os_tenant_name'],
            kwargs['os_auth_url'],
            region_name=kwargs['os_region']
        )

        self.logger = logger
        self.exec_time = exec_time
        self.overall_success = True
        self.service = 'Neutron'
        self.failure = None
        self.region = kwargs['os_region']
        self.zone = None
        self.tenant_name = kwargs['os_tenant_name']

    def run(self):
        networks.create_network(self)
        subnets.create_subnet(self)
        routers.create_router(self)
        ports.create_port(self)
        floating_ip.create_floating(self)

        networks.list_network(self)
        subnets.list_subnet(self)
        routers.list_router(self)
        ports.list_port(self)
        floating_ip.list_floating(self)

        networks.update_network(self)
        subnets.update_subnet(self)
        routers.update_router(self)
        ports.update_port(self)

        floating_ip.delete_floating(self)
        ports.delete_port(self)
        routers.delete_router(self)
        subnets.delete_subnet(self)
        networks.delete_network(self)

        if self.overall_success is True:
            exit(0)
        else:
            exit(1)
