import monitoring
from novaclient import exceptions as nova_exceptions


@monitoring.timeit
def list_flavors(self):
    """
    Generate a list of all available flavors
    """
    try:
        self.flavors = self.nova_client.flavors.list()
        self.success = True
    except nova_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 flavors not found list_flavors %s", e)
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>list_flavors Failed %s", e)


@monitoring.timeit
def get_flavor(self):
    """
    Description get flavor 101 from available flavor list
    """

    try:
        self.flavors = self.nova_client.flavors.get(
            flavor=101)
        self.success = True
    except nova_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 flavor not found get_flavors 101")
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>get_flavor Failed %s", e)
