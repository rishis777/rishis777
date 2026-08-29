import json
import uuid
from datetime import datetime, timezone

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


def lambda_handler(event, _context):
    try:
        payload = _parse_body(event or {})
    except (json.JSONDecodeError, ValueError):
        return _response(400, {"error": "Invalid JSON body"})

    missing_fields = sorted(REQUIRED_FIELDS - set(payload.keys()))
    if missing_fields:
        return _response(400, {"error": "Missing required fields", "fields": missing_fields})

    severity = str(payload.get("severity", "")).lower()
    if severity not in ALLOWED_SEVERITY:
        return _response(400, {"error": "Invalid severity"})

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
    }

    return _response(
        202,
        {
            "message": "Emergency request accepted",
            "request": request_record,
        },
    )
