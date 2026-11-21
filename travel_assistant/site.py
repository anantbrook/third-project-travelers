"""Shared navigation and presentation helpers for Trailwise pages."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from .photos import hotel_photo, place_photo


def render_site_header(active_page: str = "discover") -> None:
    """Render a compact brand and same-tab page links across the app."""
    st.markdown(
        "<style>"
        ".st-key-site-header{margin:0 0 .8rem}"
        ".st-key-site-header [data-testid='stHorizontalBlock']{align-items:center;gap:.35rem!important}"
        ".st-key-site-header .st-key-site-brand [data-testid='stMarkdownContainer']{padding:.1rem 0}"
        ".site-brand{display:flex;align-items:center;gap:.5rem;color:var(--text-color,inherit);"
        "font-size:1.25rem;font-weight:850;letter-spacing:-.04em;white-space:nowrap}"
        ".brand-mark{display:inline-grid;place-items:center;width:30px;height:30px;"
        "border-radius:10px;background:#00aa75;color:#fff;font-size:1rem}"
        ".st-key-site-header [data-testid='stPageLink']{display:flex;justify-content:center;margin:0}"
        ".st-key-site-header [data-testid='stPageLink'] a{display:flex;justify-content:center;"
        "min-height:2.2rem;padding:.4rem .45rem;border-radius:9px;color:var(--text-color,inherit);"
        "font-size:.86rem;font-weight:650;text-decoration:none!important;white-space:nowrap;"
        "transition:background-color .16s ease,color .16s ease}"
        ".st-key-site-header [data-testid='stPageLink'] a:hover{background:var(--secondary-background-color,rgba(128,144,133,.12))}"
        f".st-key-site-nav-{active_page} [data-testid='stPageLink'] a{{background:var(--secondary-background-color,rgba(128,144,133,.12))}}"
        ".st-key-site-header [data-testid='stPageLink'] a:focus-visible{outline:2px solid var(--primary-color,#087a5b);outline-offset:2px}"
        "@media(max-width:700px){.st-key-site-header [data-testid='stHorizontalBlock']{flex-wrap:wrap!important;gap:.2rem!important}"
        ".st-key-site-header{margin-bottom:.25rem}"
        ".st-key-site-header [data-testid='stHorizontalBlock']>[data-testid='stLayoutWrapper']:has(.st-key-site-brand){flex:0 0 100%!important;width:100%!important}"
        ".st-key-site-header .st-key-site-brand{min-height:2.25rem!important}"
        ".st-key-site-header .st-key-site-brand [data-testid='stMarkdownContainer']{padding:0}"
        ".site-brand{font-size:1.12rem}.brand-mark{width:27px;height:27px}"
        ".st-key-site-header [data-testid='stPageLink'] a{min-height:2rem;padding:.35rem .45rem;font-size:.8rem}}"
        "@media(prefers-reduced-motion:reduce){.st-key-site-header [data-testid='stPageLink'] a{transition:none}}"
        "</style>",
        unsafe_allow_html=True,
    )
    with st.container(key="site-header"):
        link_pages = (
            ("discover", "Discover"),
            ("things", "Things to do"),
            ("stays", "Stays"),
            ("plan", "Plan a trip"),
        )
        pages = st.session_state.get("_trailwise_site_pages", {})
        with st.container(horizontal=True, wrap=True, gap="small", vertical_alignment="center"):
            with st.container(key="site-brand", width="content"):
                st.markdown(
                    "<div class='site-brand'><span class='brand-mark' aria-hidden='true'>✦</span>TRAILWISE</div>",
                    unsafe_allow_html=True,
                    width="content",
                )
            for key, label in link_pages:
                with st.container(key=f"site-nav-{key}", width="content"):
                    st.page_link(pages[key], label=label, width="content")


def render_place_card(place: dict[str, Any]) -> None:
    title = html.escape(str(place.get("name", "Local place")))
    city = html.escape(str(place.get("city", "")))
    category = html.escape(str(place.get("type", "place")).title())
    rating = html.escape(str(place.get("rating", "—")))
    photo = place_photo(place)
    st.markdown(
        f"<article class='listing-card'><div class='listing-photo'>"
        f"<a href='{photo['credit']}' target='_blank' rel='noreferrer' aria-label='Illustrative photo source for {title}'>"
        f"<img src='{photo['url']}' alt='Illustrative {category.lower()} photo for {title} in {city}' loading='lazy' decoding='async'>"
        "<span class='photo-credit'>Illustrative photo · Unsplash ↗</span></a></div>"
        f"<div class='listing-content'><div class='listing-kicker'>{category}</div>"
        f"<h3>{title}</h3><p class='listing-city'>{city}, India</p>"
        f"<div class='listing-rating'><span class='rating-dot'>★</span><strong>{rating}</strong>"
        "<span>sample dataset rating</span></div></div></article>",
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
    photo = hotel_photo(hotel)
    st.markdown(
        f"<article class='listing-card stay-card'><div class='listing-photo'>"
        f"<a href='{photo['credit']}' target='_blank' rel='noreferrer' aria-label='Illustrative photo source for {title}'>"
        f"<img src='{photo['url']}' alt='Illustrative accommodation photo for {title} in {city}' loading='lazy' decoding='async'>"
        "<span class='photo-credit'>Illustrative photo · Unsplash ↗</span></a></div>"
        f"<div class='listing-content'><div class='listing-kicker'>{'★' * stars} stay</div>"
        f"<h3>{title}</h3><p class='listing-city'>{city}, India</p>"
        f"<p class='amenities'>{amenities}</p><div class='stay-price'>₹{price:,}"
        "<span> / night · sample price</span></div></div></article>",
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
        ".block-container{width:100%;max-width:1680px!important;box-sizing:border-box;margin-inline:auto;"
        "padding:2rem clamp(1rem,2vw,2rem) 3rem!important}"
        "[data-testid='stHeader']{background:transparent}"
        ".section-title{margin:1.7rem 0 1rem}.section-title h2{font-size:1.75rem;letter-spacing:-.04em;"
        "color:inherit;margin:0}"
        ".listing-card{display:flex;flex-direction:column;min-width:0;min-height:0;height:100%;box-sizing:border-box;"
        "border:1px solid rgba(128,144,133,.28);border-radius:18px;overflow:hidden;"
        "background:var(--secondary-background-color,rgba(128,144,133,.07));color:var(--text-color,inherit);"
        "box-shadow:0 5px 18px rgba(0,0,0,.06);margin-bottom:.7rem}"
        ".listing-photo{position:relative;display:block;flex:none;height:180px;overflow:hidden;background:#dce9df}"
        ".listing-photo>a{display:block;width:100%;height:100%;position:relative}"
        ".listing-photo img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .25s ease}"
        ".listing-photo a:hover img{transform:scale(1.035)}"
        ".photo-credit{position:absolute;right:.65rem;bottom:.65rem;padding:.3rem .5rem;border-radius:999px;"
        "background:rgba(14,28,25,.78);color:#fff;font-size:.68rem;line-height:1.2}"
        ".listing-content{min-width:0;flex:1;padding:.95rem 1.1rem 1.1rem}"
        ".listing-kicker{color:inherit;font-size:.72rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase}"
        ".listing-card h3{font-size:1.08rem;line-height:1.2;color:inherit;margin:.55rem 0 .25rem}"
        ".listing-city,.amenities{color:inherit;opacity:.72;font-size:.82rem;margin:0}"
        ".listing-rating{display:flex;align-items:center;gap:.42rem;margin-top:.85rem;font-size:.77rem;"
        "color:inherit;opacity:.78}"
        ".listing-rating strong{color:inherit;opacity:1}"
        ".rating-dot{display:inline-grid;place-items:center;width:21px;height:21px;border-radius:50%;"
        "background:#087a5b;color:white;font-size:.72rem}"
        ".stay-card{min-height:0;height:100%}.stay-price{margin-top:.65rem;color:inherit;font-weight:800;font-size:1rem;white-space:nowrap}"
        ".stay-price span{font-size:.76rem;font-weight:500;opacity:.72}"
        ".data-note{padding:.8rem 1rem;border-radius:12px;background:var(--secondary-background-color,rgba(128,144,133,.07));"
        "border:1px solid rgba(128,144,133,.36);color:var(--text-color,inherit);font-size:.78rem}"
        ".destination-preview{position:relative;isolation:isolate;display:flex;align-items:flex-end;min-height:175px;"
        "overflow:hidden;border-radius:18px;margin:.4rem 0 1rem;background:#24423d;color:#fff}"
        ".destination-preview-image{position:absolute;inset:0;z-index:0}.destination-preview img{display:block;width:100%;height:100%;"
        "position:absolute;inset:0;object-fit:cover}.destination-preview:after{content:'';position:absolute;inset:0;z-index:1;"
        "background:linear-gradient(90deg,rgba(8,38,40,.78),rgba(8,38,40,.12))}"
        ".destination-preview-copy{position:relative;z-index:2;padding:1.2rem 1.4rem;max-width:75%}"
        ".destination-preview-copy span{font-size:.68rem;letter-spacing:.1em;font-weight:800;color:#e3f4ea}"
        ".destination-preview-copy h2{margin:.3rem 0;color:#fff;font-size:1.8rem}.destination-preview-credit{position:absolute;"
        "right:.8rem;bottom:.8rem;z-index:3;padding:.28rem .5rem;border-radius:999px;background:rgba(14,28,25,.78);"
        "color:#fff;font-size:.68rem}"
        "@media(max-width:800px){.block-container{padding:2rem 1rem 2.25rem!important}"
        ".listing-photo{height:160px}"
        ".destination-preview{min-height:150px}.destination-preview-copy{padding:1rem;max-width:86%}"
        ".destination-preview-copy h2{font-size:1.45rem}"
        "[data-testid='stHorizontalBlock']{display:flex!important;flex-wrap:wrap!important;gap:.65rem!important}"
        "[data-testid='stHorizontalBlock']>[data-testid='stColumn']{flex:1 1 100%!important;"
        "width:100%!important;min-width:0!important;max-width:100%!important}}"
        "</style>",
        unsafe_allow_html=True,
    )
