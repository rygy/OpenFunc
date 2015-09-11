import monitoring
import time
from neutronclient.common import exceptions as neutron_exceptions


@monitoring.timeit
def list_port(self):
    """
    Description - Generate a list of all ports
    """
    try:
        ports = self.neutron_client.list_ports()['ports']
        self.logger.warning('Listing Ports:')
        self.success = True
        for port in ports:
            self.logger.warning(port['id'] + " " + port['name'])
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 port not found list_port %s", e)
    except Exception as e:
        self.logger.error("<*>list_port Failed %s", e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def create_port(self):
    """
    Description - Generate a new 'neutroncheck' port for self.network['network']['id']
        """
    try:
        port_name = 'neutroncheck-' + str(time.time())
        self.port = self.neutron_client.create_port(
            {'port':
                {'name': port_name,
                 'network_id': self.network['network']['id']}})
        self.logger.warning(self.port['port']['id'])
        self.success = True
    except Exception as e:
        self.logger.error('<*>create_port Failed %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def update_port(self):
    """
    Description - Update the port listed under self.port['port']['id'] name
                  value to new_port
    """
    try:
        self.new_name = "new_port"
        self.neutron_client.update_port(
            self.port['port']['id'],
            {"port": {"name": self.new_name}})
        self.success = True
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 port not found update_port %s", e)
    except Exception as e:
        self.logger.error('<*>update_port Failed %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def delete_port(self):
    """
    Description - Delete the port listed under self.port['port']['id']
    """
    try:
        self.neutron_client.delete_port(self.port['port']['id'])
        self.success = True
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 port not found delete_port %s", e)
    except Exception as e:
        self.logger.error('<*>delete_port Failed %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e
