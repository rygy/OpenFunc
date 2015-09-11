from keystoneclient.v2_0 import client as keystone_client
from swiftclient import Connection
from swiftclient import exceptions as cdn_exceptions
import sys

import httplib2
import json

from time import sleep
import time
import monitoring


class Client:

    def __init__(self, token, tenant, region, END_POINTS):
        self.token = token
        self.END_POINTS = END_POINTS
        self.tenant = tenant
        self.endpoint = self.END_POINTS[region]
        self.http_client = httplib2.Http(
            timeout=60, disable_ssl_certificate_validation=True)

    def send_request(self, fragment=''):
        if fragment == '':
            uri = "%s/v1.0/%s?format=json" % (self.endpoint, self.tenant)
        else:
            uri = "%s/v1.0/%s/%s?format=json" % (
                self.endpoint, self.tenant, fragment)

        response, content = self.http_client.request(
            uri, "GET",
            headers={'Accept': 'application/json', 'X-Auth-Token': self.token})

        if response['status'] == '200':
            return json.loads(content)
        else:
            raise Exception('Request Failed')

    def get_account(self):
        return self.send_request()


class CdnCheck:

    """

    Functional test for CDN - basic workflow as follows

    Create a CDN enabled container
    List all the CDN containers
    Select a CDN enabled container
    Upload Metadata to the account
    Retrieve Metadata to the account
    Create and upload an object
    Access the object with the CDN http url
    Access the object with the CDN https url
    Delete the object created in the previous step
    Delete the CDN container we created in our first step

    """

    def __init__(self, logger, exec_time, **kwargs):
        self.keystone_client = keystone_client.Client(
            username=kwargs['os_username'],
            password=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            auth_url=kwargs['os_auth_url'])
        self.token = self.keystone_client.auth_ref['token']['id']
        self.tenant_id = self.keystone_client.auth_ref['token']['tenant']['id']
        self.end_points = self.keystone_client.service_catalog.get_endpoints()
        self.region1 = str(self.end_points['hpext:cdn'][0]['region'])
        self.region2 = str(self.end_points['hpext:cdn'][1]['region'])
        self.url1 = str(self.end_points['hpext:cdn'][0]['versionList'])
        self.url1 = self.url1[:-1]
        self.url2 = str(self.end_points['hpext:cdn'][1]['versionList'])
        self.url2 = self.url2[:-1]

        self.END_POINTS = {
            self.region1: self.url1,
            self.region2: self.url2
        }

        self.cdn_client = Connection(
            user=kwargs['os_username'],
            key=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            authurl=kwargs['os_auth_url'],
            auth_version="2.0",
            os_options={'region_name': kwargs['os_region'],
                        'service_type': 'hpext:cdn'})

        self.swift_client = Connection(
            user=kwargs['os_username'],
            key=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            authurl=kwargs['os_auth_url'],
            auth_version="2.0",
            os_options={'region_name': kwargs['os_region']})

        self.service = 'cdn'
        self.authurl = kwargs['os_auth_url']
        self.logger = logger
        self.exec_time = exec_time
        self.zone = kwargs['os_zone']
        self.failure = None
        self.overall_success = True
        self.region = kwargs['os_region']
        self.tenant_name = kwargs['os_tenant_name']

    @monitoring.timeit
    def list_containers(self):
        """

        List all the CDN containers

        """

        try:
            self.success = True
            self.cdn_containers = self.cdn_client.get_account()[1]
            self.logger.warning('Listing CDN Containers')

            for container in self.cdn_containers:
                self.logger.warning(
                    container['name'] + ' ' + container['x-cdn-uri'] +
                    ' ' + container['x-cdn-ssl-uri'])

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Listing CDN containers failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def select_container(self):
        """

        Select a CDN enabled container. Usually this is the container we created.

        """

        try:
            self.success = True
            self.enabled_container = None
            self.container = None
            self.cdn_containers = self.cdn_client.get_account()[1]
            """
            Select the container that was created in the previous step.
            """
            for x in range(len(self.cdn_containers)):
                if self.cdn_containers[x]['name'] == self.container_name:
                    self.enabled_container = x
                    break

            if self.enabled_container is not None:
                self.container = self.cdn_containers[self.enabled_container]
            else:
                raise cdn_exceptions.ClientException("CDN container not found")

            self.logger.warning(
                "The following CDN-enabled container has been selected %s",
                self.container)

        except cdn_exceptions.ClientException:
            self.success, self.overall_success = False, False
            self.failure = "Not found"
            self.logger.error("CDN container not found")

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Selecting a CDN container failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def upload_object(self):
        """

        Create and upload a small object to the container

        """

        try:
            self.success = True
            self.object = 'cdncheckob' + str(time.time())
            contents = 'yeah this is a pretty small object'
            self.swift_client.put_object(
                self.container['name'], self.object, contents)
            self.logger.warning("Created Object %s", self.object)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Uploading object to a CDN container failed %s",
                sys.exc_info()[1])

    @monitoring.timeit
    def check_http_url(self):
        """

        Access the object we created using the CDN http url

        """

        try:
            self.success = True
            uri = self.container['x-cdn-uri'] + '/' + self.object
            self.logger.warning("HTTP URL: %s", uri)

            for x in range(1, 51):
                sleep(10)

                http_client = httplib2.Http(
                    timeout=9, disable_ssl_certificate_validation=True)

                try:
                    response, content = http_client.request(uri, "GET")
                except:
                    continue

                if response['status'] == '200':
                    self.logger.warning("Checking HTTP CDN URL Succeeded")
                    return True

            self.logger.error("Checking HTTP CDN URL Timed Out")
            exit(1)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Checking HTTP CDN URL Failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def check_https_url(self):
        """

        Access the object we created using the CDN https url

        """

        try:
            self.success = True
            uri = self.container['x-cdn-ssl-uri'] + self.object
            self.logger.warning("HTTPS URL: %s", uri)

            for x in range(1, 51):
                sleep(10)

                http_client = httplib2.Http(
                    timeout=9, disable_ssl_certificate_validation=True)
                response, content = http_client.request(uri, "GET")

                if response['status'] == '200':
                    self.logger.warning("Checking HTTPS CDN URL Succeeded")

                    return True

            self.logger.error("Checking HTTPS CDN URL Timed Out")
            exit(1)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Checking HTTPS CDN URL Failed %s", sys.exc_info()[1])

    def delete_object(self):
        """

        Delete the object we created

        """

        try:
            self.success = True
            self.swift_client.delete_object(
                self.container['name'], self.object)
            self.logger.warning("Object %s Deleted", self.object)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Object Deletion Failed  %s", sys.exc_info()[1])

    @monitoring.timeit
    def create_cdn_enabled_container(self):
        """

        Create a CDN enabled container. We use Swift client to do this except
        we use a CDN endpoint

        """

        try:
            self.success = True
            self.container_name = 'cdncheck' + str(time.time())
            self.cdn_client.put_container(self.container_name)
            self.logger.warning(
                "Created New Container %s", self.container_name)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Create CDN Container Failed  %s", sys.exc_info()[1])

    @monitoring.timeit
    def delete_container(self):
        """

        Delete the container we created

        """

        try:
            self.success = True
            self.cdn_containers[self.enabled_container]['cdn_enabled'] = False
            # This would take some time to be propagated
            # We will keep checking until it's disabled.
            self.timer = 0
            while self.cdn_containers[
                    self.enabled_container]['cdn_enabled'] is True:
                if self.timer > 90:
                    break
                sleep(1)
                self.timer = self.timer + 1
                continue

            self.logger.warning("Deleting Container: %s", self.container['name'])
            self.swift_client.delete_container(self.container_name)
            self.cdn_client.delete_container(self.container_name)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Delete CDN Container Failed  %s", sys.exc_info()[1])

    @monitoring.timeit
    def update_metadata(self):
        """

        Update the metadata of the account

        """

        try:
            self.success = True
            headers = {"X-Account-Meta-Temp-User": "updatemetadata-user"}
            self.swift_client.post_account(headers)
            self.logger.warning(
                "Posting Metadata to Account succeeded: %s", headers)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Updating MetaData for CDN Container Failed  %s",
                sys.exc_info()[1])

    @monitoring.timeit
    def retrieve_metadata(self):
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
                "Retrieve MetaData from CDN Container Failed  %s",
                sys.exc_info()[1])

    def run(self):
        """

        This is a driver function that runs all the other methods in the Class

        """

        self.create_cdn_enabled_container()
        self.list_containers()
        self.select_container()

        # Uploading metadata and retrieving it

        self.update_metadata()
        self.retrieve_metadata()

        # First create a test object. Next, test the presence of it, using
        # bot a http and hppts url. Then delete the object.

        self.upload_object()
        self.check_http_url()
        self.check_https_url()

        if hasattr(self, 'object'):
            self.delete_object()

        self.delete_container()

        if self.overall_success is True:
            exit(0)
        else:
            exit(1)
