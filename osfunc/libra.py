from libraclient.v1_1 import client as libra_client
from subprocess import PIPE
from time import sleep

import subprocess
import monitoring


class LibraCheck:
    """
    Description - This is the basic workflow of the Libra script.  This
                  script tests the basic functions of loadbalancer.  Each
                  step builds for the next step(s)

        list_lb
        create_lb
        check_status
        update_lb
        node_list_lb
        check_status
        node_create_lb
        check_status
        node_update_lb
        node_delete_lb
        monitor_show
        monitor_update
        monitor_delete
        delete_lb
    """

    def __init__(self, logger, exec_time, **kwargs):
        self.libra_client = libra_client.LoadBalancerManager(
            kwargs['os_tenant_name']
        )

        # Setup logging
        self.logger = logger
        self.exec_time = exec_time
        self.region = str(kwargs['os_region'])
        self.zone = kwargs['os_zone']
        self.service = 'Load Balancing'
        self.failure = None
        self.overall_success = True
        self.tenant_name = kwargs['os_tenant_name']

    @monitoring.timeit
    def list_lb(self):
        """
        Description - Creates a list of loadbalancers for the current
                      tenant
        """
        try:
            self.success = True
            proc = subprocess.Popen(['libra', '--insecure', '--os-region-name',
                                    self.region, 'list'])
            proc.wait()
            if proc.returncode == 0:
                self.success = True
            else:
                self.success, self.overall_success = False, False
                self.failure = "Return code " + str(proc.returncode)
                self.logger.error(
                    "<*>list_lb Failed return code %s", proc.returncode)

        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>list_lb Failed %s", e)

    @monitoring.timeit
    def create_lb(self):
        """
        Description - Creates a loadbalancer using the values provided
                      below
        """
        name = "TestLB"
        port = "443"
        protocol = "TCP"
        algorithm = "ROUND_ROBIN"
        node = "15.125.5.8:443"
        try:
            self.success = True
            proc = subprocess.Popen(['libra',
                                     '--insecure',
                                     '--os-region-name', self.region,
                                     'create',
                                     '--name', name,
                                     '--port', port,
                                     '--protocol', protocol,
                                     '--algorithm', algorithm,
                                     '--node', node], stdout=PIPE)
            proc.wait()
            outs, err = proc.communicate()
            sum_output = ''
            for lists in outs:
                sum_output = sum_output + lists
                if lists == '\n':
                    if "Id" in sum_output:
                        sum_split = sum_output.split()
                        self.lb_id = sum_split[3]
                        sum_output = ""
                    else:
                        sum_output = ""
            if proc.returncode == 0:
                self.success = True
            else:
                self.success, self.overall_success = False, False
                self.failure = "Return code " + str(proc.returncode)
                self.logger.error("<*>create_lb Failed return code %s",
                                  proc.returncode)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>create_lb Failed %s", e)

    @monitoring.timeit
    def check_status(self):
        """
        Description - Wait for newly created instance to change to active
                       or degraded status or to fail
        """
        self.lb_status = ""
        for x in range(1, 30):
            try:
                self.success = True
                proc = subprocess.Popen(['libra',
                                         '--insecure',
                                         '--os-region-name', self.region,
                                         'show', self.lb_id], stdout=PIPE)
                proc.wait()
                outs, err = proc.communicate()
                sum_output = ''
                for lists in outs:
                    sum_output = sum_output + lists
                    if lists == '\n':
                        if "Status" in sum_output:
                            sum_split = sum_output.split()
                            self.lb_status = sum_split[3]
                            self.logger.warning("Status %s", self.lb_status)
                            sum_output = ""
                        else:
                            sum_output = ""
                        if self.lb_status == "ACTIVE" or \
                            self.lb_status == "DEGRADED":
                                return True
                sleep(15)
            except Exception as e:
                self.success, self.overall_success = False, False
                self.failure = e
                self.logger.error("<*>check_status Failed %s", e)
                exit(1)

        self.success, self.overall_success = False, False
        self.logger.error("<*>check_status timed out")
        exit(1)

    @monitoring.timeit
    def delete_lb(self):
        try:
            proc = subprocess.Popen(['libra', '--insecure',
                                     '--os-region-name', self.region,
                                     'delete', self.lb_id])
            proc.wait()
            if proc.returncode == 0:
                self.success = True
            else:
                self.success, self.overall_success = False, False
                self.failure = "Return code " + str(proc.returncode)
                self.logger.error("<*>delete_lb Failed return code %s",
                                  proc.returncode)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>delete_lb Failed %s", e)

    @monitoring.timeit
    def update_lb(self):
        """
        Description - Updates the algorithm value the loadbalancer matching
                      self.lb_id
        """
        algorithm = "LEAST_CONNECTIONS"
        try:
            self.success = True
            proc = subprocess.Popen(['libra', '--insecure',
                                     '--os-region-name', self.region,
                                     'update', '--algorithm',
                                     algorithm, self.lb_id])
            proc.wait()
            if proc.returncode == 0:
                self.success = True
            else:
                self.success, self.overall_success = False, False
                self.failure = "Return code " + str(proc.returncode)
                self.logger.error("<*>update_lb Failed return code %s",
                                  proc.returncode)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>update_lb Failed %s", e)

    @monitoring.timeit
    def node_list_lb(self):
        try:
            proc = subprocess.Popen(['libra', '--insecure',
                                     '--os-region-name', self.region,
                                     'node-list', self.lb_id])
            proc.wait()
            if proc.returncode == 0:
                self.success = True
            else:
                self.success, self.overall_success = False, False
                self.failure = "Return code " + str(proc.returncode)
                self.logger.error("<*>node_list_lb Failed return code %s",
                                  proc.returncode)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>node_list_lb Failed %s", e)

    @monitoring.timeit
    def node_create_lb(self):
        """
        Description - Creates a node on the loadbalancer self.lb_id
        """
        try:
            proc = subprocess.Popen(
                ['libra', '--insecure', '--os-region-name', self.region,
                 'node-create', '--node',
                 '15.125.5.9:443', self.lb_id], stdout=PIPE)
            proc.wait()
            if proc.returncode == 0:
                self.success = True
            else:
                self.success, self.overall_success = False, False
                self.failure = "Return code " + str(proc.returncode)
                self.logger.error("<*>node_create_lb Failed return code %s",
                                  proc.returncode)
                exit(1)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>node_create_lb Failed %s", e)
            exit(1)

    @monitoring.timeit
    def node_delete_lb(self):
        """
        Description - Deletes a node, self.node_id, from the loadbalancer,
                      self.lb_id
        """
        try:
            self.success = True
            proc = subprocess.Popen(['libra', '--insecure',
                                     '--os-region-name', self.region,
                                     'node-list', self.lb_id],
                                    stdout=PIPE)
            proc.wait()
            outs, err = proc.communicate()
            sum_output = ''
            for lists in outs:
                sum_output = sum_output + lists
                if lists == '\n':
                    sum_output = ''
                if '15.125.5.9' in sum_output:
                    sum_split = sum_output.split()
                    self.node_id = sum_split[1]
                    proc = subprocess.Popen(['libra', '--insecure',
                                             '--os-region-name',
                                             self.region, 'node-delete',
                                             self.lb_id, self.node_id])
                    proc.wait()
                    if proc.returncode == 0:
                        self.success = True
                    else:
                        self.success, self.overall_success = False, False
                        self.failure = "Return code " + str(proc.returncode)
                        self.logger.error(
                            "<*>node_delete_lb Failed return code %s",
                            proc.returncode)
                    break
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>node_delete_lb Failed %s", e)

    @monitoring.timeit
    def node_update_lb(self):
        """
        Description - Updates the node, self.node_id, from the loadbalancer,
                      self.lb_id to 'ENABLED'
        """
        try:
            self.success = True
            proc = subprocess.Popen(['libra', '--insecure',
                                     '--os-region-name', self.region,
                                     'node-list', self.lb_id],
                                    stdout=PIPE)
            proc.wait()
            outs, err = proc.communicate()
            sum_output = ''
            for lists in outs:
                sum_output = sum_output + lists
                if lists == '\n':
                    sum_output = ''
                if '15.125.5.9' in sum_output:
                    sum_split = sum_output.split()
                    self.node_id = sum_split[1]
                    proc = subprocess.Popen(
                        ['libra', '--insecure',
                         '--os-region-name', self.region,
                         'node-update', self.lb_id,
                         self.node_id, '--condition', 'ENABLED'])
                    proc.wait()
                    if proc.returncode == 0:
                        self.success = True
                    else:
                        self.success, self.overall_success = False, False
                        self.failure = "Return code " + str(proc.returncode)
                        self.logger.error(
                            "<*>node_update_lb Failed return code %s",
                            proc.returncode)
                    break
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>node_update_lb Failed %s", e)

    @monitoring.timeit
    def monitor_show(self):
        """
        Description - Show the monitoring status for loadbalancer
                      self.lb_id
        """
        try:
            proc = subprocess.Popen(['libra', '--insecure',
                                     '--os-region-name', self.region,
                                     'monitor-show', self.lb_id])
            proc.wait()
            if proc.returncode == 0:
                self.success = True
            else:
                self.success, self.overall_success = False, False
                self.failure = "Return code " + str(proc.returncode)
                self.logger.error("<*>monitor_show_lb Failed return code %s",
                                  proc.returncode)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>monitor_show_lb Failed %s", e)

    @monitoring.timeit
    def monitor_update(self):
        """
        Description - Update the monitoring status for loadbalancer
                      self.lb_id
        """
        try:
            proc = subprocess.Popen(['libra', '--insecure',
                                     '--os-region-name', self.region,
                                     'monitor-update', self.lb_id])
            proc.wait()
            if proc.returncode == 0:
                self.success = True
            else:
                self.success, self.overall_success = False, False
                self.failure = "Return code " + str(proc.returncode)
                self.logger.error(
                    "<*>monitor_update_lb Failed return code %s",
                    proc.returncode)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>monitor_update_lb Failed %s", e)

    @monitoring.timeit
    def monitor_delete(self):
        """
        Description - Delete the monitoring status for loadbalancer
                      self.lb_id and create a new one
        """
        try:
            proc = subprocess.Popen(['libra', '--insecure',
                                     '--os-region-name', self.region,
                                     'monitor-delete', self.lb_id])
            proc.wait()
            if proc.returncode == 0:
                self.success = True
            else:
                self.success, self.overall_success = False, False
                self.failure = "Return code " + str(proc.returncode)
                self.logger.error("<*>monitor_delete_lb Failed return code %s",
                                  proc.returncode)
        except Exception as e:
            self.success, self.overall_success = False, False
            self.failure = e
            self.logger.error("<*>monitor_delete_lb Failed %s", e)

    def run(self):

        self.list_lb()
        self.create_lb()
        self.check_status()
        self.update_lb()
        self.node_list_lb()
        self.check_status()
        self.node_create_lb()
        self.check_status()
        self.node_update_lb()
        self.node_delete_lb()
        self.monitor_show()
        self.monitor_update()
        self.monitor_delete()
        self.delete_lb()
        if self.overall_success is True:
            exit(0)
        else:
            exit(1)
