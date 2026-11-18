"""Search and sort the sample place and stay catalogs."""

from __future__ import annotations

import math
from typing import Any


PLACE_SORT_OPTIONS = ("Top rated", "Rating: low to high", "Name A–Z", "Name Z–A")
HOTEL_SORT_OPTIONS = (
    "Recommended",
    "Price: low to high",
    "Price: high to low",
    "Stars: high to low",
    "Name A–Z",
)


def filter_places(
    places: list[dict[str, Any]],
    *,
    city: str = "All destinations",
    categories: list[str] | tuple[str, ...] = (),
    query: str = "",
) -> list[dict[str, Any]]:
    """Filter places by city, category, and a case-insensitive text query."""
    city_key = city.strip().casefold()
    category_keys = {category.strip().casefold() for category in categories if category.strip()}
    query_key = query.strip().casefold()
    matches = []
    for place in places:
        place_city = str(place.get("city", "")).strip()
        category = str(place.get("type", "")).strip()
        if city_key and city_key != "all destinations" and place_city.casefold() != city_key:
            continue
        if category_keys and category.casefold() not in category_keys:
            continue
        searchable = " ".join((str(place.get("name", "")), place_city, category)).casefold()
        if query_key and query_key not in searchable:
            continue
        matches.append(place)
    return matches


def sort_places(
    places: list[dict[str, Any]], sort_by: str = "Top rated"
) -> list[dict[str, Any]]:
    """Return a new list in the selected place order."""
    if sort_by == "Name A–Z":
        key = lambda item: (str(item.get("name", "")).casefold(), str(item.get("city", "")).casefold())
    elif sort_by == "Name Z–A":
        key = lambda item: (str(item.get("name", "")).casefold(), str(item.get("city", "")).casefold())
        return sorted(places, key=key, reverse=True)
    elif sort_by == "Rating: low to high":
        key = lambda item: (_number(item.get("rating")), str(item.get("name", "")).casefold())
    else:
        key = lambda item: (-_number(item.get("rating")), str(item.get("name", "")).casefold())
    return sorted(places, key=key)


def filter_hotels(
    hotels: list[dict[str, Any]],
    *,
    city: str = "All destinations",
    min_stars: int = 1,
    max_price: int | None = None,
    query: str = "",
) -> list[dict[str, Any]]:
    """Filter sample stays by destination, rating, price, and text."""
    city_key = city.strip().casefold()
    query_key = query.strip().casefold()
    matches = []
    for hotel in hotels:
        hotel_city = str(hotel.get("city", "")).strip()
        stars = _number(hotel.get("stars"))
        price = _number(hotel.get("price_per_night"))
        if city_key and city_key != "all destinations" and hotel_city.casefold() != city_key:
            continue
        if stars < min_stars or (max_price is not None and price > max_price):
            continue
        amenities = hotel.get("amenities", [])
        amenity_text = " ".join(map(str, amenities)) if isinstance(amenities, list) else str(amenities)
        searchable = " ".join((str(hotel.get("name", "")), hotel_city, amenity_text)).casefold()
        if query_key and query_key not in searchable:
            continue
        matches.append(hotel)
    return matches


def sort_hotels(
    hotels: list[dict[str, Any]], sort_by: str = "Recommended"
) -> list[dict[str, Any]]:
    """Return a new list in a useful, deterministic stay order."""
    if sort_by == "Price: low to high":
        key = lambda item: (_number(item.get("price_per_night")), -_number(item.get("stars")))
    elif sort_by == "Price: high to low":
        key = lambda item: (-_number(item.get("price_per_night")), -_number(item.get("stars")))
    elif sort_by == "Stars: high to low":
        key = lambda item: (-_number(item.get("stars")), _number(item.get("price_per_night")))
    elif sort_by == "Name A–Z":
        key = lambda item: (str(item.get("name", "")).casefold(), str(item.get("city", "")).casefold())
    else:
        key = lambda item: (
            -_number(item.get("stars")),
            _number(item.get("price_per_night")),
            str(item.get("name", "")).casefold(),
        )
    return sorted(hotels, key=key)


def _number(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return 0.0
    return number if math.isfinite(number) else 0.0
