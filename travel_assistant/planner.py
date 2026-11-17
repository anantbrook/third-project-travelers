"""Deterministic itinerary and budget helpers."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def calculate_budget(
    trip_days: int,
    hotel_price_per_night: int | None,
    daily_local_cost: int,
    flight_price: int | None,
) -> dict[str, Any]:
    """Calculate a transparent estimate; a three-day trip assumes two nights."""
    nights = max(trip_days - 1, 0)
    hotel_total = hotel_price_per_night * nights if hotel_price_per_night is not None else None
    local_total = daily_local_cost * trip_days
    known_subtotal = local_total + (hotel_total or 0) + (flight_price or 0)
    complete = hotel_total is not None and flight_price is not None
    return {
        "currency": "INR (assumed from the project brief; datasets do not define currency)",
        "flight": flight_price,
        "hotel_per_night": hotel_price_per_night,
        "hotel_nights": nights,
        "hotel_total": hotel_total,
        "food_and_local_per_day": daily_local_cost,
        "food_and_local_total": local_total,
        "known_subtotal": known_subtotal,
        "total_estimate": known_subtotal if complete else None,
        "complete": complete,
        "note": "Hotel nights are estimated as trip days minus one. Add a flight estimate when no flight matches the travel date.",
    }


def build_itinerary(
    destination: str,
    start_date: date,
    trip_days: int,
    places: list[dict[str, Any]],
    weather: dict[str, Any],
) -> list[dict[str, str]]:
    """Create a simple fallback schedule from the highest-ranked local places."""
    weather_by_date = {item["date"]: item for item in weather.get("days", [])}
    itinerary = []
    for index in range(trip_days):
        day_date = start_date + timedelta(days=index)
        first_place = places[index * 2] if index * 2 < len(places) else None
        second_place = places[index * 2 + 1] if index * 2 + 1 < len(places) else None
        day_weather = weather_by_date.get(day_date.isoformat())
        if day_weather:
            weather_note = (
                f"{day_weather['condition']}; high {day_weather['temperature_max_c']}°C, "
                f"low {day_weather['temperature_min_c']}°C"
            )
            chance = day_weather.get("precipitation_probability_max")
            if chance is not None:
                weather_note += f"; precipitation chance up to {chance}%"
        else:
            weather_note = "Forecast unavailable for this date."

        itinerary.append(
            {
                "day": str(index + 1),
                "date": day_date.isoformat(),
                "morning": f"Visit {first_place['name']} ({first_place['type']})" if first_place else "Keep the morning flexible or explore nearby areas.",
                "afternoon": f"Visit {second_place['name']} ({second_place['type']})" if second_place else "Choose a nearby activity based on your pace and interests.",
                "evening": f"Relax and explore dining near your accommodation in {destination}.",
                "weather": weather_note,
            }
        )
    return itinerary


def format_money(amount: int | float | None) -> str:
    """Format an amount in Indian rupees, or indicate that it is unavailable."""
    return "Not available" if amount is None else f"₹{amount:,.0f}"

