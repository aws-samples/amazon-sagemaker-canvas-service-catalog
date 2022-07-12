from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    aws_servicecatalog as sc,
    App,
    Stack,
)
from products.domain_product import DomainProduct
from products.canvas_user_product import CanvasUserProduct
from products.scheduled_shutdown_product import ScheduledShutdownProduct
from products.s3_bucket_product import BucketProduct


class SCPortfolioStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ===============================================
        # ============== CREATE PORTFOLIO ==============
        # ===============================================
        canvas_portfolio = sc.Portfolio(
            self,
            id="CanvasPortfolio",
            display_name="Canvas Portfolio",
            description="Portfolio with approved list of Canvas products",
            provider_name="IT Admins",
        )

        # ===============================================
        # =========== CREATE PRODUCTS PORTFOLIO ========
        # ===============================================
        domain_product = sc.CloudFormationProduct(
            self,
            "SCProductDomain",
            product_name="Studio Domain",
            owner="CCOE",
            description="SageMaker Studio Domain for Canvas",
            distributor="CCOE",
            product_versions=[
                sc.CloudFormationProductVersion(
                    product_version_name="v1",
                    cloud_formation_template=sc.CloudFormationTemplate.from_product_stack(
                        DomainProduct(self, "DomainProduct")
                    ),
                )
            ],
        )

        canvas_user_product = sc.CloudFormationProduct(
            self,
            "SCProductCanvasUser",
            product_name="Canvas User",
            owner="CCOE",
            description="SageMaker Studio User Profile for Canvas",
            distributor="CCOE",
            product_versions=[
                sc.CloudFormationProductVersion(
                    product_version_name="v1",
                    cloud_formation_template=sc.CloudFormationTemplate.from_product_stack(
                        CanvasUserProduct(self, "CanvasUserProduct")
                    ),
                )
            ],
        )

        canvas_scheduled_shutdown_product = sc.CloudFormationProduct(
            self,
            "SCProductCanvasScheduledShutdown",
            product_name="Canvas Scheduled Shutdown",
            owner="CCOE",
            description="Scheduled Lambda shutting down Canvas automatically",
            distributor="CCOE",
            product_versions=[
                sc.CloudFormationProductVersion(
                    product_version_name="v1",
                    cloud_formation_template=sc.CloudFormationTemplate.from_product_stack(
                        ScheduledShutdownProduct(
                            self,
                            "CanvasScheduledShutdownProduct"
                        )
                    ),
                )
            ],
        )

        s3_bucket_product = sc.CloudFormationProduct(
            self,
            "SCProductS3Bucket",
            product_name="S3 bucket with CORS",
            owner="CCOE",
            description="Default SageMaker bucket with CORS policy for Canvas",
            distributor="CCOE",
            product_versions=[
                sc.CloudFormationProductVersion(
                    product_version_name="v1",
                    cloud_formation_template=sc.CloudFormationTemplate.from_product_stack(
                        BucketProduct(self, "BucketProduct")
                    ),
                )
            ],
        )

        # ===============================================
        # ======= ASSOCIATE PRODUCTS TO PORTFOLIO ======
        # ===============================================
        canvas_portfolio.add_product(domain_product)
        canvas_portfolio.add_product(canvas_user_product)
        canvas_portfolio.add_product(canvas_scheduled_shutdown_product)
        canvas_portfolio.add_product(s3_bucket_product)

        # ===============================================
        # ========= GRANT ACCESS TO AN IAM ROLE =========
        # ===============================================
        role_arn_access = (
            "<ADD YOUR ROLE ARN FOR PORTFOLIO ACCESS>"  # Replace with your role ARN
        )

        user_role = iam.Role.from_role_arn(self, "Role", role_arn=role_arn_access)
        canvas_portfolio.give_access_to_role(user_role)


app = App()
SCPortfolioStack(app, "SCPortfolioStack")
app.synth()
