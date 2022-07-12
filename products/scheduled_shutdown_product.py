from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    aws_ecr as ecr,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_servicecatalog as sc,
    CfnParameter,
    Duration,
)


class ScheduledShutdownProduct(sc.ProductStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # ==================================================
        # ================== PARAMETERS ====================
        # ==================================================
        self.chron_scheduling_expression = CfnParameter(
            self,
            "CronSchedulingExpression",
            type="String",
            default="cron(0 18 * * ? *)",
        )

        # ==================================================
        # ================= IAM ROLE =======================
        # ==================================================
        self.role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal(service="lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambdaExecute")
            ],
        )

        self.sagemaker_policy = iam.Policy(
            self,
            "CanvasShutdownPolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "sagemaker:DeleteApp",
                        "sagemaker:ListApps",
                    ],
                    resources=["*"],
                )
            ],
        )
        self.sagemaker_policy.attach_to_role(self.role)

        # ==================================================
        # ================ LAMBDA FUNCTION =================
        # ==================================================
        self.lambda_function = lambda_.Function(
            self,
            "ShutDownCanvasLambda",
            function_name="canvas-scheduled-shutdown",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_inline(open('lambda_images/shutdown/shutdown.py').read()),
            handler="shutdown.lambda_handler",
            memory_size=128,
            role=self.role,
            timeout=Duration.seconds(300),
        )
        # ==================================================
        # ================== SCHEDULING ====================
        # ==================================================
        self.cron_rule = events.Rule(
            self,
            "CronRule",
            rule_name="scheduled-shutdown-canvas",
            schedule=events.Schedule.expression(
                self.chron_scheduling_expression.value_as_string
            ),
        )

        self.cron_rule.add_target(target=targets.LambdaFunction(self.lambda_function))
