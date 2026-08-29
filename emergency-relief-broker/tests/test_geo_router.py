import unittest

from src.geo_router.handler import lambda_handler


class GeoRouterTests(unittest.TestCase):
    def test_selects_nearest_healthy_region(self):
        event = {
            "request_location": {"lat": 19.076, "lon": 72.8777},
            "available_regions": [
                {"name": "ap-south-1", "lat": 19.076, "lon": 72.8777, "is_healthy": True, "capacity": 100},
                {"name": "eu-west-1", "lat": 53.3498, "lon": -6.2603, "is_healthy": True, "capacity": 100},
            ],
        }

        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["selected_region"], "ap-south-1")

    def test_returns_503_when_no_capacity(self):
        event = {
            "request_location": {"lat": 19.076, "lon": 72.8777},
            "available_regions": [
                {"name": "ap-south-1", "lat": 19.076, "lon": 72.8777, "is_healthy": True, "capacity": 0}
            ],
        }

        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 503)


if __name__ == "__main__":
    unittest.main()
