## Provisioning SageMaker Canvas environments easily with the AWS CDK and AWS Service Catalog

### Overview
In this repository we show how to to provisioning approved Amazon SageMaker Canvas environments management at scale, 
using the AWS Cloud Development Kit and AWS Service Catalog.

This implementation shows how to do the following:
* Create a portfolio of resources necessary for the approved usage of SageMaker Canvas using AWS Service Catalog. 
* Provision Canvas environments on demand within minutes.
* Provision a scheduled AWS Lambda function to shutdown Canvas resources and keep cost under control.


### Prerequisites
We will use [the AWS CDK](https://cdkworkshop.com/) to deploy the MLflow server.

To go through this example, make sure you have the following:
* An AWS account where the service will be deployed
* [AWS CDK installed and configured](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html). Make sure to have the credentials and permissions to deploy the stack into your account
* [Docker](https://www.docker.com) to build the Canvas Auto Shutdown Lambda container image and push it to ECR.
* This [Github repository](https://github.com/aws-samples/amazon-sagemaker-canvas-service-catalog) cloned into your environment to follow the steps

### Deploying the stack
You can view the main CDK stack details in [app.py](https://github.com/aws-samples/amazon-sagemaker-canvas-service-catalog/blob/main/app.py).
Execute the following commands to install CDK and make sure you have the right dependencies:

```
npm install -g aws-cdk@2.27.0
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

Once this is installed, you can execute the following commands to deploy the Service Catalog portfolio into your account:

```
ACCOUNT_ID=$(aws sts get-caller-identity --query Account | tr -d '"')
AWS_REGION=$(aws configure get region)
cdk bootstrap aws://${ACCOUNT_ID}/${AWS_REGION}
cdk deploy --require-approval never
```

The first 2 commands will get your account ID and current AWS region using the AWS CLI on your computer. ```cdk
bootstrap``` and ```cdk deploy``` will build the Scheduled Shutdown Lambda container image locally, push it to ECR, and deploy the stack. 

The stack will take a few minutes to create. You can then use the Service Catalog console page to provision Canvas environments.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

