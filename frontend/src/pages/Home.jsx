import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';

const MODES = [
  {
    to: '/multi-model',
    icon: '🔬',
    title: 'Multi-Model Run',
    sub: 'Run all 73 AI models or 51 math logics at once. Test pass rate (≥75% accuracy) and see live Actual vs Predicted graphs.',
    badge: 'Flagship Mode',
    color: '#6366f1',
  },
  {
    to: '/batch',
    icon: '📊',
    title: 'Batch Analysis',
    sub: 'Upload multi-sample Excel/CSV file. Run custom model or logic for each soil nutrient and view comparative curves.',
    badge: 'Multi-Sample',
    color: '#0284c7',
  },
  {
    to: '/single',
    icon: '🎯',
    title: 'Single Nutrient',
    sub: 'Test one sample for one target nutrient. Inspect full 21-wavelength input curve and step-by-step formula prediction.',
    badge: 'Targeted',
    color: '#16a34a',
  },
  {
    to: '/all12',
    icon: '🌱',
    title: 'All 12 Nutrients',
    sub: 'Analyze full 12 soil parameters (OC, N, P, K, Ca, Mg, S, Fe, Mn, Cu, Zn, B) simultaneously for one soil sample.',
    badge: 'Full Profile',
    color: '#9333ea',
  },
  {
    to: '/train',
    icon: '⚙️',
    title: 'Train Models',
    sub: 'Upload soil dataset to retrain all 70+ AI models or retrain a specific model with your latest laboratory data.',
    badge: 'AI Engine',
    color: '#f59e0b',
  },
];

export default function Home() {
  const nav = useNavigate();
  const { colors } = useTheme();

  return (
    <div style={{ textAlign: 'center', paddingTop: 24, paddingBottom: 36 }}>
      {/* Product Suite Banner */}
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: '#0284c715', border: '1px solid #0284c740', padding: '6px 16px', borderRadius: 20, marginBottom: 14 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: '#0284c7', letterSpacing: 0.5 }}>
          SCISPECTRUM LAB ESSENTIALS
        </span>
        <span style={{ color: colors.textSecondary }}>•</span>
        <span style={{ fontSize: 12, fontWeight: 800, color: '#10b981' }}>
          SoilLenz™ Workstation
        </span>
      </div>

      <h1 style={{ fontSize: 32, fontWeight: 900, color: colors.textPrimary, margin: '0 0 8px 0', letterSpacing: -0.5 }}>
        SoilLenz™ Spectroscopy Platform
      </h1>
      <p style={{ color: colors.textSecondary, fontSize: 15, maxWidth: 650, margin: '0 auto 40px auto' }}>
        What analytical test do you want to run today? Select a mode below:
      </p>
      
      <div style={{ display: 'flex', gap: 20, justifyContent: 'center', flexWrap: 'wrap' }}>
        {MODES.map(m => (
          <div
            key={m.to}
            onClick={() => nav(m.to)}
            style={{
              width: 310, 
              background: colors.cardBg, 
              borderRadius: 14, 
              padding: 26,
              cursor: 'pointer', 
              border: `1px solid ${colors.cardBorder}`,
              boxShadow: colors.cardShadow,
              transition: 'all 0.2s', 
              textAlign: 'left',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}
            onMouseEnter={e => {
              e.currentTarget.style.border = `1.5px solid ${m.color}`;
              e.currentTarget.style.transform = 'translateY(-3px)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.border = `1px solid ${colors.cardBorder}`;
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <span style={{ fontSize: 34 }}>{m.icon}</span>
                <span style={{ fontSize: 11, fontWeight: 700, color: m.color, background: `${m.color}15`, padding: '3px 8px', borderRadius: 6 }}>
                  {m.badge}
                </span>
              </div>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: colors.textPrimary, margin: '0 0 8px 0' }}>
                {m.title}
              </h2>
              <p style={{ color: colors.textSecondary, fontSize: 12.5, lineHeight: 1.55, margin: 0 }}>
                {m.sub}
              </p>
            </div>
            
            <div style={{ marginTop: 20, display: 'flex', alignItems: 'center', gap: 6, color: m.color, fontWeight: 700, fontSize: 12.5 }}>
              <span>Open Mode</span>
              <span>→</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
