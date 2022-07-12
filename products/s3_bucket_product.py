import os
from constructs import Construct
from aws_cdk import aws_servicecatalog as sc, aws_s3 as s3, aws_ssm as ssm


class BucketProduct(sc.ProductStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        self.account_id = os.environ["CDK_DEFAULT_ACCOUNT"]
        self.aws_region = os.environ["CDK_DEFAULT_REGION"]
        self.bucket_name = f"sagemaker-{self.aws_region}-{self.account_id}"

        # ==================================================
        # ========== GET DOMAIN ID AND ROLE FROM SSM =======
        # ==================================================
        self.domain_id = ssm.StringParameter.value_for_string_parameter(
            self, parameter_name="/studio/domain_id"
        )

        # ==================================================
        # ================== CORS BUCKET ===================
        # ==================================================
        self.cors_rule = s3.CorsRule(
            allowed_methods=[s3.HttpMethods.POST],
            allowed_origins=[
                f"https://{self.domain_id}.studio.{self.aws_region}.sagemaker.aws"
            ],
            exposed_headers=[],
        )

        self.bucket = s3.Bucket(
            self, "Bucket", bucket_name=self.bucket_name, cors=[self.cors_rule]
        )
