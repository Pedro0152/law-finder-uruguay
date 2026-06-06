"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import styles from './page.module.css';

export default function Home() {
  const router = useRouter();
  const [searchInput, setSearchInput] = useState('');
  const [recentNorms, setRecentNorms] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/internal/norms/recent')
      .then(res => res.json())
      .then(data => {
        if (data.results) {
          setRecentNorms(data.results);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching recent norms:", err);
        setLoading(false);
      });
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      router.push(`/chat?q=${encodeURIComponent(searchInput.trim())}`);
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'Activa': return '#34d399'; // Verde
      case 'Derogada': return '#ef4444'; // Rojo
      case 'Parcial': return '#fbbf24'; // Amarillo
      default: return '#9ca3af'; // Gris
    }
  };

  return (
    <main className={styles.main}>
      {/* Header / Navbar */}
      <nav className={styles.nav}>
        <div className={styles.navContainer}>
          <div className={styles.logoArea} onClick={() => router.push('/')} style={{cursor: 'pointer'}}>
            <div className={styles.logoIcon}>L</div>
            <span className={styles.logoText}>Law Finder <span>Uruguay</span></span>
          </div>
          <div className={styles.navLinks}>
            <a href="#" onClick={(e) => { e.preventDefault(); document.getElementById('search-box')?.focus(); }}>Buscador</a>
            <a href="/chat">Chat Legal AI</a>
            <a href="#recent">Normativa Reciente</a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <header className={styles.hero}>
        <div className={styles.badge}>
          <span className={styles.pulseDot}></span>
          Actualizado con el Diario Oficial
        </div>
        <h1 className={styles.title}>
          Toda la normativa uruguaya,<br/>al alcance de tu mano.
        </h1>
        <p className={styles.subtitle}>
          Búsqueda semántica, análisis de vigencia y resoluciones históricas. 
          Pregunta en lenguaje natural y obtén respuestas trazables al instante.
        </p>

        {/* Search Bar Component */}
        <div className={styles.searchWrapper}>
          <div className={styles.searchGlow}></div>
          <form className={styles.searchContainer} onSubmit={handleSearch}>
            <div className={styles.searchIcon}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            </div>
            <input 
              id="search-box"
              type="text" 
              placeholder="Ej: ¿Cuál es el plazo para el despido abusivo?" 
              className={styles.searchInput}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
            <button type="submit" className={styles.searchBtn}>
              Buscar
            </button>
          </form>
        </div>
      </header>

      {/* Recent Norms List */}
      <section id="recent" className={styles.recentSection}>
        <h2 className={styles.sectionTitle}>Normativa Reciente Ingresada</h2>
        <div className={styles.cardsGrid}>
          
          {loading ? (
            <p style={{color: 'rgba(255,255,255,0.5)'}}>Cargando normativa de Supabase...</p>
          ) : recentNorms.length === 0 ? (
            <p style={{color: 'rgba(255,255,255,0.5)'}}>Aún no se ha realizado el primer scraping. Ve al panel de admin para forzar actualización.</p>
          ) : (
            recentNorms.map((norma, idx) => (
              <div key={idx} className={styles.card}>
                <div className={styles.cardHeader}>
                  <span className={`${styles.tag} ${styles[norma.tipo.toLowerCase()] || styles.ley}`}>
                    {norma.tipo} {norma.numero}
                  </span>
                  <span className={styles.date}>{norma.fecha_promulgacion || 'Sin fecha'}</span>
                </div>
                <h3 className={styles.cardTitle}>{norma.titulo || 'Sin título'}</h3>
                <p className={styles.cardDesc}>Normativa procesada e indexada en la base de datos vectorial.</p>
                <div className={styles.status}>
                  <div className={styles.statusDot} style={{backgroundColor: getStatusColor(norma.estado_vigencia)}}></div>
                  <span style={{color: getStatusColor(norma.estado_vigencia)}}>{norma.estado_vigencia}</span>
                </div>
              </div>
            ))
          )}

        </div>
      </section>
    </main>
  );
}
