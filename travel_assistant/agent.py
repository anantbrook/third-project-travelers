"""Optional LangChain tool-calling agent for assembling trip itineraries."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

def create_agent_plan(
    *,
    provider: str,
    api_key: str,
    model_name: str,
    origin: str,
    destination: str,
    start_date: date,
    trip_days: int,
    interests: list[str],
    flight_matches: list[dict[str, Any]],
    route_samples: list[dict[str, Any]],
    hotel_matches: list[dict[str, Any]],
    place_matches: list[dict[str, Any]],
    weather: dict[str, Any],
    budget: dict[str, Any],
) -> dict[str, Any]:
    """Ask a LangChain agent to call the travel tools and return a typed plan."""
    from langchain.agents import create_agent
    from langchain.tools import tool
    from pydantic import BaseModel, Field

    class DayPlan(BaseModel):
        """One itinerary day in the agent's structured response."""

        date: str = Field(description="Calendar date in YYYY-MM-DD format")
        morning: str
        afternoon: str
        evening: str
        weather: str

    class TripPlan(BaseModel):
        """Typed response returned by the LangChain travel agent."""

        summary: str
        flight_recommendation: str
        hotel_recommendation: str
        days: list[DayPlan]
        budget_summary: str
        reasons: list[str]
        limitations: list[str]

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = ChatGoogleGenerativeAI(
            model=model_name,
            api_key=api_key,
            timeout=35,
            max_retries=1,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(model=model_name, temperature=0, api_key=api_key, timeout=35, max_retries=1)
    else:
        raise ValueError("Unsupported AI provider.")

    @tool
    def search_flights(origin_city: str, destination_city: str, travel_date: str) -> str:
        """Search exact-route and exact-date flights in the provided local dataset."""
        is_requested_route = (
            origin_city.casefold() == origin.casefold()
            and destination_city.casefold() == destination.casefold()
        )
        is_requested_date = travel_date == start_date.isoformat()
        data = flight_matches if is_requested_route and is_requested_date else []
        samples = route_samples if is_requested_route else []
        return json.dumps(
            {
                "date_matches": data[:5],
                "historic_route_examples_with_different_dates": samples[:5],
            },
            ensure_ascii=False,
        )

    @tool
    def recommend_hotels(city: str, maximum_price_per_night: int) -> str:
        """Find hotels in the destination ranked for budget and star preference."""
        if city.casefold() != destination.casefold():
            return "No hotel data is loaded for that city in this trip request."
        selected = [item for item in hotel_matches if item["price_per_night"] <= maximum_price_per_night]
        if not selected:
            selected = hotel_matches[:5]
        return json.dumps(selected[:5], ensure_ascii=False)

    @tool
    def discover_places(city: str, preferred_types: str) -> str:
        """Find destination attractions matching the traveler's interests."""
        if city.casefold() != destination.casefold():
            return "No attraction data is loaded for that city in this trip request."
        requested_types = {item.strip().casefold() for item in preferred_types.split(",") if item.strip()}
        selected = [
            place
            for place in place_matches
            if not requested_types or str(place.get("type", "")).casefold() in requested_types
        ]
        return json.dumps(selected[:12], ensure_ascii=False)

    @tool
    def get_weather(city: str, first_day: str, number_of_days: int) -> str:
        """Return the live forecast already fetched for this destination and date range."""
        if city.casefold() != destination.casefold() or first_day != start_date.isoformat() or number_of_days != trip_days:
            return "Weather was fetched only for the requested destination and travel dates. Do not infer other conditions."
        return json.dumps(weather, ensure_ascii=False)

    @tool
    def get_budget_estimate() -> str:
        """Return the deterministic budget estimate calculated for this trip request."""
        return json.dumps(budget, ensure_ascii=False)

    tools = [search_flights, recommend_hotels, discover_places, get_weather, get_budget_estimate]
    system_prompt = (
        "You are a travel-planning assistant. Call the supplied tools to ground the plan in the local datasets and weather response. "
        "Never invent flights, prices, attractions, or weather. A route example from a different date is historical sample data, not a bookable flight. "
        "If a forecast is unavailable, state that plainly. Return a practical day-wise schedule and short evidence-based reasons; do not provide hidden chain-of-thought. "
        "This application recommends options and does not book travel."
    )
    agent = create_agent(model=model, tools=tools, system_prompt=system_prompt, response_format=TripPlan)
    request = (
        f"Plan a {trip_days}-day trip from {origin} to {destination}, starting {start_date.isoformat()}. "
        f"Interests: {', '.join(interests) if interests else 'no specific type'}. "
        "Use the tools to check the available flight, hotel, attractions, weather, and budget information. "
        "Create a useful morning, afternoon, and evening plan for each day."
    )
    result = agent.invoke({"messages": [{"role": "user", "content": request}]})
    structured = result.get("structured_response")
    if structured is None:
        raise ValueError("The agent did not return a structured itinerary.")
    expected_dates = [(start_date + timedelta(days=index)).isoformat() for index in range(trip_days)]
    if [day.date for day in structured.days] != expected_dates:
        raise ValueError("The agent returned dates that do not match the requested trip.")

    # Keep weather factual even if the model formats or misstates its response.
    forecasts = {item["date"]: item for item in weather.get("days", [])}
    for day in structured.days:
        forecast = forecasts.get(day.date)
        if forecast:
            day.weather = (
                f"{forecast['condition']}; high {forecast['temperature_max_c']}°C, "
                f"low {forecast['temperature_min_c']}°C"
            )
            chance = forecast.get("precipitation_probability_max")
            if chance is not None:
                day.weather += f"; precipitation chance up to {chance}%"
        else:
            day.weather = "Forecast unavailable for this date."
    return structured.model_dump(mode="json")

