from __future__ import annotations

import unittest
from datetime import date

from travel_assistant.trips import build_trip_plan


class TripPlanTests(unittest.TestCase):
    def test_plan_uses_manual_flight_estimate_when_no_exact_flight_exists(self) -> None:
        datasets = {
            "flights": [],
            "hotels": [
                {
                    "hotel_id": "h1",
                    "name": "Palm Stay",
                    "city": "Goa",
                    "stars": 4,
                    "price_per_night": 3000,
                    "amenities": ["wifi"],
                }
            ],
            "places": [
                {"place_id": "p1", "name": "Old Fort", "city": "Goa", "type": "fort", "rating": 4.8}
            ],
        }

        result = build_trip_plan(
            datasets=datasets,
            origin="Delhi",
            destination="Goa",
            start_date=date(2026, 11, 20),
            trip_days=3,
            max_hotel_price=5000,
            min_stars=2,
            daily_local_cost=1000,
            estimated_flight_cost=2500,
            interests=["Fort"],
            weather={"status": "unavailable", "message": "No forecast", "days": []},
        )

        self.assertIsNone(result["selected_flight"])
        self.assertEqual(result["budget"]["flight"], 2500)
        self.assertEqual(result["budget"]["total_estimate"], 11500)
        self.assertEqual(len(result["itinerary"]), 3)
        self.assertEqual(result["export"]["trip"]["end_date"], "2026-11-22")


if __name__ == "__main__":
    unittest.main()
