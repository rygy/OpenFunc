from datetime import datetime
from random import randint
from time import sleep
from sys import exit

from designateclient.v1 import Client
from designateclient.v1.records import Record
from designateclient.v1.domains import Domain

from dns import resolver
from dns.exception import DNSException
from dns.resolver import NXDOMAIN

from monitoring import timeit


class DNSaaSCheck:
    """

    Functional test for DNSaaS - basic workflow as follows:

    List domains
    Create domain
    Create record
    List records
    Query record
    Delete record
    Delete domain

    Specify the nameserver to be used on the CLI, or export OS_NAMESERVER

    NOTE: Currently, the IP associated with the A record is hardset below in self_ip - this behaviour will change
    to be specified on the CLI or through an environment variable

    """

    def __init__(self, logger, exec_time, **kwargs):
        self.client = Client(
            auth_url=kwargs['os_auth_url'],
            username=kwargs['os_username'],
            password=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            region_name=kwargs['os_region'],
            service_type='hpext:dns'
        )

        self.logger = logger
        self.exec_time = exec_time
        self.new_record = None
        self.new_domain = None
        self.service = 'DNSaaS'
        self.domain_name = 'OSfunctional{}'.format(randint(10*100, 20*100)) \
            + '.com.'
        self.email = 'hpcs.noc@hp.com'
        self.set_ip = '15.185.104.18'
        self.failure = None
        self.success = None
        self.overall_success = True
        self.nameserver = kwargs['nameserver']
        self.zone = None
        self.region = kwargs['os_region']
        self.tenant_name = kwargs['os_tenant_name']

    @timeit
    def list_domains(self):
        """
        List all domains associated with the provided account
        """

        try:
            domains = self.client.domains.list()
            self.logger.warning('Active Domains')
            if len(domains) == 0:
                self.logger.warning('No Active Domains')
            for domain in domains:
                self.logger.warning(domain.name)
        except Exception as e:
            self.logger.warning('Could not obtain domain list')
            self.logger.warning(e)
            self.success, self.overall_success = False, False
            self.failure = e
            exit(1)
        self.success = True

    @timeit
    def create_domain(self):
        """
        Create a new domain with the following format: OSfunction + Random Integer + .com
        """
        self.new_domain = Domain(name=self.domain_name,
                                 email=self.email)
        self.logger.warning('Attempting to create domain name {}'
                            .format(self.domain_name))
        try:
            self.new_domain = self.client.domains.create(self.new_domain)
        except Exception as e:
            self.logger.error('Got Exception Trying to create a Domain {}'
                              .format(e))
            self.success, self.overall_success = False, False
            self.failure = e

            return False
        self.success = True

    @timeit
    def list_records(self):
        """
        List records associated with the newly created domain
        """
        try:
            current_records = self.client.records.list(self.new_domain.id)
            if len(current_records) == 0:
                self.logger.warning('No Active records for domain {}'
                                    .format(self.new_domain.name))
                self.success = True
                return True
            self.logger.warning('Current Records:')
            for record in current_records:
                self.logger.warning(record.name)
        except Exception as e:
            self.logger.error('Error reading records {}'.format(e))
            self.success, self.overall_success = False, False
            self.failure = e
            exit(1)

        self.success = True

    @timeit
    def create_record(self):
        """
        Creates a new record as an A record subdomain
        """

        record_name = 'jenkins' + datetime.now().strftime('%m%d%H%M') + \
            '.' + self.new_domain.name

        record = Record(name=record_name, type='A', data=self.set_ip)

        try:
            self.new_record = self.client.records.create(self.new_domain.id,
                                                         record)
            self.logger.warning('Created Record: {}'
                                .format(self.new_record.name))
        except Exception as e:
            self.logger.error('Error creating record {}'.format(e))
            self.success, self.overall_success = False, False
            self.failure = e
            exit(1)
        self.success = True

    @timeit
    def query_record(self):
        """
        Query the newly created record to ensure the nameserver returns the correct IP originally specified
        """

        res = resolver.Resolver()
        res.nameservers = [self.nameserver]
        query_domain = str({}).format(self.new_record.name[:-1])

        self.logger.warning('Using nameserver {}'.format(self.nameserver))
        query_ip = None
        sleep(5)
        try:
            query = res.query(query_domain, 'A')
            query_ip = str(query[0])
        except Exception as e:
            self.logger.error('Query failed %s', e)
            self.logger.error('Check to see if nameserver parm is present')
            self.success, self.overall_success = False, False
            self.failure = e

        if self.set_ip == query_ip:
            self.logger.warning('Query Results {}'.format(query_ip))
            self.success = True

            return True

    @timeit
    def delete_record(self):
        """
        Deletes the newly created record
        """

        self.logger.warning('Deleting record {}'.format(self.new_record.name))
        try:
            self.client.records.delete(self.new_domain.id, self.new_record.id)
        except Exception as e:
            self.logger.error('Error deleting record {}'.format(e))
            self.success = False
            self.failure = e
            exit(1)
        self.success = True

    @timeit
    def delete_domain(self):
        """
        Deletes the newly created domain
        """

        self.logger.warning('Deleting domain {}'.format(self.new_domain.name))
        try:
            self.client.domains.delete(self.new_domain.id)
        except Exception as e:
            self.logger.error('Error deleting domain {}'.format(e))
            self.success = False
            self.failure = e
            exit(1)
        self.success = True

    def delete_all(self):
        """
        This is dangerous!
        """
        for domain in self.client.domains.list():
            self.client.domains.delete(domain.id)

    def run(self):

        self.list_domains()
        self.create_domain()
        self.create_record()
        self.list_records()
        self.query_record()
        self.delete_record()
        self.delete_domain()

        if self.overall_success is True:
            exit(0)
        else:
            exit(1)
