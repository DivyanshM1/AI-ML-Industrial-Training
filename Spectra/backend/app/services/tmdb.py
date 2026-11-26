"""Small TMDB metadata client. The access token stays server-side."""
from __future__ import annotations

import json
import re
import ssl
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from typing import Any

from app.core.config import settings

_API = "https://api.themoviedb.org/3"
_IMAGE = "https://image.tmdb.org/t/p"


def _request(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    token = settings.tmdb_read_access_token
    if not token:
        raise RuntimeError("TMDB is not configured. Add SPECTRA_TMDB_READ_ACCESS_TOKEN to backend/.env and restart the API.")
    query = urllib.parse.urlencode(params or {})
    url = f"{_API}{path}" + (f"?{query}" if query else "")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "Spectra/1.0",
    })
    context = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=15, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def _normalise(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())


@lru_cache(maxsize=4096)
def _match_title(title: str, year: str) -> dict[str, Any] | None:
    clean_title = re.sub(r"\s*\(\d{4}\)$", "", title).strip()
    data = _request("/search/movie", {"query": clean_title, "include_adult": "false", "language": "en-US", "page": 1})
    results = data.get("results", [])
    wanted = _normalise(clean_title)
    exact = [item for item in results if _normalise(item.get("title", "")) == wanted]
    candidates = exact or results[:5]
    if year:
        same_year = [item for item in candidates if (item.get("release_date") or "")[:4] == year]
        if same_year:
            candidates = same_year
    if not candidates:
        return None
    item = max(candidates, key=lambda x: float(x.get("popularity") or 0))
    return {
        "tmdb_id": item.get("id"),
        "poster_url": f"{_IMAGE}/w500{item['poster_path']}" if item.get("poster_path") else None,
        "backdrop_url": f"{_IMAGE}/w1280{item['backdrop_path']}" if item.get("backdrop_path") else None,
        "overview": item.get("overview") or "",
        "release_date": item.get("release_date") or "",
        "vote_average": item.get("vote_average"),
        "vote_count": item.get("vote_count"),
    }


def artwork_for_movies(movies: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return artwork keyed by MovieLens movie_id; tolerate individual misses."""
    if not settings.tmdb_read_access_token:
        return {}
    output: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {}
        for movie in movies:
            title = str(movie.get("title", ""))
            year_match = re.search(r"\((\d{4})\)$", title)
            year = year_match.group(1) if year_match else ""
            futures[pool.submit(_match_title, title, year)] = str(movie.get("movie_id"))
        for future in as_completed(futures):
            key = futures[future]
            try:
                result = future.result()
                if result:
                    output[key] = result
            except Exception:
                # A missing poster or one failed upstream request must not break discovery.
                continue
    return output


def tmdb_status() -> dict[str, Any]:
    return {"configured": bool(settings.tmdb_read_access_token), "provider": "TMDB"}

def _format_tmdb_movie(item: dict[str, Any]) -> dict[str, Any]:
    """Convert a TMDB movie result into Spectra's catalogue format."""
    return {
        "tmdb_id": item.get("id"),
        "title": item.get("title") or item.get("original_title") or "Unknown",
        "original_title": item.get("original_title"),
        "overview": item.get("overview") or "",
        "release_date": item.get("release_date") or "",
        "poster_url": (
            f"{_IMAGE}/w500{item['poster_path']}"
            if item.get("poster_path") else None
        ),
        "backdrop_url": (
            f"{_IMAGE}/w1280{item['backdrop_path']}"
            if item.get("backdrop_path") else None
        ),
        "vote_average": item.get("vote_average"),
        "vote_count": item.get("vote_count"),
        "genre_ids": item.get("genre_ids", []),
        "original_language": item.get("original_language"),
        "popularity": item.get("popularity"),
    }


def _catalogue_request(
    path: str,
    params: dict[str, Any] | None = None
) -> dict[str, Any]:
    data = _request(path, params)

    return {
        "page": data.get("page", 1),
        "total_pages": data.get("total_pages", 0),
        "total_results": data.get("total_results", 0),
        "results": [
            _format_tmdb_movie(item)
            for item in data.get("results", [])
        ],
    }


def trending_movies(window: str = "week", page: int = 1):
    return _catalogue_request(
        f"/trending/movie/{window}",
        {"language": "en-US", "page": page}
    )


def popular_movies(page: int = 1):
    return _catalogue_request(
        "/movie/popular",
        {"language": "en-US", "page": page}
    )


def upcoming_movies(page: int = 1):
    return _catalogue_request(
        "/movie/upcoming",
        {"language": "en-US", "page": page}
    )


def search_tmdb_movies(query: str, page: int = 1):
    return _catalogue_request(
        "/search/movie",
        {
            "query": query,
            "include_adult": "false",
            "language": "en-US",
            "page": page,
        }
    )
