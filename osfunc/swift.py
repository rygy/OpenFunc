from swiftclient import Connection
from swiftclient import exceptions as cdn_exceptions
import sys
from sys import exit

import time
import monitoring


class SwiftCheck:

    """

    Functional test for Swift - basic workflow as follows:

    List containers
    List objects in those containers
    Update Metadata of the account
    Retrieve Metadata of the account
    Create a Container
    Select that container
    Update Metadata of the container
    Retrieve Metadata of the container
    Create an object in the container
    Retrieve the object in the container
    Update metadata of the object
    Retrieve metadata of the object
    Delete object
    Delete container.

    """

    def __init__(self, logger, exec_time, **kwargs):
        self.swift_client = Connection(
            user=kwargs['os_username'],
            key=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            authurl=kwargs['os_auth_url'],
            auth_version="2.0",
            os_options={'region_name': kwargs['os_region']}
        )

        self.service = 'Object Storage'
        self.logger = logger
        self.exec_time = exec_time
        self.zone = kwargs['os_zone']
        self.region = kwargs['os_region']
        self.failure = None
        self.overall_success = True
        self.tenant_name = kwargs['os_tenant_name']

    @monitoring.timeit
    def list_containers(self):
        """
        List all the existing containers
        """

        try:
            self.success = True
            self.containers = self.swift_client.get_account()[1]
            self.logger.warning("Listing Containers:")
            for self.container in self.containers:
                self.logger.warning(self.container['name'])

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Listing Swift containers failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def list_objects(self):
        """
        List all the objects contained in each container
        """

        try:
            self.success = True
            self.containers = self.swift_client.get_account()[1]
            self.logger.warning("Listing Objects:")
            for self.container in self.containers:
                try:
                    for swift_container in self.swift_client.get_container(
                            self.container['name'])[1]:
                        self.logger.warning(
                            self.container['name'] + " " +
                            swift_container['name'])
                except:
                    pass

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Listing objects failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def create_container(self):
        """
        Create a new container
        """

        try:
            self.success = True
            self.container = 'swiftcheck' + str(time.time())
            self.swift_client.put_container(self.container)

            self.logger.warning("Created Container %s", self.container)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Create Container failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def create_object(self):
        """
        Create a new object in the newly created container
        """

        try:
            self.success = True
            self.object = 'swiftcheckob' + str(time.time())
            contents = 'yeah this is a pretty small object'
            self.swift_client.put_object(self.container, self.object, contents)
            self.logger.warning("Created Object %s", self.object)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Create Object Failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def get_container(self):
        """
        Select the newly created container
        """

        try:
            self.success = True
            self.containers = self.swift_client.get_account()[1]
            self.flag = 0

            for container in self.containers:
                if container['name'] == self.container:
                    self.logger.warning(
                        "Getting Container Succeeded: %s", container['name'])
                    self.flag = self.flag + 1
            if self.flag == 0:
                raise cdn_exceptions.ClientException("Container not found")

        except cdn_exceptions.ClientException:
            self.success, self.overall_success = False, False
            self.failure = "Not found"
            self.logger.error("Container not found")

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Selecting a container failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def get_object(self):
        """
        Get the newly created object from the newly created container
        """

        try:
            self.success = True
            object = self.swift_client.get_object(self.container, self.object)
            self.logger.warning("Getting Object Succeded: %s", object)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Getting object failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def retrieve_metadata_object(self):
        """
        Retrieve the metadata of the selected object
        """

        try:
            self.success = True
            object_info = self.swift_client.head_object(
                self.container, self.object)
            self.logger.warning(
                "Getting Object Head succeeded: %s", object_info)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Retrieving Object Head failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def retrieve_metadata_account(self):
        """
        Retrieve the metadata of the account
        """

        try:
            self.success = True
            account_info = self.swift_client.head_account()
            self.logger.warning(
                "Getting Account Head succeeded: %s", account_info)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Retrieving Account Head failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def retrieve_metadata_container(self):
        """
        Retrieve the metadata of the container
        """

        try:
            self.success = True
            container_info = self.swift_client.head_container(self.container)
            self.logger.warning(
                "Getting Container Head succeeded: %s", container_info)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Getting Container Head failed: %s", sys.exc_info()[1])

    @monitoring.timeit
    def update_metadata_account(self):
        """
        Update the metadata of the account
        """

        try:
            self.success = True
            headers = {"X-Account-Meta-Temp-User": "testuser"}
            self.swift_client.post_account(headers)
            self.logger.warning(
                "Posting Metadata to Account succeeded: %s", headers)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Posting Metadata to Account failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def update_metadata_container(self):
        """
        Update the metadata of the container
        """

        try:
            self.success = True
            headers = {"X-Container-Meta-Temp-User": "testuser"}
            self.swift_client.post_container(self.container, headers)
            self.logger.warning(
                "Posting Metadata to Container succeeded: %s", headers)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Posting Metadata to Container failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def update_metadata_object(self):
        """
        Update the metadata of the object
        """

        try:
            self.success = True
            headers = {"X-Object-Meta-Temp-User": "testuser"}
            self.swift_client.post_object(self.container, self.object, headers)
            self.logger.warning(
                "Posting Metadata to Object succeeded: %s", headers)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Posting Metadata to Object failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def delete_object(self):
        """
        Delete the object created earlier in the process flow
        """

        try:
            self.swift_client.delete_object(self.container, self.object)
            self.logger.warning("Object Deleted")

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Object Delete failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def delete_container(self):
        """
        Delete the container that was created earlier in the process flow
        """

        try:
            self.swift_client.delete_container(self.container)
            self.logger.warning("Container %s Deleted", self.container)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Container Delete Failed %s", sys.exc_info()[1])

    def run(self):
        """
        The driver method that runs all the steps in the process flow
        """

        self.list_containers()
        self.list_objects()

        self.update_metadata_account()
        self.retrieve_metadata_account()

        self.create_container()
        self.get_container()
        self.update_metadata_container()
        self.retrieve_metadata_container()

        self.create_object()
        self.get_object()
        self.update_metadata_object()
        self.retrieve_metadata_object()

        if hasattr(self, 'object'):
            self.delete_object()

        if hasattr(self, 'container'):
            self.delete_container()

        if self.overall_success is True:
            exit(0)
        else:
            exit(1)
