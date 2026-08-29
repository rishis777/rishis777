import json
import unittest
from unittest.mock import patch

from src.priority_dispatcher.handler import lambda_handler


class FakeDispatchTable:
    def __init__(self):
        self.updated = []

    def update_item(self, **kwargs):
        self.updated.append(kwargs)


class PriorityDispatcherTests(unittest.TestCase):
    @patch.dict("os.environ", {"REQUEST_TABLE_NAME": "requests"}, clear=False)
    def test_updates_dispatch_status(self):
        table = FakeDispatchTable()

        event = {
            "Records": [
                {
                    "body": json.dumps(
                        {
                            "request_id": "req-1",
                            "severity": "critical",
                        }
                    )
                }
            ]
        }

        with patch("src.priority_dispatcher.handler._get_dynamodb_table", return_value=table):
            result = lambda_handler(event, None)

        self.assertEqual(result["dispatched_count"], 1)
        self.assertEqual(result["failed_count"], 0)
        self.assertEqual(len(table.updated), 1)


if __name__ == "__main__":
    unittest.main()
