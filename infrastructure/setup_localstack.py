"""
LocalStack infrastructure setup script.
Run once after `docker-compose up` to create all AWS resources locally.

Usage:
    python infrastructure/setup_localstack.py
"""

import boto3
import json
import os
import zipfile
import io
import time

ENDPOINT = "http://localhost:4566"
REGION = "ap-southeast-1"
ACCOUNT_ID = "000000000000"  # LocalStack default

session = boto3.Session(
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name=REGION,
)

dynamodb = session.resource("dynamodb", endpoint_url=ENDPOINT)
lambda_client = session.client("lambda", endpoint_url=ENDPOINT)
apigateway = session.client("apigateway", endpoint_url=ENDPOINT)
events = session.client("events", endpoint_url=ENDPOINT)
s3 = session.client("s3", endpoint_url=ENDPOINT)

PRICE_TABLE = "gold-prices"
SCRAPER_FUNCTION = "gold-scraper"
API_FUNCTION = "gold-api"
FRONTEND_BUCKET = "gold-frontend"
EVENT_RULE = "daily-gold-scraper"


def create_dynamodb():
    print("Creating DynamoDB table...")
    try:
        dynamodb.create_table(
            TableName=PRICE_TABLE,
            KeySchema=[{"AttributeName": "date", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "date", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"  Table '{PRICE_TABLE}' created.")
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"  Table '{PRICE_TABLE}' already exists.")


def zip_lambda(source_dir: str, extra_dirs: list[str] = None) -> bytes:
    """Zip a Lambda directory into bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, source_dir)
                zf.write(full_path, arcname)
        if extra_dirs:
            for extra in extra_dirs:
                for root, _, files in os.walk(extra):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arcname = os.path.join("shared", os.path.relpath(full_path, extra))
                        zf.write(full_path, arcname)
    return buf.getvalue()


def create_or_update_lambda(name: str, zip_bytes: bytes, handler: str, env: dict = None):
    env = env or {}
    base_env = {
        "LOCALSTACK_ENDPOINT": ENDPOINT,
        "AWS_DEFAULT_REGION": REGION,
        "PRICE_TABLE": PRICE_TABLE,
    }
    base_env.update(env)

    try:
        lambda_client.create_function(
            FunctionName=name,
            Runtime="python3.12",
            Role=f"arn:aws:iam::{ACCOUNT_ID}:role/lambda-role",
            Handler=handler,
            Code={"ZipFile": zip_bytes},
            Environment={"Variables": base_env},
            Timeout=60,
            MemorySize=256,
        )
        print(f"  Lambda '{name}' created.")
    except lambda_client.exceptions.ResourceConflictException:
        lambda_client.update_function_code(FunctionName=name, ZipFile=zip_bytes)
        print(f"  Lambda '{name}' updated.")


def create_lambdas():
    print("Creating Lambda functions...")
    base = os.path.dirname(os.path.abspath(__file__))
    shared_dir = os.path.join(base, "../backend/shared")

    scraper_dir = os.path.join(base, "../backend/lambdas/scraper")
    scraper_zip = zip_lambda(scraper_dir, extra_dirs=[shared_dir])
    create_or_update_lambda(SCRAPER_FUNCTION, scraper_zip, "handler.lambda_handler")

    api_dir = os.path.join(base, "../backend/lambdas/api")
    api_zip = zip_lambda(api_dir, extra_dirs=[shared_dir])
    create_or_update_lambda(API_FUNCTION, api_zip, "handler.lambda_handler")


def create_api_gateway():
    print("Creating API Gateway...")
    apis = apigateway.get_rest_apis()["items"]
    existing = next((a for a in apis if a["name"] == "gold-api"), None)

    if existing:
        api_id = existing["id"]
        print(f"  API Gateway already exists: {api_id}")
    else:
        api = apigateway.create_rest_api(name="gold-api")
        api_id = api["id"]
        print(f"  API Gateway created: {api_id}")

    root = apigateway.get_resources(restApiId=api_id)["items"][0]["id"]

    lambda_arn = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{API_FUNCTION}"
    integration_uri = (
        f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31"
        f"/functions/{lambda_arn}/invocations"
    )

    # Create /prices resource
    try:
        prices_resource = apigateway.create_resource(
            restApiId=api_id, parentId=root, pathPart="prices"
        )
        prices_id = prices_resource["id"]
    except apigateway.exceptions.ConflictException:
        resources = apigateway.get_resources(restApiId=api_id)["items"]
        prices_id = next(r["id"] for r in resources if r.get("pathPart") == "prices")

    for method in ["GET", "OPTIONS"]:
        try:
            apigateway.put_method(
                restApiId=api_id, resourceId=prices_id,
                httpMethod=method, authorizationType="NONE"
            )
            apigateway.put_integration(
                restApiId=api_id, resourceId=prices_id,
                httpMethod=method, type="AWS_PROXY",
                integrationHttpMethod="POST", uri=integration_uri,
            )
        except Exception:
            pass

    # Create /prices/latest and /prices/roi sub-resources
    resources = apigateway.get_resources(restApiId=api_id)["items"]
    for path_part in ["latest", "roi"]:
        existing = next((r for r in resources if r.get("pathPart") == path_part), None)
        if existing:
            sub_id = existing["id"]
        else:
            sub = apigateway.create_resource(
                restApiId=api_id, parentId=prices_id, pathPart=path_part
            )
            sub_id = sub["id"]
        for method in ["GET", "OPTIONS"]:
            try:
                apigateway.put_method(
                    restApiId=api_id, resourceId=sub_id,
                    httpMethod=method, authorizationType="NONE"
                )
                apigateway.put_integration(
                    restApiId=api_id, resourceId=sub_id,
                    httpMethod=method, type="AWS_PROXY",
                    integrationHttpMethod="POST", uri=integration_uri,
                )
            except Exception:
                pass

    apigateway.create_deployment(restApiId=api_id, stageName="prod")
    print(f"  API deployed: {ENDPOINT}/restapis/{api_id}/prod/_user_request_/prices")
    return api_id


def create_eventbridge_rule():
    print("Creating EventBridge daily rule...")
    try:
        events.put_rule(
            Name=EVENT_RULE,
            ScheduleExpression="cron(0 6 * * ? *)",  # 6 AM UTC = 12 PM BST
            State="ENABLED",
            Description="Daily gold price scraper trigger",
        )
        lambda_arn = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{SCRAPER_FUNCTION}"
        events.put_targets(
            Rule=EVENT_RULE,
            Targets=[{"Id": "scraper-target", "Arn": lambda_arn}],
        )
        print(f"  Rule '{EVENT_RULE}' created.")
    except Exception as e:
        print(f"  EventBridge rule error (may already exist): {e}")


def create_s3_frontend():
    print("Creating S3 frontend bucket...")
    try:
        s3.create_bucket(
            Bucket=FRONTEND_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
        s3.put_bucket_website(
            Bucket=FRONTEND_BUCKET,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": "index.html"},
                "ErrorDocument": {"Key": "index.html"},
            },
        )
        print(f"  Bucket '{FRONTEND_BUCKET}' created with static hosting.")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"  Bucket '{FRONTEND_BUCKET}' already exists.")


if __name__ == "__main__":
    print("Setting up LocalStack infrastructure...\n")
    create_dynamodb()
    time.sleep(1)
    create_lambdas()
    create_api_gateway()
    create_eventbridge_rule()
    create_s3_frontend()
    print("\nDone! LocalStack infrastructure ready.")
