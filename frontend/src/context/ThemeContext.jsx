import React, { createContext, useContext, useState, useEffect } from 'react';

export const themeColors = {
  light: {
    name: 'light',
    bg: '#f8fafc',
    cardBg: '#ffffff',
    cardBorder: '#cbd5e1',
    cardShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
    textPrimary: '#0f172a',
    textSecondary: '#334155',
    textMuted: '#64748b',
    grid: '#e2e8f0',
    inputBg: '#ffffff',
    inputBorder: '#cbd5e1',
    inputColor: '#0f172a',
    navBg: '#ffffff',
    navBorder: '#cbd5e1',
    navLink: '#475569',
    navLinkActive: '#0284c7',
    navLinkActiveBg: '#e0f2fe',
    accent: '#0284c7',
    spectralLine: '#0284c7',
    spectralDot: '#0369a1',
    actualSeries: '#6366f1',
    predictedSeries: '#0284c7',
    tableHeaderBg: '#f1f5f9',
    tableBorder: '#e2e8f0',
    tableAltRow: '#f8fafc',
    modalOverlay: 'rgba(15, 23, 42, 0.6)',
  },
  dark: {
    name: 'dark',
    bg: '#0f172a',
    cardBg: '#1e293b',
    cardBorder: '#334155',
    cardShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
    textPrimary: '#f1f5f9',
    textSecondary: '#cbd5e1',
    textMuted: '#94a3b8',
    grid: '#334155',
    inputBg: '#0f172a',
    inputBorder: '#334155',
    inputColor: '#f1f5f9',
    navBg: '#0f172a',
    navBorder: '#1e293b',
    navLink: '#94a3b8',
    navLinkActive: '#38bdf8',
    navLinkActiveBg: '#1e3a5f',
    accent: '#38bdf8',
    spectralLine: '#38bdf8',
    spectralDot: '#7dd3fc',
    actualSeries: '#818cf8',
    predictedSeries: '#38bdf8',
    tableHeaderBg: '#1e293b',
    tableBorder: '#334155',
    tableAltRow: '#0f172a44',
    modalOverlay: 'rgba(0, 0, 0, 0.75)',
  }
};

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('soil_app_theme') || 'light';
  });

  useEffect(() => {
    localStorage.setItem('soil_app_theme', theme);
    document.body.style.backgroundColor = themeColors[theme].bg;
    document.body.style.color = themeColors[theme].textPrimary;
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  const colors = themeColors[theme];

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, colors }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
