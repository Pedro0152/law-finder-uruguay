import styles from './page.module.css';

export default function Home() {
  return (
    <main className={styles.main}>
      {/* Header / Navbar */}
      <nav className={styles.nav}>
        <div className={styles.navContainer}>
          <div className={styles.logoArea}>
            <div className={styles.logoIcon}>L</div>
            <span className={styles.logoText}>Law Finder <span>Uruguay</span></span>
          </div>
          <div className={styles.navLinks}>
            <a href="#">Buscador</a>
            <a href="#">Chat Legal AI</a>
            <a href="#">Normativa Reciente</a>
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
          <div className={styles.searchContainer}>
            <div className={styles.searchIcon}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            </div>
            <input 
              type="text" 
              placeholder="Ej: ¿Cuál es el plazo para el despido abusivo?" 
              className={styles.searchInput}
            />
            <button className={styles.searchBtn}>
              Buscar
            </button>
          </div>
        </div>
      </header>

      {/* Recent Norms / MVP List */}
      <section className={styles.recentSection}>
        <h2 className={styles.sectionTitle}>Normativa Reciente Ingresada</h2>
        <div className={styles.cardsGrid}>
          
          {/* Mock Card 1 */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={`${styles.tag} ${styles.ley}`}>Ley 19.889</span>
              <span className={styles.date}>09/07/2020</span>
            </div>
            <h3 className={styles.cardTitle}>Ley de Urgente Consideración (LUC)</h3>
            <p className={styles.cardDesc}>Aprobación de la Ley de Urgente Consideración con modificaciones en seguridad pública, economía, educación y vivienda.</p>
            <div className={styles.status}>
              <div className={`${styles.statusDot} ${styles.active}`}></div>
              <span style={{color: '#34d399'}}>Vigente</span>
            </div>
          </div>

          {/* Mock Card 2 */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={`${styles.tag} ${styles.decreto}`}>Decreto 150/007</span>
              <span className={styles.date}>26/04/2007</span>
            </div>
            <h3 className={styles.cardTitle}>Reglamentación del IRPF</h3>
            <p className={styles.cardDesc}>Reglamentación del Impuesto a las Rentas de las Personas Físicas. Texto actualizado y concordado.</p>
            <div className={styles.status}>
              <div className={`${styles.statusDot} ${styles.partial}`}></div>
              <span style={{color: '#fbbf24'}}>Parcialmente Vigente</span>
            </div>
          </div>

          {/* Mock Card 3 */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={`${styles.tag} ${styles.resolucion}`}>Resolución</span>
              <span className={styles.date}>15/02/2024</span>
            </div>
            <h3 className={styles.cardTitle}>Ajuste Base de Prestaciones y Contribuciones (BPC)</h3>
            <p className={styles.cardDesc}>Se fija el valor de la Base de Prestaciones y Contribuciones a partir del 1° de enero de 2024.</p>
            <div className={styles.status}>
              <div className={`${styles.statusDot} ${styles.active}`}></div>
              <span style={{color: '#34d399'}}>Vigente</span>
            </div>
          </div>

        </div>
      </section>
    </main>
  );
}
