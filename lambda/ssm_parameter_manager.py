import json
import boto3
import urllib3

ssm = boto3.client("ssm")
http = urllib3.PoolManager()

def send_response(event, context, status, data=None):
    response_body = {
        "Status": status,
        "Reason": f"See CloudWatch logs: {context.log_stream_name}",
        "PhysicalResourceId": event.get("PhysicalResourceId", context.log_stream_name),
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
        props = event["ResourceProperties"]
        name = props["Name"]
        value = props["Value"]
        param_type = props.get("Type", "String")

        if event["RequestType"] in ["Create", "Update"]:
            params = {
                "Name": name,
                "Value": value,
                "Type": param_type,
                "Overwrite": True
            }
            ssm.put_parameter(**params)

        elif event["RequestType"] == "Delete":
            try:
                ssm.delete_parameter(Name=name)
            except ssm.exceptions.ParameterNotFound:
                pass

        send_response(event, context, "SUCCESS")

    except Exception as e:
        send_response(event, context, "FAILED", {"Error": str(e)})