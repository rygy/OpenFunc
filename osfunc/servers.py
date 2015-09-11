import time
import monitoring

from time import sleep
from sys import exit

from novaclient import exceptions as nova_exceptions


@monitoring.timeit
def delete_instance(self):
    """
    Issues a delete on a server object via the Nova CLI
    """

    try:
        self.instance.delete()
        self.success = True
    except nova_exceptions.NotFound:
        self.logger.error("404 instance not found %s", self.instance.id)
        self.success, self.overall_success = False, True
        self.failure = "Not Found"
    except Exception as e:
        self.success, self.overall_success = False, True
        self.failure = e
        self.logger.error("<*>delete_instance %s", e)


@monitoring.timeit
def create_instance(self):
    """

    Description - Create a instance using the selected values for
                   self.image.id
                   Self.network['id']
                   self.key_pair.name
                   Set the valiable self.instanceid to the newly
                   created self.instance.id
    """

    try:
        instance_name = 'novacheck' + str(time.time())
        self.instance = self.nova_client.servers.create(
            name=instance_name,
            image=self.image.id,
            nics=[{'net-id': self.network['id']}],
            flavor=101,
            key_name=self.key_pair.name,
            availability_zone=self.zone
        )
        self.success = True
        self.logger.warning('Created Instance with ID: {}'
                            .format(self.instance.id))
        self.instanceid = self.instance.id
    except nova_exceptions.OverLimit:
        self.success, self.overall_success = False, False
        self.failure = 'OverLimit'
        self.logger.error("<*>create_instance Failed OverLimit")
        self.logger.error(
            "Execute cleanup script to remove extra instances")
        exit(1)
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>create_instance Failed %s", e)
        exit(1)


@monitoring.timeit
def create_volume_instance(self):
    """
     Description - Create a instance using the selected values for
                   self.image.id
                   Self.network['id']
                   self.key_pair.name
                   Set the valiable self.instanceid to the newly
                   created self.instance.id
    """

    try:
        instance_name = 'cindercheck' + str(time.time())
        self.instance = self.nova_client.servers.create(
            name=instance_name,
            image=self.image.id,
            nics=[{'net-id': self.network['id']}],
            flavor=101,
            key_name=self.key_pair.name,
            availability_zone=self.zone
        )
        self.success = True
        self.logger.warning('Created Instance with ID: {}'
                            .format(self.instance.id))
        self.instanceid = self.instance.id
    except nova_exceptions.OverLimit:
        self.success, self.overall_success = False, False
        self.failure = 'OverLimit'
        self.logger.error("<*>create_instance Failed OverLimit")
        self.logger.error(
            "Execute cleanup script to remove extra instances")
        exit(1)
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>create_instance Failed %s", e)
        exit(1)


@monitoring.timeit
def create_instance_with_bdm(self):
    """
    Description - Create a instance using the selected values for
                   self.image.id
                   Self.network['id']
                   self.key_pair.name
                   bdm - block_device_mapping
                   Set the variable self.instanceid to the newly
                   created self.instance.id
    """
    bdm = [{'uuid': self.volume.id,
            'source': 'volume',
            'dest': 'volume'}]
    try:
        instance_name = 'novacheck' + str(time.time())
        self.instance = self.nova_client.servers.create(
            name=instance_name,
            image=self.image.id,
            flavor=103,
            nics=[{'net-id': self.network['id']}],
            key_name=self.key_pair.name,
            block_device_mapping_v2=bdm,
            availability_zone=self.zone
        )
        self.success = True
        self.logger.warning(self.instance.id)
        self.instanceid = self.instance.id
    except nova_exceptions.OverLimit:
        self.success, self.overall_success = False, False
        self.failure = 'OverLimit'
        self.logger.error("<*>create_instance_with_bdm Failed OverLimit")
        self.logger.error(
            "Execute cleanup script to remove extra instances")
        exit(1)
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>create_instance_with_bdm Failed %s", e)
        exit(1)


@monitoring.timeit
def check_active(self):
    """
    Description - Wait for newly created instance to change to active
                   status or to fail
    """

    for x in range(1, 30):
        try:
            status = \
                str(self.nova_client.servers.get(self.instance.id).status)
            self.logger.warning('Instance Status %s', status)
            if status == 'ACTIVE':
                self.success = True
                return True
            if status == 'ERROR':
                self.success, self.overall_success = False, False
                self.failure = 'ErrorStatus'
                self.instance.delete()
                self.logger.error("Deleting instance")
                exit(1)
        except nova_exceptions.NotFound:
            self.success, self.overall_success = False, False
            self.failure = 'Instance Not Found'
            self.logger.error('<*>check_active Failed - Instance Not Found - {}'.format(nova_exceptions.NotFound.http_status))
            exit(1)
        sleep(15)
    self.success, self.overall_success = False, False
    self.failure = 'TimeOut'
    self.logger.error("<*>check_active Failed TimeOut - Exiting")
    self.instance.delete()
    self.logger.error("Deleting instance")
    exit(1)


@monitoring.timeit
def check_stopped(self):
    """
    Description - Wait for newly created network to change to stopped or
                   shutoff status or to fail
    """

    for x in range(1, 30):
        try:
            status = \
                str(self.nova_client.servers.get(self.instance.id).status)
            self.logger.warning('Instance Status %s', status)
            if status == 'SHUTOFF':
                self.success = True
                return True
            if status == 'ERROR':
                self.success, self.overall_success = False, False
                self.failure = 'ErrorStatus'
                self.instance.delete()
                self.logger.error("Deleting instance")
                exit(1)
        except nova_exceptions.NotFound:
            self.success, self.overall_success = False, False
            self.failure = 'NotFound'
            self.logger.error("<*>check_stopped Failed NotFound")
            exit(1)
        sleep(15)
    self.success, self.overall_success = False, False
    self.failure = "TimeOut"
    self.logger.error("<*>check_stopped Failed TimeOut")
    self.instance.delete()
    self.logger.error("Deleting instance")
    exit(1)


@monitoring.timeit
def get_server(self):
    """
    Description - Get server using the self.instance.id
    """
    try:
        self.instance = self.nova_client.servers.get(self.instance.id)
        self.success = True
    except nova_exceptions.NotFound:
        self.logger.error("404 instance not found %s", self.instance.id)
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
        exit(1)
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>get_server Failed %s", e)
        exit(1)


@monitoring.timeit
def stop_server(self):
    """
    Description - Stop instance using self.instance.id
    """
    try:
        self.instance_unused =  \
            self.nova_client.servers.stop(self.instance.id)
        self.success = True
        self.logger.warning(self.instance.id)
    except nova_exceptions.NotFound:
        self.logger.error("404 instance not found %s", self.instance.id)
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>stop_server Failed %s", e)


@monitoring.timeit
def start_server(self):
    """
    Description - Start instance using self.instance.id
    """
    try:
        self.instance_unused =  \
            self.nova_client.servers.start(self.instance.id)
        self.success = True
        self.logger.warning(self.instance.id)
    except nova_exceptions.NotFound:
        self.logger.error("404 instance not found %s", self.instance.id)
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>start_server Failed %s", e)


@monitoring.timeit
def reboot_server_hard(self):
    """
    Description - Perform a hard reboot on the instance using
                   self.instance.id
    """

    try:
        self.nova_client.servers.reboot(server=self.instance.id,
                                        reboot_type='HARD')
        self.success = True
        self.logger.warning(self.instance.id)
    except nova_exceptions.NotFound:
        self.logger.error("404 instance not found %s", self.instance.id)
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>reboot_server_hard Failed %s", e)


@monitoring.timeit
def reboot_server_soft(self):
    """
    Description - Perform a hard reboot on the instance using
                   self.instance.id
    """
    try:
        self.nova_client.servers.reboot(server=self.instance.id,
                                        reboot_type='SOFT')
        self.success = True
        self.logger.warning(self.instance.id)
    except nova_exceptions.NotFound:
        self.logger.error("404 instance not found %s", self.instance.id)
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>reboot_server_soft Failed %s", e)


@monitoring.timeit
def set_server_metadata(self):
    """
    Description - Insert metadata for instance listed under
                   self.instance.id
    """

    try:
        self.nova_client.servers.set_meta(self.instance.id,
                                          {1: "Test metadata"})
        self.success = True
        self.logger.warning(self.instance.id)
    except nova_exceptions.NotFound:
        self.logger.error("404 instance not found %s", self.instance.id)
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>set_server_metadata Failed %s", e)


@monitoring.timeit
def delete_server_metadata(self):
    """
    Description - Delete metadata for instance listed under
                   self.instance.id
    """
    try:
        self.nova_client.servers.delete_meta(self.instance.id, {})
        self.success = True
        self.logger.warning(self.instance.id)
    except nova_exceptions.NotFound:
        self.logger.error("404 instance not found %s", self.instance.id)
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>delete_server_metadata Failed %s", e)


@monitoring.timeit
def select_instance(self):
    """

    Selects / creates an instance object based on the supplied AZ
    based on the instance name - instances created
    by the library contain the string 'novacheck',
    if no instance is available with that string in the name, an
    instance is not selected

    """

    try:
        for instance in self.nova_client.servers.list():
            if 'novacheck' in str(instance.name) \
                and getattr(instance, 'OS-EXT-AZ:availability_zone') \
                == self.zone and \
                    instance.status == 'ACTIVE':
                self.instance = instance
        if self.instance:
            self.logger.warning("Selected Instance %s : %s" %
                                (self.instance.id, self.instance.name))
            self.success = True
        else:
            self.logger.error("No Instance Available")
            self.success, self.overall_success = False, False
            self.failure = "No Instance Available"
            self.instance.delete()
            self.logger.error("Deleting instance")
            exit(1)
    except nova_exceptions.NotFound:
        self.logger.error("404 instance not found")
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
        self.instance.delete()
        self.logger.error("Deleting instance")
        exit(1)
    except Exception as e:
        self.logger.error("Selecting Instance Failed")
        self.success, self.overall_success = False, False
        self.failure = e
        self.instance.delete()
        self.logger.error("Deleting instance")
        exit(1)
