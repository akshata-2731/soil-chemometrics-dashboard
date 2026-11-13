import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { ThemeProvider, useTheme } from './context/ThemeContext';
import Home from './pages/Home';
import ModeBatch from './pages/ModeBatch';
import ModeSingle from './pages/ModeSingle';
import ModeAll12 from './pages/ModeAll12';
import TrainModels from './pages/TrainModels';
import History from './pages/History';
import CalibrationManagement from './pages/CalibrationManagement';
import LogicManagement from './pages/LogicManagement';
import MultiModelScreen from './pages/MultiModelScreen';
import ScispectrumFooter from './components/ScispectrumFooter';

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/multi-model', label: 'Multi-Model Run (Test All)' },
  { to: '/batch', label: 'Batch (Multi-Sample)' },
  { to: '/single', label: 'Single Nutrient' },
  { to: '/all12', label: 'All 12 Nutrients' },
  { to: '/train', label: 'Train Models (Retrain AI)' },
  { to: '/calibration', label: 'Calibration (Zero Set)' },
  { to: '/logics', label: 'Logic Library (Formulas)' },
  { to: '/history', label: 'History (Logs)' },
];

// Research edition (served on the ArkaShine site at /research): analysis only.
const RESEARCH = import.meta.env.VITE_RESEARCH_MODE === '1';
const ADMIN_ONLY = ['/train', '/calibration', '/logics'];
const VISIBLE_LINKS = RESEARCH ? NAV_LINKS.filter(l => !ADMIN_ONLY.includes(l.to)) : NAV_LINKS;

function NavContent() {
  const loc = useLocation();
  const { theme, toggleTheme, colors } = useTheme();

  return (
    <nav style={{
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      gap: 12,
      background: colors.navBg, 
      padding: '10px 24px', 
      borderBottom: `1px solid ${colors.navBorder}`,
      flexWrap: 'wrap',
      boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
        {/* Brand identity logo */}
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 30,
            height: 30,
            borderRadius: 7,
            background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 900,
            fontSize: 16,
            boxShadow: '0 2px 4px rgba(2, 132, 199, 0.25)'
          }}>
            S
          </div>
          <span style={{
            color: colors.textPrimary, 
            fontWeight: 800, 
            fontSize: 17,
            letterSpacing: -0.3,
          }}>
            SCISPECTRUM
          </span>
          <span style={{
            fontSize: 11,
            padding: '2px 8px',
            borderRadius: 4,
            background: '#10b981',
            color: '#fff',
            fontWeight: 800,
            letterSpacing: 0.3
          }}>
            SoilLenz™
          </span>
        </Link>

        {/* Clean pill navigation links */}
        <div style={{ display: 'flex', gap: 2, flexWrap: 'wrap', background: colors.name === 'dark' ? '#0f172a' : '#f1f5f9', padding: '3px', borderRadius: 8 }}>
          {VISIBLE_LINKS.map(l => {
            const active = loc.pathname === l.to;
            return (
              <Link 
                key={l.to} 
                to={l.to} 
                style={{
                  color: active ? '#0284c7' : colors.textMuted, 
                  textDecoration: 'none',
                  fontSize: 12, 
                  padding: '5px 10px', 
                  borderRadius: 6,
                  background: active ? colors.cardBg : 'transparent',
                  fontWeight: active ? 700 : 500,
                  boxShadow: active ? '0 1px 2px rgba(0,0,0,0.08)' : 'none',
                  transition: 'all 0.15s ease',
                  whiteSpace: 'nowrap'
                }}
              >
                {l.label}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Dark / Light Toggle */}
      <button
        onClick={toggleTheme}
        style={{
          background: theme === 'light' ? '#f1f5f9' : '#1e293b',
          color: colors.textPrimary,
          border: `1px solid ${colors.cardBorder}`,
          borderRadius: 8,
          padding: '6px 12px',
          fontSize: 12,
          fontWeight: 600,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 6
        }}
      >
        {theme === 'light' ? '🌙 Dark' : '☀ Light'}
      </button>
    </nav>
  );
}

function MainApp() {
  const { colors } = useTheme();

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: colors.bg, color: colors.textPrimary, transition: 'background-color 0.2s, color 0.2s' }}>
      <NavContent />
      <div style={{ flex: 1, maxWidth: 1240, width: '100%', margin: '0 auto', padding: '24px 16px' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/multi-model" element={<MultiModelScreen />} />
          <Route path="/batch" element={<ModeBatch />} />
          <Route path="/single" element={<ModeSingle />} />
          <Route path="/all12" element={<ModeAll12 />} />
          <Route path="/history" element={<History />} />
          {!RESEARCH && <Route path="/calibration" element={<CalibrationManagement />} />}
          {!RESEARCH && <Route path="/logics" element={<LogicManagement />} />}
          {!RESEARCH && <Route path="/train" element={<TrainModels />} />}
        </Routes>
      </div>
      <ScispectrumFooter />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, '') || '/'}>
        <MainApp />
      </BrowserRouter>
    </ThemeProvider>
  );
}
