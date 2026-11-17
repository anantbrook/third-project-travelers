"""Shared navigation and presentation helpers for Trailwise pages."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st


def render_site_header() -> None:
    """Render the shared brand beneath Streamlit's multipage navigation."""
    st.markdown(
        "<style>"
        ".site-header{font-size:1.35rem;font-weight:850;letter-spacing:-.04em;white-space:nowrap;color:#183b36;padding:.25rem 0 1rem}"
        ".brand-mark{display:inline-grid;place-items:center;width:30px;height:30px;margin-right:.42rem;"
        "border-radius:10px;background:#00aa75;color:white;font-size:1rem}"
        "@media(max-width:700px){.site-header{font-size:1rem}.brand-mark{width:25px;height:25px;margin-right:.25rem}"
        ".site-header{padding-bottom:.55rem}}"
        "</style>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<header class='site-header'><span class='brand-mark'>✦</span>TRAILWISE</header>",
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


def render_listing_styles() -> None:
    st.markdown(
        "<style>"
        ".stApp{background:#f7f8f5;color:#1d2927}.block-container{max-width:1240px;padding-top:1rem;padding-bottom:4rem}"
        "[data-testid='stHeader']{background:transparent}[data-testid='stSidebar']{background:#f0f3ed}"
        ".section-title{margin:2rem 0 1rem}.section-title h2{font-size:1.75rem;letter-spacing:-.04em;color:#1b302c;margin:0}"
        ".listing-card{min-height:170px;height:auto;box-sizing:border-box;padding:1.1rem 1.15rem;border:1px solid #e2e8e1;"
        "border-radius:18px;background:#fff;box-shadow:0 5px 18px rgba(26,56,47,.045);margin-bottom:.7rem}"
        ".listing-kicker{color:#16875f;font-size:.72rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase}"
        ".listing-card h3{font-size:1.08rem;line-height:1.2;color:#253b36;margin:.55rem 0 .25rem}"
        ".listing-city,.amenities{color:#74837e;font-size:.82rem;margin:0}"
        ".listing-rating{display:flex;align-items:center;gap:.42rem;margin-top:.85rem;font-size:.77rem;color:#7b8983}"
        ".listing-rating strong{color:#253b36}.rating-dot{display:inline-grid;place-items:center;width:21px;height:21px;"
        "border-radius:50%;background:#00aa75;color:white;font-size:.72rem}"
        ".stay-card{min-height:205px;height:auto}.stay-price{margin-top:.65rem;color:#213933;font-weight:800;font-size:1rem;white-space:nowrap}"
        ".stay-price span{font-size:.76rem;font-weight:500;color:#7b8983}"
        ".data-note{padding:.8rem 1rem;border-radius:12px;background:#eef4ed;border:1px solid #dfe9df;color:#5c7168;font-size:.78rem}"
        "</style>",
        unsafe_allow_html=True,
    )
