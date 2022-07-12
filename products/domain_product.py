from constructs import Construct
from aws_cdk import aws_servicecatalog as sc, aws_sagemaker as sagemaker, aws_ssm as ssm

from studio_constructs.iam_role import IAMRole
from studio_constructs.networking import Networking
from studio_constructs.kms_key import KMSKey


class DomainProduct(sc.ProductStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

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
        # ================= STUDIO DOMAIN ==================
        # ==================================================
        self.studio_domain = sagemaker.CfnDomain(
            self,
            "sagemaker-domain",
            domain_name="domain",
            auth_mode="IAM",
            app_network_access_type="VpcOnly",
            vpc_id=network.vpc_id,
            subnet_ids=network.subnet_ids,
            kms_key_id=kms_key.encryption_key.key_id,
            default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=user_role.role.role_arn, security_groups=[network.sg_id]
            ),
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
