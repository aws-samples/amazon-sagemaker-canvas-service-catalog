import os
from constructs import Construct
from aws_cdk import (
    CfnParameter, CfnOutput, CustomResource, Duration, Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3 as s3,
    aws_servicecatalog as sc,
)


class BucketProduct(sc.ProductStack):
    def __init__(self, scope: Construct, id: str, bucket_name: str, kms_key: str):
        super().__init__(scope, id)

        # ==================================================
        # ============== CORS CONFIGURATION =================
        # ==================================================
        self.cors_rule = s3.CorsRule(
            allowed_methods=[
                s3.HttpMethods.POST,
                s3.HttpMethods.PUT,
                s3.HttpMethods.GET,
                s3.HttpMethods.HEAD,
                s3.HttpMethods.DELETE
            ],
            allowed_origins=["https://*.sagemaker.aws"],
            allowed_headers=["*"],
            exposed_headers=['ETag', 'x-amz-delete-marker', 'x-amz-id-2', 'x-amz-request-id', 'x-amz-server-side-encryption', 'x-amz-version-id']
        )

        # ==================================================
        # ============== LAMBDA FUNCTION ====================
        # ==================================================
        self.lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "AllowS3Actions": iam.PolicyDocument(statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "s3:PutBucketCors",
                            "s3:GetBucketCors",
                            "s3:CreateBucket",
                            "s3:HeadBucket"
                        ],
                        resources=[f"arn:aws:s3:::{self.bucket_name}", f"arn:aws:s3:::{self.bucket_name}/*"]
                    )
                ])
            }
        )

        self.cors_lambda = _lambda.Function(
            self, "CorsLambda",
            function_name="ApplyCorsConfiguration",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            role=self.lambda_role,
            code=_lambda.Code.from_inline(
                """\
import json
import boto3

def handler(event, context):
    s3 = boto3.client('s3')
    bucket_name = event['BucketName']
    cors_configuration = {
        'CORSRules': [{
            'AllowedMethods': ['POST', 'PUT', 'GET', 'HEAD', 'DELETE'],
            'AllowedOrigins': ['https://*.sagemaker.aws'],
            'AllowedHeaders': ['*'],
            'ExposeHeaders': ['ETag', 'x-amz-delete-marker', 'x-amz-id-2', 'x-amz-request-id', 'x-amz-server-side-encryption', 'x-amz-version-id']
        }]
    }
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} exists. Applying CORS configuration.")
    except s3.exceptions.ClientError:
        print(f"Bucket {bucket_name} does not exist. Creating bucket and applying CORS configuration.")
        s3.create_bucket(Bucket=bucket_name)
    
    s3.put_bucket_cors(
        Bucket=bucket_name,
        CORSConfiguration=cors_configuration
    )
    return {
        'statusCode': 200,
        'body': json.dumps(f"CORS configuration applied to {bucket_name}")
    }"""),
            timeout=Duration.seconds(30)
        )

        # ==================================================
        # ============== APPLY CORS VIA LAMBDA ==============
        # ==================================================
        self.cors_lambda.add_environment("BucketName", self.bucket_name)

        # Trigger the Lambda function to apply CORS configuration
        CfnOutput(self, "TriggerLambda", value=self.cors_lambda.function_arn)

        CustomResource(
            self, "CustomResource",
            service_token=self.cors_lambda.function_arn,
            properties={"BucketName": self.bucket_name}
        )