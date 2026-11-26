SPECTRA FRONTEND

Requirements:
- Node.js 18 or newer
- Spectra FastAPI backend running at http://127.0.0.1:8000

Install and run (Windows CMD):
1. Open a NEW terminal.
2. cd /d D:\AI-ML-TRAINING\Spectra\frontend
3. npm install
4. npm run dev
5. Open http://127.0.0.1:5173

The frontend uses the existing backend routes:
GET  /api/v1/health
GET  /api/v1/movies/search?q=...
GET  /api/v1/recommendations/user/1
GET  /api/v1/recommendations/movie/{movie_id}
POST /api/v1/recommendations/profile

To change the API address, create frontend/.env with:
VITE_API_URL=http://127.0.0.1:8000

Keep the backend terminal running while using the frontend.
