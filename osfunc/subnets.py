import monitoring
import time
from neutronclient.common import exceptions as neutron_exceptions


@monitoring.timeit
def list_subnet(self):
    """
    Description - Generate a list of all subnet for tenant
    """
    try:
        subnets = self.neutron_client.list_subnets()['subnets']
        self.success = True
        self.logger.warning('Listing Subnets:')
        for subnet in subnets:
            self.logger.warning(subnet['id'] + " " + subnet['name'])
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 subnet not found list_subnet %s", e)
    except Exception as e:
        self.logger.error("<*>list_subnet Failed %s", e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def create_subnet(self):
    """
    Description - Generate a new 'neutroncheck' subnet for selected values
                    self.network['network']['id']
                    name subnet
                    ip_version 4
                    cidr 192.168.3.0/24
    """
    try:
        subnet_name = 'neutroncheck-' + str(time.time())
        self.subnet = self.neutron_client.create_subnet(
            {'subnet':
                {'name': subnet_name,
                 'network_id': self.network['network']['id'],
                 'ip_version': '4',
                 'cidr': '192.168.3.0/24',
                 'enable_dhcp': True}})
        self.newsubnet = self.subnet['subnet']['id']
        self.success = True
        self.logger.warning('Created New Subnet: {0}'
            .format(self.newsubnet))
    except neutron_exceptions.OverLimit as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>Subnet quota exceeded %s", e)
        self.logger.error(
            "Execute cleanup script to remove extra Subnets")
        exit(1)
    except Exception as e:
        self.logger.error('<*>create_subnet Failed %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def update_subnet(self):
    """
    Description - Update the network listed under
                   self.subnet['subnet']['id'] change name value
                   to new_network
    """
    try:
        self.new_name = "new_subnet"
        self.neutron_client.update_subnet(
            self.subnet['subnet']['id'],
            {"subnet": {"name": self.new_name}})
        self.success = True
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 subnet not found update_subnet %s", e)
    except Exception as e:
        self.logger.error('<*>update_subnet Failed %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def delete_subnet(self):
    """
    Description - Delete the network listed under self.subnet['subnet']['id']
    """
    try:
        self.neutron_client.delete_subnet(self.subnet['subnet']['id'])
        self.success = True
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 subnet not found delete_subnet %s", e)
    except Exception as e:
        self.logger.error('<*>delete_subnet Failed %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e
