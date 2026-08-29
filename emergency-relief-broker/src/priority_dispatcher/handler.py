import json
import os
from datetime import datetime, timezone

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None

PRIORITY_ORDER = {"critical": 1, "high": 2, "medium": 3, "low": 4}


def _get_dynamodb_table(table_name: str):
    if boto3 is None:
        raise RuntimeError("boto3 is required for DynamoDB integrations")
    return boto3.resource("dynamodb").Table(table_name)


def lambda_handler(event, _context):
    records = (event or {}).get("Records", [])
    table_name = os.getenv("REQUEST_TABLE_NAME", "")

    dispatched = []
    failed = 0

    table = _get_dynamodb_table(table_name) if table_name else None

    for record in records:
        try:
            body = json.loads(record.get("body", "{}"))
            severity = str(body.get("severity", "low")).lower()
            priority = PRIORITY_ORDER.get(severity, 4)

            dispatch_entry = {
                "request_id": body.get("request_id"),
                "severity": severity,
                "dispatch_priority": priority,
                "target_channel": "rapid-response" if priority <= 2 else "standard-response",
            }
            dispatched.append(dispatch_entry)

            if table and dispatch_entry["request_id"]:
                table.update_item(
                    Key={"request_id": dispatch_entry["request_id"]},
                    UpdateExpression="SET #status=:status, dispatched_at=:dispatched_at, dispatch_priority=:dispatch_priority, target_channel=:target_channel",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":status": "dispatched",
                        ":dispatched_at": datetime.now(tz=timezone.utc).isoformat(),
                        ":dispatch_priority": priority,
                        ":target_channel": dispatch_entry["target_channel"],
                    },
                )
        except json.JSONDecodeError:
            failed += 1

    return {
        "dispatched_count": len(dispatched),
        "failed_count": failed,
        "dispatched": dispatched,
    }
