SPECTRA - TMDB ARTWORK INTEGRATION PATCH

This patch adds a server-side TMDB metadata lookup and poster artwork to the existing app.
It does not replace or retrain the MovieLens recommendation model.

INSTALL
1. Stop the FastAPI server (Ctrl+C).
2. Extract this ZIP into D:\AI-ML-TRAINING\Spectra and choose to merge folders/overwrite files.
   It contains only these replacement/additional files:
   backend\app\core\config.py
   backend\app\api\routes.py
   backend\app\services\__init__.py
   backend\app\services\tmdb.py
   frontend\src\App.jsx
   frontend\src\lib\api.js
   frontend\src\tmdb-artwork.css
3. Confirm backend\.env contains:
   SPECTRA_TMDB_READ_ACCESS_TOKEN=YOUR_REAL_READ_ACCESS_TOKEN
4. Confirm backend\.env is NOT tracked by Git. Add this line to the project root .gitignore if absent:
   backend/.env
5. Start backend from CMD:
   cd /d D:\AI-ML-TRAINING\Spectra\backend
   python -m uvicorn app.main:app --reload
6. Check:
   http://127.0.0.1:8000/api/v1/tmdb/status
   Expected: {"configured":true,"provider":"TMDB"}
7. Restart frontend if needed:
   cd /d D:\AI-ML-TRAINING\Spectra\frontend
   npm run dev

NOTES
- TMDB access token stays in backend/.env and is never sent to the browser.
- The artwork endpoint matches MovieLens titles/year to TMDB search results. Matches are best-effort;
  ambiguous remakes or alternate titles may occasionally select the wrong artwork.
- If TMDB is not configured or an artwork match is unavailable, the existing designed poster fallback remains.
- TMDB API usage requires attribution. The app footer includes the required non-endorsement notice.
- Do not commit backend/.env or expose your token in screenshots, logs, or GitHub.
