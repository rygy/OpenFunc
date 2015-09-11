import monitoring
import servers

from time import sleep
from random import choice
from cinderclient import exceptions as cinder_exceptions


@monitoring.timeit
def list_volumes(self):
    """
    Description - Generate a list of all volumes in the specified zone
                  for the tenant
    """
    try:
        volumes = self.cinder_client.volumes.list()
        self.success = True
        self.logger.warning("Listing Volumes")
        for volume in volumes:
            if volume.availability_zone == self.zone:
                self.logger.warning(volume.id + " " +
                                    str(volume.display_name))
    except cinder_exceptions.NotFound:
        self.logger.error("No Volumes found")
        self.success, self.overall_success = False, True
        self.failure = "Not found"
    except Exception as e:
        self.logger.error("Listing Volumes Failed")
        self.logger.error('Got exception: {}'.format(e))
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def list_delete_snapshots(self):
    """
    Description - Generate a list of all snapshots for the tenant and
                  delete all with an available status
    """
    try:
        snapshots = self.cinder_client.volume_snapshots.list()
        self.success = True
        self.logger.warning("Listing snapshots")
        for snapshot in snapshots:
            self.logger.warning(snapshot.id + " " +
                                str(snapshot.display_name))
            if snapshot.status == 'available':
                try:
                    self.logger.warning("deleting snapshot " + snapshot.id)
                    snapshot.delete()
                except Exception as e:
                    self.logger.error("Delete snapshot failed")
                    self.logger.error('Got exception: {}'.format(e))
            else:
                self.logger.error('Cannot delete snapshot in state {}'
                    .format(snapshot.status))
    except cinder_exceptions.NotFound:
        self.logger.error("No Snapshots found")
        self.success, self.overall_success = False, True
        self.failure = "Not found"
    except Exception as e:
        self.logger.error("Listing Snapshots Failed")
        self.success, self.overall_success = False, False
        self.logger.error('Got exception: {}'.format(e))
        self.failure = e


@monitoring.timeit
def list_volume_type(self):
    """
    Description - Generate a list of all volumes types
    """
    try:
        volumes = self.cinder_client.volume_types.list()
        self.success = True
        self.logger.warning("Listing Volume types")
        for volume in volumes:
                self.logger.warning(volume.id + " " +
                                    str(volume.name))
    except cinder_exceptions.NotFound:
        self.logger.error("No Volume types found")
        self.success, self.overall_success = False, True
        self.failure = "Not found"
    except Exception as e:
        self.logger.error("Listing Volume Types Failed")
        self.logger.error('Got exception: {}'.format(e))
        self.success, self.overall_success = False, False
        self.failure = e


@monitoring.timeit
def delete_available(self):
    """
    Description - Delete all volumes for the tenant in the zone with a status
                  of available and a display name containing cindercheck
    """
    volumes = self.cinder_client.volumes.list()
    try:
        for volume in volumes:
            self.success = True
            if volume.availability_zone == self.zone:
                if 'cindercheck' in volume.display_name:
                    if self.cinder_client.volumes.get(volume.id).status\
                            == 'available':
                        self.logger.warning('Deleting unused volume: %s' %
                                            volume.id)
                        volume.delete()
    except cinder_exceptions.NotFound:
        self.logger.error("No Volumes found to delete")
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
    except Exception as e:
        self.logger.warning(
            'Caught exception trying to delete old volumes: %s' % e)
        self.success, self.overall_success = False, False
        self.logger.error('Got exception: {}'.format(e))
        self.failure = e


@monitoring.timeit
def create_volume(self):
    """
    Description - Create a volume using the selected values
                    Type '1'
                    display name 'cindercheck'
                    zone self.zone
                  Generate self.volume.id
    """
    try:
        volume = self.cinder_client.volumes.create(
            "1",
            display_name="cindercheck",
            availability_zone=self.zone)
        self.logger.warning("Created Volume %s", volume.id)
        self.volume = volume
        self.success = True
    except cinder_exceptions.OverLimit:
        self.logger.error("Creating Volume Failed: Over Quota Limit")
        self.logger.error(
            "Execute cleanup script to remove extra volumes")
        self.success, self.overall_success = False, False
        self.failure = "Over Quota Limit"
        exit(1)

    except Exception as e:
        self.logger.error('Creating Volume Failed')
        self.logger.error('Got exception: {}'.format(e))
        self.success, self.overall_success = False, False
        self.failure = e
        exit(1)


@monitoring.timeit
def create_with_image(self):
    """
    Description - Create a volume using the selected values
                    Type '1'
                    display name 'cindercheck'
                    zone self.zone
                    imageRef self.image.id
                  Generate self.volume.id
    """
    try:
        volume = self.cinder_client.volumes.create(
            "30",
            display_name="cindercheck",
            imageRef=self.image.id,
            availability_zone=self.zone)
        self.logger.warning("Created Volume with image %s", volume.id)
        self.volume = volume
        self.success = True
    except cinder_exceptions.OverLimit:
        self.logger.error("Creating Volume with image Failed: Over Quota")
        self.success, self.overall_success = False, False
        self.failure = "Over Quota Limit"
        self.logger.error("execute cleanup script to remove extra volumes")
        exit(1)

    except Exception as e:
        self.logger.error('Creating Volume with image Failed:')
        self.logger.error('Got exception: {}'.format(e))
        self.success, self.overall_success = False, False
        self.failure = e
        exit(1)


@monitoring.timeit
def check_available(self):
    """
    Description - Wait for newly created volume to change to active
                   status or to fail
    """
    try:
        for x in range(1, 20):
            status = self.cinder_client.volumes.get(self.volume.id).status
            self.logger.warning("Status %s", status)
            if status == 'available':
                self.logger.warning("Volume Is Available")
                self.success = True
                return True
            if status == 'error':
                self.loffer.warning("Volume is in error state")
                self.success, self.overall_success = False, False
                return True
            sleep(15)
    except cinder_exceptions.NotFound:
        self.logger.error("404 volume not found %s", self.volume.id)
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
        exit(1)
    except Exception as e:
        self.logger.error('Check_available volume Failed: %s' % e)
        self.success, self.overall_success = False, False
        self.failure = e
        exit(1)
    self.logger.error("Volume Never Became Available - Timeout")
    self.success, self.overall_success = False, False
    self.failure = "Volume Never Became Available - Timeout"
    exit(1)


@monitoring.timeit
def attach_volume(self):
    """
    Description - Attach volume to a instance using the values
                    self.instance.id
                    self.volume.id

                  After the volume is attached wait for the status to
                  change to in-use or fail or time-out
    """
    sleep(5)
    try:
        device_list = []
        device_path = 'cdefghijklmnopqrstuvwxyz'
        for volume in self.nova_client.volumes.get_server_volumes(
                self.instance.id):
            device_list.append(volume.device)
        device = '/dev/sd%s' % choice(device_path)
        self.logger.warning("Using Device %s", device)
        try:
            self.nova_client.volumes.create_server_volume(
                self.instance.id, self.volume.id, device)
            self.success = True
        except cinder_exceptions.ClientException as e:
            self.logger.warning(e)
            device = '/dev/sd%s' % \
                choice(device_path.strip(device.split()[-1]))
            try:
                self.nova_client.volumes.create_server_volume(
                    self.instance.id, self.volume.id, device)
                self.success = True
            except Exception as e:
                self.logger.error("Volume attach failed ")
                self.logger.error('Got exception: {}'.format(e))
                self.success, self.overall_success = False, False
                self.failure = e
                servers.delete_instance(self)
                self.delete_volume()
                self.logger.error("Deleting volume")
                exit(1)
        try:
            for x in range(1, 20):
                sleep(10)
                self.logger.warning('Volume Status: %s' %
                                    str(self.cinder_client.volumes.get(
                                        self.volume.id).status))
                if self.cinder_client.volumes.get(self.volume.id).status == \
                        'in-use':
                    self.logger.warning("Volume Is Attached")
                    self.success = True
                    return True
                if self.cinder_client.volumes.get(self.volume.id).status == \
                        'error':
                    self.logger.warning("Volume Is In Error State")
                    self.success, self.overall_success = False, False
                    servers.delete_instance(self)
                    self.delete_volume()
                    self.logger.error("Deleting volume")
                    exit(1)
        except cinder_exceptions.NotFound:
            self.logger.error("404 volume not found %s", self.volume.id)
            self.success, self.overall_success = False, False
            self.failure = "Not Found"
            servers.delete_instance(self)
            self.delete_volume()
            self.logger.error("Deleting volume")
            exit(1)
        self.logger.error("Volume Attach Timed out")
        self.success, self.overall_success = False, False
        self.failure = "Volume Attach Timed Out"
        servers.delete_instance(self)
        self.delete_volume()
        self.logger.error("Deleting volume")
        exit(1)
    except Exception as e:
        self.logger.warning("Volume Attachment Failed ")
        self.logger.error('Got exception: {}'.format(e))
        self.success, self.overall_success = False, False
        self.failure = e
        servers.delete_instance(self)
        exit(1)


@monitoring.timeit
def detach_volume(self):
    """
    Description - Detach volume from an instance using the values
                    self.instance.id
                    self.volume.id

                  After the volume is detached wait for the status to
                  change to available, fail or time-out
    """
    sleep(5)
    try:
        self.nova_client.volumes.delete_server_volume(
            self.instance.id, self.volume.id)
        for x in range(1, 10):
            sleep(5)
            if self.cinder_client.volumes.get(self.volume.id).status == \
                    'available':
                self.logger.warning("Volume Detached")
                self.success = True
                return True

        self.logger.warning("Volume Detach Timed Out")
        self.success, self.overall_success = False, False
        self.failure = "Volume Detach Time Out"
        servers.delete_instance(self)
        self.delete_volume()
        self.logger.error("Deleting volume")
        exit(1)
    except cinder_exceptions.NotFound:
        self.logger.error("404 volume not found detach failed %s",
                          self.volume.id)
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
        servers.delete_instance(self)
        self.delete_volume()
        self.logger.error("Deleting volume")
        exit(1)
    except Exception as e:
        self.logger.warning("Volume Detach Failed")
        self.logger.error('Got exception: {}'.format(e))
        self.success, self.overall_success = False, False
        self.failure = e
        servers.delete_instance(self)
        self.delete_volume()
        self.logger.error("Deleting volume")
        exit(1)


@monitoring.timeit
def delete_volume(self):
    """
    Description - Delete last volume accessed
    """
    sleep(5)
    try:
        self.volume.delete()
        self.logger.warning("Volume Deleted")
        self.success = True
        return True

    except cinder_exceptions.NotFound:
        self.logger.error("404 volume not found delete failed %s",
                          self.volume.id)
        self.success, self.overall_success = False, True
        self.failure = "Not Found"

    except cinder_exceptions.BadRequest:
        self.logger.error(
            'Volume is not available for deletion due to status {}'
            .format(self.volume.status))
        self.success = False

    except Exception as e:
        self.logger.error("Volume Deletion Failed")
        self.logger.error('Got exception: {}'.format(e))
        self.success, self.overall_success = False, True
        self.failure = e
