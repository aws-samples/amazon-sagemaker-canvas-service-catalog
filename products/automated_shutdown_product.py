from aws_cdk import (
    CfnParameter, Fn, Duration, CfnTag, Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch,
    aws_ssm as ssm,
    aws_servicecatalog as sc,
)
from constructs import Construct

class AutoShutdownProduct(sc.ProductStack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        region = Stack.of(self).region
        account = Stack.of(self).account

        # ==================================================
        # ================== PARAMETERS ====================
        # ==================================================
        self.idle_timeout = CfnParameter(self, "IdleTimeout", 
            type="Number",
            description="Time (in seconds) that the SageMaker Canvas app is allowed to stay in idle before gets shutdown. Default value is 2 hours.",
            default=7200
        )

        self.alarm_period = CfnParameter(self, "AlarmPeriod", 
            type="Number",
            description="Aggregation time (in seconds) used by CloudWatch Alarm to compute the idle timeout. Default value is 20 minutes.",
            default=1200
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
        # ================= RESOURCES ======================
        # ==================================================

        # Lambda Execution Role
        self.lambda_execution_role = iam.Role(self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "LambdaPolicy": iam.PolicyDocument(statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                            "cloudwatch:GetMetricData",
                        ],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "sagemaker:DeleteApp",
                            "sagemaker:DescribeApp",
                        ],
                        resources=[
                            f"arn:aws:sagemaker:{region}:{account}:app/{self.domain_id}/*/canvas/default"
                        ]
                    )
                ])
            }
        )

        # Lambda Function
        self.delete_canvas_app_function = _lambda.Function(self, "DeleteCanvasAppFunction",
            function_name="DeleteCanvasApp",
            handler="index.lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(30),
            memory_size=128,
            reserved_concurrent_executions=1,
            role=self.lambda_execution_role,
            code=_lambda.Code.from_inline(
                """
import boto3
from botocore.config import Config
import os
import datetime

def lambda_handler(event, context):
    region = event['region']
    
    try:
        config = Config(region_name=region)
        cloudwatch = boto3.client('cloudwatch', config=config)
        sagemaker = boto3.client('sagemaker', config=config)
        # Check which user is in timeout
        metric_data_results = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    "Id": "q1",
                    "Expression": f'SELECT AVG(TimeSinceLastActive) FROM "/aws/sagemaker/Canvas/AppActivity" WHERE DomainId=\'{os.environ['DOMAIN_ID']}\' GROUP BY DomainId, UserProfileName',
                    "Period": int(os.environ['ALARM_PERIOD'])
                }
            ],
            StartTime=datetime.datetime(2023, 10, 20),
            EndTime=datetime.datetime.now(),
            ScanBy='TimestampAscending'
        )
        for metric in metric_data_results['MetricDataResults']:
            domain_id, user_profile_name = metric['Label'].split(' ')
            latest_value = metric['Values'][-1]
            if latest_value >= int(os.environ['TIMEOUT_THRESHOLD']):
                status = sagemaker.describe_app(
                    DomainId=domain_id,
                    UserProfileName=user_profile_name,
                    AppType='Canvas',
                    AppName='default'
                )['Status'] # Possible options: 'Deleted'|'Deleting'|'Failed'|'InService'|'Pending'
                if status == 'InService':
                    print(f"Canvas App for {user_profile_name} in domain {domain_id} will be deleted.")
                    response = sagemaker.delete_app(
                        DomainId=domain_id,
                        UserProfileName=user_profile_name,
                        AppType='Canvas',
                        AppName='default'
                    )
                else:
                    print(f"Canvas App for {user_profile_name} in domain {domain_id} is in {status} status. Will not delete for now.")
                    continue
    except Exception as e:
        print(str(e))
        raise e
                """
            ),
            environment={
                "TIMEOUT_THRESHOLD": self.idle_timeout.value_as_string,
                "ALARM_PERIOD": self.alarm_period.value_as_string,
                "DOMAIN_ID": self.domain_id
            }
        )

        # CloudWatch Alarm
        self.time_since_last_active_alarm = cloudwatch.CfnAlarm(
            self, "TimeSinceLastActiveAlarm",
            alarm_name="TimeSinceLastActiveAlarm",
            alarm_description="Alarm when TimeSinceLastActive exceeds 2 hours",
            evaluation_periods=1,
            threshold=self.idle_timeout.value_as_number,
            comparison_operator="GreaterThanOrEqualToThreshold",
            treat_missing_data="notBreaching",
            metrics=[
                cloudwatch.CfnAlarm.MetricDataQueryProperty(
                    id="q1",
                    label="Find the highest timeout across all of the user profiles in this domain",
                    expression=f'SELECT MAX(TimeSinceLastActive) FROM "/aws/sagemaker/Canvas/AppActivity" WHERE DomainId=\'{self.domain_id}\'',
                    period=self.alarm_period.value_as_number
                )
            ],
            tags=[CfnTag(key="cost-center", value=self.user_tag_param.value_as_string)],
        )

        # EventBridge Rule
        self.event_bridge_rule = events.Rule(self, "EventBridgeToLambdaRule",
            rule_name="CanvasAutoShutdownRule",
            description="Rule that executes a Lambda function whenever the Alarm is triggered",
            event_bus=events.EventBus.from_event_bus_name(self, "DefaultEventBus", "default"),
            event_pattern=events.EventPattern(
                source=["aws.cloudwatch"],
                detail_type=["CloudWatch Alarm State Change"],
                resources=[self.time_since_last_active_alarm.attr_arn]
            ),
            targets=[targets.LambdaFunction(self.delete_canvas_app_function)],
        )

        # Lambda Permission
        self.lambda_permission = _lambda.CfnPermission(self, "EventBridgeLambdaPermission",
            action="lambda:InvokeFunction",
            function_name=self.delete_canvas_app_function.function_arn,
            principal="events.amazonaws.com",
            source_arn=self.event_bridge_rule.rule_arn
            # Fn.get_att("EventBridgeToLambdaRule", "Arn").to_string()
        )