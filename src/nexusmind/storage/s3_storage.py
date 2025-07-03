import logging

import boto3
from botocore.exceptions import ClientError

from ..base_config import MinioConfig
from .storage_base import StorageBase

logger = logging.getLogger(__name__)


class S3Storage(StorageBase):
    def __init__(self, config: MinioConfig):
        self.config = config
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.config.access_key,
            aws_secret_access_key=self.config.secret_key.get_secret_value(),
            endpoint_url=self.config.endpoint,
        )
        self._create_bucket_if_not_exists()

    def _create_bucket_if_not_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.config.bucket)
            logger.debug(f"Bucket '{self.config.bucket}' already exists.")
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.info(f"Bucket '{self.config.bucket}' not found. Creating it.")
                self.s3_client.create_bucket(Bucket=self.config.bucket)
            else:
                logger.error(f"Error checking bucket: {e}")
                raise

    def save(self, file_path: str, content: bytes) -> None:
        pass

    def get(self, file_path: str) -> bytes:
        pass

    def delete(self, file_path: str) -> None:
        pass

    def exists(self, file_path: str) -> bool:
        pass


def get_s3_storage() -> S3Storage:
    # This is a placeholder for dependency injection
    # In a real app, this would get the config from a global registry or context
    config = MinioConfig()
    return S3Storage(config=config) 