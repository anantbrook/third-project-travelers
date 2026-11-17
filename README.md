# Agentic AI-Based Travel Planning Assistant

A Streamlit trip planner built around the supplied flights, hotels, and places JSON files. It filters and ranks local records, requests a live weather forecast from Open-Meteo, estimates trip costs, and creates a 3-7 day itinerary. With a Gemini free-tier or OpenAI API key configured, a LangChain tool-calling agent assembles the itinerary. Without a key, the app still produces a deterministic plan from the same data.

## Project contents

- app.py: Streamlit user interface.
- travel_assistant/data.py: JSON loading, validation, and dataset search.
- travel_assistant/weather.py: Open-Meteo daily forecast integration.
- travel_assistant/planner.py: Budget calculations and non-LLM itinerary fallback.
- travel_assistant/agent.py: LangChain tools and structured itinerary generation.
- flights.json, hotels.json, places.json: supplied local datasets.

## Run locally

On Windows, double-click `run_travel_planner.bat`. It creates the virtual environment if needed, installs dependencies, and starts Streamlit.

Or run the steps manually:

1. Use Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Install dependencies with `python -m pip install -r requirements.txt`.
4. Copy `.env.example` to `.env`. For the free Gemini API tier, get a key at [Google AI Studio](https://aistudio.google.com/apikey) and set `GEMINI_API_KEY`. The default model is `gemini-3.5-flash-lite`; change it with `GEMINI_MODEL`. OpenAI is also supported with `OPENAI_API_KEY` and `OPENAI_MODEL`.
5. Start the app with `streamlit run app.py`.

The planner works without an API key. In that mode, it uses deterministic filtering and ranking to build the day plan. Open-Meteo weather lookup does not need a key.

## Data notes

The supplied flight records cover January through December 2025. They are historical examples and do not provide current flight availability. The app searches for an exact route and date and does not present a flight from another date as a current offer. Add a manual flight estimate in the form if you want it included in the budget.

Hotel prices and flight fares do not include a currency field. The interface assumes Indian rupees based on the project brief and labels that assumption. Hotel nights are estimated as trip length minus one. Food and local travel cost is an editable per-day estimate.

The places dataset does not contain coordinates. Weather uses a small city-coordinate mapping for the eight cities present in the supplied files. Open-Meteo forecasts are available up to 16 days ahead; dates outside that window are clearly marked unavailable.

This app provides recommendations only. It does not make reservations or purchases.

## Configuration

The optional agent uses LangChain's `create_agent` API and structured output. Gemini's free tier has provider-set usage limits, and Google may use free-tier prompts to improve its products. For Streamlit Community Cloud, add `GEMINI_API_KEY` in the app's Secrets settings. Do not commit `.env` or put API keys in source files.

## Documentation

- [LangChain agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain tools](https://docs.langchain.com/oss/python/langchain/tools)
- [Open-Meteo forecast API](https://open-meteo.com/en/docs)
- [Streamlit API reference](https://docs.streamlit.io/develop/api-reference)


