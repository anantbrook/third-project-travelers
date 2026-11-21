"""Streamlit entry point for the agentic travel planning assistant."""

from __future__ import annotations

import html

import streamlit as st

from travel_assistant.cache import get_cached_datasets
from travel_assistant.data import DatasetError, list_cities
from travel_assistant.photos import HERO_PHOTO, LOCATION_PHOTOS
from travel_assistant.site import render_hotel_card, render_listing_styles, render_place_card, render_site_header


st.set_page_config(
    page_title="Trailwise | India Travel Guide",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _render_city_card(city: str, places_count: int, hotels_count: int) -> None:
    photo = LOCATION_PHOTOS.get(city)
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


def _render_home() -> None:
    render_listing_styles()
    render_site_header("discover")
    st.markdown(
        "<style>"
        "[data-testid='stHeader']{background:transparent}"
        ".hero{position:relative;isolation:isolate;display:flex;align-items:flex-end;min-height:340px;overflow:hidden;"
        "padding:2.4rem 2.8rem;border-radius:28px;color:#fff;background-image:linear-gradient(90deg,rgba(8,38,40,.82),rgba(8,38,40,.18)),"
        f"url('{HERO_PHOTO['url']}');background-position:center 53%;background-size:cover;box-shadow:0 18px 45px rgba(22,54,47,.16)}}"
        ".hero-copy{max-width:690px}.eyebrow{font-size:.75rem;letter-spacing:.15em;font-weight:800;color:#d5f4df}"
        ".hero h1{font-size:clamp(2.35rem,5vw,4.2rem);line-height:1.02;letter-spacing:-.055em;margin:.65rem 0 1rem;color:#fff}"
        ".hero p{font-size:1.08rem;max-width:590px;line-height:1.55;color:#eef6f1;margin:0}"
        ".section-title{margin:2.1rem 0 1rem}.section-title h2{font-size:1.75rem;letter-spacing:-.04em;color:inherit;margin:0}"
        ".section-title p{color:inherit;opacity:.72;margin:.35rem 0 0}.destination-card{height:250px;position:relative;overflow:hidden;"
        "border-radius:20px;background:#dce9df;box-shadow:0 8px 24px rgba(29,55,47,.1);transition:transform .2s ease}"
        ".destination-card:hover{transform:translateY(-4px)}.destination-card img{width:100%;height:100%;object-fit:cover;display:block}"
        ".destination-shade{position:absolute;inset:0;background:linear-gradient(180deg,transparent 30%,rgba(11,31,31,.78))}"
        ".destination-copy{position:absolute;left:1rem;right:1rem;bottom:1rem;color:white}.destination-copy span{font-size:.65rem;letter-spacing:.13em;font-weight:800;opacity:.85}"
        ".destination-copy h3{font-size:1.55rem;margin:.2rem 0;color:white}.destination-copy p{font-size:.77rem;margin:0;color:#f1f5f1}"
        ".photo-note{color:inherit;opacity:.64;font-size:.7rem;margin-top:.6rem}"
        "@media(max-width:800px){.hero{min-height:300px;padding:1.5rem;border-radius:20px}"
        ".destination-card{height:210px}.section-title{margin-top:1.5rem}"
        "[data-testid='stHorizontalBlock']{display:flex!important;flex-wrap:wrap!important;gap:.65rem!important}"
        "[data-testid='stHorizontalBlock']>[data-testid='stColumn']{flex:1 1 calc(50% - .65rem)!important;"
        "width:calc(50% - .65rem)!important;min-width:min(100%,240px)!important;max-width:100%!important}}"
        "</style>"
        "<section class='hero' id='discover'><div class='hero-copy'><div class='eyebrow'>GO A LITTLE FURTHER</div>"
        "<h1>Find your next<br>favorite place.</h1>"
        "<p>Discover memorable places to visit, stays for every kind of trip, and a plan that fits your budget.</p></div></section>",
        unsafe_allow_html=True,
    )

    try:
        datasets = get_cached_datasets()
    except DatasetError as exc:
        st.error(str(exc))
        st.stop()

    cities = list_cities(datasets)
    if len(cities) < 2:
        st.error("The travel datasets need at least two cities to plan a route.")
        st.stop()

    st.markdown(
        "<div class='section-title'><h2>Where would you like to go?</h2>"
        "<p>Search the destinations and sample listings included with this travel guide.</p></div>",
        unsafe_allow_html=True,
    )
    city_options = ["All destinations", *cities]
    previous_city = st.session_state.get("discovery_city", "All destinations")
    if previous_city not in city_options:
        previous_city = "All destinations"
    search_scope = st.radio(
        "Browse",
        ["Everything", "Things to do", "Stays"],
        horizontal=True,
        label_visibility="collapsed",
        key="discovery_scope_input",
    )
    search_city = st.selectbox(
        "Destination",
        city_options,
        index=city_options.index(previous_city),
        key="discovery_city_input",
    )
    st.caption("Browse filters update as soon as you change an option.")
    st.session_state["discovery_scope"] = search_scope
    st.session_state["discovery_city"] = search_city
    st.session_state["browse_city"] = search_city
    active_scope = search_scope
    active_city = search_city
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
    destination_cities = [city for city in cities if city in LOCATION_PHOTOS]
    for start in range(0, len(destination_cities), 4):
        city_batch = destination_cities[start : start + 4]
        destination_columns = st.columns(len(city_batch))
        for column, city in zip(destination_columns, city_batch):
            with column:
                place_count = sum(place.get("city") == city for place in datasets["places"])
                hotel_count = sum(hotel.get("city") == city for hotel in datasets["hotels"])
                _render_city_card(city, place_count, hotel_count)
    photo_credits = " · ".join(
        f"<a href='{LOCATION_PHOTOS[city]['credit']}' target='_blank' rel='noreferrer'>{html.escape(city)} photo</a>"
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
                place_columns = st.columns(min(3, len(top_places) - start))
                for column, place in zip(place_columns, top_places[start:start + 3]):
                    with column:
                        render_place_card(place)
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
                hotel_columns = st.columns(min(3, len(top_hotels) - start))
                for column, hotel in zip(hotel_columns, top_hotels[start:start + 3]):
                    with column:
                        render_hotel_card(hotel)
        else:
            st.info("No stays are listed for this destination in the sample dataset.")

    st.markdown(
        "<div id='planner' class='section-title'><h2>Ready to plan your trip?</h2>"
        "<p>Your chosen destination will carry into the trip planner.</p></div>",
        unsafe_allow_html=True,
    )
    st.page_link(
        "pages/3_Plan_your_trip.py",
        label="Open trip planner",
        icon="🧭",
        width="stretch",
    )


def main() -> None:
    pages = {
        "discover": st.Page(_render_home, title="Discover", url_path="discover", default=True),
        "things": st.Page("pages/1_Things_to_do.py", title="Things to do", url_path="things-to-do"),
        "stays": st.Page("pages/2_Stays.py", title="Stays", url_path="stays"),
        "plan": st.Page("pages/3_Plan_your_trip.py", title="Plan a trip", url_path="plan-a-trip"),
    }
    st.session_state["_trailwise_site_pages"] = pages
    selected_page = st.navigation(list(pages.values()), position="hidden")
    selected_page.run()


if __name__ == "__main__":
    main()

