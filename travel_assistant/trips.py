"""Build one data-grounded trip result for the planner page."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .agent import create_agent_plan
from .data import (
    departure_date_range,
    find_flights,
    find_route_samples,
    flight_duration_minutes,
    recommend_hotels,
    recommend_places,
)
from .planner import build_itinerary, calculate_budget


def build_trip_plan(
    *,
    datasets: dict[str, list[dict[str, Any]]],
    origin: str,
    destination: str,
    start_date: date,
    trip_days: int,
    max_hotel_price: int,
    min_stars: int,
    daily_local_cost: int,
    estimated_flight_cost: int,
    interests: list[str],
    weather: dict[str, Any],
    ai_provider: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return recommendations, a fallback plan, and a downloadable export."""
    flight_matches = find_flights(datasets["flights"], origin, destination, start_date)
    route_samples = find_route_samples(datasets["flights"], origin, destination)
    fastest_flight = min(flight_matches, key=flight_duration_minutes) if flight_matches else None
    hotel_matches = recommend_hotels(datasets["hotels"], destination, max_hotel_price, min_stars)
    places = recommend_places(datasets["places"], destination, interests)

    selected_flight = flight_matches[0] if flight_matches else None
    selected_hotel = hotel_matches[0] if hotel_matches else None
    flight_cost = (
        int(selected_flight["price"])
        if selected_flight
        else (int(estimated_flight_cost) or None)
    )
    hotel_rate = int(selected_hotel["price_per_night"]) if selected_hotel else None
    budget = calculate_budget(trip_days, hotel_rate, daily_local_cost, flight_cost)
    fallback_itinerary = build_itinerary(destination, start_date, trip_days, places, weather)

    agent_plan = None
    agent_error = None
    if ai_provider:
        try:
            agent_plan = create_agent_plan(
                provider=ai_provider["provider"],
                api_key=ai_provider["api_key"],
                model_name=ai_provider["model"],
                origin=origin,
                destination=destination,
                start_date=start_date,
                trip_days=trip_days,
                interests=interests,
                flight_matches=flight_matches,
                route_samples=route_samples,
                hotel_matches=hotel_matches,
                place_matches=places,
                weather=weather,
                budget=budget,
            )
        except Exception as exc:
            agent_error = f"AI itinerary failed ({type(exc).__name__}); showing the standard plan."

    flight_range = departure_date_range(datasets["flights"])
    flight_coverage = (
        f"{flight_range[0]} to {flight_range[1]}" if flight_range else "no valid departure dates"
    )
    end_date = start_date + timedelta(days=trip_days - 1)
    reasons = _build_reasons(selected_flight, selected_hotel, places, interests, route_samples)
    trip = {
        "origin": origin,
        "destination": destination,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days": trip_days,
        "interests": interests,
    }
    itinerary = agent_plan["days"] if agent_plan else fallback_itinerary
    export = {
        "trip": trip,
        "flight": selected_flight,
        "fastest_flight": fastest_flight,
        "historic_route_examples": route_samples if not selected_flight else [],
        "hotel": selected_hotel,
        "places": places,
        "weather": weather,
        "budget": budget,
        "itinerary": itinerary,
        "agent_plan": agent_plan,
        "reasons": reasons,
        "data_notes": [
            f"Flight schedule dates cover {flight_coverage}; historic examples are not current offers.",
            "Dataset prices have no currency field; INR is assumed based on the project brief.",
            "Hotel nights are estimated as trip days minus one.",
            "This tool recommends travel options and does not book them.",
        ],
    }
    return {
        "trip": trip,
        "flight_matches": flight_matches,
        "fastest_flight_id": fastest_flight.get("flight_id") if fastest_flight else None,
        "route_samples": route_samples,
        "hotel_matches": hotel_matches,
        "places": places,
        "weather": weather,
        "budget": budget,
        "itinerary": itinerary,
        "flight_coverage": flight_coverage,
        "selected_flight": selected_flight,
        "selected_hotel": selected_hotel,
        "agent_plan": agent_plan,
        "agent_error": agent_error,
        "agent_provider": ai_provider.get("name", "") if ai_provider else "",
        "ai_requested": ai_provider is not None,
        "reasons": reasons,
        "export": export,
    }


def _build_reasons(
    flight: dict[str, Any] | None,
    hotel: dict[str, Any] | None,
    places: list[dict[str, Any]],
    interests: list[str],
    route_samples: list[dict[str, Any]],
) -> list[str]:
    reasons = []
    if hotel:
        if hotel["within_budget"]:
            reasons.append(
                f"{hotel['name']} is the highest-star hotel in the matching results within your nightly budget."
            )
        else:
            reasons.append(
                f"No matching hotel met the nightly budget; {hotel['name']} is the highest-ranked available option."
            )
    if places:
        reasons.append(
            "Attractions were filtered by your selected types and ranked by their supplied ratings."
            if interests
            else "Attractions were ranked by their supplied ratings."
        )
    if flight:
        reasons.append("The selected flight matches the requested route and date and has the lowest listed fare.")
    elif route_samples:
        reasons.append("No current flight matches the requested date; historic route examples are excluded from the estimate.")
    return reasons
