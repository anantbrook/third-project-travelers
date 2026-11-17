from __future__ import annotations

import unittest
from datetime import date

from travel_assistant.planner import build_itinerary, calculate_budget


class PlannerTests(unittest.TestCase):
    def test_budget_uses_trip_nights_and_daily_cost(self) -> None:
        budget = calculate_budget(
            trip_days=3,
            hotel_price_per_night=1000,
            daily_local_cost=500,
            flight_price=2000,
        )

        self.assertEqual(budget["hotel_nights"], 2)
        self.assertEqual(budget["hotel_total"], 2000)
        self.assertEqual(budget["food_and_local_total"], 1500)
        self.assertEqual(budget["total_estimate"], 5500)
        self.assertTrue(budget["complete"])

    def test_itinerary_handles_partial_weather_data(self) -> None:
        itinerary = build_itinerary(
            "Goa",
            date(2026, 11, 20),
            1,
            [],
            {"days": [{"date": "2026-11-20", "condition": "Clear sky"}]},
        )

        self.assertEqual(len(itinerary), 1)
        self.assertIn("Clear sky", itinerary[0]["weather"])
        self.assertIn("temperatures unavailable", itinerary[0]["weather"])


if __name__ == "__main__":
    unittest.main()
