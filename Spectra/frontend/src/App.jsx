import { useEffect, useState } from 'react'
import { Aperture, ArrowDownRight, ArrowLeft, ArrowUpRight, Check, Clapperboard, Compass, Film, Heart, LoaderCircle, Search, Sparkles, Star } from 'lucide-react'
import { api } from './lib/api'
import './tmdb-artwork.css'

const palettes = [['#b58bd8','#382a50'],['#8ebac0','#213d49'],['#d49b85','#56333c'],['#c4b47f','#48432d'],['#9a9bd1','#34345c'],['#c68aa9','#512e49']]
const cleanTitle = (s = '') => s.replace(/\s*\(\d{4}\)$/, '')
const yearOf = (s = '') => s.match(/\((\d{4})\)$/)?.[1] || s.slice(0,4)

function Poster({ movie, index = 0, image, action, label = 'EXPLORE' }) {
  const [accent, shade] = palettes[index % palettes.length]
  return <button className="poster" onClick={action} style={{'--accent':accent,'--shade':shade}} type="button">
    {image ? <img className="poster-art" src={image} alt={`${movie.title} poster`} loading="lazy"/> : <><span className="poster-orbit orbit-a"/><span className="poster-orbit orbit-b"/></>}
    <span className="poster-index">SPECTRA / {String(index+1).padStart(2,'0')}</span>
    <span className="poster-glyph"><Film size={27} strokeWidth={1.15}/></span>
    <span className="poster-title">{cleanTitle(movie.title || 'Untitled')}</span>
    <span className="poster-year">{yearOf(movie.release_date || movie.title) || 'A FILM'}</span>
    <span className="poster-open">{label} <ArrowUpRight size={13}/></span>
  </button>
}

function TmdbCard({ movie, index, onOpen }) {
  return <article className="movie-card">
    <Poster movie={movie} index={index} image={movie.poster_url} label="VIEW DETAILS" action={() => onOpen(movie)}/>
    <div className="movie-meta"><div className="movie-heading"><h3>{movie.title}</h3>{movie.vote_average > 0 && <span className="match"><Star size={11}/> {Number(movie.vote_average).toFixed(1)}</span>}</div>
    <p className="genres">{yearOf(movie.release_date) || 'Release date TBA'}{movie.original_language ? ` · ${movie.original_language.toUpperCase()}` : ''}</p></div>
  </article>
}

function MlCard({ movie, index, artwork, rating, onRate, onSimilar }) {
  const genres = Array.isArray(movie.genres) ? movie.genres : String(movie.genres || '').split('|').filter(Boolean)
  return <article className="movie-card">
    <Poster movie={movie} index={index} image={artwork?.poster_url} label="EXPLORE SIMILAR" action={() => onSimilar(movie)}/>
    <div className="movie-meta"><div className="movie-heading"><h3>{movie.title}</h3>{movie.score != null && <span className="match"><Sparkles size={11}/>{Number(movie.score).toFixed(2)}</span>}</div>
    <p className="genres">{genres.slice(0,3).join(' · ') || 'Cinema'}</p>
    <div className="rate-line"><span>YOUR RATING</span><div className="stars">{[1,2,3,4,5].map(n => <button key={n} title={`Rate ${n} out of 5`} className={rating >= n ? 'selected' : ''} onClick={() => onRate(movie,n)} type="button"><Star size={14} fill={rating >= n ? 'currentColor' : 'none'}/></button>)}</div></div></div>
  </article>
}

function Details({ movie, close }) {
  if (!movie) return null
  return <div className="detail-overlay" role="dialog" aria-modal="true" aria-label={`${movie.title} details`}>
    <div className="detail-panel"><button className="detail-close" onClick={close} type="button">×</button>
      {movie.backdrop_url && <img className="detail-backdrop" src={movie.backdrop_url} alt=""/>}
      <div className="detail-content"><div className="eyebrow muted">TMDB CATALOGUE / FILM DETAILS</div><h2>{movie.title}</h2>
      <p className="detail-facts">{movie.release_date || 'Release date unavailable'}{movie.vote_average ? ` · TMDB ${Number(movie.vote_average).toFixed(1)}/10` : ''}</p>
      <p>{movie.overview || 'No synopsis is available for this title.'}</p><button className="back-button" onClick={close} type="button"><ArrowLeft size={15}/> Back to discovery</button></div>
    </div>
  </div>
}

export default function App() {
  const [health,setHealth] = useState(null), [query,setQuery] = useState('')
  const [category,setCategory] = useState('trending'), [tab,setTab] = useState('discover')
  const [catalogue,setCatalogue] = useState([]), [recommendations,setRecommendations] = useState([])
  const [similar,setSimilar] = useState(null), [similarResults,setSimilarResults] = useState([])
  const [artwork,setArtwork] = useState({}), [ratings,setRatings] = useState({})
  const [selected,setSelected] = useState(null), [loading,setLoading] = useState(true)
  const [saving,setSaving] = useState(false), [error,setError] = useState(''), [notice,setNotice] = useState('')

  useEffect(() => { api.health().then(setHealth).catch(() => setHealth({model_loaded:false})) }, [])

  useEffect(() => {
    if (tab !== 'discover' || similar) return
    let active = true
    const timer = setTimeout(async () => {
      setLoading(true); setError('')
      try {
        const data = query.trim() ? await api.tmdbSearch(query.trim()) :
          category === 'popular' ? await api.popular() :
          category === 'upcoming' ? await api.upcoming() : await api.trending('week')
        if (active) setCatalogue(data.results || [])
      } catch (e) { if (active) setError(e.message) }
      finally { if (active) setLoading(false) }
    }, query.trim() ? 350 : 0)
    return () => { active = false; clearTimeout(timer) }
  }, [query,category,tab,similar])

  useEffect(() => {
    if (tab !== 'for-you') return
    let active = true; setLoading(true); setError('')
    api.forUser(1,12).then(data => { if (active) setRecommendations(data) })
      .catch(e => { if (active) setError(e.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [tab])

  useEffect(() => {
    const ids = [...new Set([...recommendations,...similarResults].map(m => m.movie_id).filter(Boolean))]
    if (!ids.length) return
    let active = true
    api.artwork(ids).then(data => { if (active) setArtwork(old => ({...old,...data})) }).catch(() => {})
    return () => { active = false }
  }, [recommendations,similarResults])

  async function openSimilar(movie) {
    setSimilar(movie); setSimilarResults([]); setError('')
    try { setSimilarResults(await api.similar(movie.movie_id,12)) } catch (e) { setError(e.message) }
  }
  async function rateMovie(movie,value) {
    const next = {...ratings,[movie.movie_id]:{movie_id:movie.movie_id,rating:value}}
    setRatings(next); setSaving(true); setNotice(`Rated ${movie.title} ${value}/5`)
    try { setRecommendations(await api.fromRatings(Object.values(next),12)); setTab('for-you') }
    catch (e) { setNotice(`Rating kept locally. ${e.message}`) }
    finally { setSaving(false); window.setTimeout(() => setNotice(''),2800) }
  }

  const forYou = tab === 'for-you' && !similar
  const items = similar ? similarResults : forYou ? recommendations : catalogue
  const heading = similar ? `Because you explored ${similar.title}` : forYou ? 'A reflection of your taste.' :
    query.trim() ? `Search results for “${query.trim()}”` :
    category === 'popular' ? 'Popular across the spectrum.' : category === 'upcoming' ? 'Stories on the horizon.' : 'What the world is watching.'

  return <div className="app-shell">
    <header className="topbar"><a className="brand" href="#top"><span className="brand-icon"><Aperture size={22}/></span><span className="brand-name">SPECTRA<small>CINEMATIC DISCOVERY</small></span></a>
      <nav className="main-nav"><button className={tab === 'discover' ? 'active' : ''} onClick={() => {setTab('discover');setSimilar(null)}}><Compass size={15}/> Discover</button><button className={tab === 'for-you' ? 'active' : ''} onClick={() => {setTab('for-you');setSimilar(null)}}><Heart size={15}/> For you</button></nav>
      <div className="system-status"><span className={health?.model_loaded ? 'status-dot online' : 'status-dot'}/>{health?.model_loaded ? 'ENGINE ONLINE' : 'CONNECTING'}</div>
    </header>
    <main id="top">
      <section className="hero"><div className="hero-grain"/><div className="hero-copy"><div className="eyebrow"><span className="eyebrow-line"/> A MORE PERSONAL WAY TO WATCH</div>
        <h1>Find films that<br/><em>feel like you.</em></h1><p>Beyond the watchlist. Into your taste. Discover stories, worlds and feelings through machine intelligence.</p>
        <button className="hero-link" onClick={() => document.getElementById('collection')?.scrollIntoView({behavior:'smooth'})}>Explore the collection <ArrowDownRight size={16}/></button></div>
        <div className="hero-art" aria-hidden="true"><div className="hero-ring ring-one"/><div className="hero-ring ring-two"/><div className="hero-core"><Aperture size={76} strokeWidth={0.8}/></div><span className="art-label label-one">CONTENT SIGNAL</span><span className="art-label label-two">COLLECTIVE TASTE</span><span className="art-label label-three">HYBRID MODEL / 01</span></div>
        <div className="hero-bottom"><span>01 — DISCOVER</span><span>CURATED BY INTELLIGENCE, GUIDED BY YOU</span><span>EST. 2026</span></div></section>
      <section className="collection" id="collection"><div className="section-top"><div><div className="eyebrow muted">THE COLLECTION / 01</div><h2>{heading}</h2>
        <p>{similar ? 'Similar films from the MovieLens recommendation engine.' : forYou ? 'Recommendations from your MovieLens profile or ratings.' : 'Live movie discovery powered by TMDB, alongside Spectra’s historical recommendation engine.'}</p></div><div className="section-code">S<span>/</span>01</div></div>
        {!similar && !forYou && <><div className="collection-tools"><label className="search-field"><Search size={17}/><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search movies across TMDB..."/><kbd>LIVE</kbd></label><div className="result-count">{catalogue.length} TITLES FOUND</div></div>
          {!query.trim() && <div className="catalogue-tabs"><button className={category === 'trending' ? 'active' : ''} onClick={() => setCategory('trending')}>Trending</button><button className={category === 'popular' ? 'active' : ''} onClick={() => setCategory('popular')}>Popular</button><button className={category === 'upcoming' ? 'active' : ''} onClick={() => setCategory('upcoming')}>Upcoming</button></div>}</>}
        {similar && <button className="back-button" onClick={() => {setSimilar(null);setSimilarResults([])}}><ArrowLeft size={15}/> Back to recommendations</button>}
        {error && <div className="error-state"><strong>Unable to load films</strong><span>{error}</span></div>}
        {loading ? <div className="loading-state"><LoaderCircle className="spin" size={19}/> Preparing your collection…</div> :
          <div className="movie-grid">{items.map((movie,index) => forYou || similar ?
            <MlCard key={movie.movie_id} movie={movie} index={index} artwork={artwork[movie.movie_id]} rating={ratings[movie.movie_id]?.rating || 0} onRate={rateMovie} onSimilar={openSimilar}/> :
            <TmdbCard key={movie.tmdb_id} movie={movie} index={index} onOpen={setSelected}/>)}</div>}
        {!loading && !error && !items.length && <div className="empty-state">No titles found. Try a different search.</div>}
        {saving && <div className="saving-note"><LoaderCircle className="spin" size={14}/> Updating your taste profile…</div>}
      </section>
      <section className="method-section"><div className="method-intro"><div className="eyebrow muted">UNDER THE LENS / 02</div><h2>Not random.<br/><em>Remarkably personal.</em></h2><p>A recommendation system that learns from both the films themselves and the people who watch them.</p></div>
        <div className="method-card"><span>01</span><Clapperboard size={19}/><h3>Content intelligence</h3><p>TF-IDF represents movie titles and genres as weighted feature vectors.</p></div>
        <div className="method-card"><span>02</span><Heart size={19}/><h3>Collective taste</h3><p>TruncatedSVD finds latent patterns across viewer-rating behaviour.</p></div>
        <div className="method-card"><span>03</span><Sparkles size={19}/><h3>Taste clusters</h3><p>K-Means groups users with related preference signatures.</p></div></section>
    </main>
    <footer><a className="brand" href="#top"><span className="brand-icon"><Aperture size={19}/></span><span className="brand-name">SPECTRA<small>CINEMATIC DISCOVERY</small></span></a><span>BUILT TO FIND YOUR NEXT FAVOURITE.</span><span>© 2026 SPECTRA · This product uses the TMDB API but is not endorsed or certified by TMDB.</span></footer>
    {notice && <div className="toast"><Check size={15}/>{notice}</div>}
    {selected && <Details movie={selected} close={() => setSelected(null)}/>}
  </div>
}
