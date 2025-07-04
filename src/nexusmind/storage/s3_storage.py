import logging

import boto3
from botocore.exceptions import ClientError

from ..base_config import MinioConfig
from .storage_base import StorageBase

logger = logging.getLogger(__name__)


class S3Storage(StorageBase):
    def __init__(self, config: MinioConfig, s3_client):
        self.config = config
        self.s3_client = s3_client
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
        try:
            self.s3_client.put_object(
                Bucket=self.config.bucket, Key=file_path, Body=content
            )
            logger.info(
                f"File '{file_path}' saved to S3 bucket '{self.config.bucket}'."
            )
            return file_path
        except ClientError as e:
            logger.error(f"Failed to save file '{file_path}' to S3: {e}")
            raise

    def get(self, file_path: str) -> bytes:
        try:
            response = self.s3_client.get_object(
                Bucket=self.config.bucket, Key=file_path
            )
            logger.info(
                f"File '{file_path}' retrieved from S3 bucket '{self.config.bucket}'."
            )
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"Failed to get file '{file_path}' from S3: {e}")
            raise

    def delete(self, file_path: str) -> None:
        pass

    def exists(self, file_path: str) -> bool:
        pass


def get_s3_storage() -> S3Storage:
    # This is a placeholder for dependency injection
    # In a real app, this would get the config from a global registry or context
    config = MinioConfig()
    client_kwargs = {
        "aws_access_key_id": config.access_key,
        "aws_secret_access_key": config.secret_key.get_secret_value(),
        "region_name": "us-east-1",
    }
    if config.endpoint:
        client_kwargs["endpoint_url"] = config.endpoint

    s3_client = boto3.client("s3", **client_kwargs)

    return S3Storage(config=config, s3_client=s3_client)
