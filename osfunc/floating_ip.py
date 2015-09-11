import paramiko
import os
import monitoring

from neutronclient.common import exceptions as neutron_exceptions
from random import randint
from time import sleep


@monitoring.timeit
def list_floating(self):
    """
    Description - List all floating ip addresses
    """
    try:
        floating_ips = self.nova_client.floating_ips.list()
        self.logger.warning('Listing IPs:')
        self.success = True
        for floating_ip in floating_ips:
            self.logger.warning(floating_ip.ip + ' ' + floating_ip.id)
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 floating IP not found list_floating %s", e)
    except Exception as e:
        self.logger.error("<*>list_floating Failed %s", e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def create_floating(self):
    """
    Description - Create a floating_ip address
    """
    try:
        floating_ips = self.nova_client.floating_ips.create()
        self.logger.warning('Create IPs: ')
        self.success = True
        self.floating_ip = floating_ips
        self.logger.warning(self.floating_ip.ip + ' ' + self.floating_ip.id)
    except Exception as e:
        self.logger.error("<*>create_floating Failed %s", e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def delete_floating(self):
    """
    Description - Delete the current floating_ip.id address
    """
    try:
        self.nova_client.floating_ips.delete(self.floating_ip.id)
        self.success = True
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 floating IP not found delete_floating %s",
                          e)
    except Exception as e:
        self.logger.error("<*>delete_floating Failed %s", e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def add_floating(self):
    """
    Description - Add the floating_ip.ip address to the current
                  self.instance.id
    """
    try:
        floating_ips = self.nova_client.servers.add_floating_ip(
            self.instance.id,
            self.floating_ip.ip,
            fixed_address=None)

        self.logger.warning("Added IP address " + self.floating_ip.ip)
        self.success = True
        sleep(15)

    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 not found add_floating %s", e)

    except Exception as e:
        self.logger.error("<*>add_floating Failed %s", e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def ssh_to_instance(self):
    """
    Description - SSH to the current floating_ip.ip address
    """

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if self.ssh_timeout is None:
        self.ssh_timeout = 180

    for x in range(0, int(self.ssh_timeout) / 15):
        sleep(15)
        try:
            self.logger.warning('Attempting to SSH to {}'
                .format(self.floating_ip.ip))
            ssh_client.connect(self.floating_ip.ip,
                               username='ubuntu',
                               key_filename=
                               os.path.expanduser('~/.ssh/id_rsa'),
                               timeout=3)
            stdin, stdout, stderr = ssh_client.exec_command('uptime')

            self.logger.warning('Uptime reported: {}'
                                .format(stdout.readlines()))
            self.success = True

            return True

        except Exception as e:
            self.logger.error('Got an error attempting SSH: {}'.format(e))
            self.failure = e
            if e == 'Authentication failed':
                return False
    self.logger.error('SSH Timed Out..')
    self.success = False


@monitoring.timeit
def create_delete_security_group(self):
    """
    Description - Add a security rule to the sec_group.id pulled
                  from a security group list.  When complete the
                  security rule is then deleted
    """
    port = randint(0, 65535)
    try:
        self.logger.warning(
            'Attempting to retrieve / update default sec group')
        sec_group = self.nova_client.security_groups.list()[0]
        sec_group_rule = self.nova_client.security_group_rules.create(
            sec_group.id,
            from_port=port,
            to_port=port,
            cidr='0.0.0.0/8',
            ip_protocol='TCP')
        sleep(5)
        self.logger.warning('Removing sec group rule')
        sec_group_rule.delete()

        self.success = True

        return True
    except Exception as e:
        self.logger.error('Exception {}'.format(e))

        self.success, self.overall_success = False, False
        self.failure = e
