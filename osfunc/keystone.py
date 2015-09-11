from keystoneclient.v2_0 import client as keystone_client_2
from keystoneclient.v3 import client as keystone_client_3

import sys
import requests
import monitoring


class KeystoneCheck:

    def __init__(self, logger, exec_time, **kwargs):
        self.username = kwargs['os_username']
        self.password = kwargs['os_password']
        self.tenant = kwargs['os_tenant_name']
        self.domain_id = kwargs['os_domain_id']
        self.auth_url = kwargs['os_auth_url']
        self.region = kwargs['os_region']

        self.service = 'keystone'
        self.logger = logger
        self.exec_time = exec_time
        self.zone = kwargs['os_zone']
        self.failure = None
        self.overall_success = True
        self.tenant_name = kwargs['os_tenant_name']

    @monitoring.timeit
    def authenticate_v2(self):
        try:
            self.success = True
            self.keystone_client = keystone_client_2.Client(
                username=self.username,
                password=self.password,
                tenant_name=self.tenant,
                auth_url=self.auth_url
            )

            self.v2_token = self.keystone_client.auth_ref['token']['id']
            self.v2_url = self.keystone_client.auth_ref['serviceCatalog']\
                [0]['endpoints'][0]['publicURL']

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Authentication V2.0 Failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def authenticate_v3(self):
        try:
            self.success = True
            # Modify auth_url this is hacky
            # should figure out a better way to handle these
            auth_url = self.auth_url.replace('v2.0', 'v3')

            self.keystone_client = keystone_client_3.Client(
                username=self.username,
                password=self.password,
                domain_id=self.domain_id,
                auth_url=auth_url
            )

            self.v3_url = self.keystone_client.auth_ref['catalog']\
                [0]['endpoints'][3]['url']
            self.v3_token = self.keystone_client.auth_ref['auth_token']
            self.v3_headers = {'Accept': 'application/json',
                               'X-Auth-Token': self.v3_token}
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Authentication V3.0 Failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def list_credentials(self):
        try:

            r = requests.get(self.v3_url + 'credentials',
                             headers=self.v3_headers)
            self.user_id = r.json()['credentials'][0]['user_id']

            if r.status_code == 200:
                return True

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Unable to list credentials %s", sys.exc_info()[1])

    @monitoring.timeit
    def list_user_projects(self):
        try:
            r = requests.get(self.v3_url +
                             'users/{}/projects'.format(self.user_id),
                             headers=self.v3_headers)
            try:
                self.project_id = r.json()['projects'][0]['id']
            except Exception as e:
                self.logger.warning('No Projects associated with Account')
                self.logger.warning('Caught Exception: {}'.format(e))

                return True

            if r.status_code == 200:
                return True

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Listing User Projects Failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def get_project(self):
        try:
            r = requests.get(self.v3_url +
                             '/projects/{}'.format(self.project_id),
                             headers=self.v3_headers)
            if r.status_code == 200:
                return True

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error(
                "Get User Project Failed %s", sys.exc_info()[1])

    @monitoring.timeit
    def create_credential(self):
        pass

    def run(self):
        self.authenticate_v2()
        self.authenticate_v3()
        self.list_credentials()
        self.list_user_projects()
        self.get_project()

        if self.overall_success is True:
            exit(0)
        else:
            exit(1)
