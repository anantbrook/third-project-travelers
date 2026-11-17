"""Shared navigation and presentation helpers for Trailwise pages."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st


def render_site_header() -> None:
    """Render the shared brand beneath Streamlit's multipage navigation."""
    st.markdown(
        "<style>"
        ".site-header{display:flex;align-items:center;justify-content:flex-start;font-size:1.35rem;"
        "font-weight:850;letter-spacing:-.04em;white-space:nowrap;color:inherit;padding:.25rem 0 .8rem}"
        ".brand{display:flex;align-items:center;gap:.45rem}"
        ".brand-mark{display:inline-grid;place-items:center;width:30px;height:30px;"
        "border-radius:10px;background:#00aa75;color:white;font-size:1rem}"
        "@media(max-width:800px){.site-header{font-size:1.08rem;padding-bottom:.5rem}.brand-mark{width:25px;height:25px}}"
        "</style>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<header class='site-header'><div class='brand'><span class='brand-mark'>✦</span><span>TRAILWISE</span></div></header>",
        unsafe_allow_html=True,
    )


def render_place_card(place: dict[str, Any]) -> None:
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


def render_hotel_card(hotel: dict[str, Any]) -> None:
    title = html.escape(str(hotel.get("name", "Local stay")))
    city = html.escape(str(hotel.get("city", "")))
    stars = _safe_int(hotel.get("stars"))
    price = _safe_int(hotel.get("price_per_night"))
    amenities_data = hotel.get("amenities", [])
    if not isinstance(amenities_data, list):
        amenities_data = []
    amenities = ", ".join(str(item).title() for item in amenities_data[:3])
    amenities = html.escape(amenities or "Details not listed")
    st.markdown(
        f"<article class='listing-card stay-card'><div class='listing-kicker'>{'★' * stars} stay</div>"
        f"<h3>{title}</h3><p class='listing-city'>{city}, India</p>"
        f"<p class='amenities'>{amenities}</p><div class='stay-price'>₹{price:,}"
        "<span> / night · sample price</span></div></article>",
        unsafe_allow_html=True,
    )


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default


def render_listing_styles() -> None:
    st.markdown(
        "<style>"
        ".block-container{width:100%;max-width:1240px;box-sizing:border-box;margin-inline:auto;"
        "padding:1rem clamp(1rem,3vw,2.5rem) 4rem}"
        "[data-testid='stHeader']{background:transparent}"
        ".section-title{margin:1.7rem 0 1rem}.section-title h2{font-size:1.75rem;letter-spacing:-.04em;"
        "color:inherit;margin:0}"
        ".listing-card{min-width:0;min-height:170px;height:auto;box-sizing:border-box;padding:1.1rem 1.15rem;"
        "border:1px solid rgba(128,144,133,.28);border-radius:18px;"
        "background:var(--secondary-background-color,rgba(128,144,133,.07));color:var(--text-color,inherit);"
        "box-shadow:0 5px 18px rgba(0,0,0,.06);margin-bottom:.7rem}"
        ".listing-kicker{color:inherit;font-size:.72rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase}"
        ".listing-card h3{font-size:1.08rem;line-height:1.2;color:inherit;margin:.55rem 0 .25rem}"
        ".listing-city,.amenities{color:inherit;opacity:.72;font-size:.82rem;margin:0}"
        ".listing-rating{display:flex;align-items:center;gap:.42rem;margin-top:.85rem;font-size:.77rem;"
        "color:inherit;opacity:.78}"
        ".listing-rating strong{color:inherit;opacity:1}"
        ".rating-dot{display:inline-grid;place-items:center;width:21px;height:21px;border-radius:50%;"
        "background:#087a5b;color:white;font-size:.72rem}"
        ".stay-card{min-height:205px;height:auto}.stay-price{margin-top:.65rem;color:inherit;font-weight:800;font-size:1rem;white-space:nowrap}"
        ".stay-price span{font-size:.76rem;font-weight:500;opacity:.72}"
        ".data-note{padding:.8rem 1rem;border-radius:12px;background:var(--secondary-background-color,rgba(128,144,133,.07));"
        "border:1px solid rgba(128,144,133,.36);color:var(--text-color,inherit);font-size:.78rem}"
        "@media(max-width:800px){.block-container{padding:.75rem 1rem 3rem!important}"
        "[data-testid='stHorizontalBlock']{display:flex!important;flex-wrap:wrap!important;gap:.65rem!important}"
        "[data-testid='stHorizontalBlock']>[data-testid='stColumn']{flex:1 1 100%!important;"
        "width:100%!important;min-width:0!important;max-width:100%!important}}"
        "</style>",
        unsafe_allow_html=True,
    )
