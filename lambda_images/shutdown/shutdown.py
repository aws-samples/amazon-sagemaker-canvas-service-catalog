import boto3
import logging
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

config = Config(retries={"max_attempts": 10, "mode": "standard"})
sagemaker = boto3.client("sagemaker", config=config)
paginator = sagemaker.get_paginator("list_apps")


def delete_app(domain_id, user_profile_name, app_type, app_name):
    logger.info(
        f"deleting {app_type}: {app_name} for user: {user_profile_name} in Domain: {domain_id}"
    )

    sagemaker.delete_app(
        DomainId=domain_id,
        UserProfileName=user_profile_name,
        AppType=app_type,
        AppName=app_name,
    )


def lambda_handler(event, context):
    try:
        app_page_iterator = paginator.paginate(PaginationConfig={"PageSize": 50})

        for app_page in app_page_iterator:
            for app in app_page["Apps"]:
                if app["AppType"] == "Canvas" and app["Status"] != "Deleted":
                    delete_app(
                        app["DomainId"],
                        app["UserProfileName"],
                        app["AppType"],
                        app["AppName"],
                    )

    except Exception as e:
        logger.error(e)

    logger.info("Canvas apps deleted")
