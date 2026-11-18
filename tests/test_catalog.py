from __future__ import annotations

import unittest

from travel_assistant.catalog import (
    filter_hotels,
    filter_places,
    sort_hotels,
    sort_places,
)
from travel_assistant.data import load_datasets


class CatalogTests(unittest.TestCase):
    def test_sample_place_category_matches_its_name(self) -> None:
        places = load_datasets()["places"]

        self.assertTrue(
            all(place["type"].casefold() == place["name"].rsplit(" ", 1)[-1].casefold() for place in places)
        )

    def test_place_search_category_and_sort(self) -> None:
        places = [
            {"name": "Old Fort", "city": "Goa", "type": "fort", "rating": 4.3},
            {"name": "City Beach", "city": "Goa", "type": "beach", "rating": 4.8},
            {"name": "Old Fort", "city": "Delhi", "type": "fort", "rating": 4.9},
        ]

        filtered = filter_places(places, city="goa", categories=["FORT"], query="old")
        sorted_results = sort_places(filtered, "Top rated")

        self.assertEqual([place["city"] for place in sorted_results], ["Goa"])
        self.assertEqual(sorted_results[0]["rating"], 4.3)
        self.assertEqual(places[0]["rating"], 4.3)

    def test_hotel_search_includes_amenities_and_sort(self) -> None:
        hotels = [
            {"name": "Palm Stay", "city": "Goa", "stars": 4, "price_per_night": 4200, "amenities": ["Pool"]},
            {"name": "Bay Hotel", "city": "Goa", "stars": 3, "price_per_night": 3000, "amenities": ["Wifi"]},
            {"name": "Palm Stay", "city": "Delhi", "stars": 5, "price_per_night": 2500, "amenities": ["Pool"]},
        ]

        filtered = filter_hotels(hotels, city="Goa", min_stars=2, max_price=5000, query="pool")
        sorted_results = sort_hotels(filtered, "Price: low to high")

        self.assertEqual([hotel["name"] for hotel in sorted_results], ["Palm Stay"])
        self.assertEqual(sorted_results[0]["city"], "Goa")


if __name__ == "__main__":
    unittest.main()
