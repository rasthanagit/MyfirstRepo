import os
import json
import boto3
import urllib3

ssm = boto3.client("ssm")
http = urllib3.PoolManager()

def send_response(event, context, status, data=None):
    response_body = {
        "Status": status,
        "Reason": f"See CloudWatch logs: {context.log_stream_name}",
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data": data or {}
    }

    http.request(
        "PUT",
        event["ResponseURL"],
        body=json.dumps(response_body),
        headers={"Content-Type": "application/json"}
    )

def handler(event, context):
    try:
        if event["RequestType"] == "Delete":
            send_response(event, context, "SUCCESS")
            return

        params = event["ResourceProperties"]["Parameters"]

        for p in params:
            name = p["Name"]
            param_type = p.get("Type", "String")
            secret_name = p["SecretName"]

            value = os.environ.get(secret_name)

            if not value:
                raise Exception(f"Missing secret: {secret_name}")

            ssm.put_parameter(
                Name=name,
                Value=value,
                Type=param_type,
                Overwrite=True
            )

        send_response(event, context, "SUCCESS")

    except Exception as e:
        send_response(event, context, "FAILED", {"Error": str(e)})