from app.core.config import MODEL_PATH, settings
from app.ml.recommender import RecommenderEngine
import joblib


def main():
    required = ["movies.dat", "ratings.dat"]
    missing = [name for name in required if not (settings.dataset_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing dataset files in {settings.dataset_dir}: {', '.join(missing)}. "
            "Run: python -m scripts.prepare_data"
        )

    print("Loading MovieLens 1M...")
    movies, ratings = RecommenderEngine.load_dataset(settings.dataset_dir)
    print(f"Loaded {len(movies):,} movies and {len(ratings):,} ratings.")
    print("Training TF-IDF, TruncatedSVD and K-Means models. This may take a few minutes...")

    engine = RecommenderEngine(movies, ratings)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(engine, MODEL_PATH, compress=3)

    print("\nTraining completed.")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Users: {len(engine.user_ids):,} | Movies: {len(engine.movie_ids):,} | Clusters: {engine.kmeans.n_clusters}")


if __name__ == "__main__":
    main()
