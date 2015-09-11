import monitoring
from novaclient import exceptions as nova_exceptions

from random import randint
from sys import exit


@monitoring.timeit
def select_keypair(self):
    """
    Descrtiption - Select the last kepair from the keypair list
    """
    try:
        self.key_pairs = self.nova_client.keypairs.list()
        self.success = True
        for self.key_pair in self.key_pairs:
            if 'OSfuncTest' not in self.key_pair.name:

                break
    except IndexError:
        self.success, self.overall_success = False, False
        self.logger.error('<*>No Keypairs available - Cannot continue')
        exit(1)
    except nova_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 keypairs not found select_keypair %s", e)
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>select_keypair Failed %s", e)


@monitoring.timeit
def list_keypair(self):
    """
    Description - Generate a list of all available keypairs
    """
    try:
        self.keypair = self.nova_client.keypairs.list()
        self.success = True
        for keypairs in self.keypair:
            self.logger.warning(keypairs.name)
    except nova_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 keypairs not found list_keypair %s", e)
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>list_keypair Failed %s", e)


@monitoring.timeit
def create_keypair(self):
    """
    Description - Create keypair instance for given name
    """
    self.kp_name = 'OSfuncTest{}'.format(randint(0,10000))

    try:
        self.keypair = self.nova_client.keypairs.create(name=self.kp_name)
        self.success = True
        self.logger.warning(self.keypair.name)
    except nova_exceptions.OverLimit:
        self.logger.error("Creating_keypair Failed: Over Quota")
        self.success, self.overall_success = False, False
        self.failure = "Over Quota Limit"
        self.logger.error("execute cleanup script to remove extra keypairs")
        exit(1)
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>create_keypair Failed %s", e)


@monitoring.timeit
def delete_keypair(self):
    """
    Description - Delete keypair matching self.kp_name
    """
    try:
        self.keypair = self.nova_client.keypairs.delete(self.kp_name)
        self.success = True
    except nova_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 keypairs not found delete_keypair %s", e)
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>delete_keypair Failed %s", e)
