from constructs import Construct
from aws_cdk import (
    Duration, CustomResource, CfnResource, Stack,
    aws_servicecatalog as sc, 
    aws_sagemaker as sagemaker, 
    aws_ssm as ssm,
    aws_iam as iam,
    aws_lambda as lambda_,
)
from studio_constructs.s3 import S3Bucket
from studio_constructs.iam_role import IAMRole
from studio_constructs.networking import Networking
from studio_constructs.kms_key import KMSKey
import os


class DomainProduct(sc.ProductStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # self.account_id = os.environ["CDK_DEFAULT_ACCOUNT"]
        # self.aws_region = os.environ["CDK_DEFAULT_REGION"]
        self.account_id = Stack.of(self).account
        self.aws_region = Stack.of(self).region
        self.bucket_name = f"sagemaker-{self.aws_region}-{self.account_id}" # If you change this, apply it to the Domain

        # ==================================================
        # ================== IAM ROLE ======================
        # ==================================================
        user_role = IAMRole(self, "user_role")

        # ==================================================
        # ================== NETWORKING ====================
        # ==================================================
        network = Networking(self, "vpc")

        # ==================================================
        # =================== KMS KEY ======================
        # ==================================================
        kms_key = KMSKey(self, "key", role_arn=user_role.role.role_arn)

        # ==================================================
        # =================== S3 BUCKET ====================
        # ==================================================
        bucket = S3Bucket(self, "bucket", bucket_name=self.bucket_name, kms_key=kms_key.encryption_key)

        # ==================================================
        # ================= STUDIO DOMAIN ==================
        # ==================================================
        self.studio_domain = sagemaker.CfnDomain(
            self, "sagemaker-domain",
            domain_name="domain",
            auth_mode="IAM",
            app_network_access_type="VpcOnly",
            vpc_id=network.vpc_id,
            subnet_ids=network.subnet_ids,
            kms_key_id=kms_key.encryption_key.key_id,
            default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=user_role.role.role_arn, security_groups=[network.sg_id],
                studio_web_portal="ENABLED", default_landing_uri="studio::",
                sharing_settings=sagemaker.CfnDomain.SharingSettingsProperty(
                    notebook_output_option="Allowed",
                    s3_output_path=f"s3://{bucket.bucket.bucket_name}/shared-notebooks/",
                    s3_kms_key_id=kms_key.encryption_key.key_id,
                ),
            ),
        )
        # SageMaker Canvas configuration not available via CloudFormation
        self.custom_settings_canvas_role = iam.Role(self, "CustomSettingsCanvas",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "SageMakerCanvasExtraSettingsPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["sagemaker:UpdateDomain"],
                            resources=[self.studio_domain.attr_domain_arn]
                        )
                    ]
                ),
                "PassRole": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["iam:PassRole"],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        self.enable_canvas_settings_lambda = lambda_.Function(self, "EnableCanvasSettingsLambda",
            function_name="CFEnableSagemakerCanvasSettings",
            code=lambda_.InlineCode("""\
import json
import boto3
import cfnresponse

client = boto3.client('sagemaker')

def lambda_handler(event, context):
    response_status = cfnresponse.SUCCESS
    sagemaker_domain_id = event['ResourceProperties']['SageMakerDomainId']
    sagemaker_execution_role = event['ResourceProperties']['SageMakerExecutionRoleARN']
    canvas_bucket_artifacts = event['ResourceProperties']['CanvasBucketName']

    if 'RequestType' in event and event['RequestType'] == 'Create':
        client.update_domain(
            DomainId=sagemaker_domain_id,
            DefaultUserSettings={
                'CanvasAppSettings': {
                    'WorkspaceSettings': {'S3ArtifactPath': f's3://{canvas_bucket_artifacts}/'},
                    'TimeSeriesForecastingSettings': {'Status': 'ENABLED'},
                    'ModelRegisterSettings': {'Status': 'ENABLED'},
                    'DirectDeploySettings': {'Status': 'ENABLED'},
                    'KendraSettings': {'Status': 'DISABLED'}, # Change to ENABLED when you want to use Kendra for RAG
                    'GenerativeAiSettings': {'AmazonBedrockRoleArn':sagemaker_execution_role},
                    # Uncomment and modify the below if you need to add OAuth for Salesforce or Snowflake
                    # 'IdentityProviderOAuthSettings': [
                    #     {
                    #         'DataSourceName': 'SalesforceGenie'|'Snowflake',
                    #         'Status': 'ENABLED'|'DISABLED',
                    #         'SecretArn': 'string'
                    #     },
                    # ],
                }
            }
        )
    cfnresponse.send(event, context, response_status, {}, '')"""
            ),
            description="Enable SageMaker Canvas Settings",
            handler="index.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            memory_size=128,
            timeout=Duration.seconds(30),
            role=self.custom_settings_canvas_role
        )
        CustomResource(self, "EnableCanvasSettings",
            service_token=self.enable_canvas_settings_lambda.function_arn,
            properties={
                "SageMakerDomainId": self.studio_domain.attr_domain_id,
                "SageMakerExecutionRoleARN": user_role.role.role_arn,
                "CanvasBucketName": bucket.bucket.bucket_name,
            }
        )


        # ==================================================
        # ================ SSM PARAMETERS ==================
        # ==================================================
        ssm.StringParameter(
            self,
            "StudioDomainID",
            parameter_name="/studio/domain_id",
            string_value=self.studio_domain.attr_domain_id,
        )
