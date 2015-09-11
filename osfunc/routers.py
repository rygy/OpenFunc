import monitoring
import time
from neutronclient.common import exceptions as neutron_exceptions


@monitoring.timeit
def list_router(self):
    """
    Description - Generate a list of all routers for tenant
    """
    try:
        routers = self.neutron_client.list_routers()['routers']
        self.success = True
        self.logger.warning('Listing Routers:')
        for router in routers:
            self.logger.warning(router['id'] + " " + router['name'])
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 router not found list_router %s", e)
    except Exception as e:
        self.logger.error("<*>list_router Failed %s", e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def create_router(self):
    """
    Description - Generate a new 'neutroncheck' router.
    """
    try:
        name = 'neutroncheck-' + str(time.time())
        self.router = self.neutron_client.create_router(
            {'router':
                {'name': name}})
        self.success = True
        self.logger.warning('Created new router {0}'
            .format(self.router['router']['id']))
    except neutron_exceptions.OverLimit as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>Router quota exceeded %s", e)
        self.logger.error(
            "Execute cleanup script to remove extra Routers")
        exit(1)
    except Exception as e:
        self.logger.error('<*>create_router Failed %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def update_router(self):
    """
    Description - Update the router listed under self.router['router']['id']
                  name value to new_router
    """
    try:
        self.new_name = "new_router"
        self.neutron_client.update_router(
            self.router['router']['id'],
            {"router": {"name": self.new_name}})
        self.success = True
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 router not found update_router %s", e)
    except Exception as e:
        self.logger.error('<*>update_router Failed %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def delete_router(self):
    """
    Description - Delete the router listed under self.router['router']['id']
    """
    try:
        self.neutron_client.delete_router(self.router['router']['id'])
        self.success = True
    except neutron_exceptions.NotFound as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>404 router not found delete_router %s", e)
    except Exception as e:
        self.logger.error('<*>delete_router Failed %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e
