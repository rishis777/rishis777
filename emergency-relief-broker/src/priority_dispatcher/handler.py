import json

PRIORITY_ORDER = {"critical": 1, "high": 2, "medium": 3, "low": 4}


def lambda_handler(event, _context):
    records = (event or {}).get("Records", [])

    dispatched = []
    failed = 0

    for record in records:
        try:
            body = json.loads(record.get("body", "{}"))
            severity = str(body.get("severity", "low")).lower()
            priority = PRIORITY_ORDER.get(severity, 4)

            dispatched.append(
                {
                    "request_id": body.get("request_id"),
                    "severity": severity,
                    "dispatch_priority": priority,
                    "target_channel": "rapid-response" if priority <= 2 else "standard-response",
                }
            )
        except json.JSONDecodeError:
            failed += 1

    return {
        "dispatched_count": len(dispatched),
        "failed_count": failed,
        "dispatched": dispatched,
    }
