#!/usr/bin/env python

import argparse
import datetime
import logging
import os

import cdn
import cinder
import designate
import glance
import keystone
import libra
import neutron
import nova
import swift
import trove
import cleanup
import purge_service

from sys import exit


class OpenstackFunctionalShell():
    """
    OpenstackFunctionShell class serves as the entry point into the testing library - handles the various services
    that can be tested

    Example usage:

    $ osfunc --os-zone az2 --os-service nova

    OpenStack Credentials must be exported prior to usage or specified on the CLI

    $ export OS_REGION_NAME=region-a.geo-1
    $ export OS_PASSWORD=<password>
    $ export OS_AUTH_URL=https://region-b.geo-1.identity.hpcloudsvc.com:35357/v2.0/
    $ export OS_USERNAME=<user_name>
    $ export OS_TENANT_NAME=<tenant_name>

    When executing novaneutron include the os-id parameter to select specific tenant
        --os-id <tenant id>

    """

    def __init__(self):

        # Logging Setup

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.WARNING)
        self.logger.addHandler(logging.StreamHandler())
        self.exec_time = datetime.datetime.now()
        self.overall_success = True
        self.failure = None

    def get_args(self):
        parser = argparse.ArgumentParser(usage=__doc__)

        parser.add_argument('--os-service',
                            help='Name of Openstack service to test - \
                                    defaults to env[OS_SERVICE_NAME]', 
                            default=os.environ.get('OS_SERVICE_NAME', None),
                            required=True)
        parser.add_argument('--os-username',
                            help='Username - defaults env[to OS_USERNAME]',
                            default=os.environ.get('OS_USERNAME', None))
        parser.add_argument('--os-password',
                            help='Password - defaults to env[OS_USERNAME]',
                            default=os.environ.get('OS_PASSWORD', None))
        parser.add_argument('--os-region',
                            help="Openstack region - \
                            defaults to env[OS_REGION_NAME]",
                            default=os.environ.get('OS_REGION_NAME', None))
        parser.add_argument('--os-zone',
                            help="Openstack availability zone - \
                            defaults to env[OS_ZONE]",
                            default=os.environ.get('OS_ZONE', None))
        parser.add_argument('--os-tenant-name',
                            help="Tenant / Project Name - \
                            defaults to env[OS_TENANT_NAME]",
                            default=os.environ.get('OS_TENANT_NAME', None))
        parser.add_argument('--os-auth-url',
                            help="Identity Endpoint - defaults to env[OS_AUTH_URL]",
                            default=os.environ.get('OS_AUTH_URL', None))
        parser.add_argument('--os-domain-id',
                            help="Domain ID - defaults to env[OS_DOMAIN_ID]",
                            default=os.environ.get('OS_DOMAIN_ID', None))
        parser.add_argument('--nameserver',
                            help='Nameserver for use with designate to perform lookup - \
                                    defaults to env[OS_NAMESERVER]',
                            default=os.environ.get('OS_NAMESERVER'))
        parser.add_argument('--os-purge-service',
                            help='Service to reset quotas - \
                                    defaults to env[OS_PURGE_SERVICE]',
                            default=os.environ.get('OS_PURGE_SERVICE'))
        parser.add_argument('--db-string',
                            help='Option connection string to log results to a database - \
                                    defaults to env[OS_DB_STRING]',
                            default=os.environ.get('OS_DB_STRING'))

        parser.add_argument('--os-id',
                            help='Option ID for execution of E2E - \
                                    defaults to env[OS_ID]',
                            default=os.environ.get('OS_ID'))
        parser.add_argument('--ssh-to-instance',
                            help='Specify whether to attempt to establish an SSH connection during Nova '
                                 'workflow - set to True',
                            default=os.environ.get('ssh_to_instance'))
        parser.add_argument('--ssh-timeout',
                            help='SSH timeout in seconds',
                            default=os.environ.get('ssh_timeout'))

        args = parser.parse_args()

        return args


def main():
    shell = OpenstackFunctionalShell()
    args = shell.get_args()

    if args is None:
        shell.logger.warning('Please supply valid OpenStack Credentials\n\nosfunc --help')
        exit(1)

    exec_time = datetime.datetime.now()

    if args.os_service == 'swift':
        check = swift.SwiftCheck(logger=shell.logger,
                                 exec_time=exec_time,
                                 **vars(args))
    if args.os_service == 'nova':
        check = nova.NovaCheck(logger=shell.logger,
                               exec_time=exec_time,
                               **vars(args))
    if args.os_service == 'glance':
        check = glance.GlanceCheck(logger=shell.logger,
                                   exec_time=exec_time,
                                   **vars(args))
    if args.os_service == 'cdn':
        check = cdn.CdnCheck(logger=shell.logger,
                             exec_time=exec_time,
                             **vars(args))
    if args.os_service == 'cinder':
        check = cinder.CinderCheck(logger=shell.logger,
                                   exec_time=exec_time,
                                   **vars(args))
    if args.os_service == 'designate':
        check = designate.DNSaaSCheck(logger=shell.logger,
                                      exec_time=exec_time,
                                      **vars(args))
    if args.os_service == 'keystone':
        check = keystone.KeystoneCheck(logger=shell.logger,
                                       exec_time=exec_time,
                                       **vars(args))
    if args.os_service == 'libra':
        check = libra.LibraCheck(logger=shell.logger,
                                 exec_time=exec_time,
                                 **vars(args))
    if args.os_service == 'neutron':
        check = neutron.NeutronCheck(logger=shell.logger,
                                     exec_time=exec_time,
                                     **vars(args))
    if args.os_service == 'trove':
        check = trove.TroveCheck(logger=shell.logger,
                                 exec_time=exec_time,
                                 **vars(args))
    if args.os_service == 'cleanup':
        check = cleanup.CleanupCheck(logger=shell.logger,
                                     exec_time=exec_time,
                                     **vars(args))
    if args.os_service == 'purge_service':
        check = purge_service.PurgeCheck(logger=shell.logger,
                                         exec_time=exec_time,
                                         **vars(args))

    check.run()

if __name__ == '__main__':
    main()
