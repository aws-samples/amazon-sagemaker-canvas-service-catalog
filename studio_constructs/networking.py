import os
from constructs import Construct
from aws_cdk import aws_ec2 as ec2


class Networking(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # ==================================================
        # ===================== VPC ========================
        # ==================================================
        self.region = os.environ["CDK_DEFAULT_REGION"]

        self.vpc = ec2.Vpc(
            self,
            "DomainVPC",
            cidr="10.0.0.0/16",
            max_azs=3,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=26
                ),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
            nat_gateways=1,
        )

        self.vpc.add_gateway_endpoint(
            "S3Endpoint", service=ec2.GatewayVpcEndpointAwsService.S3
        )
        self.vpc.add_interface_endpoint(
            "KMSEndpoint", service=ec2.InterfaceVpcEndpointAwsService.KMS
        )
        self.vpc.add_interface_endpoint(
            "ECREndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR
        )
        self.vpc.add_interface_endpoint(
            "ECRDockerEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER
        )
        self.vpc.add_interface_endpoint(
            "SMAPIEndpoint", service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_API
        )
        self.vpc.add_interface_endpoint(
            "SMRuntimeEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_RUNTIME,
        )
        self.vpc.add_interface_endpoint(
            "SMNotebookEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_NOTEBOOK,
        )
        self.vpc.add_interface_endpoint(
            "AthenaEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ATHENA
        )
        self.vpc.add_interface_endpoint(
            "STSEndpoint", service=ec2.InterfaceVpcEndpointAwsService.STS
        )
        self.vpc.add_interface_endpoint(
            "SSMEndpoint", service=ec2.InterfaceVpcEndpointAwsService.SSM
        )
        self.vpc.add_interface_endpoint(
            "CWLogsEndpoint", service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS
        )
        self.vpc.add_interface_endpoint(
            "CWEndpoint", service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH
        )
        self.vpc.add_interface_endpoint(
            "SecretsEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
        )
        self.vpc.add_interface_endpoint(
            "RedshiftEndpoint",
            service=ec2.InterfaceVpcEndpointService(
                f"com.amazonaws.{self.region}.redshift", 443
            ),
        )
        self.vpc.add_interface_endpoint(
            "RedshiftDataEndpoint",
            service=ec2.InterfaceVpcEndpointService(
                f"com.amazonaws.{self.region}.redshift-data", 443
            ),
        )
        self.vpc.add_interface_endpoint(
            "ForecastEndpoint",
            service=ec2.InterfaceVpcEndpointService(
                f"com.amazonaws.{self.region}.forecast", 443
            ),
        )
        self.vpc.add_interface_endpoint(
            "ForecastQueryEndpoint",
            service=ec2.InterfaceVpcEndpointService(
                f"com.amazonaws.{self.region}.forecastquery", 443
            ),
        )

        self.vpc_id = self.vpc.vpc_id
        self.subnet_ids = [subnet.subnet_id for subnet in self.vpc.private_subnets]

        # ==================================================
        # ================ SECURITY GROUP ==================
        # ==================================================
        self.security_group = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=self.vpc,
            description="Security Group for SageMaker Studio",
        )

        self.security_group.add_ingress_rule(
            self.security_group, ec2.Port.all_traffic()
        )

        self.sg_id = self.security_group.security_group_id
