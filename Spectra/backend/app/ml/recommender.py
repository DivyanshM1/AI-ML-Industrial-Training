from __future__ import annotations
import re
from typing import Iterable
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

class RecommenderEngine:
    """Hybrid recommender combining movie metadata and collaborative signals."""
    def __init__(self, movies: pd.DataFrame, ratings: pd.DataFrame, n_components: int = 50, n_clusters: int = 8):
        self.movies = movies.copy().reset_index(drop=True)
        self.ratings = ratings.copy()
        self.movie_ids = self.movies["movie_id"].astype(int).tolist()
        self.movie_id_to_idx = {movie_id: idx for idx, movie_id in enumerate(self.movie_ids)}
        self.user_ids = sorted(self.ratings["user_id"].astype(int).unique().tolist())
        self.user_id_to_idx = {user_id: idx for idx, user_id in enumerate(self.user_ids)}
        self._build_content_model()
        self._build_collaborative_model(n_components, n_clusters)

    @staticmethod
    def load_dataset(dataset_dir):
        dataset_dir = str(dataset_dir)
        movies = pd.read_csv(f"{dataset_dir}/movies.dat", sep="::", engine="python", names=["movie_id", "title", "genres"], encoding="latin-1")
        ratings = pd.read_csv(f"{dataset_dir}/ratings.dat", sep="::", engine="python", names=["user_id", "movie_id", "rating", "timestamp"], encoding="latin-1")
        movies["movie_id"] = movies["movie_id"].astype(int)
        ratings["user_id"] = ratings["user_id"].astype(int)
        ratings["movie_id"] = ratings["movie_id"].astype(int)
        ratings["rating"] = ratings["rating"].astype(float)
        return movies, ratings

    def _build_content_model(self):
        def features(row):
            title = re.sub(r"\(\d{4}\)$", "", str(row.title)).lower()
            genres = str(row.genres).replace("|", " ")
            return f"{title} {genres}"
        corpus = self.movies.apply(features, axis=1).tolist()
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        self.content_matrix = self.vectorizer.fit_transform(corpus)

    def _build_collaborative_model(self, n_components, n_clusters):
        user_rows = self.ratings["user_id"].map(self.user_id_to_idx).to_numpy()
        movie_cols = self.ratings["movie_id"].map(self.movie_id_to_idx).to_numpy()
        values = self.ratings["rating"].to_numpy(dtype=np.float32)
        self.user_item_matrix = csr_matrix((values, (user_rows, movie_cols)), shape=(len(self.user_ids), len(self.movie_ids)))
        # Center each user's ratings around their mean to reduce rating-scale bias.
        user_means = np.asarray(self.user_item_matrix.sum(axis=1)).ravel() / np.maximum(np.diff(self.user_item_matrix.indptr), 1)
        centered_values = values - user_means[user_rows]
        centered = csr_matrix((centered_values, (user_rows, movie_cols)), shape=(len(self.user_ids), len(self.movie_ids)))
        max_components = max(2, min(n_components, min(centered.shape) - 1))
        self.svd = TruncatedSVD(n_components=max_components, random_state=42, n_iter=7)
        self.user_factors = self.svd.fit_transform(centered)
        self.item_factors = normalize(self.svd.components_.T)
        actual_clusters = max(2, min(n_clusters, len(self.user_ids)))
        self.kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
        self.user_clusters = self.kmeans.fit_predict(self.user_factors)
        self.user_means = user_means
        self.centered_matrix = centered

    def _movie_record(self, idx: int, score: float, reason: str):
        row = self.movies.iloc[int(idx)]
        return {"movie_id": int(row.movie_id), "title": str(row.title), "genres": str(row.genres), "score": float(score), "reason": reason}

    def search_movies(self, query: str, limit: int = 20):
        q = str(query).strip().lower()
        if not q:
            return []
        mask = self.movies["title"].str.lower().str.contains(re.escape(q), na=False)
        matches = self.movies.loc[mask].head(limit)
        return [{"movie_id": int(r.movie_id), "title": str(r.title), "genres": str(r.genres)} for r in matches.itertuples()]

    def get_movie(self, movie_id: int):
        idx = self.movie_id_to_idx.get(int(movie_id))
        if idx is None:
            return None
        row = self.movies.iloc[idx]
        title = str(row.title)
        match = re.search(r"\((\d{4})\)$", title)
        return {"movie_id": int(row.movie_id), "title": title, "genres": str(row.genres), "year": int(match.group(1)) if match else None}

    def recommend_for_movie(self, movie_id: int, limit: int = 10):
        idx = self.movie_id_to_idx.get(int(movie_id))
        if idx is None:
            return []
        content_scores = cosine_similarity(self.content_matrix[idx], self.content_matrix).ravel()
        collab_scores = self.item_factors @ self.item_factors[idx]
        scores = 0.65 * content_scores + 0.35 * collab_scores
        scores[idx] = -1
        top = np.argsort(scores)[::-1][:limit]
        return [self._movie_record(i, scores[i], "Similar themes, genres and audience patterns") for i in top]

    def recommend_for_user(self, user_id: int, limit: int = 10):
        user_idx = self.user_id_to_idx.get(int(user_id))
        if user_idx is None:
            return []
        scores = self.user_factors[user_idx] @ self.svd.components_
        rated = self.user_item_matrix[user_idx].indices
        scores[rated] = -np.inf
        top = np.argsort(scores)[::-1][:limit]
        return [self._movie_record(i, scores[i], "Based on ratings from users with related taste") for i in top if np.isfinite(scores[i])]

    def recommend_for_profile(self, ratings: Iterable[dict], limit: int = 10):
        valid = [(self.movie_id_to_idx.get(int(r["movie_id"])), float(r["rating"])) for r in ratings]
        valid = [(idx, rating) for idx, rating in valid if idx is not None]
        if not valid:
            return []
        idxs = np.array([x[0] for x in valid], dtype=int)
        vals = np.array([x[1] - 3.0 for x in valid], dtype=float)
        if np.allclose(vals, 0):
            vals = np.ones_like(vals)
        content_profile = self.content_matrix[idxs].multiply(vals[:, None]).sum(axis=0)
        content_scores = cosine_similarity(csr_matrix(content_profile), self.content_matrix).ravel()
        collaborative_profile = (self.item_factors[idxs] * vals[:, None]).sum(axis=0)
        collaborative_scores = self.item_factors @ collaborative_profile
        scores = 0.60 * content_scores + 0.40 * collaborative_scores
        scores[idxs] = -np.inf
        top = np.argsort(scores)[::-1][:limit]
        return [self._movie_record(i, scores[i], "Personalized from your ratings and similar viewers") for i in top if np.isfinite(scores[i])]

    def get_user_cluster(self, user_id: int):
        user_idx = self.user_id_to_idx.get(int(user_id))
        if user_idx is None:
            return None
        cluster = int(self.user_clusters[user_idx])
        members = np.where(self.user_clusters == cluster)[0]
        return {"cluster_id": cluster, "cluster_size": int(len(members)), "description": "A group of viewers with similar rating patterns"}
