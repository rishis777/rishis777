import json
import unittest

from src.request_router.handler import lambda_handler


class RequestRouterTests(unittest.TestCase):
    def test_missing_required_fields_returns_400(self):
        event = {"body": json.dumps({"citizen_id": "abc"})}

        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("fields", body)

    def test_valid_request_returns_202(self):
        event = {
            "body": json.dumps(
                {
                    "citizen_id": "abc",
                    "severity": "critical",
                    "location": {"lat": 19.0, "lon": 73.0},
                    "description": "Road blocked and injuries reported",
                }
            )
        }

        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 202)
        body = json.loads(response["body"])
        self.assertEqual(body["request"]["priority_lane"], "HIGH_PRIORITY")


if __name__ == "__main__":
    unittest.main()
