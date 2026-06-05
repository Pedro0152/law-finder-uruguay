"use client";

import styles from './page.module.css';

export default function AdminDashboard() {
  const handleScrapeTrigger = async () => {
    try {
      const res = await fetch('/api/internal/scrape/trigger', { method: 'POST' });
      if (res.ok) {
        alert("Proceso de Scraping encolado en el backend.");
      } else {
        alert("Error al encolar el proceso.");
      }
    } catch (e) {
      alert("Error de conexión con el backend.");
    }
  };

  return (
    <div className={styles.main}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <div className={styles.logoArea}>
          <div className={styles.logoIcon}>LF</div>
          <span style={{fontWeight: 600}}>Admin Panel</span>
        </div>
        <nav className={styles.navMenu}>
          <div className={`${styles.navItem} ${styles.active}`}>Dashboard</div>
          <div className={styles.navItem}>Normativas Activas</div>
          <div className={styles.navItem}>Trabajos de Scraping</div>
          <div className={styles.navItem}>Logs del Sistema</div>
          <div className={styles.navItem}>Configuración</div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className={styles.content}>
        <header className={styles.header}>
          <h1 className={styles.title}>Dashboard General</h1>
          <button className={styles.actionBtn} onClick={handleScrapeTrigger}>
            Forzar Actualización (Scraping)
          </button>
        </header>

        {/* Stats Grid */}
        <section className={styles.grid}>
          <div className={styles.statCard}>
            <div className={styles.statTitle}>Leyes y Decretos Totales</div>
            <div className={styles.statValue}>12,450</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statTitle}>Artículos Vectorizados (Embeddings)</div>
            <div className={styles.statValue}>145,820</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statTitle}>Consultas RAG (Últimos 30 días)</div>
            <div className={styles.statValue}>3,210</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statTitle}>Estado de la Cola (Celery)</div>
            <div className={styles.statValue} style={{color: '#34d399'}}>Libre</div>
          </div>
        </section>

        {/* Scraping Jobs Table */}
        <section className={styles.tableContainer}>
          <div className={styles.tableHeader}>Últimos Trabajos de Scraping</div>
          <table className={styles.tableElement}>
            <thead>
              <tr>
                <th className={styles.thElement}>Fuente</th>
                <th className={styles.thElement}>Fecha Inicio</th>
                <th className={styles.thElement}>Duración</th>
                <th className={styles.thElement}>Items Procesados</th>
                <th className={styles.thElement}>Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className={styles.tdElement}>IMPO - Diario Oficial</td>
                <td className={styles.tdElement}>Hoy, 04:00 AM</td>
                <td className={styles.tdElement}>2m 14s</td>
                <td className={styles.tdElement}>15</td>
                <td className={styles.tdElement}><span className={`${styles.status} ${styles.success}`}>Completado</span></td>
              </tr>
              <tr>
                <td className={styles.tdElement}>IMPO - Base de Leyes</td>
                <td className={styles.tdElement}>Ayer, 04:00 AM</td>
                <td className={styles.tdElement}>34m 50s</td>
                <td className={styles.tdElement}>120</td>
                <td className={styles.tdElement}><span className={`${styles.status} ${styles.success}`}>Completado</span></td>
              </tr>
              <tr>
                <td className={styles.tdElement}>Parlamento - Resoluciones</td>
                <td className={styles.tdElement}>Hace 2 días</td>
                <td className={styles.tdElement}>--</td>
                <td className={styles.tdElement}>0</td>
                <td className={styles.tdElement}><span className={`${styles.status} ${styles.error}`}>Error HTTP 503</span></td>
              </tr>
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}
