
from fastapi import APIRouter, HTTPException, Query

from app.schemas import (
    ProfileCreate,
    ProfileOut,
    ProfileRecommendationRequest,
)
from app.database import create_profile, get_profile

from app.services.tmdb import (
    artwork_for_movies,
    tmdb_status,
    trending_movies,
    popular_movies,
    upcoming_movies,
    search_tmdb_movies,
)

router = APIRouter()
_engine = None


def set_engine(engine):
    global _engine
    _engine = engine


def engine_or_503():
    if _engine is None:
        raise HTTPException(
            status_code=503,
            detail="Recommendation model is not loaded."
        )
    return _engine


def tmdb_request_or_error(callback):
    try:
        return callback()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"TMDB request failed: {exc}"
        )


# HEALTH AND TMDB STATUS

@router.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": _engine is not None,
        "tmdb_configured": tmdb_status()["configured"],
    }


@router.get("/tmdb/status")
def tmdb_health():
    return tmdb_status()


# TMDB CATALOGUE

@router.get("/movies/trending")
def get_trending_movies(
    window: str = Query(default="week", pattern="^(day|week)$"),
    page: int = Query(default=1, ge=1, le=500),
):
    return tmdb_request_or_error(
        lambda: trending_movies(window, page)
    )


@router.get("/movies/popular")
def get_popular_movies(
    page: int = Query(default=1, ge=1, le=500),
):
    return tmdb_request_or_error(
        lambda: popular_movies(page)
    )


@router.get("/movies/upcoming")
def get_upcoming_movies(
    page: int = Query(default=1, ge=1, le=500),
):
    return tmdb_request_or_error(
        lambda: upcoming_movies(page)
    )


@router.get("/tmdb/search")
def search_tmdb_catalogue(
    q: str = Query(min_length=1),
    page: int = Query(default=1, ge=1, le=500),
):
    return tmdb_request_or_error(
        lambda: search_tmdb_movies(q, page)
    )


# MOVIE ARTWORK

@router.get("/movies/artwork")
def movies_artwork(
    movie_ids: str = Query(
        min_length=1,
        description="Comma-separated MovieLens movie IDs"
    )
):
    engine = engine_or_503()
    ids = []

    for value in movie_ids.split(",")[:40]:
        try:
            ids.append(int(value.strip()))
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="movie_ids must contain comma-separated integers"
            )

    movies = [engine.get_movie(movie_id) for movie_id in ids]
    movies = [movie for movie in movies if movie is not None]

    return artwork_for_movies(movies)


# MOVIELENS SEARCH AND MOVIE DETAILS

@router.get("/movies/search")
def search_movies(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=50)
):
    return engine_or_503().search_movies(q, limit)


@router.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = engine_or_503().get_movie(movie_id)

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    return movie


# RECOMMENDATIONS

@router.get("/recommendations/movie/{movie_id}")
def recommendations_for_movie(
    movie_id: int,
    limit: int = Query(default=10, ge=1, le=50)
):
    engine = engine_or_503()

    if engine.get_movie(movie_id) is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    return engine.recommend_for_movie(movie_id, limit)


@router.get("/recommendations/user/{user_id}")
def recommendations_for_user(
    user_id: int,
    limit: int = Query(default=10, ge=1, le=50)
):
    engine = engine_or_503()

    if user_id not in engine.user_id_to_idx:
        raise HTTPException(
            status_code=404,
            detail="User not found in MovieLens dataset"
        )

    return engine.recommend_for_user(user_id, limit)


@router.post("/recommendations/profile")
def recommendations_for_profile(
    payload: ProfileRecommendationRequest
):
    engine = engine_or_503()

    return engine.recommend_for_profile(
        [r.model_dump() for r in payload.ratings],
        payload.limit
    )


# USER PROFILES

@router.post("/profiles", response_model=ProfileOut)
def save_profile(payload: ProfileCreate):
    engine = engine_or_503()

    unknown = [
        r.movie_id
        for r in payload.ratings
        if r.movie_id not in engine.movie_id_to_idx
    ]

    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown movie IDs: {unknown[:10]}"
        )

    profile_id = create_profile(
        payload.name,
        [r.model_dump() for r in payload.ratings]
    )

    return {
        "profile_id": profile_id,
        "name": payload.name,
        "ratings_count": len(payload.ratings)
    }


@router.get("/profiles/{profile_id}")
def read_profile(profile_id: int):
    profile = get_profile(profile_id)

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "profile_id": profile["profile_id"],
        "name": profile["name"],
        "ratings": profile["ratings"]
    }


@router.get("/profiles/{profile_id}/recommendations")
def profile_recommendations(
    profile_id: int,
    limit: int = Query(default=10, ge=1, le=50)
):
    engine = engine_or_503()
    profile = get_profile(profile_id)

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return engine.recommend_for_profile(profile["ratings"], limit)


@router.get("/users/{user_id}/taste-cluster")
def user_taste_cluster(user_id: int):
    result = engine_or_503().get_user_cluster(user_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User not found in MovieLens dataset"
        )

    return result
