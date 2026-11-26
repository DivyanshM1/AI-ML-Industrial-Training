from pydantic import BaseModel, Field
from typing import Optional

class MovieOut(BaseModel):
    movie_id: int
    title: str
    genres: str
    year: Optional[int] = None

class RecommendationOut(BaseModel):
    movie_id: int
    title: str
    genres: str
    score: float
    reason: str = "Recommended based on your taste"

class ProfileRating(BaseModel):
    movie_id: int
    rating: float = Field(ge=0.5, le=5.0)

class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    ratings: list[ProfileRating] = Field(min_length=1)

class ProfileOut(BaseModel):
    profile_id: int
    name: str
    ratings_count: int

class ProfileRecommendationRequest(BaseModel):
    ratings: list[ProfileRating] = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
