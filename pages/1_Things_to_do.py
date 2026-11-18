"""Attraction discovery page."""

from __future__ import annotations

import streamlit as st

from travel_assistant.cache import get_cached_datasets
from travel_assistant.catalog import PLACE_SORT_OPTIONS, filter_places, sort_places
from travel_assistant.data import DatasetError, list_cities
from travel_assistant.site import render_listing_styles, render_place_card


st.set_page_config(
    page_title="Things to do | Trailwise",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)
render_listing_styles()


try:
    datasets = get_cached_datasets()
except DatasetError as exc:
    st.error(str(exc))
    st.stop()

cities = list_cities(datasets)
st.title("Things to do")
st.caption("Explore sample attractions and filter them by destination or category.")

selected_city = st.session_state.get("browse_city", "All destinations")
city_options = ["All destinations", *cities]
if selected_city not in city_options:
    selected_city = "All destinations"
city_col, search_col = st.columns([1, 1.4])
with city_col:
    city = st.selectbox("Destination", city_options, index=city_options.index(selected_city), key="things_destination")
with search_col:
    query = st.text_input("Search places", placeholder="Name, city, or category", key="things_search_query")
st.session_state["browse_city"] = city

categories = sorted({str(place.get("type", "")).title() for place in datasets["places"] if place.get("type")})
category_col, sort_col = st.columns([1.4, 1])
with category_col:
    selected_categories = st.multiselect("Category", categories, key="things_categories")
with sort_col:
    sort_by = st.selectbox("Sort by", PLACE_SORT_OPTIONS, key="things_sort_by")
places = sort_places(
    filter_places(
        datasets["places"],
        city=city,
        categories=selected_categories,
        query=query,
    ),
    sort_by,
)

st.markdown(
    "<div class='data-note'>Attraction names and ratings are supplied sample data, not live listings or traveler reviews.</div>",
    unsafe_allow_html=True,
)
st.write(f"Showing {len(places)} of {len(datasets['places'])} sample places. Filters update as you change them.")

if not places:
    st.info("No places match the selected destination and category.")
else:
    for start in range(0, len(places), 3):
        columns = st.columns(min(3, len(places) - start))
        for column, place in zip(columns, places[start:start + 3]):
            with column:
                render_place_card(place)
