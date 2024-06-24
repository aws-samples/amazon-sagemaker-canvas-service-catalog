from constructs import Construct
from aws_cdk import (
    Stack,
    aws_iam as iam, 
    aws_ssm as ssm,
)
import os


class IAMRole(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # Get Region and Account ID from stack
        self.account_id = Stack.of(self).account
        self.aws_region = Stack.of(self).region

        # ==================================================
        # =================== IAM ROLE =====================
        # ==================================================
        self.kms_policy = iam.Policy(
            self,
            "KMSPolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:CreateGrant",
                        "kms:Decrypt",
                        "kms:DescribeKey",
                        "kms:Encrypt",
                        "kms:ReEncrypt",
                        "kms:GenerateDataKey",
                    ],
                    resources=["*"],
                )
            ],
        )

        self.role = iam.Role(self, f"CanvasExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerCanvasFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerCanvasDataPrepFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerCanvasBedrockAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerCanvasAIServicesAccess"),
                iam.ManagedPolicy.from_managed_policy_arn(
                    self, "direct-deployment-managed-policy",
                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AmazonSageMakerCanvasDirectDeployAccess"
                )
            ],
            inline_policies={
                "canvasPolicy": iam.PolicyDocument(statements=[
                    iam.PolicyStatement(sid="SageMakerUserAndAppsDetails",
                                        effect=iam.Effect.ALLOW,
                                        actions=[
                                            "sagemaker:DescribeApp",
                                            "sagemaker:DescribeDomain",
                                            "sagemaker:DescribeSpace",
                                            "sagemaker:DescribeUserProfile",
                                            "sagemaker:ListUserProfiles",
                                            "sagemaker:ListApps",
                                            "sagemaker:ListDomains",
                                            "sagemaker:ListSpaces",
                                            "sagemaker:ListTags",
                                            "sagemaker:ListUserProfiles",
                                        ],
                                        resources=["*"]
                    ),
                    iam.PolicyStatement(sid="SageMakerAppPermissions",
                                        effect=iam.Effect.ALLOW,
                                        actions=[
                                            "sagemaker:CreateApp",
                                            "sagemaker:DeleteApp",
                                        ],
                                        resources=[
                                            f"arn:aws:sagemaker:{self.aws_region}:{self.account_id}:app/*/*/Canvas/*",
                                            f"arn:aws:sagemaker:{self.aws_region}:{self.account_id}:app/*/*/canvas/*",
                                        ],
                                        conditions={
                                            "Null": {"sagemaker:OwnerUserProfileArn": "true"}
                                        }),
                    iam.PolicyStatement(sid="SMStudioAppPermissionsTagOnCreate",
                                        effect=iam.Effect.ALLOW,
                                        actions=["sagemaker:AddTags"],
                                        resources=[f"arn:aws:sagemaker:{self.aws_region}:{self.account_id}:*/*"],
                                        conditions={
                                            "Null": {
                                                "sagemaker:TaggingAction": "false"
                                            }
                                        }
                    ),
                    iam.PolicyStatement(sid="PutMetricData",
                        effect=iam.Effect.ALLOW,
                        actions=["cloudwatch:PutMetricData"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(sid="S3Permissions",
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "s3:ListBucket",
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject",
                            "s3:GetObjectVersion",
                            "s3:GetBucketCors",
                            "s3:GetBucketLocation",
                            "s3:AbortMultipartUpload"
                        ],
                        resources=[
                            "arn:aws:s3:::sagemaker-*",
                            "arn:aws:s3:::sagemaker-*/canvas",
                            "arn:aws:s3:::sagemaker-*/canvas/*",
                            "arn:aws:s3:::sagemaker-*/Canvas",
                            "arn:aws:s3:::sagemaker-*/Canvas/*",
                            "arn:aws:s3:::*SageMaker*",
                            "arn:aws:s3:::*Sagemaker*",
                            "arn:aws:s3:::*sagemaker*",
                        ]
                    ),
                    iam.PolicyStatement(sid="SecurityAndNetworking",
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "ec2:DescribeNetworkInterfaces",
                            "ec2:DescribeSubnets",
                            "ec2:DescribeSecurityGroups",
                            "ec2:DescribeVpcs",
                            "ec2:DescribeVpcEndpoints",
                            "ec2:DescribeVpcEndpointServices",
                            "ec2:DescribeRouteTables",
                            "kms:ListAliases"
                        ],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(sid="KMSKeyPermission",
                                        effect=iam.Effect.ALLOW,
                                        actions=[
                                            "kms:Encrypt",
                                            "kms:Decrypt",
                                            "kms:DescribeKey"
                                        ],
                                        resources=["arn:aws:kms:*:*:key/*"]
                    )
                ])
            }
        )

        self.kms_policy.attach_to_role(self.role)

        # ==================================================
        # ================ SSM PARAMETERS ==================
        # ==================================================
        ssm.StringParameter(
            self,
            "StudioUserRole",
            parameter_name="/studio/user_role",
            string_value=self.role.role_arn,
        )
