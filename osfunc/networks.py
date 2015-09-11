import monitoring
from neutronclient.common import exceptions as neutron_exceptions
import time


@monitoring.timeit
def select_network(self):
    """
    Description - Select the network with a name that does not contain
                  any of the following
                  'Ext-Net'
                  'new'
                  'neutron'

                  This is done to ensure that one of the networks Created
                  by these scripts are not used.
    """
    try:
        for network in self.neutron_client.list_networks()['networks']:
            self.success = True
            if 'Ext-Net' in str(network['name']) or \
                'new' in str(network['name']) or \
                'neutron' in str(network['name']):
                pass
            else:
                self.network = network
                break
        self.logger.warning('Selected network {}'.format(self.network['name']))
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 network not found select_network %s", e)
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>select_network Failed %s", e)


@monitoring.timeit
def list_network(self):
    """
    Description - Generate a list of all networks
    """
    try:
        networks = self.neutron_client.list_networks()['networks']
        self.success = True
        self.logger.warning('Listing Networks:')
        for network in networks:
            self.logger.warning(network['id'] + " " + network['name'])
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 network not found list_network %s", e)
    except Exception as e:
        self.logger.error("<*>list_network Failed %s", e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def create_network(self):
    """
    Description - Generate a new 'neutroncheck' network.
    """
    try:
        network_name = 'neutroncheck-' + str(time.time())
        self.network = self.neutron_client.create_network(
            {'network':
                {'name': network_name, 'admin_state_up': True}})
        self.logger.warning('Created New Network: {0}'
            .format(self.network['network']['id']))
        self.success = True
    except neutron_exceptions.NeutronException as e:
        self.logger.error('<*>create_network Failed %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e
        exit(1)


@monitoring.timeit
def update_network(self):
    """
    Description - Update the network listed under
                  self.network['network']['id'] name value
                  to new_network
    """
    try:
        self.new_name = "new_network"
        self.neutron_client.update_network(
            self.network['network']['id'],
            {"network": {"name": self.new_name}})
        self.success = True
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 network not found update_network %s", e)
    except Exception as e:
        self.logger.error('<*>update_network Failed %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def delete_network(self):
    """
    Description - Delete the network listed under
                  self.network['network']['id']
    """
    try:
        self.neutron_client.delete_network(self.network['network']['id'])
        self.success = True
    except neutron_exceptions.NotFound as e:
        self.success = False
        self.failure = e
        self.logger.error("<*>404 network not found delete_network %s", e)
    except Exception as e:
        self.logger.error('<*>delete_network Failed %s' % e)
        self.success = False
        self.failure = e
