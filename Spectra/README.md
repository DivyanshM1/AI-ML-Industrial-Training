# Spectra ML Research Notebooks

These notebooks document the modelling and evaluation work behind Spectra.

## Requirements
Use the existing Spectra Python environment. From the project root:

```cmd
.venv\Scripts\activate
python -m pip install jupyterlab ipykernel matplotlib scikit-learn scipy pandas numpy
jupyter lab
```

Open notebooks in order from `notebooks/`.

## Dataset
The notebooks expect the MovieLens 1M files at:

`datasets/ml-1m/movies.dat`, `ratings.dat`, `users.dat`

Run from the Spectra project root or the `notebooks` directory. Each notebook includes path resolution.

## Notebook sequence
1. `01_movie_data_exploration.ipynb` — dataset quality, EDA and sparsity.
2. `02_content_based_recommendation.ipynb` — TF-IDF and cosine similarity.
3. `03_collaborative_filtering.ipynb` — per-user holdout and TruncatedSVD.
4. `04_user_taste_clustering.ipynb` — K-Means and cluster interpretation.
5. `05_hybrid_model_evaluation.ipynb` — top-N metrics and baselines.

## Important reproducibility note
These are research notebooks built around the MovieLens 1M schema and the algorithms used in Spectra. They are not evidence that experiments have already been executed. Run every cell, inspect outputs, and save the executed notebooks before including them in a portfolio. The notebook implementations are transparent baselines; compare them against the deployed implementation in `backend/app/ml/recommender.py` before claiming exact code parity.

## Evaluation cautions
- The collaborative and hybrid notebooks use per-user random holdout.
- The relevance threshold (`rating >= 4`) is an explicit evaluation choice.
- Results are not directly comparable to published benchmarks unless protocol and candidate sets match.
- K-Means labels are arbitrary and should not be interpreted as fixed personality categories.
