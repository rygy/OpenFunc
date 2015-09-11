import monitoring
import random

from sys import exit
from time import sleep

from novaclient import exceptions as nova_exceptions


@monitoring.timeit
def select_image(self):
    """
    Description - Pull full list of images except for Blu Age,
                  Partner Image and that contains Ubuntu and
                  then randomly select a image from the list of
                  active images
    """
    try:
        images = []
        for image in self.nova_client.images.list():
            self.success = True
            if 'Windows' not in image.name and \
                'BLU AGE Modernization Cobol2SpringMVC' not in image.name \
                and 'Partner Image' not in image.name \
                and 'HP_LR-PC' not in image.name \
                and 'Ubuntu' in image.name \
                and 'deprecated' not in image.name \
                and 'Rescue' not in image.name \
                    and image.status == "ACTIVE":
                images.append(image)
        self.image = self.nova_client.images.get(random.choice(images))
    except nova_exceptions.NotFound:
        self.logger.error("No Images found")
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>select_image Failed %s", e)


@monitoring.timeit
def create_snapshot_of_volume(self):
    """
    Description - Select the first image with a status of available
                  then using the volume.id and volume.display_name
                  create a snapshot of that volume
    """
    try:
        volumes = self.cinder_client.volumes.list()
        self.logger.warning("Volume")
        for volume in volumes:
            if volume.status == "available":
                self.logger.warning(volume.id + " " +
                                    str(volume.display_name))
                self.snapshot = self.cinder_client.volume_snapshots.create(
                    volume_id=volume.id,
                    force=True,
                    display_name=volume.display_name)
                self.success = True
                break
    except nova_exceptions.OverLimit:
        self.logger.error("Creating Snapshot Failed: Over Quota Limit")
        self.logger.error(
            "Execute cleanup script to remove extra snapshots")
        self.success, self.overall_success = False, False
        self.failure = "Over Quota Limit"
        exit(1)
    except Exception as e:
        self.logger.error(volume.id + " " + volume.display_name)
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>create_snapshot_of_volume Failed %s", e)


@monitoring.timeit
def create_image(self):
    """
    Description - Generate an image from the current self.instance.id
    """
    try:
        image_create = self.nova_client.servers.create_image(
            self.instance.id,
            image_name='TestImage')
        self.success = True

        self.image_new = self.nova_client.images.get(image_create)
        self.logger.warning('Created image: {}'.format(self.image_new.name))

    except nova_exceptions.OverLimit:
        self.logger.error("Creating Image Failed: Over Quota Limit")
        self.logger.error(
            "Execute cleanup script to remove extra images")
        self.success, self.overall_success = False, False
        self.failure = "Over Quota Limit"
        exit(1)

    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>create_image Failed %s", e)


@monitoring.timeit
def delete_image(self):
    """
    Description - Delete the image with for the current self.image
    """
    try:
        self.image_new.delete()
        self.logger.warning('Deleting Image: {}'.format(self.image_new.name))
        self.success = True
    except nova_exceptions.NotFound:
        self.logger.error("No Image found to delete %s", self.image)
        self.success = False
        self.failure = "Not Found"
    except Exception as e:
        self.success = False
        self.failure = e
        self.logger.error("<*>delete_image Failed %s", e)


@monitoring.timeit
def list_images(self):
    """
    Description - Generate a list of all images by image.id
    """
    try:
        self.image_list = self.nova_client.images.list()

        if not self.image_list:
            self.success, self.overall_success = False, False

            return False

        self.success = True

    except nova_exceptions.NotFound:
        self.logger.error("No Images found")
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>list_image Failed %s", e)


@monitoring.timeit
def check_image_status(self):
    """
    Wait for image status to become active
    """

    try:
        for time in range(1, 31):
            sleep(10)
            try:
                check_active = self.nova_client.images.get(self.image_new.id)
            except nova_exceptions.NotFound:
                pass

            self.logger.warning('Image status: {}'.format(check_active.status))

            if check_active.status == u'ACTIVE':
                self.success = True

                return True

        self.success, self.overall_success = False, False
        self.logger.error('<*>Image Status to Active Exceeded {} minutes'.format(str(len(range(1, 31)) * 10 / 60)))
        exit(1)

    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>Error checking image status: {}".format(e))
        exit(1)

@monitoring.timeit
def get_image(self):

    """
    Description - Get image for the current self.image.id
    """
    try:
        self.image_retrieval = self.nova_client.images.get(self.image_new.id)
        self.success = True
    except nova_exceptions.NotFound:
        self.logger.error("No Image found %s", self.image_new.id)
        self.success, self.overall_success = False, False
        self.failure = "Not Found"
    except Exception as e:
        self.success, self.overall_success = False, False
        self.failure = e
        self.logger.error("<*>get_image Failed %s", e)
