"""Standalone trip builder page."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta

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
from travel_assistant.site import render_listing_styles
from travel_assistant.weather import get_weather_forecast


load_dotenv()
st.set_page_config(
    page_title="Plan a trip | Trailwise",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)
render_listing_styles()


def setting(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, "")).strip()


@st.cache_data(show_spinner=False)
def get_datasets():
    return load_datasets()


@st.cache_data(ttl=900, show_spinner=False)
def get_weather(city: str, start: date, days: int):
    return get_weather_forecast(city, start, days)


try:
    datasets = get_datasets()
except DatasetError as exc:
    st.error(str(exc))
    st.stop()

cities = list_cities(datasets)
st.title("Plan your trip")
st.caption("Choose a route, dates, and budget to build a practical day-by-day plan.")

provider_keys = {}
gemini_key = setting("GEMINI_API_KEY") or setting("GOOGLE_API_KEY")
openai_key = setting("OPENAI_API_KEY")
if gemini_key:
    provider_keys["Gemini (free tier)"] = ("gemini", gemini_key, setting("GEMINI_MODEL") or "gemini-3.5-flash-lite")
if openai_key:
    provider_keys["OpenAI"] = ("openai", openai_key, setting("OPENAI_MODEL") or "gpt-6-luna")

with st.sidebar:
    st.header("AI itinerary")
    provider_label = ""
    if len(provider_keys) > 1:
        provider_label = st.selectbox("AI provider", list(provider_keys), key="plan_ai_provider")
    elif provider_keys:
        provider_label = next(iter(provider_keys))
    selected_provider = provider_keys.get(provider_label)
    use_ai = st.checkbox(
        "Use AI itinerary",
        value=bool(selected_provider),
        key="plan_use_ai",
        help="When an API key is connected, this creates the itinerary with Gemini or OpenAI.",
    )
    if selected_provider:
        st.caption(f"Connected: {provider_label} · {selected_provider[2]}")
    else:
        st.caption("No AI key is connected; the standard planner remains available.")
        with st.expander("Enable free Gemini AI"):
            st.markdown("Create a key in [Google AI Studio](https://aistudio.google.com/apikey), then add this in Streamlit Cloud Secrets:")
            st.code('GEMINI_API_KEY = "paste_your_key_here"', language="toml")
    if use_ai and not selected_provider:
        st.warning("AI is not connected yet. This trip will use the standard planner until a key is added.")

flight_range = departure_date_range(datasets["flights"])
if flight_range:
    coverage = f"{flight_range[0]} to {flight_range[1]}"
    if flight_range[1] < date.today():
        st.info(f"Flight samples cover {coverage} and are historical. Future trips may need a manual flight estimate.")
else:
    coverage = "no valid departure dates"

with st.form("standalone_trip_request"):
    route_left, route_right = st.columns(2)
    origin_default = cities.index("Delhi") if "Delhi" in cities else 0
    origin = route_left.selectbox("Starting city", cities, index=origin_default)
    destinations = [city for city in cities if city != origin]
    browse_city = st.session_state.get("browse_city")
    if browse_city not in destinations:
        browse_city = "Goa" if "Goa" in destinations else destinations[0]
    destination_default = destinations.index(browse_city)
    destination = route_right.selectbox("Destination", destinations, index=destination_default)

    date_col, duration_col = st.columns(2)
    start_date = date_col.date_input("Trip start date", value=date.today() + timedelta(days=7), min_value=date.today())
    days = duration_col.slider("Trip length (days)", min_value=3, max_value=7, value=3)

    hotel_col, star_col = st.columns(2)
    max_hotel_price = hotel_col.number_input("Maximum hotel price per night (₹)", 0, 100000, 5000, 500)
    min_stars = star_col.slider("Minimum hotel stars", min_value=2, max_value=5, value=2)
    daily_local_cost = st.number_input("Food and local travel allowance per day (₹)", 0, 100000, 2000, 500)
    estimated_flight_cost = st.number_input("Optional flight estimate (₹)", 0, 500000, 0, 500)
    interest_types = sorted({str(place.get("type", "")).title() for place in datasets["places"] if place.get("type")})
    interests = st.multiselect("Interests", interest_types)
    submitted = st.form_submit_button("Build my trip plan", type="primary", width="stretch")

if submitted:
    flight_matches = find_flights(datasets["flights"], origin, destination, start_date)
    route_samples = find_route_samples(datasets["flights"], origin, destination)
    fastest_flight = min(flight_matches, key=flight_duration_minutes) if flight_matches else None
    hotel_matches = recommend_hotels(datasets["hotels"], destination, int(max_hotel_price), min_stars)
    places = recommend_places(datasets["places"], destination, interests)
    flight = flight_matches[0] if flight_matches else None
    hotel = hotel_matches[0] if hotel_matches else None
    flight_cost = int(flight["price"]) if flight else (int(estimated_flight_cost) or None)
    hotel_rate = int(hotel["price_per_night"]) if hotel else None
    weather = get_weather(destination, start_date, days)
    budget = calculate_budget(days, hotel_rate, int(daily_local_cost), flight_cost)
    itinerary = build_itinerary(destination, start_date, days, places, weather)
    agent_plan = None
    if use_ai and selected_provider:
        provider, api_key, model_name = selected_provider
        try:
            agent_plan = create_agent_plan(
                provider=provider,
                api_key=api_key,
                model_name=model_name,
                origin=origin,
                destination=destination,
                start_date=start_date,
                trip_days=days,
                interests=interests,
                flight_matches=flight_matches,
                route_samples=route_samples,
                hotel_matches=hotel_matches,
                place_matches=places,
                weather=weather,
                budget=budget,
            )
        except Exception as exc:
            st.warning(f"AI itinerary failed ({type(exc).__name__}); showing the standard plan.")

    st.subheader(f"Your {days}-day trip to {destination}")
    metrics = st.columns(3)
    metrics[0].metric("Flight", format_money(budget["flight"]))
    metrics[1].metric("Hotel", format_money(budget["hotel_total"]))
    total_label = "Estimated total" if budget["complete"] else "Known subtotal"
    metrics[2].metric(total_label, format_money(budget["total_estimate"] or budget["known_subtotal"]))
    st.caption(budget["currency"] + ". " + budget["note"])

    if agent_plan:
        st.success(f"Itinerary assembled with {provider_label}.")
        st.write(agent_plan.get("summary", ""))
        itinerary = agent_plan.get("days", itinerary)
    elif use_ai and not selected_provider:
        st.info("Using the standard data-grounded planner. Add a Gemini key in the sidebar setup to enable AI.")

    st.subheader("Day-by-day itinerary")
    for index, day in enumerate(itinerary, start=1):
        title = f"Day {day.get('day', index)} · {day.get('date', '')}".strip(" ·")
        with st.expander(title, expanded=True):
            left, right = st.columns(2)
            left.markdown(f"**Morning**  \n{day.get('morning', 'Open time')}")
            right.markdown(f"**Afternoon**  \n{day.get('afternoon', 'Open time')}")
            st.markdown(f"**Evening**  \n{day.get('evening', 'Open time')}")
            st.caption(f"Weather: {day.get('weather', 'Forecast unavailable for this date.')}")

    if flight_matches:
        st.subheader("Flight samples")
        st.dataframe(
            [{"Airline": item.get("airline"), "Route": f"{item.get('from')} → {item.get('to')}",
              "Departure": item.get("departure_time"), "Arrival": item.get("arrival_time"), "Fare (assumed ₹)": item.get("price")}
             for item in flight_matches[:8]],
            hide_index=True,
            width="stretch",
        )
    elif route_samples:
        st.caption(f"No flight matches the requested date. Historical route samples cover {coverage}.")

    if hotel_matches:
        st.subheader("Accommodation samples")
        for start in range(0, min(6, len(hotel_matches)), 3):
            columns = st.columns(min(3, len(hotel_matches) - start))
            for column, hotel_item in zip(columns, hotel_matches[start:start + 3]):
                with column:
                    from travel_assistant.site import render_hotel_card
                    render_hotel_card(hotel_item)
    if places:
        st.subheader("Places to visit")
        for start in range(0, min(6, len(places)), 3):
            columns = st.columns(min(3, len(places) - start))
            for column, place in zip(columns, places[start:start + 3]):
                with column:
                    from travel_assistant.site import render_place_card
                    render_place_card(place)

    export = {
        "origin": origin,
        "destination": destination,
        "start_date": start_date.isoformat(),
        "days": days,
        "budget": budget,
        "itinerary": itinerary,
        "flight": flight,
        "hotel": hotel,
        "places": places,
        "weather": weather,
        "ai_plan": agent_plan,
    }
    st.download_button(
        "Download trip plan as JSON",
        data=json.dumps(export, ensure_ascii=False, indent=2, default=str),
        file_name=f"{destination.lower()}-trip-plan.json",
        mime="application/json",
    )
