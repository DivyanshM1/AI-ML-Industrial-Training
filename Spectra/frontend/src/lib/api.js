const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `API request failed (${response.status})`)
  return body
}

export const api = {
  health: () => request('/api/v1/health'),
  artwork: (ids) => ids.length ? request(`/api/v1/movies/artwork?movie_ids=${ids.join(',')}`) : Promise.resolve({}),
  search: (q, limit = 24) => request(`/api/v1/movies/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  similar: (id, limit = 12) => request(`/api/v1/recommendations/movie/${id}?limit=${limit}`),
  forUser: (id = 1, limit = 12) => request(`/api/v1/recommendations/user/${id}?limit=${limit}`),
  fromRatings: (ratings, limit = 12) => request('/api/v1/recommendations/profile', { method: 'POST', body: JSON.stringify({ ratings, limit }) }),
  trending: (window = 'week', page = 1) => request(`/api/v1/movies/trending?window=${window}&page=${page}`),
  popular: (page = 1) => request(`/api/v1/movies/popular?page=${page}`),
  upcoming: (page = 1) => request(`/api/v1/movies/upcoming?page=${page}`),
  tmdbSearch: (q, page = 1) => request(`/api/v1/tmdb/search?q=${encodeURIComponent(q)}&page=${page}`),
}
