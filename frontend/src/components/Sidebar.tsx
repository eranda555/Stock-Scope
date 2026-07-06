/* ═══════════════════════════════════════════════════════════════
   Sidebar - Navigation sidebar
   ═══════════════════════════════════════════════════════════════ */

import React from 'react';
import type { Section } from '../App';

interface SidebarProps {
  activeSection: Section;
  onNavigate: (section: Section) => void;
}

interface NavItem {
  id: Section;
  label: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'market-overview', label: 'Market Overview', icon: '📊' },
  { id: 'stock-search', label: 'Stock Search', icon: '🔍' },
  { id: 'watchlist', label: 'Watchlist', icon: '⭐' },
];

const Sidebar: React.FC<SidebarProps> = ({ activeSection, onNavigate }) => {
  return (
    <aside style={styles.sidebar}>
      {/* Logo */}
      <div style={styles.logoArea}>
        <div style={styles.logoIcon}>SS</div>
        <div>
          <div style={styles.logoText}>Stock</div>
          <div style={styles.logoTextAccent}>Scope</div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={styles.nav}>
        {NAV_ITEMS.map((item) => {
          const isActive = activeSection === item.id;
          return (
            <button
              key={item.id}
              style={{
                ...styles.navItem,
                ...(isActive ? styles.navItemActive : {}),
              }}
              onClick={() => onNavigate(item.id)}
            >
              <span style={styles.navIcon}>{item.icon}</span>
              <span>{item.label}</span>
              {isActive && <div style={styles.activeIndicator} />}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={styles.footer}>
        <div style={styles.version}>v1.0.0</div>
        <div style={styles.build}>CSE &bull; US Markets</div>
      </div>
    </aside>
  );
};

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    position: 'fixed',
    top: 0,
    left: 0,
    width: 'var(--sidebar-width)',
    height: '100vh',
    backgroundColor: 'var(--bg-secondary)',
    borderRight: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    zIndex: 200,
    overflow: 'hidden',
  },
  logoArea: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '20px 20px 24px',
    borderBottom: '1px solid var(--border)',
  },
  logoIcon: {
    width: 40,
    height: 40,
    borderRadius: '10px',
    background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 800,
    fontSize: '0.9rem',
    color: '#fff',
    fontFamily: 'var(--font-sans)',
  },
  logoText: {
    fontSize: '0.85rem',
    fontWeight: 500,
    color: 'var(--text-muted)',
    lineHeight: 1.2,
  },
  logoTextAccent: {
    fontSize: '1.2rem',
    fontWeight: 800,
    color: 'var(--text-primary)',
    lineHeight: 1.2,
    letterSpacing: '-0.02em',
  },
  nav: {
    flex: 1,
    padding: '12px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '10px 14px',
    borderRadius: '8px',
    border: 'none',
    backgroundColor: 'transparent',
    color: 'var(--text-secondary)',
    fontSize: '0.88rem',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
    textAlign: 'left',
    width: '100%',
    position: 'relative',
    fontFamily: 'var(--font-sans)',
  },
  navItemActive: {
    backgroundColor: 'var(--accent-blue-light)',
    color: 'var(--accent-blue)',
    fontWeight: 600,
  },
  navIcon: {
    fontSize: '1.1rem',
    width: 24,
    textAlign: 'center' as const,
  },
  activeIndicator: {
    position: 'absolute',
    left: 0,
    top: '50%',
    transform: 'translateY(-50%)',
    width: 3,
    height: 20,
    borderRadius: '0 3px 3px 0',
    backgroundColor: 'var(--accent-blue)',
  },
  footer: {
    padding: '16px 20px',
    borderTop: '1px solid var(--border)',
  },
  version: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    fontWeight: 500,
  },
  build: {
    fontSize: '0.7rem',
    color: 'var(--text-muted)',
    marginTop: 2,
  },
};

export default Sidebar;
