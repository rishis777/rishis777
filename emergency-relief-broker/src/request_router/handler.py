import json
import os
import uuid
from datetime import datetime, timezone

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None

REQUIRED_FIELDS = {"citizen_id", "severity", "location", "description"}
ALLOWED_SEVERITY = {"critical", "high", "medium", "low"}


def _response(status_code: int, payload: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _parse_body(event: dict) -> dict:
    body = event.get("body", "{}")
    if isinstance(body, str):
        return json.loads(body)
    if isinstance(body, dict):
        return body
    raise ValueError("Invalid request body")


def _get_header(event: dict, header_name: str) -> str:
    headers = (event or {}).get("headers") or {}
    for key, value in headers.items():
        if key.lower() == header_name.lower():
            return value
    return ""


def _is_authorized(event: dict) -> bool:
    expected_api_key = os.getenv("EXPECTED_API_KEY", "")
    if not expected_api_key:
        return True
    provided_key = _get_header(event, "x-api-key")
    return provided_key == expected_api_key


def _get_dynamodb_table(table_name: str):
    if boto3 is None:
        raise RuntimeError("boto3 is required for DynamoDB integrations")
    return boto3.resource("dynamodb").Table(table_name)


def _get_sqs_client():
    if boto3 is None:
        raise RuntimeError("boto3 is required for SQS integrations")
    return boto3.client("sqs")


def _extract_duplicate_request_id(error: Exception) -> str:
    response = getattr(error, "response", {}) or {}
    error_code = ((response.get("Error") or {}).get("Code"))
    if error_code != "ConditionalCheckFailedException":
        return ""

    request_id = ""
    item = (response.get("Item") or {})
    if isinstance(item, dict):
        request_id = item.get("request_id") or ""
    return request_id


def lambda_handler(event, _context):
    event = event or {}

    if not _is_authorized(event):
        return _response(401, {"error": "Unauthorized"})

    try:
        payload = _parse_body(event)
    except (json.JSONDecodeError, ValueError):
        return _response(400, {"error": "Invalid JSON body"})

    missing_fields = sorted(REQUIRED_FIELDS - set(payload.keys()))
    if missing_fields:
        return _response(400, {"error": "Missing required fields", "fields": missing_fields})

    severity = str(payload.get("severity", "")).lower()
    if severity not in ALLOWED_SEVERITY:
        return _response(400, {"error": "Invalid severity"})

    queue_url = os.getenv("REQUEST_QUEUE_URL", "")
    request_table_name = os.getenv("REQUEST_TABLE_NAME", "")
    idempotency_table_name = os.getenv("IDEMPOTENCY_TABLE_NAME", "")

    if not queue_url or not request_table_name:
        return _response(500, {"error": "Server misconfiguration"})

    idempotency_key = _get_header(event, "x-idempotency-key")
    if not idempotency_key:
        return _response(400, {"error": "Missing X-Idempotency-Key header"})

    request_id = payload.get("request_id") or f"req-{uuid.uuid4()}"
    accepted_at = datetime.now(tz=timezone.utc).isoformat()
    priority_lane = "HIGH_PRIORITY" if severity in {"critical", "high"} else "STANDARD"

    request_record = {
        "request_id": request_id,
        "citizen_id": payload["citizen_id"],
        "severity": severity,
        "location": payload["location"],
        "description": payload["description"],
        "priority_lane": priority_lane,
        "accepted_at": accepted_at,
        "status": "queued",
        "idempotency_key": idempotency_key,
    }

    request_table = _get_dynamodb_table(request_table_name)
    if idempotency_table_name:
        idempotency_table = _get_dynamodb_table(idempotency_table_name)
        try:
            idempotency_table.put_item(
                Item={
                    "idempotency_key": idempotency_key,
                    "request_id": request_id,
                    "created_at": accepted_at,
                },
                ConditionExpression="attribute_not_exists(idempotency_key)",
            )
        except Exception as exc:  # pragma: no cover - branch tested via stubs
            duplicate_request_id = _extract_duplicate_request_id(exc)
            if not duplicate_request_id:
                raise

            existing_item = request_table.get_item(Key={"request_id": duplicate_request_id}).get("Item")
            return _response(
                200,
                {
                    "message": "Duplicate request acknowledged",
                    "request": existing_item or {"request_id": duplicate_request_id},
                },
            )

    request_table.put_item(Item=request_record)

    sqs = _get_sqs_client()
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(request_record),
        MessageAttributes={
            "severity": {"DataType": "String", "StringValue": severity},
            "priority_lane": {"DataType": "String", "StringValue": priority_lane},
        },
    )

    return _response(
        202,
        {
            "message": "Emergency request accepted",
            "request": request_record,
        },
    )
