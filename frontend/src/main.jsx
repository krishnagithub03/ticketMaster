import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  ArrowRight, CalendarDays, Check, ChevronDown, Clock3, Heart, MapPin,
  Menu, Play, Search, Star, Ticket, UserRound, X
} from 'lucide-react';
import './styles.css';

const movies = [
  {
    id: 1, title: 'The Wild Robot', genre: 'Animation · Adventure', rating: '9.1',
    language: 'English', format: '2D', duration: '1h 42m',
    image: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=900&q=85',
    accent: '#83a9bf', label: 'A heartwarming adventure'
  },
  {
    id: 2, title: 'Dune: Part Two', genre: 'Action · Sci-fi · Drama', rating: '8.9',
    language: 'English', format: 'IMAX', duration: '2h 46m',
    image: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=900&q=85',
    accent: '#d79c70', label: 'The desert awaits'
  },
  {
    id: 3, title: 'Inside Out 2', genre: 'Animation · Comedy', rating: '8.7',
    language: 'English', format: '3D', duration: '1h 36m',
    image: 'https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=900&q=85',
    accent: '#d18ac1', label: 'Feel all the feelings'
  },
  {
    id: 4, title: 'A Quiet Place: Day One', genre: 'Horror · Thriller', rating: '8.4',
    language: 'English', format: '2D', duration: '1h 40m',
    image: 'https://images.unsplash.com/photo-1515630278258-407f66498911?auto=format&fit=crop&w=900&q=85',
    accent: '#718a9c', label: 'Silence is survival'
  }
];

const events = [
  { title: 'Sunset Sessions', type: 'Music', date: 'SAT, 28 SEP', place: 'The Courtyard, Pune', image: 'https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=800&q=80' },
  { title: 'Laugh Lines Live', type: 'Comedy', date: 'FRI, 04 OCT', place: 'The Habitat, Mumbai', image: 'https://images.unsplash.com/photo-1585699324551-f6c309eedeca?auto=format&fit=crop&w=800&q=80' },
  { title: 'The Art of Film', type: 'Workshop', date: 'SUN, 13 OCT', place: 'Studio 9, Bengaluru', image: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=800&q=80' }
];

function App() {
  const [query, setQuery] = useState('');
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [liked, setLiked] = useState([]);
  const [toast, setToast] = useState('');
  const [location, setLocation] = useState('Pune');
  const filteredMovies = useMemo(() => movies.filter((movie) =>
    `${movie.title} ${movie.genre}`.toLowerCase().includes(query.toLowerCase())
  ), [query]);

  const toggleLike = (id) => setLiked((current) => current.includes(id)
    ? current.filter((item) => item !== id) : [...current, id]);
  const notify = (message) => {
    setToast(message);
    window.setTimeout(() => setToast(''), 2400);
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <button className="brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="ticketly home">
            <span className="brand-mark"><Ticket size={18} strokeWidth={2.5} /></span>
            <span>ticketly<span className="brand-dot">.</span></span>
          </button>
          <div className="search-box">
            <Search size={18} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search for movies, events and more" aria-label="Search" />
            {query && <button className="clear-search" onClick={() => setQuery('')}><X size={15} /></button>}
          </div>
          <div className="top-actions">
            <button className="location-picker" onClick={() => setLocation(location === 'Pune' ? 'Mumbai' : 'Pune')}><MapPin size={16} /> {location}<ChevronDown size={14} /></button>
            <button className="login-button" onClick={() => notify('Sign in is coming soon')}>Sign in</button>
            <button className="menu-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="Open menu"><Menu size={21} /></button>
          </div>
        </div>
        {menuOpen && <nav className="mobile-nav"><a href="#movies">Movies</a><a href="#events">Events</a><a href="#offers">Offers</a><a href="#about">About us</a></nav>}
      </header>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">YOUR CITY, YOUR MOMENTS</p>
            <h1>Make plans.<br /><em>Make memories.</em></h1>
            <p className="hero-subtitle">The best of movies, music, comedy and more — all in one place.</p>
            <div className="hero-actions"><button className="primary-button" onClick={() => document.getElementById('movies').scrollIntoView({ behavior: 'smooth' })}>Explore what's on <ArrowRight size={17} /></button><button className="watch-button" onClick={() => notify('Trailer player coming soon')}><span className="play-icon"><Play size={13} fill="currentColor" /></span> Watch trailer</button></div>
          </div>
          <div className="hero-art">
            <div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" />
            <div className="hero-poster"><img src={movies[0].image} alt="The Wild Robot" /><div className="poster-shade" /><div className="poster-caption"><span>NOW SHOWING</span><strong>The Wild Robot</strong></div></div>
            <div className="floating-note note-rating"><Star size={14} fill="currentColor" /><strong>9.1</strong><span>Audience rating</span></div>
            <div className="floating-note note-date"><CalendarDays size={15} /><span>Tonight<br /><strong>7:30 PM</strong></span></div>
          </div>
        </section>

        <section className="quick-links">
          <div className="section-container quick-links-inner">
            <button onClick={() => document.getElementById('movies').scrollIntoView({ behavior: 'smooth' })}><span className="quick-icon movie-icon">◉</span><span>Movies</span><ArrowRight size={15} /></button>
            <button onClick={() => document.getElementById('events').scrollIntoView({ behavior: 'smooth' })}><span className="quick-icon event-icon">✦</span><span>Events</span><ArrowRight size={15} /></button>
            <button onClick={() => notify('No saved tickets yet')}><span className="quick-icon ticket-icon">⌁</span><span>My tickets</span><ArrowRight size={15} /></button>
            <button onClick={() => notify('Offers will be available soon')}><span className="quick-icon offer-icon">%</span><span>Offers</span><ArrowRight size={15} /></button>
          </div>
        </section>

        <section className="content-section section-container" id="movies">
          <div className="section-heading"><div><p className="eyebrow">HANDPICKED FOR YOU</p><h2>Now showing</h2></div><button className="text-button" onClick={() => notify('Showing all movies')}>View all <ArrowRight size={15} /></button></div>
          <div className="movie-grid">
            {filteredMovies.length ? filteredMovies.map((movie) => <MovieCard key={movie.id} movie={movie} isLiked={liked.includes(movie.id)} onLike={() => toggleLike(movie.id)} onSelect={() => setSelectedMovie(movie)} />) : <div className="empty-state">No shows match “{query}”. Try another search.</div>}
          </div>
        </section>

        <section className="promo-section section-container" id="offers">
          <div className="promo-card"><div className="promo-copy"><p className="eyebrow">TICKETLY REWARDS</p><h2>Your next great night<br /><em>starts here.</em></h2><p>Get ₹150 off on your first booking. No complicated points, just more reasons to go out.</p><button className="light-button" onClick={() => notify('Offer code FIRSTNIGHT copied')}>Use code FIRSTNIGHT <ArrowRight size={15} /></button></div><div className="promo-stamp">₹<strong>150</strong><span>OFF</span></div><div className="promo-spark spark-a">✦</div><div className="promo-spark spark-b">✦</div></div>
        </section>

        <section className="content-section section-container events-section" id="events">
          <div className="section-heading"><div><p className="eyebrow">DON'T JUST WATCH</p><h2>Live it.</h2></div><button className="text-button" onClick={() => notify('Showing all events')}>All events <ArrowRight size={15} /></button></div>
          <div className="event-grid">{events.map((event) => <button className="event-card" key={event.title} onClick={() => notify(`${event.title} details coming soon`)}><img src={event.image} alt="" /><div className="event-gradient" /><div className="event-info"><span className="event-type">{event.type}</span><h3>{event.title}</h3><p><CalendarDays size={13} /> {event.date} <span>·</span> <MapPin size={13} /> {event.place}</p></div></button>)}</div>
        </section>
      </main>

      <footer id="about"><div className="footer-inner"><div className="brand footer-brand"><span className="brand-mark"><Ticket size={18} strokeWidth={2.5} /></span><span>ticketly<span className="brand-dot">.</span></span></div><p>Good times, made easy.</p><div className="footer-links"><a href="#about">About</a><a href="#about">Help</a><a href="#about">Terms</a><a href="#about">Privacy</a></div><small>© 2024 ticketly</small></div></footer>
      {selectedMovie && <BookingModal movie={selectedMovie} onClose={() => setSelectedMovie(null)} onBook={() => { setSelectedMovie(null); notify('Your seats are reserved!'); }} />}
      {toast && <div className="toast"><Check size={16} /> {toast}</div>}
    </div>
  );
}

function MovieCard({ movie, isLiked, onLike, onSelect }) {
  return <article className="movie-card"><div className="movie-image-wrap"><img src={movie.image} alt={movie.title} /><span className="format-badge">{movie.format}</span><button className={`like-button ${isLiked ? 'is-liked' : ''}`} onClick={onLike} aria-label={`Like ${movie.title}`}><Heart size={17} fill={isLiked ? 'currentColor' : 'none'} /></button><div className="image-fade" /></div><div className="movie-details"><div className="movie-title-row"><h3>{movie.title}</h3><span className="rating"><Star size={12} fill="currentColor" /> {movie.rating}</span></div><p>{movie.genre}</p><div className="movie-meta"><span>{movie.language}</span><span className="meta-dot">·</span><span>{movie.duration}</span></div><button className="book-button" onClick={onSelect}>Book tickets <ArrowRight size={15} /></button></div></article>;
}

function BookingModal({ movie, onClose, onBook }) {
  const [day, setDay] = useState('Today');
  const [time, setTime] = useState('07:30 PM');
  return <div className="modal-backdrop" onClick={onClose}><div className="booking-modal" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={onClose}><X size={19} /></button><div className="modal-head"><img src={movie.image} alt="" /><div><span className="eyebrow">BOOKING FOR</span><h2>{movie.title}</h2><p>{movie.language} · {movie.format} · {movie.duration}</p></div></div><div className="booking-field"><label><CalendarDays size={16} /> Choose a day</label><div className="choice-row">{['Today', 'Tomorrow', 'Sat, 28 Sep'].map((item) => <button key={item} className={day === item ? 'selected-choice' : ''} onClick={() => setDay(item)}>{item}</button>)}</div></div><div className="booking-field"><label><Clock3 size={16} /> Select a showtime</label><div className="choice-row">{['05:00 PM', '07:30 PM', '10:15 PM'].map((item) => <button key={item} className={time === item ? 'selected-choice' : ''} onClick={() => setTime(item)}>{item}</button>)}</div></div><div className="booking-summary"><span><MapPin size={15} /> Cinepolis, Seasons Mall</span><strong>{day} · {time}</strong></div><button className="primary-button modal-book" onClick={onBook}>Continue to seats <ArrowRight size={17} /></button></div></div>;
}

createRoot(document.getElementById('root')).render(<App />);
