import logging

import boto3
from utils.environment import Environment
from utils.functions import retry_if_exception_for_method
from utils.storages.base import Storage

logger = logging.getLogger(__name__)


STORAGE_RETRY_COUNT = 2
STORAGE_RETRY_SLEEP = 5


class AWSStorage(Storage):

    def __init__(
        self,
        aws_bucket_name: str,
        aws_region: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        environment: Environment,
        namespace: str | None,
    ):
        super(AWSStorage, self).__init__(environment, namespace)
        self.aws_bucket_name = aws_bucket_name
        self.aws_region = aws_region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key

    @retry_if_exception_for_method(STORAGE_RETRY_COUNT, STORAGE_RETRY_SLEEP)
    def upload(self, source: str, output: str):
        logger.info("AWSStorage -> upload('%s', '%s')" % (source, output))
        s3 = boto3.resource(
            's3',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        bucket = s3.Bucket(self.aws_bucket_name)
        bucket.upload_file(source, output)

    def describe(self):
        return '(AWS region: %s, S3 Bucket: %s)' % (self.aws_region, self.aws_bucket_name)
