from health_check.exceptions import ServiceUnavailable
from health_check.storage.backends import StorageHealthCheck

from .base import AbstractHealthCheckBackend


class BaseStorageHealthCheck(StorageHealthCheck, AbstractHealthCheckBackend):
    """Overridden to get more info when error occurs."""

    def check_status(self):
        """Check that we can create, get, and delete files from storage."""
        try:
            file_name = self.get_file_name()
            file_content = self.get_file_content()
            file_name = self.check_save(file_name, file_content)
            self.check_delete(file_name)
        except Exception as e:
            self.add_error(ServiceUnavailable(e), cause=e)


class S3StorageHealthCheck(BaseStorageHealthCheck):
    """Checks that s3 storage is working alright."""
    storage = 'storages.backends.s3boto3.S3Boto3Storage'
    _identifier = 's3_storage'
    _description = 'S3 Storage Health Check'

    def check_delete(self, file_name):
        storage = self.get_storage()
        storage.delete(file_name)
