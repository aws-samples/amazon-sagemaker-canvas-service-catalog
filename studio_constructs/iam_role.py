from constructs import Construct
from aws_cdk import aws_iam as iam, aws_ssm as ssm


class IAMRole(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

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

        self.role = iam.Role(
            self,
            "CanvasUserRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
            ],
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
