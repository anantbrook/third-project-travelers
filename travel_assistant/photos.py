"""Illustrative Unsplash photos used throughout the travel guide."""

from __future__ import annotations

from typing import Any


def _photo(photo_id: str, credit_url: str) -> dict[str, str]:
    return {
        "url": f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=1100&q=85",
        "credit": credit_url,
    }


LOCATION_PHOTOS = {
    "Delhi": _photo(
        "photo-1609258678760-ba05d9b95bb9",
        "https://unsplash.com/photos/people-walking-on-brown-concrete-arch-during-daytime-_q0DyZcOlMY",
    ),
    "Goa": _photo(
        "photo-1512343879784-a960bf40e7f2",
        "https://unsplash.com/s/photos/goa-beaches",
    ),
    "Jaipur": _photo(
        "photo-1578999935853-4ec5fa6c1f60",
        "https://unsplash.com/photos/hawa-mahal-with-many-windows-Gow54BJA3tc",
    ),
    "Mumbai": _photo(
        "photo-1625731226721-b4d51ae70e20",
        "https://unsplash.com/photos/people-walking-near-white-concrete-building-under-blue-sky-during-daytime-xH43OxDSXYw",
    ),
    "Bangalore": _photo(
        "photo-1687158266948-bf538937c74a",
        "https://unsplash.com/photos/a-view-of-a-city-from-the-top-of-a-hill-vJ94Yh36524",
    ),
    "Chennai": _photo(
        "photo-1724992609113-bb30249a2573",
        "https://unsplash.com/photos/an-aerial-view-of-a-city-with-a-beach-in-the-background-Ylw1zy8lUVw",
    ),
    "Hyderabad": _photo(
        "photo-1787044050317-5f3ac3f7c5c0",
        "https://unsplash.com/photos/charminar-monument-in-hyderabad-market-c_KoDTRR43c",
    ),
    "Kolkata": _photo(
        "photo-1663949248565-5fbe5531fa33",
        "https://unsplash.com/photos/a-fountain-in-front-of-a-body-of-water-BFmL4TlWxLs",
    ),
}

HERO_PHOTO = _photo(
    "photo-1523979934836-981ca2ded72f",
    "https://unsplash.com/photos/white-and-brown-concrete-structure--nWdnO-ny2Q",
)

PLACE_PHOTOS = {
    "beach": LOCATION_PHOTOS["Goa"],
    "fort": _photo(
        "photo-1757168896313-4f1fec6c2601",
        "https://unsplash.com/photos/ancient-indian-fort-complex-on-a-lush-green-hill-IzmYU8uIIcw",
    ),
    "temple": _photo(
        "photo-1768728677938-5a44a0fcec26",
        "https://unsplash.com/photos/a-hindu-temple-with-intricate-architecture-and-a-tall-spire-lx9TL7-VUag",
    ),
    "museum": _photo(
        "photo-1733061501621-177e1120b20f",
        "https://unsplash.com/photos/a-large-building-with-a-dome-in-the-background-f0Zr0RNR8V8",
    ),
    "lake": _photo(
        "photo-1632053441013-6128ccc2e7e5",
        "https://unsplash.com/photos/a-body-of-water-with-a-city-in-the-background-3qw4BKxPBRw",
    ),
    "park": _photo(
        "photo-1652912369196-64f0a5d1d837",
        "https://unsplash.com/photos/a-circular-garden-with-trees-and-bushes-in-a-park-fWlxFdhgcOM",
    ),
    "market": _photo(
        "photo-1769634306787-7f2fff1cca7d",
        "https://unsplash.com/photos/people-browsing-stalls-at-a-colorful-outdoor-market-OZnYSO-HHJs",
    ),
    "monument": _photo(
        "photo-1523979934836-981ca2ded72f",
        "https://unsplash.com/photos/white-and-brown-concrete-structure--nWdnO-ny2Q",
    ),
}

_HOTEL_ROOM = _photo(
    "photo-1765423587693-afd93c579a2d",
    "https://unsplash.com/photos/a-neatly-made-hotel-bed-with-pillows-and-lamp-1EL9yeKl6fY",
)
_HOTEL_ROOM_WINDOW = _photo(
    "photo-1702255489644-392758161f1f",
    "https://unsplash.com/photos/a-hotel-room-with-a-bed-chair-and-window-T6WRDVQBn8M",
)
_RESORT_POOL = _photo(
    "photo-1701421016474-09b19faa9f77",
    "https://unsplash.com/photos/a-view-of-a-pool-from-a-hotel-room-oKa061UnJBM",
)
_HERITAGE_HOTEL = _photo(
    "photo-1720070143795-52e5f5ed7eaf",
    "https://unsplash.com/photos/a-large-building-with-a-lawn-in-front-of-it-TvPYUlxXa00",
)

HOTEL_PHOTOS = {
    "grand palace hotel": (_HERITAGE_HOTEL, _HOTEL_ROOM),
    "comfort suites": (_HOTEL_ROOM_WINDOW, _HOTEL_ROOM),
    "green leaf resort": (_RESORT_POOL, PLACE_PHOTOS["park"]),
    "sunrise hotel": (_HOTEL_ROOM, _HOTEL_ROOM_WINDOW),
    "blue lagoon resort": (_RESORT_POOL, PLACE_PHOTOS["beach"]),
    "royal heritage": (_HERITAGE_HOTEL, PLACE_PHOTOS["fort"]),
    "budget stay inn": (_HOTEL_ROOM_WINDOW, _HOTEL_ROOM),
    "sea view resort": (_RESORT_POOL, PLACE_PHOTOS["beach"]),
    "city center hotel": (_HOTEL_ROOM, LOCATION_PHOTOS["Mumbai"]),
}


def location_photo(city: str) -> dict[str, str]:
    return LOCATION_PHOTOS.get(city, LOCATION_PHOTOS["Delhi"])


def place_photo(place: dict[str, Any]) -> dict[str, str]:
    category = str(place.get("type", "")).casefold()
    return PLACE_PHOTOS.get(category, location_photo(str(place.get("city", ""))))


def hotel_photo(hotel: dict[str, Any]) -> dict[str, str]:
    name = str(hotel.get("name", "")).strip().casefold()
    options = HOTEL_PHOTOS.get(name, (_HOTEL_ROOM, _HOTEL_ROOM_WINDOW))
    identifier = str(hotel.get("hotel_id", "0"))
    suffix = "".join(character for character in identifier if character.isdigit())
    variant = int(suffix or 0) % len(options)
    return options[variant]
