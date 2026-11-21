"""Standalone trip planner page."""

from __future__ import annotations

import html
import os
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

from travel_assistant.cache import get_cached_datasets, get_cached_weather
from travel_assistant.data import (
    DatasetError,
    departure_date_range,
    list_cities,
    recommend_hotels,
    recommend_places,
)
from travel_assistant.photos import location_photo
from travel_assistant.site import render_hotel_card, render_listing_styles, render_place_card, render_site_header
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
render_site_header("plan")


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
provider_label = next(iter(providers), "")
selected_provider = providers.get(provider_label)

flight_range = departure_date_range(datasets["flights"])
if flight_range and flight_range[1] < date.today():
    coverage = f"{flight_range[0]} to {flight_range[1]}"
    st.info(f"Flight samples cover {coverage} and are historical. Future trips may need a manual flight estimate.")

def _clear_previous_plan() -> None:
    st.session_state.pop("trip_result", None)


def _change_origin(city_options: list[str]) -> None:
    origin_value = st.session_state.get("plan_origin")
    destinations = [city for city in city_options if city != origin_value]
    if st.session_state.get("plan_destination") not in destinations:
        browse_city = st.session_state.get("browse_city")
        fallback = "Goa" if "Goa" in destinations else destinations[0]
        st.session_state["plan_destination"] = browse_city if browse_city in destinations else fallback
    _clear_previous_plan()


origin_default = "Delhi" if "Delhi" in cities else cities[0]
if st.session_state.get("plan_origin") not in cities:
    st.session_state["plan_origin"] = origin_default
available_destinations = [city for city in cities if city != st.session_state["plan_origin"]]
browse_city = st.session_state.get("browse_city")
fallback_destination = "Goa" if "Goa" in available_destinations else available_destinations[0]
destination_default = browse_city if browse_city in available_destinations else fallback_destination
if st.session_state.get("plan_destination") not in available_destinations:
    st.session_state["plan_destination"] = destination_default

route_left, route_right = st.columns(2)
origin = route_left.selectbox(
    "Starting city",
    cities,
    key="plan_origin",
    on_change=_change_origin,
    args=(cities,),
)
destinations = [city for city in cities if city != origin]
destination = route_right.selectbox(
    "Destination",
    destinations,
    key="plan_destination",
    on_change=_clear_previous_plan,
)
st.session_state["browse_city"] = destination
preview_slot = st.empty()

date_col, duration_col = st.columns(2)
today = date.today()
saved_start_date = st.session_state.get("plan_start_date")
if not isinstance(saved_start_date, date) or saved_start_date < today:
    st.session_state["plan_start_date"] = today + timedelta(days=7)
start_date = date_col.date_input(
    "Trip start date",
    min_value=today,
    key="plan_start_date",
    on_change=_clear_previous_plan,
)
days = duration_col.slider(
    "Trip length (days)",
    min_value=3,
    max_value=7,
    value=3,
    key="plan_days",
    on_change=_clear_previous_plan,
)

hotel_col, star_col = st.columns(2)
max_hotel_price = hotel_col.number_input(
    "Maximum hotel price per night (₹)",
    min_value=0,
    max_value=100000,
    value=5000,
    step=500,
    key="plan_max_hotel_price",
    on_change=_clear_previous_plan,
)
min_stars = star_col.slider(
    "Minimum hotel stars",
    min_value=2,
    max_value=5,
    value=2,
    key="plan_min_stars",
    on_change=_clear_previous_plan,
)
local_cost_col, flight_cost_col = st.columns(2)
daily_local_cost = local_cost_col.number_input(
    "Food and local travel per day (₹)",
    min_value=0,
    max_value=100000,
    value=2000,
    step=500,
    key="plan_daily_local_cost",
    on_change=_clear_previous_plan,
)
estimated_flight_cost = flight_cost_col.number_input(
    "Optional flight estimate (₹)",
    min_value=0,
    max_value=500000,
    value=0,
    step=500,
    key="plan_estimated_flight_cost",
    help="Used only when the dataset has no flight matching your exact route and date. Leave 0 to exclude flights from the total.",
    on_change=_clear_previous_plan,
)
interest_types = sorted({
    str(place.get("type", "")).title()
    for place in datasets["places"]
    if place.get("type")
})
interests = st.multiselect(
    "Interests",
    interest_types,
    key="plan_interests",
    on_change=_clear_previous_plan,
)

use_ai = st.checkbox(
    "Use AI for this itinerary (optional)",
    value=False,
    key="plan_use_ai_opt_in",
    help="When enabled, your trip request is sent to the connected provider and uses its quota or billing.",
    on_change=_clear_previous_plan,
)
with st.expander("AI provider settings", expanded=False):
    if len(providers) > 1:
        provider_label = st.selectbox("AI provider", list(providers), key="plan_ai_provider")
        selected_provider = providers.get(provider_label)
    if selected_provider:
        st.caption(f"Connected: {provider_label} · {selected_provider['model']}")
        st.caption("The connected provider is used only when the AI option above is enabled.")
    else:
        st.caption("No AI key is connected; the standard planner works without one.")
        st.markdown(
            "Create a free Gemini key in [Google AI Studio](https://aistudio.google.com/apikey), "
            "then add it in Streamlit Cloud Secrets:"
        )
        st.code('GEMINI_API_KEY = "paste_your_key_here"', language="toml")
if selected_provider:
    st.caption(f"{provider_label} is connected and will only be used when AI is enabled above.")
elif use_ai:
    st.warning("No AI provider is connected. This trip will use the standard planner.")

submitted = st.button("Build my trip plan", type="primary", width="stretch")

if submitted:
    st.session_state.pop("trip_result", None)
    try:
        with st.spinner("Checking the forecast and building your trip plan…"):
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
    except Exception as exc:
        st.error(f"Could not build this trip plan: {exc}")

trip_result = st.session_state.get("trip_result")
if trip_result:
    render_trip_result(trip_result)
else:
    photo = location_photo(destination)
    safe_destination = html.escape(destination)
    with preview_slot.container():
        st.subheader(f"A first look at {destination}")
        st.markdown(
            f"<div class='destination-preview'><a class='destination-preview-image' href='{photo['credit']}' target='_blank' rel='noreferrer' "
            f"aria-label='Open the illustrative {safe_destination} photo source'>"
            f"<img src='{photo['url']}' alt='Illustrative destination photo for {safe_destination}' loading='lazy' decoding='async'></a>"
            f"<div class='destination-preview-copy'><span>DESTINATION PREVIEW</span><h2>{safe_destination}</h2>"
            "<span>Sample guide · representative destination photo</span></div>"
            f"<a class='destination-preview-credit' href='{photo['credit']}' target='_blank' rel='noreferrer'>Photo source ↗</a></div>",
            unsafe_allow_html=True,
        )
        preview_places = recommend_places(datasets["places"], destination, interests)
        city_hotels = recommend_hotels(datasets["hotels"], destination, int(max_hotel_price), min_stars)
        preview_hotel = next((hotel for hotel in city_hotels if hotel["within_budget"]), None)
        preview_cols = st.columns(2)
        with preview_cols[0]:
            st.caption("SAMPLE PLACE")
            if preview_places:
                render_place_card(preview_places[0])
            else:
                st.info("No sample places are listed for this destination.")
        with preview_cols[1]:
            st.caption("SAMPLE STAY THAT FITS YOUR FILTERS")
            if preview_hotel:
                render_hotel_card(preview_hotel)
            else:
                st.info("No sample stay matches these filters. Try a higher price or a lower star level.")
