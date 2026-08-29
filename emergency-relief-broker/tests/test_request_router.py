import json
import unittest
from unittest.mock import patch

from src.request_router.handler import lambda_handler


class ConditionalCheckFailed(Exception):
    def __init__(self, request_id):
        self.response = {
            "Error": {"Code": "ConditionalCheckFailedException"},
            "Item": {"request_id": request_id},
        }


class FakeRequestTable:
    def __init__(self):
        self.items = {}

    def put_item(self, Item, **_kwargs):
        self.items[Item["request_id"]] = Item

    def get_item(self, Key):
        item = self.items.get(Key["request_id"])
        return {"Item": item} if item else {}


class FakeIdempotencyTable:
    def __init__(self):
        self.keys = {}

    def put_item(self, Item, ConditionExpression=None):  # noqa: N803
        key = Item["idempotency_key"]
        if key in self.keys:
            raise ConditionalCheckFailed(self.keys[key])
        self.keys[key] = Item["request_id"]


class FakeSqs:
    def __init__(self):
        self.messages = []

    def send_message(self, **kwargs):
        self.messages.append(kwargs)


class RequestRouterTests(unittest.TestCase):
    def setUp(self):
        self.request_table = FakeRequestTable()
        self.idempotency_table = FakeIdempotencyTable()
        self.fake_sqs = FakeSqs()

    def _table_lookup(self, table_name):
        if table_name == "requests":
            return self.request_table
        if table_name == "idempotency":
            return self.idempotency_table
        raise AssertionError(f"unexpected table {table_name}")

    @patch.dict(
        "os.environ",
        {
            "REQUEST_QUEUE_URL": "https://sqs.example/queue",
            "REQUEST_TABLE_NAME": "requests",
            "IDEMPOTENCY_TABLE_NAME": "idempotency",
            "EXPECTED_API_KEY": "secret",
        },
        clear=False,
    )
    def test_missing_required_fields_returns_400(self):
        event = {
            "headers": {"x-api-key": "secret", "x-idempotency-key": "idem-1"},
            "body": json.dumps({"citizen_id": "abc"}),
        }

        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("fields", body)

    @patch.dict(
        "os.environ",
        {
            "REQUEST_QUEUE_URL": "https://sqs.example/queue",
            "REQUEST_TABLE_NAME": "requests",
            "IDEMPOTENCY_TABLE_NAME": "idempotency",
            "EXPECTED_API_KEY": "secret",
        },
        clear=False,
    )
    def test_valid_request_returns_202_and_enqueues(self):
        event = {
            "headers": {"x-api-key": "secret", "x-idempotency-key": "idem-2"},
            "body": json.dumps(
                {
                    "request_id": "req-123",
                    "citizen_id": "abc",
                    "severity": "critical",
                    "location": {"lat": 19.0, "lon": 73.0},
                    "description": "Road blocked and injuries reported",
                }
            ),
        }

        with patch("src.request_router.handler._get_dynamodb_table", side_effect=self._table_lookup), patch(
            "src.request_router.handler._get_sqs_client", return_value=self.fake_sqs
        ):
            response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 202)
        body = json.loads(response["body"])
        self.assertEqual(body["request"]["priority_lane"], "HIGH_PRIORITY")
        self.assertEqual(len(self.fake_sqs.messages), 1)

    @patch.dict(
        "os.environ",
        {
            "REQUEST_QUEUE_URL": "https://sqs.example/queue",
            "REQUEST_TABLE_NAME": "requests",
            "IDEMPOTENCY_TABLE_NAME": "idempotency",
            "EXPECTED_API_KEY": "",
        },
        clear=False,
    )
    def test_duplicate_idempotency_key_returns_existing_request(self):
        existing = {
            "request_id": "req-existing",
            "citizen_id": "abc",
            "severity": "high",
            "location": {"lat": 19.0, "lon": 73.0},
            "description": "Fire in building",
            "priority_lane": "HIGH_PRIORITY",
            "accepted_at": "2026-01-01T00:00:00+00:00",
            "status": "queued",
            "idempotency_key": "idem-duplicate",
        }
        self.request_table.put_item(Item=existing)
        self.idempotency_table.keys["idem-duplicate"] = "req-existing"

        event = {
            "headers": {"x-idempotency-key": "idem-duplicate"},
            "body": json.dumps(
                {
                    "citizen_id": "abc",
                    "severity": "high",
                    "location": {"lat": 19.0, "lon": 73.0},
                    "description": "Fire in building",
                }
            ),
        }

        with patch("src.request_router.handler._get_dynamodb_table", side_effect=self._table_lookup), patch(
            "src.request_router.handler._get_sqs_client", return_value=self.fake_sqs
        ):
            response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["request"]["request_id"], "req-existing")
        self.assertEqual(len(self.fake_sqs.messages), 0)


if __name__ == "__main__":
    unittest.main()
