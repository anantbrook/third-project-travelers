"""Shared Streamlit caches for data reused across travel pages."""

from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

from .data import load_datasets
from .weather import get_weather_forecast


@st.cache_data(ttl=300, show_spinner=False)
def get_cached_datasets() -> dict[str, list[dict[str, Any]]]:
    """Load the project datasets once per Streamlit cache lifetime."""
    return load_datasets()


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_weather(city: str, start: date, days: int) -> dict[str, Any]:
    """Cache weather requests so page reruns do not repeat network calls."""
    return get_weather_forecast(city, start, days)
