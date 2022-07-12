from constructs import Construct
from aws_cdk import (
    aws_ssm as ssm,
    aws_servicecatalog as sc,
    aws_sagemaker as sagemaker,
    CfnParameter,
    CfnTag,
)


class CanvasUserProduct(sc.ProductStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # ==================================================
        # ================== PARAMETERS ====================
        # ==================================================
        self.user_name_param = CfnParameter(
            self,
            "UserName",
            type="String",
        )

        self.user_tag_param = CfnParameter(
            self,
            "UserCostCenter",
            type="String",
        )
        # ==================================================
        # ========== GET DOMAIN ID AND ROLE FROM SSM =======
        # ==================================================
        self.domain_id = ssm.StringParameter.value_for_string_parameter(
            self, parameter_name="/studio/domain_id"
        )

        self.user_role = ssm.StringParameter.value_for_string_parameter(
            self, parameter_name="/studio/user_role"
        )

        # ==================================================
        # ================== STUDIO USER ===================
        # ==================================================
        self.user_profile = sagemaker.CfnUserProfile(
            self,
            "CanvasUserProfile",
            domain_id=self.domain_id,
            user_profile_name=self.user_name_param.value_as_string,
            user_settings=sagemaker.CfnUserProfile.UserSettingsProperty(
                execution_role=self.user_role,
            ),
            tags=[CfnTag(key="cost-center", value=self.user_tag_param.value_as_string)],
        )
