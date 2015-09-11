import monitoring
import subprocess
import cdn

from subprocess import PIPE

from neutronclient.v2_0 import client as neutron_client
from novaclient.v1_1 import client as nova_client
from cinderclient.v1 import client as cinder_client
from cinderclient import exceptions as cinder_exceptions
from designateclient.v1 import Client as Designate
from novaclient import exceptions as nova_exceptions
from troveclient.v1 import client
from keystoneclient.v2_0 import client as keystone_client
from swiftclient import Connection, RequestException


class PurgeCheck:
    """
        Description - Purge left over elements created by each service.
                      Service is selected and then specific deletes for
                      that service are executed.
        Basic workflow

        if cdn
            delete_cdn_containers
        if cinder
            delete_snapshots
            delete_volume
        if domains
            delete_domains
        if keystone
            pass
        if libra
            delete_lb
        if neutron
            delete_floating
            delete_port
            delete_router
            delete_subnet
            delete_network
        if nova
            delete_instance
            delete_floating
            delete_keypair
        if swift
            delete_swift_containers
        if trove
            delete_db
    """

    def __init__(self, logger, exec_time, **kwargs):
        self.neutron_client = neutron_client.Client(
            username=kwargs['os_username'],
            password=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            auth_url=kwargs['os_auth_url'],
            region_name=kwargs['os_region']
        )
        self.nova_client = nova_client.Client(
            kwargs['os_username'],
            kwargs['os_password'],
            kwargs['os_tenant_name'],
            kwargs['os_auth_url'],
            region_name=kwargs['os_region']
        )
        self.cinder_client = cinder_client.Client(
            kwargs['os_username'],
            kwargs['os_password'],
            kwargs['os_tenant_name'],
            kwargs['os_auth_url'],
            region_name=kwargs['os_region'],
            service_type="volume"
        )
        self.client = client.Client(
            kwargs['os_username'],
            kwargs['os_password'],
            kwargs['os_tenant_name'],
            kwargs['os_auth_url'],
            region_name=kwargs['os_region'],
        )
        self.keystone_client = keystone_client.Client(
            username=kwargs['os_username'],
            password=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            auth_url=kwargs['os_auth_url']
        )

        self.designate_client = Designate(
            auth_url=kwargs['os_auth_url'],
            username=kwargs['os_username'],
            password=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            region_name=kwargs['os_region'],
            service_type='hpext:dns'
        )

        self.swift_cdn_client = Connection(
            user=kwargs['os_username'],
            key=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            authurl=kwargs['os_auth_url'],
            auth_version="2.0",
            os_options={'region_name': kwargs['os_region'],
                        'service_type': 'hpext:cdn'}
        )

        self.swift_client = Connection(
            user=kwargs['os_username'],
            key=kwargs['os_password'],
            tenant_name=kwargs['os_tenant_name'],
            authurl=kwargs['os_auth_url'],
            auth_version="2.0",
            os_options={'region_name': kwargs['os_region']}
        )

        #self.cdn_client = cdn.Client(
        #    self.token, self.tenant_id, kwargs['os_region'], self.END_POINTS
        #)

        self.region = str(kwargs['os_region'])
        self.container = None
        self.cdn_object = None

        self.logger = logger
        self.exec_time = exec_time
        self.success = True
        self.overall_success = True
        self.purge_service = kwargs['os_purge_service']
        self.service = 'Purge Service'
        self.failure = None
        self.tenant_name = kwargs['os_tenant_name']

    @monitoring.timeit
    def delete_keypair(self):
        """
        Description - Delete all keypairs where OSfunctest is part of the name
        """
        try:
            self.logger.warning('Delete Keypairs:')
            for kp in self.nova_client.keypairs.list():
                if 'OSfuncTest' in kp.name:
                    self.keypair = self.nova_client.keypairs.delete(kp.name)
                    self.success = True
        except nova_exceptions.NotFound as e:
            self.success, self.overall_success = False, True
            self.failure = e
            self.logger.error("<*>404 keypairs not found delete_keypair %s", e)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>delete_keypair Failed %s", e)

    @monitoring.timeit
    def delete_floating(self):
        """
        Description - Delete all floating IPs where floatingip['port_id'] is
                        none and floatingip['fixed_ip_address'] is none
        """
        try:
            floatingips = self.neutron_client.list_floatingips()['floatingips']
            self.success = True
            self.logger.warning('Delete Floating IP:')
            for floatingip in floatingips:
                if floatingip['port_id'] is None:
                    if floatingip['fixed_ip_address'] is None:
                        floating_ips = self.neutron_client.delete_floatingip(
                            floatingip['id'])
                        self.logger.warning(
                            'Delete ' + floatingip['id'])

        except Exception as e:
            self.logger.error("<*>delete_floating Failed %s", e)
            self.success, self.overall_success = False, False
            self.failure = e

    @monitoring.timeit
    def delete_network(self):
        """
        Description - Delete all networks where network['name'] is new_network
                        or contains 'neutroncheck'
        """
        try:
            networks = self.neutron_client.list_networks()['networks']
            self.success = True
            self.logger.warning('Deleting Networks:')
            for network in networks:
                try:
                    if network['name'] == 'new_network' or \
                            'neutroncheck' in network['name']:
                        self.neutron_client.delete_network(network['id'])
                        self.logger.warning(
                            'Delete ' + network['id'] + " " + network['name'])
                    else:
                        self.logger.warning("Did not delete %s", network['id'])
                except Exception as e:
                    self.logger.warning("Did not delete %s", network['id'])
        except Exception as e:
            self.logger.error("<*>delete_network Failed %s", e)
            self.success, self.overall_success = False, False
            self.failure = e

    @monitoring.timeit
    def delete_port(self):
        """
        Description - Delete all ports where port['name'] contains
                        'neutroncheck'
        """
        try:
            ports = self.neutron_client.list_ports()['ports']
            self.logger.warning('Deleting Ports:')
            self.success = True
            for port in ports:
                try:
                    if 'neutroncheck' in port['name']:
                        self.neutron_client.delete_port(port['id'])
                        self.logger.warning(
                            'Deleting ' + port['id'] + " " + port['name'])
                    else:
                        self.logger.warning("Did not delete " + port['id'])
                except:
                    self.logger.warning("Did not delete %s", port['id'])
        except Exception as e:
            self.logger.error("<*>delete_port Failed %s", e)
            self.success, self.overall_success = False, False
            self.failure = e

    @monitoring.timeit
    def delete_router(self):
        """
        Description - Delete all routers where router['name'] contains
                        'neutroncheck'
        """
        try:
            routers = self.neutron_client.list_routers()['routers']
            self.success = True
            self.logger.warning('Deleting Routers:')
            for router in routers:
                try:
                    if 'neutroncheck' in router['name']:
                        self.neutron_client.delete_router(router['id'])
                        self.logger.warning(
                            'Deleting ' + router['id'] + " " + router['name'])
                    else:
                        self.logger.warning("Did not delete %s", router['id'])
                except:
                    self.logger.warning("Did not delete %s", router['id'])
        except Exception as e:
            self.logger.error("<*>delete_router Failed %s", e)
            self.success, self.overall_success = False, False
            self.failure = e

    @monitoring.timeit
    def delete_subnet(self):
        """
        Description - Delete all subnets where subnet['name'] contains
                        'neutroncheck'
        """
        try:
            subnets = self.neutron_client.list_subnets()['subnets']
            self.success = True
            self.logger.warning('Deleting Subnets:')
            for subnet in subnets:
                try:
                    if 'neutroncheck' in subnet['name']:
                        self.neutron_client.delete_subnet(subnet['id'])
                        self.logger.warning(
                            'Delete ' + subnet['id'] + " " + subnet['name'])
                    else:
                        self.logger.warning("Did not delete %s", subnet['id'])
                except:
                    self.logger.warning("Did not delete %s", subnet['id'])
        except Exception as e:
            self.logger.error("<*>list_subnet Failed %s", e)
            self.success, self.overall_success = False, False
            self.failure = e

    @monitoring.timeit
    def delete_volume(self):
        """
        Description - Delete all volumes where volume.display_name contains
                        'cinder'
        """
        volumes = self.cinder_client.volumes.list()
        try:
            self.logger.warning('Deleting Volumes:')
            for volume in volumes:
                self.success = True
                if 'cinder' in volume.display_name:
                    if self.cinder_client.volumes.get(volume.id).status\
                            == 'available':
                        try:
                            volume.delete()
                            self.logger.warning('Deleting unused volume: %s' %
                                                volume.id)
                        except Exception as e:
                            self.logger.error('Unable to delete volume: {}'
                                .format(e))
                    else:
                        self.logger.warning('Did not delete ' + volume.id)
        except cinder_exceptions.NotFound:
            self.logger.error("No Volumes found to delete")
            self.success, self.overall_success = False, True
            self.failure = "Not Found"
        except Exception as e:
            self.logger.warning(
                'Caught exception trying to delete old volumes: %s' % e)
            self.success, self.overall_success = False, False
            self.failure = e

    @monitoring.timeit
    def delete_snapshots(self):
        """
        Description - Delete all snapshots
        """

        try:
            snapshots = self.cinder_client.volume_snapshots.list()
            self.success = True
            self.logger.warning("deleting snapshots")
            for snapshot in snapshots:
                try:
                    snapshot.delete()
                    self.logger.warning("Deleting snapshot %s", snapshot.id)
                except Exception as e:
                    self.logger.error("Delete snapshot failed %s", e)
        except cinder_exceptions.NotFound:
            self.logger.error("No Snapshots found")
            self.success, self.overall_success = False, True
            self.failure = "Not found"
        except Exception as e:
            self.logger.error("Deleting Snapshots Failed")
            self.success, self.overall_success = False, False
            self.failure = e

    @monitoring.timeit
    def delete_instance(self):
        """
        Description - Delete all instances where instance.name contains
                        'novacheck'
        """
        try:
            instances = self.nova_client.servers.list()
            self.success = True
            self.logger.warning("Deleting instances")
            for instance in instances:
                if 'novacheck' in instance.name:
                    instance.delete()
                    self.logger.warning("delete %s", instance.id)
                else:
                    self.logger.warning("did not delete " + instance.id)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>delete_instance %s", e)

    @monitoring.timeit
    def delete_db(self):
        """
        Description - Delete all databases where instance.name contains
                        'DBaas' and the instance.status is active
        """
        try:
            instances = self.client.instances.list()
            self.logger.warning('Delete db instances')
            self.success = True
            for instance in instances:
                if instance.status == "ACTIVE":
                    if 'DBaaS' in instance.name:
                        try:
                            instance.delete()
                            self.logger.warning(
                                'delete ' + instance.id + ' ' + str(instance.name))
                        except Exception as e:
                            self.logger.error('could not delete %s', instance.name)
                    else:
                        self.logger.warning('did not delete %s', instance.name)
                else:
                    self.logger.warning('Not active %s', instance.name)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.warning('Error Deleting Instance %s', e)

    @monitoring.timeit
    def delete_lb(self):
        """
        Description - Delete all loadbalancers where name equals TestLB
        """
        name = "TestLB"
        try:
            self.logger.warning('Delete Load Balancers:')
            self.success = True
            proc = subprocess.Popen(['libra',
                                     '--insecure',
                                     '--os-region-name',
                                     self.region,
                                     'list'], stdout=PIPE)
            proc.wait()
            outs, err = proc.communicate()
            sum_output = ''
            for lists in outs:
                sum_output = sum_output + lists
                if lists == '\n':
                    sum_output = ''
                if name in sum_output:
                    sum_split = sum_output.split()
                    proc = subprocess.Popen(['libra',
                                             '--insecure',
                                             '--os-region-name',
                                             self.region,
                                             'delete', sum_split[1]])
                    sum_output = ''
                    proc.wait()
                    if proc.returncode == 0:
                        self.logger.warning('deleting %s', sum_split[1])
                    else:
                        self.failure = "Return code " + str(proc.returncode)
                        self.logger.error("did not delete lb return code %s",
                                          proc.returncode)
        except Exception as e:
            self.success, self.overall_success = False, True
            self.failure = e
            self.logger.error("<*>delete_lb Failed %s", e)

    @monitoring.timeit
    def delete_cdn_containers(self):
        """
        Description - Delete all containers where name starts with
                        'cdncheck' and all objects in that container
        """
        try:
            self.success = True
            self.cdn_containers = self.cdn_client.get_account()[1]

            if len(self.cdn_containers) == 0:
                self.logger.warning(
                    'No CDN containers to clean up')
                return

            self.cdn_container_names = []
            for i in self.cdn_containers:
                if str(i['name']).startswith('cdncheck'):
                    self.cdn_container_names.append(str(i['name']))

            if len(self.cdn_container_names) == 0:
                self.logger.warning(
                    'No CDN containers (cdncheck string) to delete')
                return

            for self.container_name in self.cdn_container_names:

                try:
                    self.objects = self.swift_client.get_container(
                        self.container_name)[1]
                except Exception:
                    self.logger.warning(
                        "Couldn't retrieve objects for %s", self.container_name)
                    self.logger.warning("Deleting the container directly")
                    self.cdn_client.delete_container(self.container_name)
                    continue

                if len(self.objects) == 0:
                    self.logger.warning(
                        'No objects found for %s', self.container_name)
                    self.logger.warning(
                        'Deleting CDN container %s', self.container_name)
                    self.swift_client.delete_container(self.container_name)
                    self.cdn_client.delete_container(self.container_name)
                    continue

                self.object_names = []
                for i in self.swift_client.get_container(self.container_name)[1]:
                    self.object_names.append(str(i['name']))

                self.logger.warning(
                    'Deleting objects for %s', self.container_name)

                for i in self.object_names:
                    self.logger.warning('    Deleting object %s', i)
                    self.swift_client.delete_object(self.container_name, i)

                self.logger.warning(
                    'Deleting CDN container %s', self.container_name)
                self.swift_client.delete_container(self.container_name)
                self.cdn_client.delete_container(self.container_name)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>delete_cdn_containers Failed %s", e)

    @monitoring.timeit
    def delete_swift_containers(self):
        """
        Description - Delete all containers where name starts with
                        'swiftcheck' and all objects in that container
        """
        try:
            self.success = True
            self.swift_containers = self.swift_client.get_account()[1]
            if len(self.swift_containers) == 0:
                self.logger.warning('No Swift containers to delete')
                return

            self.swift_container_names = []
            for i in self.swift_containers:
                if i['name'].startswith('swiftcheck'):
                    self.swift_container_names.append(str(i['name']))

            for self.container_name in self.swift_container_names:
                self.logger.warning('Container: %s', self.container_name)
                self.objects = self.swift_client.get_container(
                    self.container_name)[1]
                if len(self.objects) == 0:
                    self.logger.warning(
                        'No objects found for %s', self.container_name)
                    self.logger.warning(
                        'Deleting container: %s', self.container_name)
                    self.swift_client.delete_container(self.container_name)
                    continue

                self.object_names = []
                for i in self.swift_client.get_container(self.container_name)[1]:
                    self.object_names.append(str(i['name']))

                self.logger.warning(
                    'Deleting objects for %s', self.container_name)

                for i in self.object_names:
                    self.logger.warning('   Deleting %s', i)
                    self.swift_client.delete_object(self.container_name, i)

                self.logger.warning(
                    'Deleting container: %s', self.container_name)
                self.swift_client.delete_container(self.container_name)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>delete_swift_containers Failed %s", e)

    def delete_domains(self):
        """
        Description - Delete all domains where domain.name contains
                        'OSfunctional'
        """
        try:
            self.logger.warning("Delete Domains")
            for domain in self.designate_client.domains.list():
                if 'OSfunctional' in domain.name:
                    self.logger.warning('Deleting Domain {}'.format(domain.name))
                    self.designate_client.domains.delete(domain.id)
        except Exception as e:
            self.logger.error('<*>Domain Deletion Failed: {}'.format(e))

    def run(self):
        if self.purge_service == "cdn":
            self.delete_cdn_containers()
        elif self.purge_service == "cinder":
            self.delete_snapshots()
            self.delete_volume()
        elif self.purge_service == "domains":
            self.delete_domains()
        elif self.purge_service == "keystone":
            pass
        elif self.purge_service == "libra":
            self.delete_lb()
        elif self.purge_service == "neutron":
            self.delete_floating()
            self.delete_port()
            self.delete_router()
            self.delete_subnet()
            self.delete_network()
        elif self.purge_service == "nova":
            self.delete_instance()
            self.delete_floating()
            self.delete_keypair()
        elif self.purge_service == "swift":
            self.delete_swift_containers()
        elif self.purge_service == "trove":
            self.delete_db()
        else:
            self.logger.error("Invalid service entered")

        if self.overall_success is True:
            exit(0)
        else:
            exit(1)
