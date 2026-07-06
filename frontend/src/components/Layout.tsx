/* ═══════════════════════════════════════════════════════════════
   Layout - Main Application Shell with Sidebar + Header + Content
   ═══════════════════════════════════════════════════════════════ */

import React from 'react';
import Sidebar from './Sidebar';
import type { Section } from '../App';

interface LayoutProps {
  children: React.ReactNode;
  activeSection: Section;
  selectedMarket: 'CSE' | 'US';
  onNavigate: (section: Section) => void;
  onMarketChange: (market: 'CSE' | 'US') => void;
}

const Layout: React.FC<LayoutProps> = ({
  children,
  activeSection,
  selectedMarket,
  onNavigate,
  onMarketChange,
}) => {
  return (
    <div style={styles.container}>
      <Sidebar activeSection={activeSection} onNavigate={onNavigate} />
      <div style={styles.mainArea}>
        {/* ── Header ── */}
        <header style={styles.header}>
          <div style={styles.headerLeft}>
            <h1 style={styles.appTitle}>Stock Scope</h1>
            <span style={styles.tagline}>Investment Dashboard</span>
          </div>
          <div style={styles.headerRight}>
            <div style={styles.marketSelector}>
              <button
                style={{
                  ...styles.marketBtn,
                  ...(selectedMarket === 'CSE' ? styles.marketBtnActive : {}),
                  borderRadius: '6px 0 0 6px',
                }}
                onClick={() => onMarketChange('CSE')}
              >
                CSE
              </button>
              <button
                style={{
                  ...styles.marketBtn,
                  ...(selectedMarket === 'US' ? styles.marketBtnActive : {}),
                  borderRadius: '0 6px 6px 0',
                }}
                onClick={() => onMarketChange('US')}
              >
                US
              </button>
            </div>
          </div>
        </header>

        {/* ── Content ── */}
        <main style={styles.content}>{children}</main>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: 'var(--bg-primary)',
  },
  mainArea: {
    flex: 1,
    marginLeft: 'var(--sidebar-width)',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    height: 'var(--header-height)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 var(--space-8)',
    borderBottom: '1px solid var(--border)',
    backgroundColor: 'var(--bg-secondary)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  appTitle: {
    fontSize: '1.25rem',
    fontWeight: 700,
    color: 'var(--text-primary)',
    letterSpacing: '-0.02em',
    margin: 0,
  },
  tagline: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
    padding: '4px 10px',
    backgroundColor: 'var(--bg-card)',
    borderRadius: '999px',
    fontWeight: 500,
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--space-4)',
  },
  marketSelector: {
    display: 'flex',
    border: '1px solid var(--border-light)',
    borderRadius: '6px',
    overflow: 'hidden',
  },
  marketBtn: {
    padding: '6px 16px',
    fontSize: '0.82rem',
    fontWeight: 600,
    cursor: 'pointer',
    border: 'none',
    backgroundColor: 'var(--bg-card)',
    color: 'var(--text-muted)',
    transition: 'all var(--transition-fast)',
    fontFamily: 'var(--font-sans)',
  },
  marketBtnActive: {
    backgroundColor: 'var(--accent-blue)',
    color: '#ffffff',
  },
  content: {
    flex: 1,
    padding: 'var(--space-6) var(--space-8)',
    overflowY: 'auto',
  },
};

export default Layout;
