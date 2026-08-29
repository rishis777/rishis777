import math


def _haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def lambda_handler(event, _context):
    event = event or {}
    request_location = event.get("request_location", {})
    regions = event.get("available_regions", [])

    if not request_location or "lat" not in request_location or "lon" not in request_location:
        return {"statusCode": 400, "error": "request_location with lat/lon is required"}

    healthy_regions = [r for r in regions if r.get("is_healthy") and r.get("capacity", 0) > 0]
    if not healthy_regions:
        return {"statusCode": 503, "error": "No healthy regions with available capacity"}

    nearest = min(
        healthy_regions,
        key=lambda r: _haversine_km(
            request_location["lat"],
            request_location["lon"],
            r["lat"],
            r["lon"],
        ),
    )

    return {
        "statusCode": 200,
        "selected_region": nearest["name"],
    }
