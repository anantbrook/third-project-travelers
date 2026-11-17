"""Stay discovery page."""

from __future__ import annotations

import streamlit as st

from travel_assistant.cache import get_cached_datasets
from travel_assistant.data import DatasetError, list_cities
from travel_assistant.site import render_hotel_card, render_listing_styles


st.set_page_config(
    page_title="Stays | Trailwise",
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
st.title("Stays")
st.caption("Find sample hotels by destination, star level, and nightly budget.")

city_col, stars_col, price_col = st.columns([1.35, 1, 1.5])
city_options = ["All destinations", *cities]
selected_city = st.session_state.get("browse_city", "All destinations")
if selected_city not in city_options:
    selected_city = "All destinations"
with city_col:
    city = st.selectbox("Destination", city_options, index=city_options.index(selected_city), key="stays_destination")
st.session_state["browse_city"] = city
with stars_col:
    min_stars = st.slider("Minimum stars", min_value=1, max_value=5, value=1, key="stays_min_stars")
with price_col:
    max_price = st.slider(
        "Maximum sample nightly price (₹)",
        min_value=1000,
        max_value=10000,
        value=10000,
        step=500,
        key="stays_max_price",
    )

hotels = [
    hotel for hotel in datasets["hotels"]
    if (city == "All destinations" or hotel.get("city") == city)
    and int(hotel.get("stars", 0)) >= min_stars
    and int(hotel.get("price_per_night", 0)) <= max_price
]
hotels.sort(key=lambda item: (int(item.get("price_per_night", 0)), -int(item.get("stars", 0))))

st.markdown(
    "<div class='data-note'>Hotel details and prices are supplied sample data, not live offers or booking availability.</div>",
    unsafe_allow_html=True,
)
st.write(f"Showing {len(hotels)} sample stays. Filters update as you change them.")

if not hotels:
    st.info("No stays match these filters.")
else:
    for start in range(0, len(hotels), 3):
        columns = st.columns(min(3, len(hotels) - start))
        for column, hotel in zip(columns, hotels[start:start + 3]):
            with column:
                render_hotel_card(hotel)
