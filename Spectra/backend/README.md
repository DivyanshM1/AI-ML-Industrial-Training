# Spectra backend

FastAPI backend for Spectra, a hybrid movie discovery and recommendation project.

## Requirements
- Python 3.10+
- MovieLens 1M dataset in `../datasets/ml-1m/`

## Setup (from the existing project environment)
Activate the existing root environment, then run from `backend`:

```powershell
python -m pip install -r requirements.txt
python -m scripts.train_model
uvicorn app.main:app --reload
```

The dataset files should be `movies.dat`, `ratings.dat`, and `users.dat`. If needed, run `python -m scripts.prepare_data` from this directory.

## API
- `GET /` API information
- `GET /api/v1/health` model status
- `GET /api/v1/movies/search?q=matrix`
- `GET /api/v1/movies/{movie_id}`
- `GET /api/v1/recommendations/movie/{movie_id}`
- `GET /api/v1/recommendations/user/{user_id}`
- `POST /api/v1/recommendations/profile`
- `POST /api/v1/profiles`
- `GET /api/v1/profiles/{profile_id}`
- `GET /api/v1/profiles/{profile_id}/recommendations`
- `GET /api/v1/users/{user_id}/taste-cluster`

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Model design
- TF-IDF on movie titles and genres for content similarity.
- TruncatedSVD on the user–movie rating matrix for latent collaborative signals.
- A weighted hybrid score for item-to-item and profile recommendations.
- K-Means clustering over learned user factors for taste segmentation.

This is a project/research recommender trained on MovieLens 1M, not a production-scale ranking service. Validate quality with a held-out evaluation before making performance claims.
