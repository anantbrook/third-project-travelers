from __future__ import annotations

import unittest

from travel_assistant.data import recommend_hotels


class RecommendationTests(unittest.TestCase):
    def test_hotel_ranking_does_not_mutate_cached_input(self) -> None:
        hotels = [
            {"name": "Over budget", "city": "Goa", "stars": 5, "price_per_night": 9000},
            {"name": "Within budget", "city": "Goa", "stars": 4, "price_per_night": 4000},
        ]

        results = recommend_hotels(hotels, "goa", max_price_per_night=5000, min_stars=2)

        self.assertEqual([hotel["name"] for hotel in results], ["Within budget", "Over budget"])
        self.assertTrue(results[0]["within_budget"])
        self.assertFalse(results[1]["within_budget"])
        self.assertNotIn("within_budget", hotels[0])
        self.assertNotIn("within_budget", hotels[1])


if __name__ == "__main__":
    unittest.main()
