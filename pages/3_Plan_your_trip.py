"""Standalone trip planner page."""

from __future__ import annotations

import os
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

from travel_assistant.cache import get_cached_datasets, get_cached_weather
from travel_assistant.data import DatasetError, departure_date_range, list_cities
from travel_assistant.site import render_listing_styles
from travel_assistant.trip_view import render_trip_result
from travel_assistant.trips import build_trip_plan


load_dotenv()
st.set_page_config(
    page_title="Plan a trip | Trailwise",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)
render_listing_styles()


def setting(name: str) -> str:
    """Read a secret from Streamlit Cloud first, then from the local environment."""
    try:
        secret = st.secrets.get(name, "")
    except Exception:
        secret = ""
    return str(secret or os.getenv(name, "")).strip()


def configured_providers() -> dict[str, dict[str, str]]:
    providers = {}
    gemini_key = setting("GEMINI_API_KEY") or setting("GOOGLE_API_KEY")
    openai_key = setting("OPENAI_API_KEY")
    if gemini_key:
        providers["Gemini (free tier)"] = {
            "name": "Gemini",
            "provider": "gemini",
            "api_key": gemini_key,
            "model": setting("GEMINI_MODEL") or "gemini-3.5-flash-lite",
        }
    if openai_key:
        providers["OpenAI"] = {
            "name": "OpenAI",
            "provider": "openai",
            "api_key": openai_key,
            "model": setting("OPENAI_MODEL") or "gpt-6-luna",
        }
    return providers


try:
    datasets = get_cached_datasets()
except DatasetError as exc:
    st.error(str(exc))
    st.stop()

cities = list_cities(datasets)
if len(cities) < 2:
    st.error("The travel datasets need at least two cities to plan a route.")
    st.stop()

st.title("Plan your trip")
st.caption("Choose a route, dates, and budget to build a practical day-by-day plan.")

providers = configured_providers()
with st.sidebar:
    st.header("AI itinerary")
    provider_label = ""
    if len(providers) > 1:
        provider_label = st.selectbox("AI provider", list(providers), key="plan_ai_provider")
    elif providers:
        provider_label = next(iter(providers))
    selected_provider = providers.get(provider_label)
    use_ai = st.checkbox(
        "Use AI itinerary",
        value=bool(selected_provider),
        key="plan_use_ai",
        help="When an API key is connected, this creates the itinerary with Gemini or OpenAI.",
    )
    if selected_provider:
        st.caption(f"Connected: {provider_label} · {selected_provider['model']}")
    else:
        st.caption("No AI key is connected; the standard planner remains available.")
        with st.expander("Enable free Gemini AI"):
            st.markdown(
                "Create a key in [Google AI Studio](https://aistudio.google.com/apikey), "
                "then add this in Streamlit Cloud Secrets:"
            )
            st.code('GEMINI_API_KEY = "paste_your_key_here"', language="toml")
    if use_ai and not selected_provider:
        st.warning("AI is not connected yet. This trip will use the standard planner until a key is added.")

flight_range = departure_date_range(datasets["flights"])
if flight_range and flight_range[1] < date.today():
    coverage = f"{flight_range[0]} to {flight_range[1]}"
    st.info(f"Flight samples cover {coverage} and are historical. Future trips may need a manual flight estimate.")

with st.form("trip_request"):
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
    start_date = date_col.date_input(
        "Trip start date",
        value=date.today() + timedelta(days=7),
        min_value=date.today(),
    )
    days = duration_col.slider("Trip length (days)", min_value=3, max_value=7, value=3)

    hotel_col, star_col = st.columns(2)
    max_hotel_price = hotel_col.number_input(
        "Maximum hotel price per night (₹)", min_value=0, max_value=100000, value=5000, step=500
    )
    min_stars = star_col.slider("Minimum hotel stars", min_value=2, max_value=5, value=2)
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
    interest_types = sorted({
        str(place.get("type", "")).title()
        for place in datasets["places"]
        if place.get("type")
    })
    interests = st.multiselect("Interests", interest_types)
    submitted = st.form_submit_button("Build my trip plan", type="primary", width="stretch")

if submitted:
    weather = get_cached_weather(destination, start_date, days)
    st.session_state["trip_result"] = build_trip_plan(
        datasets=datasets,
        origin=origin,
        destination=destination,
        start_date=start_date,
        trip_days=days,
        max_hotel_price=int(max_hotel_price),
        min_stars=min_stars,
        daily_local_cost=int(daily_local_cost),
        estimated_flight_cost=int(estimated_flight_cost),
        interests=interests,
        weather=weather,
        ai_provider=selected_provider if use_ai else None,
    )

trip_result = st.session_state.get("trip_result")
if trip_result:
    render_trip_result(trip_result)
