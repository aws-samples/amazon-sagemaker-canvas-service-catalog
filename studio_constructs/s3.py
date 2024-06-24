from constructs import Construct
from aws_cdk import (
    aws_s3 as s3,
    aws_kms as kms,
)
import os


class S3Bucket(Construct):
    def __init__(self, scope: Construct, id: str, bucket_name: str, kms_key: kms.Key):
        super().__init__(scope, id)

        # ==================================================
        # ================== CORS BUCKET ===================
        # ==================================================
        self.cors_rule = s3.CorsRule(
            allowed_methods=[
                s3.HttpMethods.POST,
                s3.HttpMethods.PUT, 
                s3.HttpMethods.GET, 
                s3.HttpMethods.HEAD, 
                s3.HttpMethods.DELETE,
            ],
            allowed_origins=["https://*.sagemaker.aws"],
            allowed_headers=["*"],
            exposed_headers=[
                'ETag', 
                'x-amz-delete-marker', 
                'x-amz-id-2', 
                'x-amz-request-id', 
                'x-amz-server-side-encryption', 
                'x-amz-version-id'
            ],
        )

        self.bucket = s3.Bucket(
            self, "Bucket", bucket_name=bucket_name, cors=[self.cors_rule],
            encryption=s3.BucketEncryption.KMS,
            encryption_key=kms_key,
        )