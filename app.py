"""Streamlit entry point for the agentic travel planning assistant."""

from __future__ import annotations

import html
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


CITY_PHOTOS = {
    "Delhi": {
        "url": "https://images.unsplash.com/photo-1609258678760-ba05d9b95bb9?auto=format&fit=crop&w=1100&q=85",
        "credit": "https://unsplash.com/photos/people-walking-on-brown-concrete-arch-during-daytime-_q0DyZcOlMY",
    },
    "Goa": {
        "url": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1100&q=85",
        "credit": "https://unsplash.com/s/photos/goa-beaches",
    },
    "Jaipur": {
        "url": "https://images.unsplash.com/photo-1578999935853-4ec5fa6c1f60?auto=format&fit=crop&w=1100&q=85",
        "credit": "https://unsplash.com/photos/hawa-mahal-with-many-windows-Gow54BJA3tc",
    },
    "Mumbai": {
        "url": "https://images.unsplash.com/photo-1625731226721-b4d51ae70e20?auto=format&fit=crop&w=1100&q=85",
        "credit": "https://unsplash.com/photos/people-walking-near-white-concrete-building-under-blue-sky-during-daytime-xH43OxDSXYw",
    },
}
HERO_PHOTO = "https://images.unsplash.com/photo-1523979934836-981ca2ded72f?auto=format&fit=crop&w=2000&q=90"


load_dotenv()
st.set_page_config(page_title="Trailwise | India Travel Guide", page_icon="🧭", layout="wide")


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


def _render_place_card(place: dict[str, Any]) -> None:
    title = html.escape(str(place.get("name", "Local place")))
    city = html.escape(str(place.get("city", "")))
    category = html.escape(str(place.get("type", "place")).title())
    rating = html.escape(str(place.get("rating", "—")))
    st.markdown(
        f"<article class='listing-card'><div class='listing-kicker'>{category}</div>"
        f"<h3>{title}</h3><p class='listing-city'>{city}, India</p>"
        f"<div class='listing-rating'><span class='rating-dot'>★</span><strong>{rating}</strong>"
        "<span>sample dataset rating</span></div></article>",
        unsafe_allow_html=True,
    )


def _render_hotel_card(hotel: dict[str, Any]) -> None:
    title = html.escape(str(hotel.get("name", "Local stay")))
    city = html.escape(str(hotel.get("city", "")))
    stars = int(hotel.get("stars", 0))
    price = int(hotel.get("price_per_night", 0))
    amenities = ", ".join(str(item).title() for item in hotel.get("amenities", [])[:3])
    amenities = html.escape(amenities or "Details not listed")
    st.markdown(
        f"<article class='listing-card stay-card'><div class='listing-kicker'>{'★' * stars} stay</div>"
        f"<h3>{title}</h3><p class='listing-city'>{city}, India</p>"
        f"<p class='amenities'>{amenities}</p><div class='stay-price'>₹{price:,}"
        "<span> / night · sample price</span></div></article>",
        unsafe_allow_html=True,
    )


def _render_city_card(city: str, places_count: int, hotels_count: int) -> None:
    photo = CITY_PHOTOS.get(city)
    if not photo:
        return
    safe_city = html.escape(city)
    st.markdown(
        f"<article class='destination-card'><img src='{photo['url']}' alt='{safe_city} destination' loading='lazy'>"
        f"<div class='destination-shade'></div><div class='destination-copy'>"
        f"<span>INDIA · EXPLORE</span><h3>{safe_city}</h3>"
        f"<p>{places_count} places · {hotels_count} stays in this sample</p></div></article>",
        unsafe_allow_html=True,
    )


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
        "<style>"
        ":root{--primary-color:#07966a}.stApp{background:#f7f8f5;color:#1d2927}.block-container{max-width:1240px;padding-top:1rem;padding-bottom:4rem}"
        "[data-testid='stHeader']{background:transparent} [data-testid='stSidebar']{background:#f0f3ed;border-right:1px solid #e2e9e2}"
        ".site-header{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.2rem .15rem 1.15rem;color:#183b36}"
        ".brand{font-size:1.4rem;font-weight:850;letter-spacing:-.04em}.brand-mark{display:inline-grid;place-items:center;"
        "width:30px;height:30px;margin-right:.42rem;border-radius:10px;background:#00aa75;color:white;font-size:1rem}"
        ".site-nav{display:flex;gap:1.5rem;font-size:.92rem;font-weight:650}.site-nav a{color:#294642;text-decoration:none}"
        ".site-meta{color:#56716a;font-size:.85rem;font-weight:650}"
        ".hero{position:relative;isolation:isolate;display:flex;align-items:flex-end;min-height:340px;overflow:hidden;"
        "padding:2.4rem 2.8rem;border-radius:28px;color:#fff;background-image:linear-gradient(90deg,rgba(8,38,40,.82),rgba(8,38,40,.18)),"
        f"url('{HERO_PHOTO}');background-position:center 53%;background-size:cover;box-shadow:0 18px 45px rgba(22,54,47,.16)}}"
        ".hero-copy{max-width:690px}.eyebrow{font-size:.75rem;letter-spacing:.15em;font-weight:800;color:#d5f4df}"
        ".hero h1{font-size:clamp(2.35rem,5vw,4.2rem);line-height:1.02;letter-spacing:-.055em;margin:.65rem 0 1rem;color:#fff}"
        ".hero p{font-size:1.08rem;max-width:590px;line-height:1.55;color:#eef6f1;margin:0}"
        ".section-title{margin:2.35rem 0 1rem}.section-title h2{font-size:1.75rem;letter-spacing:-.04em;color:#1b302c;margin:0}"
        ".section-title p{color:#6b7e78;margin:.35rem 0 0}.destination-card{height:250px;position:relative;overflow:hidden;"
        "border-radius:20px;background:#dce9df;box-shadow:0 8px 24px rgba(29,55,47,.1);transition:transform .2s ease}"
        ".destination-card:hover{transform:translateY(-4px)}.destination-card img{width:100%;height:100%;object-fit:cover;display:block}"
        ".destination-shade{position:absolute;inset:0;background:linear-gradient(180deg,transparent 30%,rgba(11,31,31,.78))}"
        ".destination-copy{position:absolute;left:1rem;right:1rem;bottom:1rem;color:white}.destination-copy span{font-size:.65rem;letter-spacing:.13em;font-weight:800;opacity:.85}"
        ".destination-copy h3{font-size:1.55rem;margin:.2rem 0;color:white}.destination-copy p{font-size:.77rem;margin:0;color:#f1f5f1}"
        ".listing-card{min-height:170px;height:auto;box-sizing:border-box;padding:1.1rem 1.15rem;border:1px solid #e2e8e1;border-radius:18px;background:#fff;"
        "box-shadow:0 5px 18px rgba(26,56,47,.045);margin-bottom:.7rem}.listing-kicker{color:#16875f;font-size:.72rem;font-weight:800;"
        "letter-spacing:.07em;text-transform:uppercase}.listing-card h3{font-size:1.08rem;line-height:1.2;color:#253b36;margin:.55rem 0 .25rem}"
        ".listing-city,.amenities{color:#74837e;font-size:.82rem;margin:0}.listing-rating{display:flex;align-items:center;gap:.42rem;margin-top:.85rem;"
        "font-size:.77rem;color:#7b8983}.listing-rating strong{color:#253b36}.rating-dot{display:inline-grid;place-items:center;"
        "width:21px;height:21px;border-radius:50%;background:#00aa75;color:white;font-size:.72rem}.stay-card{min-height:205px;height:auto}"
        ".stay-price{margin-top:.65rem;color:#213933;font-weight:800;font-size:1rem;white-space:nowrap}.stay-price span{font-size:.76rem;font-weight:500;color:#7b8983}"
        ".photo-note{color:#87928d;font-size:.7rem;margin-top:.6rem}.data-note{padding:.8rem 1rem;border-radius:12px;"
        "background:#eef4ed;border:1px solid #dfe9df;color:#5c7168;font-size:.78rem}"
        "div[data-testid='stForm']{border:1px solid #e3e9e2;background:#fff;border-radius:20px;padding:1rem 1.2rem}"
        "div[data-testid='stFormSubmitButton'] button,div.stButton button[kind='primary']{border-radius:12px;font-weight:750;background:#07966a!important;border-color:#07966a!important;color:#fff!important}"
        "@media(max-width:700px){.site-header{gap:.35rem;align-items:flex-start;flex-wrap:wrap}.brand{font-size:1.15rem;white-space:nowrap;flex:0 0 100%}"
        ".brand-mark{width:25px;height:25px;margin-right:.25rem}.site-nav{gap:.82rem;font-size:.72rem;max-width:calc(100vw - 120px);overflow-x:auto}"
        ".site-meta{display:none}.hero{min-height:300px;padding:1.5rem;border-radius:20px}.destination-card{height:210px}}"
        "</style>"
        "<header class='site-header'><div class='brand'><span class='brand-mark'>✦</span>TRAILWISE</div>"
        "<nav class='site-nav'><a href='#discover'>Discover</a><a href='#stays'>Stays</a>"
        "<a href='#things'>Things to do</a><a href='#planner'>Plan a trip</a></nav>"
        "<div class='site-meta'>INDIA&nbsp;&nbsp; · &nbsp;&nbsp;₹ INR</div></header>"
        "<section class='hero' id='discover'><div class='hero-copy'><div class='eyebrow'>GO A LITTLE FURTHER</div>"
        "<h1>Find your next<br>favorite place.</h1>"
        "<p>Discover memorable places to visit, stays for every kind of trip, and a plan that fits your budget.</p></div></section>",
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
    else:
        flight_coverage = "no valid departure dates"

    st.markdown(
        "<div class='section-title'><h2>Where would you like to go?</h2>"
        "<p>Search the destinations and sample listings included with this travel guide.</p></div>",
        unsafe_allow_html=True,
    )
    city_options = ["All destinations", *cities]
    with st.form("discovery_search"):
        search_scope = st.radio(
            "Browse",
            ["Everything", "Things to do", "Stays"],
            horizontal=True,
            label_visibility="collapsed",
            key="discovery_scope_input",
        )
        search_left, search_right = st.columns([3, 1])
        search_city = search_left.selectbox(
            "Destination",
            city_options,
            index=city_options.index(st.session_state.get("discovery_city", "All destinations")),
            key="discovery_city_input",
        )
        search_submit = search_right.form_submit_button("Search", type="primary", width="stretch")
    if search_submit:
        st.session_state["discovery_scope"] = search_scope
        st.session_state["discovery_city"] = search_city
    active_scope = st.session_state.get("discovery_scope", st.session_state.get("discovery_scope_input", "Everything"))
    active_city = st.session_state.get("discovery_city", st.session_state.get("discovery_city_input", "All destinations"))
    place_records = [
        place for place in datasets["places"]
        if active_city == "All destinations" or place.get("city") == active_city
    ]
    hotel_records = [
        hotel for hotel in datasets["hotels"]
        if active_city == "All destinations" or hotel.get("city") == active_city
    ]
    st.markdown(
        "<div class='data-note'>This guide uses sample project data. Ratings, hotel prices, and flight schedules are not live offers or traveler reviews.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='section-title' id='destinations'><h2>Places that stay with you</h2>"
        "<p>Start with a city, then explore the places and stays in its sample guide.</p></div>",
        unsafe_allow_html=True,
    )
    destination_cities = [city for city in ("Goa", "Jaipur", "Delhi", "Mumbai") if city in cities]
    destination_columns = st.columns(len(destination_cities))
    for column, city in zip(destination_columns, destination_cities):
        with column:
            place_count = sum(place.get("city") == city for place in datasets["places"])
            hotel_count = sum(hotel.get("city") == city for hotel in datasets["hotels"])
            _render_city_card(city, place_count, hotel_count)
    photo_credits = " · ".join(
        f"<a href='{CITY_PHOTOS[city]['credit']}' target='_blank' rel='noreferrer'>{html.escape(city)} photo</a>"
        for city in destination_cities
    )
    st.markdown(
        f"<div class='photo-note'>Destination photos via Unsplash: {photo_credits}. Hero image: "
        "<a href='https://unsplash.com/photos/white-and-brown-concrete-structure--nWdnO-ny2Q' target='_blank' rel='noreferrer'>Taj Mahal</a>.</div>",
        unsafe_allow_html=True,
    )

    if active_scope in {"Everything", "Things to do"}:
        st.markdown(
            "<div class='section-title' id='things'><h2>Things to do</h2>"
            "<p>Popular places from the supplied destination dataset.</p></div>",
            unsafe_allow_html=True,
        )
        top_places = sorted(place_records, key=lambda item: float(item.get("rating", 0)), reverse=True)[:6]
        if top_places:
            for start in range(0, len(top_places), 3):
                place_columns = st.columns(3)
                for column, place in zip(place_columns, top_places[start:start + 3]):
                    with column:
                        _render_place_card(place)
        else:
            st.info("No places are listed for this destination in the sample dataset.")

    if active_scope in {"Everything", "Stays"}:
        st.markdown(
            "<div class='section-title' id='stays'><h2>Stay somewhere you’ll love</h2>"
            "<p>Compare the sample stays by star level, nightly price, and amenities.</p></div>",
            unsafe_allow_html=True,
        )
        top_hotels = sorted(
            hotel_records,
            key=lambda item: (-int(item.get("stars", 0)), int(item.get("price_per_night", 0))),
        )[:6]
        if top_hotels:
            for start in range(0, len(top_hotels), 3):
                hotel_columns = st.columns(3)
                for column, hotel in zip(hotel_columns, top_hotels[start:start + 3]):
                    with column:
                        _render_hotel_card(hotel)
        else:
            st.info("No stays are listed for this destination in the sample dataset.")

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

    st.markdown(
        "<div id='planner' class='section-title'><h2>Plan your trip</h2>"
        "<p>Set your dates, choose a budget, and turn the listings above into a day-by-day plan.</p></div>",
        unsafe_allow_html=True,
    )
    if flight_range and flight_range[1] < date.today():
        st.info(
            f"The supplied flight schedule covers {flight_coverage} and contains only past dates. "
            "Future trips may need a manual flight estimate."
        )
    elif flight_range:
        st.caption(f"Flight sample dates in this project: {flight_coverage}.")

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

