"""Render the shared results for a generated trip plan."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import streamlit as st

from .planner import format_money
from .site import render_hotel_card, render_place_card


def render_trip_result(result: dict[str, Any]) -> None:
    trip = result["trip"]
    budget = result["budget"]
    flight = result["selected_flight"]
    hotel = result["selected_hotel"]

    st.divider()
    st.header(f"Your {trip['days']}-day trip to {trip['destination']}")
    st.caption(f"{trip['start_date']} to {trip['end_date']} · From {trip['origin']}")

    if flight is None:
        st.warning(
            f"No flight in the dataset matches this route and travel date. The supplied schedule covers "
            f"{result['flight_coverage']}. Historical samples are shown only for reference."
        )

    metrics = st.columns(3)
    metrics[0].metric("Flight", format_money(budget["flight"]))
    metrics[1].metric("Hotel", format_money(budget["hotel_total"]))
    total_label = "Estimated total" if budget["complete"] else "Known subtotal"
    total = budget["total_estimate"]
    metrics[2].metric(total_label, format_money(total if total is not None else budget["known_subtotal"]))
    st.caption(f"{budget['currency']}. {budget['note']}")

    if result["agent_plan"]:
        st.success(f"Itinerary assembled with {result['agent_provider']}.")
        st.subheader("Trip overview")
        st.write(result["agent_plan"].get("summary", ""))
    elif result["ai_requested"]:
        st.info("AI is unavailable for this request; showing the standard data-grounded plan.")
    if result["agent_error"]:
        st.warning(result["agent_error"])

    if result["reasons"]:
        st.write("**Why these options**")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

    st.subheader("Day-by-day itinerary")
    for index, day in enumerate(result["itinerary"], start=1):
        title = f"Day {day.get('day', index)} · {day.get('date', '')}".strip(" ·")
        with st.expander(title, expanded=index == 1):
            morning, afternoon = st.columns(2)
            morning.markdown(f"**Morning**  \n{day.get('morning', 'Open time')}")
            afternoon.markdown(f"**Afternoon**  \n{day.get('afternoon', 'Open time')}")
            st.markdown(f"**Evening**  \n{day.get('evening', 'Open time')}")
            st.caption(f"Weather: {day.get('weather', 'Forecast unavailable for this date.')}")

    _render_flights(result)
    _render_listings("Accommodation samples", result["hotel_matches"], render_hotel_card)
    _render_listings("Places to visit", result["places"], render_place_card)

    st.subheader("Weather")
    st.caption(result["weather"].get("message", "Forecast unavailable."))
    if result["weather"].get("days"):
        st.dataframe(result["weather"]["days"], hide_index=True, width="stretch")

    st.subheader("Budget breakdown")
    budget_rows = [
        {"Item": "Flight", "Estimate": format_money(budget["flight"])},
        {"Item": f"Hotel ({budget['hotel_nights']} nights)", "Estimate": format_money(budget["hotel_total"])},
        {"Item": f"Food and local travel ({trip['days']} days)", "Estimate": format_money(budget["food_and_local_total"])},
        {"Item": "Known subtotal", "Estimate": format_money(budget["known_subtotal"])},
        {"Item": "Estimated total", "Estimate": format_money(budget["total_estimate"])},
    ]
    st.dataframe(budget_rows, hide_index=True, width="stretch")

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


def _render_flights(result: dict[str, Any]) -> None:
    st.subheader("Flight options")
    flights = result["flight_matches"]
    if flights:
        cheapest_id = flights[0].get("flight_id")
        fastest_id = result["fastest_flight_id"]
        rows = []
        for item in flights[:8]:
            labels = []
            if item.get("flight_id") == cheapest_id:
                labels.append("Cheapest")
            if item.get("flight_id") == fastest_id:
                labels.append("Fastest")
            rows.append(
                {
                    "Recommendation": " + ".join(labels),
                    "Airline": item.get("airline"),
                    "Route": f"{item.get('from')} → {item.get('to')}",
                    "Departure": item.get("departure_time"),
                    "Arrival": item.get("arrival_time"),
                    "Fare (assumed ₹)": item.get("price"),
                }
            )
        st.dataframe(rows, hide_index=True, width="stretch")
    elif result["route_samples"]:
        st.caption("Historical route samples from the supplied dataset; dates and fares are not current offers.")
        rows = [
            {
                "Airline": item.get("airline"),
                "Route": f"{item.get('from')} → {item.get('to')}",
                "Departure": item.get("departure_time"),
                "Arrival": item.get("arrival_time"),
                "Fare (assumed ₹)": item.get("price"),
            }
            for item in result["route_samples"]
        ]
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.info("No flight records for this route are in the supplied dataset.")


def _render_listings(
    title: str,
    records: list[dict[str, Any]],
    render_card: Callable[[dict[str, Any]], None],
) -> None:
    st.subheader(title)
    if not records:
        st.info(f"No {title.lower()} match this trip.")
        return
    for start in range(0, min(6, len(records)), 3):
        columns = st.columns(min(3, len(records) - start))
        for column, record in zip(columns, records[start : start + 3]):
            with column:
                render_card(record)
