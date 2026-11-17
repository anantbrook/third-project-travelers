"""Load and query the project's local JSON travel datasets."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = {
    "flights": "flights.json",
    "hotels": "hotels.json",
    "places": "places.json",
}

REQUIRED_FIELDS = {
    "flights": {
        "flight_id",
        "airline",
        "from",
        "to",
        "departure_time",
        "arrival_time",
        "price",
    },
    "hotels": {
        "hotel_id",
        "name",
        "city",
        "stars",
        "price_per_night",
        "amenities",
    },
    "places": {"place_id", "name", "city", "type", "rating"},
}


class DatasetError(ValueError):
    """Raised when a local travel dataset is missing or malformed."""


def _load_records(dataset_name: str) -> list[dict[str, Any]]:
    filename = DATA_FILES[dataset_name]
    path = PROJECT_ROOT / filename
    if not path.is_file():
        raise DatasetError(f"Could not find {filename} in the project folder.")

    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetError(f"Could not read {filename}: {exc}") from exc

    if not isinstance(records, list):
        raise DatasetError(f"{filename} must contain a JSON list of records.")

    required = REQUIRED_FIELDS[dataset_name]
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise DatasetError(f"Record {index} in {filename} must be a JSON object.")
        missing = required.difference(record)
        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise DatasetError(f"Record {index} in {filename} is missing: {missing_fields}.")
    return records


def load_datasets() -> dict[str, list[dict[str, Any]]]:
    """Load all three datasets and check their required fields."""
    return {name: _load_records(name) for name in DATA_FILES}


def list_cities(datasets: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Return the distinct cities represented across all three datasets."""
    cities: set[str] = set()
    for record in datasets["hotels"] + datasets["places"]:
        city = record.get("city")
        if isinstance(city, str) and city.strip():
            cities.add(city.strip())
    for flight in datasets["flights"]:
        for key in ("from", "to"):
            city = flight.get(key)
            if isinstance(city, str) and city.strip():
                cities.add(city.strip())
    return sorted(cities)


def find_flights(
    flights: list[dict[str, Any]], origin: str, destination: str, departure_date: date
) -> list[dict[str, Any]]:
    """Return flights matching route and exact departure date, cheapest first."""
    matches = []
    for flight in flights:
        if flight.get("from", "").casefold() != origin.casefold():
            continue
        if flight.get("to", "").casefold() != destination.casefold():
            continue
        try:
            flight_date = datetime.fromisoformat(flight["departure_time"]).date()
        except (KeyError, TypeError, ValueError):
            continue
        if flight_date == departure_date:
            matches.append(flight)
    return sorted(matches, key=lambda item: float(item.get("price", 0)))


def flight_duration_minutes(flight: dict[str, Any]) -> float:
    """Return the scheduled flight duration in minutes, or a large fallback value."""
    try:
        departure = datetime.fromisoformat(flight["departure_time"])
        arrival = datetime.fromisoformat(flight["arrival_time"])
    except (KeyError, TypeError, ValueError):
        return float("inf")
    return max((arrival - departure).total_seconds() / 60, 0)


def find_route_samples(
    flights: list[dict[str, Any]], origin: str, destination: str, limit: int = 5
) -> list[dict[str, Any]]:
    """Return route examples for context; these may not match the requested date."""
    matches = [
        flight
        for flight in flights
        if flight.get("from", "").casefold() == origin.casefold()
        and flight.get("to", "").casefold() == destination.casefold()
    ]
    return sorted(matches, key=lambda item: float(item.get("price", 0)))[:limit]


def recommend_hotels(
    hotels: list[dict[str, Any]], city: str, max_price_per_night: int, min_stars: int
) -> list[dict[str, Any]]:
    """Rank city hotels, preferring those within budget and with more stars."""
    matches = [
        hotel
        for hotel in hotels
        if hotel.get("city", "").casefold() == city.casefold()
        and int(hotel.get("stars", 0)) >= min_stars
    ]
    for hotel in matches:
        hotel["within_budget"] = int(hotel.get("price_per_night", 0)) <= max_price_per_night
    return sorted(
        matches,
        key=lambda hotel: (
            not hotel["within_budget"],
            -int(hotel.get("stars", 0)),
            int(hotel.get("price_per_night", 0)),
        ),
    )


def recommend_places(
    places: list[dict[str, Any]], city: str, interests: list[str]
) -> list[dict[str, Any]]:
    """Rank attractions for a city, prioritizing requested types and ratings."""
    city_places = [
        place for place in places if place.get("city", "").casefold() == city.casefold()
    ]
    requested = {item.casefold() for item in interests}
    if requested:
        matching = [
            place
            for place in city_places
            if str(place.get("type", "")).casefold() in requested
        ]
        if matching:
            city_places = matching
    return sorted(city_places, key=lambda place: float(place.get("rating", 0)), reverse=True)


def departure_date_range(flights: list[dict[str, Any]]) -> tuple[date, date] | None:
    """Return the date range represented by valid flight schedule records."""
    dates: list[date] = []
    for flight in flights:
        try:
            dates.append(datetime.fromisoformat(flight["departure_time"]).date())
        except (KeyError, TypeError, ValueError):
            continue
    if not dates:
        return None
    return min(dates), max(dates)

