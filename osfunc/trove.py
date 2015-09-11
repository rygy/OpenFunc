import time
import monitoring

from troveclient.v1 import client
from time import sleep
from troveclient.common import exceptions as trove_exceptions


class TroveCheck:
    """
    Functional test for DBaaS - basic workflow as follows:

        list_db
        create_db
        check_active_db
        get_db
        configuration_db
        resize_instance_db
        check_active_db
        restart_db
        check_active_db
        delete_db
    """

    def __init__(self, logger, exec_time, **kwargs):
        self.client = client.Client(
            kwargs['os_username'],
            kwargs['os_password'],
            kwargs['os_tenant_name'],
            kwargs['os_auth_url'],
            region_name=kwargs['os_region'],
        )

        self.instance = ''
        self.logger = logger
        self.exec_time = exec_time
        self.overall_success = True
        self.service = 'mySQL'
        self.failure = None
        self.region = kwargs['os_region']
        self.zone = None
        self.tenant_name = kwargs['os_tenant_name']

    @monitoring.timeit
    def list_db(self):
        """
        Description - Generate a list of all databases for the tenant
        """
        try:
            instances = self.client.instances.list()
            self.logger.warning('Currently Active Instances')
            self.success = True
            for instance in instances:
                self.logger.warning(instance.id + ' ' + str(instance.name))
        except trove_exceptions.NotFound as e:
            self.success, self.overall_success = False, True
            self.failure = e
            self.logger.error("<*>404 db not found list_db %s", e)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.warning('Error listing Instance %s', e)

    @monitoring.timeit
    def get_db(self):
        """
        Description - Get a specific database for selected value of
                        self.instance.id
        """
        try:
            instance = self.client.instances.get(self.instance.id)
            self.logger.warning('Currently Active Instances')
            self.success = True
            self.logger.warning(instance.id + " " + instance.name)

        except trove_exceptions.NotFound as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>404 db not found get_db %s", e)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.warning('Error getting Instance %s', e)

    @monitoring.timeit
    def configuration_db(self):
        """
        Description - Pull up the configuration for a specific
                      database for selected value of
                        self.instance.id
        """
        try:
            self.client.instances.configuration(self.instance.id)
            self.success = True

        except trove_exceptions.NotFound as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>404 db not found configuration_db %s", e)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.warning('Error getting Configuration %s', e)

    @monitoring.timeit
    def create_db(self):
        """
        Description - Create a database for selected value of
                        flavor 1001
        """
        try:
            self.success = True
            name = 'DBaaSCheck-' + str(time.time())
            self.instance = self.client.instances.create(
                name,
                1001
            )
            self.logger.warning('Created Instance')
            self.logger.warning(self.instance.id + ' ' + self.instance.name)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.logger.warning('Create Instance Error %s', e)
            exit(1)

    @monitoring.timeit
    def check_active_db(self):
        """
        Description - Wait for newly created database to change to active
                       status or to fail
        """
        for x in range(1, 30):
            try:
                status = self.client.instances.get(self.instance.id).status
                self.logger.warning('Instance Status: %s' % status)
                if status == u'ACTIVE':
                    self.success = True
                    self.logger.warning('Instance is Active')
                    return True
                elif status == u'ERROR':
                    self.success, self.overall_success = False, False
                    self.logger.warning('Instance is in Error State')
                    self.failure = "Instance is in error state"
                    exit(1)
            except trove_exceptions.NotFound as e:
                self.success, self.overall_success = False, False
                self.failure = e
                self.logger.error("<*>404 db not found check_active_db %s", e)
            except Exception as e:
                self.success, self.overall_success = False, False
                self.logger.warning('Instance Error %s', e)
                self.failure = e
                exit(1)
            sleep(20)
        self.logger.error('Instance Build Timed Out')
        exit(1)

    @monitoring.timeit
    def delete_db(self):
        """
        Description - Delete last database instance accessed
        """
        try:
            self.instance.delete()
            self.success = True
            self.logger.warning("Delete instance")
        except trove_exceptions.NotFound as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>404 db not found delete_db %s", e)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.logger.warning('Delete Error %s', e)
            self.failure = e

    @monitoring.timeit
    def resize_instance_db(self):
        """
        Description - Resize database for selected values
                        self.instance.id
                        flavor 1002
        """
        try:
            self.instance_hold = self.instance
            self.instances = self.client.instances.resize_instance(
                self.instance.id, flavor_id=1002)
            self.instance = self.instance_hold
            self.success = True
            self.logger.warning("Resize instance")
        except trove_exceptions.NotFound as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>404 db not found resize_db %s", e)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.logger.warning('Resize Instance Error %s', e)
            self.failure = e

    @monitoring.timeit
    def restart_db(self):
        """
        Description - Restart database for selected values
                        self.instance.id
        """
        try:
            self.instance_hold = self.instance
            self.instance = self.client.instances.restart(self.instance.id)
            self.instance = self.instance_hold
            self.success = True
            self.logger.warning("Restart instance")
        except trove_exceptions.NotFound as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>404 db not found restart_db %s", e)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.logger.warning('Restart Error %s', e)
            self.failure = e

    def run(self):

        self.list_db()
        self.create_db()
        self.check_active_db()
        self.get_db()
        self.configuration_db()
        # self.resize_instance_db()
        # self.check_active_db()
        self.restart_db()
        self.check_active_db()
        self.delete_db()
        if self.overall_success is True:
            exit(0)
        else:
            exit(1)
