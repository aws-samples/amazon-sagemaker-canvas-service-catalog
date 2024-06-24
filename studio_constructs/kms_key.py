from constructs import Construct
from aws_cdk import (
    aws_kms as kms, aws_iam as iam,
    Stack
)


class KMSKey(Construct):
    def __init__(self, scope: Construct, id: str, role_arn: str):
        super().__init__(scope, id)

        # ==================================================
        # =================== KMS KEY ======================
        # ==================================================
        self.canvas_user_role = iam.Role.from_role_arn(self, "TrustedRole", role_arn)

        # Creates a limited admin policy and assigns to the account root.
        self.custom_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey",
                    ],
                    principals=[self.canvas_user_role],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    actions=["kms:CreateGrant", "kms:ListGrants", "kms:RevokeGrant"],
                    principals=[self.canvas_user_role],
                    resources=["*"],
                    # conditions={"kms:GrantIsForAWSResource": True},
                ),
                iam.PolicyStatement(
                    actions=[
                        "kms:*",
                    ],
                    principals=[iam.AccountRootPrincipal()],
                    resources=["*"],
                ),
            ]
        )

        self.encryption_key = kms.Key(
            self,
            "KMSKey",
            description="key used to encrypt the SageMaker Studio EFS volume",
            policy=self.custom_policy,
        )
