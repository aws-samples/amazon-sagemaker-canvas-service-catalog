import os
from constructs import Construct
from aws_cdk import (
    Stack,
    aws_ec2 as ec2
)


class Networking(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # ==================================================
        # ===================== VPC ========================
        # ==================================================
        self.account_id = Stack.of(self).account
        self.aws_region = Stack.of(self).region

        self.vpc = ec2.Vpc(
            self,
            "DomainVPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=3,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
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
            "SMAPIEndpoint", service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_API
        )
        self.vpc.add_interface_endpoint(
            "SMRuntimeEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_RUNTIME,
        )
        self.vpc.add_interface_endpoint(
            "SMStudioeEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_STUDIO,
        )
        self.vpc.add_interface_endpoint(
            "SMNotebookEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_NOTEBOOK,
        )
        self.vpc.add_interface_endpoint(
            "STSEndpoint", service=ec2.InterfaceVpcEndpointAwsService.STS
        )
        self.vpc.add_interface_endpoint(
            "CWLogsEndpoint", service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS
        )
        self.vpc.add_interface_endpoint(
            "CWEndpoint", service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH
        )
        self.vpc.add_interface_endpoint(
            "ECREndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR
        )
        self.vpc.add_interface_endpoint(
            "ECRDockerEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER
        )
        self.vpc.add_interface_endpoint(
            "KMSEndpoint", service=ec2.InterfaceVpcEndpointAwsService.KMS
        )
        self.vpc.add_interface_endpoint(
            "EC2Endpoint", service=ec2.InterfaceVpcEndpointAwsService.EC2
        )
        self.vpc.add_interface_endpoint(
            "ApplicationAutoScalingEndpoint", service=ec2.InterfaceVpcEndpointAwsService.APPLICATION_AUTOSCALING
        )
        self.vpc.add_interface_endpoint(
            "AthenaEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ATHENA
        )
        self.vpc.add_interface_endpoint(
            "SSMEndpoint", service=ec2.InterfaceVpcEndpointAwsService.SSM
        )
        self.vpc.add_interface_endpoint(
            "SecretsEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
        )
        self.vpc.add_interface_endpoint(
            "RedshiftEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.REDSHIFT
        )
        self.vpc.add_interface_endpoint(
            "RedshiftDataEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.REDSHIFT_DATA
        )
        self.vpc.add_interface_endpoint(
            "GlueEndpoint", 
            service=ec2.InterfaceVpcEndpointAwsService.GLUE
        )
        self.vpc.add_interface_endpoint(
            "RDSEndpoint", 
            service=ec2.InterfaceVpcEndpointAwsService.RDS
        )
        self.vpc.add_interface_endpoint(
            "ComprehendEndpoint", 
            service=ec2.InterfaceVpcEndpointAwsService.COMPREHEND
        )
        self.vpc.add_interface_endpoint(
            "RekognitionEndpoint", 
            service=ec2.InterfaceVpcEndpointAwsService.REKOGNITION
        )
        self.vpc.add_interface_endpoint(
            "TextractEndpoint", 
            service=ec2.InterfaceVpcEndpointAwsService.TEXTRACT
        )
        self.vpc.add_interface_endpoint(
            "BedrockEndpoint", 
            service=ec2.InterfaceVpcEndpointAwsService.BEDROCK
        )
        self.vpc.add_interface_endpoint(
            "BedrockRuntimeEndpoint", 
            service=ec2.InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME
        )
        self.vpc.add_interface_endpoint(
            "KendraEndpoint", 
            service=ec2.InterfaceVpcEndpointAwsService.KENDRA
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
