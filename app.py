"""Streamlit entry point for the agentic travel planning assistant."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from travel_assistant.agent import create_agent_plan
from travel_assistant.data import (
    DatasetError,
    departure_date_range,
    find_flights,
    find_route_samples,
    flight_duration_minutes,
    list_cities,
    load_datasets,
    recommend_hotels,
    recommend_places,
)
from travel_assistant.planner import build_itinerary, calculate_budget, format_money
from travel_assistant.weather import get_weather_forecast


load_dotenv()
st.set_page_config(page_title="Travel Planner", page_icon="🧭", layout="wide")


def _setting(name: str) -> str:
    """Read a setting from Streamlit Cloud secrets or a local environment file."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, "")).strip()


@st.cache_data(show_spinner=False)
def cached_datasets() -> dict[str, list[dict[str, Any]]]:
    return load_datasets()


@st.cache_data(ttl=900, show_spinner=False)
def cached_weather(city: str, start: date, days: int) -> dict[str, Any]:
    return get_weather_forecast(city, start, days)


def _format_flight(flight: dict[str, Any], recommendation: str = "") -> dict[str, Any]:
    return {
        "Recommendation": recommendation,
        "Airline": flight.get("airline"),
        "Route": f"{flight.get('from')} → {flight.get('to')}",
        "Departure": flight.get("departure_time"),
        "Arrival": flight.get("arrival_time"),
        "Fare (assumed ₹)": flight.get("price"),
    }


def _format_hotel(hotel: dict[str, Any]) -> dict[str, Any]:
    return {
        "Hotel": hotel.get("name"),
        "City": hotel.get("city"),
        "Stars": hotel.get("stars"),
        "Price/night (assumed ₹)": hotel.get("price_per_night"),
        "Within budget": hotel.get("within_budget"),
        "Amenities": ", ".join(hotel.get("amenities", [])),
    }


def _format_place(place: dict[str, Any]) -> dict[str, Any]:
    return {
        "Attraction": place.get("name"),
        "Type": place.get("type"),
        "Rating": place.get("rating"),
    }


def _render_result(result: dict[str, Any]) -> None:
    trip = result["trip"]
    budget = result["budget"]
    flight = result["flight"]
    hotel = result["hotel"]

    st.divider()
    st.header(f"Your {trip['days']}-day trip to {trip['destination']}")
    st.caption(f"{trip['start_date']} to {trip['end_date']} · From {trip['origin']}")

    if flight is None:
        flight_coverage = result.get("flight_coverage", "the dates represented in the supplied dataset")
        st.warning(
            f"No flight in the dataset matches this route and travel date. The supplied schedule covers {flight_coverage}. "
            "Historic route examples are shown for reference and are not current offers."
        )

    metric_columns = st.columns(3)
    metric_columns[0].metric("Flight", format_money(budget["flight"]))
    metric_columns[1].metric("Hotel", format_money(budget["hotel_total"]))
    total_label = "Estimated total" if budget["complete"] else "Known subtotal"
    metric_columns[2].metric(total_label, format_money(budget["total_estimate"] or budget["known_subtotal"]))
    st.caption(budget["currency"] + ". " + budget["note"])

    if result["agent_plan"]:
        provider_name = result.get("agent_provider") or "LangChain"
        st.success(f"Itinerary assembled with the {provider_name} AI tool-calling agent.")
        agent_plan = result["agent_plan"]
        st.subheader("Trip overview")
        st.write(agent_plan.get("summary", ""))
        itinerary = agent_plan.get("days", [])
    else:
        st.info(
            "Showing a data-grounded itinerary. Add a free Gemini API key in Streamlit secrets "
            "to enable the AI itinerary. [Get a Gemini API key](https://aistudio.google.com/apikey)."
        )
        itinerary = result["itinerary"]
    if result["reasons"]:
        st.write("**Why these options**")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

    st.subheader("Day-by-day itinerary")
    for day_number, day in enumerate(itinerary, start=1):
        title = f"Day {day.get('day', day_number)} · {day.get('date', '')}".strip(" ·")
        with st.expander(title, expanded=True):
            left, right = st.columns(2)
            left.markdown(f"**Morning**  \n{day.get('morning', 'Open time')}")
            right.markdown(f"**Afternoon**  \n{day.get('afternoon', 'Open time')}")
            st.markdown(f"**Evening**  \n{day.get('evening', 'Open time')}")
            st.caption(f"Weather: {day.get('weather', 'Forecast unavailable for this date.')}")

    st.subheader("Flight options")
    if result["flight_matches"]:
        cheapest_id = result["flight_matches"][0]["flight_id"]
        fastest_id = result["fastest_flight_id"]
        rows = []
        for item in result["flight_matches"]:
            labels = []
            if item["flight_id"] == cheapest_id:
                labels.append("Cheapest")
            if item["flight_id"] == fastest_id:
                labels.append("Fastest")
            rows.append(_format_flight(item, " + ".join(labels)))
        st.dataframe(rows, hide_index=True, width="stretch")
    elif result["route_samples"]:
        st.caption("Historic route examples from the supplied dataset; dates and fares are for reference only.")
        st.dataframe(
            [_format_flight(item) for item in result["route_samples"]],
            hide_index=True,
            width="stretch",
        )
    else:
        st.write("No records for this route were found in the supplied flight dataset.")

    st.subheader("Accommodation")
    if result["hotel_matches"]:
        st.dataframe(
            [_format_hotel(item) for item in result["hotel_matches"][:8]],
            hide_index=True,
            width="stretch",
        )
        if hotel:
            st.caption(f"Recommended: {hotel['name']} · {hotel['stars']} stars · {format_money(hotel['price_per_night'])} per night")
            if not hotel["within_budget"]:
                st.caption("No hotel meeting the nightly budget was found at the selected star rating; this option is above your limit.")
    else:
        st.write("No hotels matched the selected city and minimum star rating.")

    st.subheader("Places to visit")
    if result["places"]:
        st.dataframe(
            [_format_place(item) for item in result["places"][:12]],
            hide_index=True,
            width="stretch",
        )
    else:
        st.write("No attractions were found for this destination.")

    st.subheader("Weather")
    weather = result["weather"]
    st.caption(weather["message"])
    if weather.get("days"):
        st.dataframe(weather["days"], hide_index=True, width="stretch")

    st.subheader("Budget breakdown")
    budget_rows = [
        {"Item": "Flight", "Estimate": format_money(budget["flight"])},
        {"Item": f"Hotel ({budget['hotel_nights']} nights)", "Estimate": format_money(budget["hotel_total"])},
        {"Item": f"Food and local travel ({trip['days']} days)", "Estimate": format_money(budget["food_and_local_total"])},
        {"Item": "Known subtotal", "Estimate": format_money(budget["known_subtotal"])},
        {"Item": "Estimated total", "Estimate": format_money(budget["total_estimate"])},
    ]
    st.dataframe(budget_rows, hide_index=True, width="stretch")

    if result["agent_error"]:
        st.warning(result["agent_error"])
    if result["agent_plan"] and result["agent_plan"].get("limitations"):
        st.write("**Planning notes**")
        for note in result["agent_plan"]["limitations"]:
            st.write(f"- {note}")

    st.download_button(
        "Download plan as JSON",
        data=json.dumps(result["export"], ensure_ascii=False, indent=2),
        file_name=f"{trip['destination'].lower()}-trip-plan.json",
        mime="application/json",
    )


def main() -> None:
    st.markdown(
        "<div class='hero'><div class='eyebrow'>TRAVEL PLANNING ASSISTANT</div>"
        "<h1>Plan a trip that fits your days and budget.</h1>"
        "<p>Compare the supplied travel data, check the forecast, and shape a day-by-day itinerary.</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<style>"
        ".hero{padding:1.7rem 2rem;margin:0 0 1.1rem;border-radius:18px;"
        "background:linear-gradient(120deg,#0f766e,#164e63);color:white;}"
        ".hero .eyebrow{font-size:.75rem;letter-spacing:.13em;opacity:.82;font-weight:700;}"
        ".hero h1{font-size:2.2rem;margin:.45rem 0;}"
        ".hero p{font-size:1.05rem;margin:0;opacity:.93;}"
        "</style>",
        unsafe_allow_html=True,
    )

    try:
        datasets = cached_datasets()
    except DatasetError as exc:
        st.error(str(exc))
        st.stop()

    cities = list_cities(datasets)
    if len(cities) < 2:
        st.error("The travel datasets need at least two cities to plan a route.")
        st.stop()

    flight_range = departure_date_range(datasets["flights"])
    if flight_range:
        flight_coverage = f"{flight_range[0]} to {flight_range[1]}"
        if flight_range[1] < date.today():
            st.info(
                f"The supplied flight schedule covers {flight_coverage} and contains only past dates. "
                "Future trips may need a manual flight estimate."
            )
        else:
            st.info(f"The supplied flight schedule covers {flight_coverage}.")
    else:
        flight_coverage = "no valid departure dates"

    provider_keys = {}
    gemini_key = _setting("GEMINI_API_KEY") or _setting("GOOGLE_API_KEY")
    openai_key = _setting("OPENAI_API_KEY")
    if gemini_key:
        provider_keys["Gemini (free tier)"] = (
            "gemini",
            gemini_key,
            _setting("GEMINI_MODEL") or "gemini-3.5-flash-lite",
        )
    if openai_key:
        provider_keys["OpenAI"] = (
            "openai",
            openai_key,
            _setting("OPENAI_MODEL") or "gpt-6-luna",
        )
    with st.sidebar:
        st.header("Trip settings")
        if len(provider_keys) > 1:
            provider_label = st.selectbox("AI provider", list(provider_keys))
        else:
            provider_label = next(iter(provider_keys), "")
        selected_provider = provider_keys.get(provider_label)
        use_agent = st.checkbox(
            "Use AI itinerary",
            value=bool(selected_provider),
            disabled=not bool(selected_provider),
            help="Add GEMINI_API_KEY in .env or Streamlit secrets to use Gemini's free tier.",
        )
        if selected_provider:
            st.caption(f"Provider: {provider_label} · Model: {selected_provider[2]}")
        else:
            st.caption("AI is optional. The planner works without a key. Add a free Gemini key to enable AI.")

    origin_default = cities.index("Delhi") if "Delhi" in cities else 0
    with st.form("trip_request"):
        route_left, route_right = st.columns(2)
        origin = route_left.selectbox("Starting city", cities, index=origin_default)
        destination_options = [city for city in cities if city != origin]
        default_destination = destination_options.index("Goa") if "Goa" in destination_options else 0
        destination = route_right.selectbox("Destination", destination_options, index=default_destination)

        date_column, duration_column = st.columns(2)
        start_date = date_column.date_input(
            "Trip start date",
            value=date.today() + timedelta(days=7),
            min_value=date.today(),
        )
        trip_days = duration_column.slider("Trip length (days)", min_value=3, max_value=7, value=3)

        budget_column, stars_column = st.columns(2)
        max_hotel_price = budget_column.number_input(
            "Maximum hotel price per night (₹)", min_value=0, max_value=100000, value=5000, step=500
        )
        min_stars = stars_column.slider("Minimum hotel stars", min_value=2, max_value=5, value=2)
        daily_local_cost = st.number_input(
            "Food and local travel allowance per day (₹)", min_value=0, max_value=100000, value=2000, step=500
        )
        estimated_flight_cost = st.number_input(
            "Optional flight estimate (₹)",
            min_value=0,
            max_value=500000,
            value=0,
            step=500,
            help="Used only when the dataset has no flight matching your exact route and date. Leave 0 to exclude flights from the total.",
        )
        interest_types = sorted({str(place.get("type", "")).title() for place in datasets["places"] if place.get("type")})
        interests = st.multiselect("Interests", interest_types, help="Choose attraction types to prioritize.")
        submitted = st.form_submit_button("Build my trip plan", type="primary", width="stretch")

    if submitted:
        flight_matches = find_flights(datasets["flights"], origin, destination, start_date)
        route_samples = find_route_samples(datasets["flights"], origin, destination)
        fastest_flight = min(flight_matches, key=flight_duration_minutes) if flight_matches else None
        hotel_matches = recommend_hotels(datasets["hotels"], destination, int(max_hotel_price), min_stars)
        place_matches = recommend_places(datasets["places"], destination, interests)
        selected_flight = flight_matches[0] if flight_matches else None
        selected_hotel = hotel_matches[0] if hotel_matches else None
        selected_flight_cost = int(selected_flight["price"]) if selected_flight else (int(estimated_flight_cost) or None)
        selected_hotel_rate = int(selected_hotel["price_per_night"]) if selected_hotel else None
        weather = cached_weather(destination, start_date, trip_days)
        budget = calculate_budget(trip_days, selected_hotel_rate, int(daily_local_cost), selected_flight_cost)
        fallback_itinerary = build_itinerary(destination, start_date, trip_days, place_matches, weather)

        agent_plan = None
        agent_error = None
        agent_provider_name = provider_label if selected_provider else ""
        if use_agent and selected_provider:
            provider, api_key, model_name = selected_provider
            try:
                agent_plan = create_agent_plan(
                    provider=provider,
                    api_key=api_key,
                    model_name=model_name,
                    origin=origin,
                    destination=destination,
                    start_date=start_date,
                    trip_days=trip_days,
                    interests=interests,
                    flight_matches=flight_matches,
                    route_samples=route_samples,
                    hotel_matches=hotel_matches,
                    place_matches=place_matches,
                    weather=weather,
                    budget=budget,
                )
            except Exception as exc:
                agent_error = f"The AI itinerary could not be generated ({type(exc).__name__}). Showing the data-grounded itinerary instead."

        end_date = start_date + timedelta(days=trip_days - 1)
        reasons = []
        if selected_hotel:
            if selected_hotel["within_budget"]:
                reasons.append(
                    f"{selected_hotel['name']} is the highest-star hotel in the matching results within your nightly budget."
                )
            else:
                reasons.append(
                    f"No matching hotel met the nightly budget; {selected_hotel['name']} is the highest-ranked available option."
                )
        if place_matches:
            if interests:
                reasons.append("Attractions were filtered by your selected types and ranked by their supplied ratings.")
            else:
                reasons.append("Attractions were ranked by their supplied ratings.")
        if selected_flight:
            reasons.append("The selected flight matches the requested route and departure date and has the lowest listed fare.")
        elif route_samples:
            reasons.append("No current flight matches the requested date; historic route examples are excluded from the estimate.")
        export = {
            "trip": {
                "origin": origin,
                "destination": destination,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": trip_days,
                "interests": interests,
            },
            "flight": selected_flight,
            "fastest_flight": fastest_flight,
            "historic_route_examples": route_samples if not selected_flight else [],
            "hotel": selected_hotel,
            "places": place_matches,
            "weather": weather,
            "budget": budget,
            "itinerary": agent_plan["days"] if agent_plan else fallback_itinerary,
            "agent_plan": agent_plan,
            "reasons": reasons,
            "data_notes": [
                f"Flight schedule dates cover {flight_coverage}; historic examples are not current offers.",
                "Dataset prices have no currency field; INR is assumed based on the project brief.",
                "Hotel nights are estimated as trip days minus one.",
                "This tool recommends travel options and does not book them.",
            ],
        }
        st.session_state["trip_result"] = {
            "trip": {
                "origin": origin,
                "destination": destination,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": trip_days,
            },
            "flight": selected_flight,
            "hotel": selected_hotel,
            "flight_matches": flight_matches,
            "fastest_flight_id": fastest_flight["flight_id"] if fastest_flight else None,
            "route_samples": route_samples,
            "hotel_matches": hotel_matches,
            "places": place_matches,
            "weather": weather,
            "budget": budget,
            "itinerary": fallback_itinerary,
            "agent_plan": agent_plan,
            "agent_provider": agent_provider_name,
            "agent_error": agent_error,
            "reasons": reasons,
            "flight_coverage": flight_coverage,
            "export": export,
        }

    if st.session_state.get("trip_result"):
        _render_result(st.session_state["trip_result"])


if __name__ == "__main__":
    main()

