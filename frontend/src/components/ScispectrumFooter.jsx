import React from 'react';
import { useTheme } from '../context/ThemeContext';

export default function ScispectrumFooter() {
  const { colors } = useTheme();

  return (
    <footer style={{
      background: '#0a2540',
      color: '#e2e8f0',
      borderTop: '2px solid #0284c7',
      marginTop: 48,
      padding: '36px 24px 20px',
      fontSize: 13,
      lineHeight: 1.6
    }}>
      <div style={{
        maxWidth: 1240,
        margin: '0 auto',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 28,
        marginBottom: 28
      }}>
        {/* Col 1: Corporate Details */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <span style={{ fontSize: 22, fontWeight: 900, color: '#38bdf8', letterSpacing: 1 }}>
              SCISPECTRUM
            </span>
          </div>
          <p style={{ fontWeight: 700, margin: '0 0 6px 0', color: '#fff', fontSize: 13 }}>
            Scispectrum Lab Essentials Pvt Ltd
          </p>
          <p style={{ margin: '0 0 6px 0', color: '#94a3b8', fontSize: 12 }}>
            5-141-A2, Bharathi Nagar, Navalur Kuttapattu, Trichy, Tamil Nadu – 620009, India
          </p>
          <p style={{ margin: '0 0 4px 0', color: '#94a3b8', fontSize: 12 }}>
            <strong style={{ color: '#cbd5e1' }}>GSTIN:</strong> 33ABMCS4318R1ZP
          </p>
          <p style={{ margin: '0 0 4px 0', color: '#94a3b8', fontSize: 12 }}>
            <strong style={{ color: '#cbd5e1' }}>Phone:</strong> +91 74488 82650
          </p>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: 12 }}>
            <strong style={{ color: '#cbd5e1' }}>Email:</strong> info@scispectrum.in
          </p>
        </div>

        {/* Col 2: The Lenz Product Family */}
        <div>
          <h4 style={{ color: '#38bdf8', fontSize: 14, fontWeight: 700, margin: '0 0 12px 0', letterSpacing: 0.5 }}>
            LENZ™ PRODUCT SUITE
          </h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12 }}>
            <li style={{ color: '#fff', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ color: '#10b981' }}>●</span>
              <span>SoilLenz™ (Active Software)</span>
            </li>
            <li style={{ color: '#94a3b8' }}>• LeafLenz™ (Plant & Foliar Test)</li>
            <li style={{ color: '#94a3b8' }}>• HarvestLenz™ (Crop & Grain Test)</li>
            <li style={{ color: '#94a3b8' }}>• AquaLenz™ (Water Quality Test)</li>
            <li style={{ color: '#94a3b8' }}>• EnviroLenz™ (Environment Test)</li>
          </ul>
        </div>

        {/* Col 3: Analytical Features & Scientific Methods */}
        <div>
          <h4 style={{ color: '#38bdf8', fontSize: 14, fontWeight: 700, margin: '0 0 12px 0', letterSpacing: 0.5 }}>
            ANALYTICAL PLATFORM
          </h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12, color: '#94a3b8' }}>
            <li>• Spectroscopy (Light wave test: 200–2500 nm)</li>
            <li>• 12 Nutrients (OC, N, P, K, Ca, Mg, S, Fe, Mn, Cu, Zn, B)</li>
            <li>• 73 ML Models (AI algorithms)</li>
            <li>• 51 Math Logics (Physics formulas)</li>
            <li>• 75% QC Accuracy (Pass threshold)</li>
          </ul>
        </div>

        {/* Col 4: Quality & Compliance */}
        <div>
          <h4 style={{ color: '#38bdf8', fontSize: 14, fontWeight: 700, margin: '0 0 12px 0', letterSpacing: 0.5 }}>
            QUALITY & SUPPORT
          </h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12, color: '#94a3b8' }}>
            <li>• Actual vs Predicted (Real vs Model test)</li>
            <li>• Excel Auto Reports (With Scatter & Line graphs)</li>
            <li>• Zero-point Calibration (Sensor zero adjust)</li>
            <li>• Audit History (Saved test runs)</li>
            <li>• Mon–Sat: 9:30 AM – 6:00 PM IST</li>
          </ul>
        </div>
      </div>

      <div style={{
        maxWidth: 1240,
        margin: '0 auto',
        paddingTop: 16,
        borderTop: '1px solid #1e3a5f',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 10,
        fontSize: 11,
        color: '#64748b'
      }}>
        <div>
          © 2026 Scispectrum Lab Essentials Pvt Ltd. All Rights Reserved.
        </div>
        <div>
          SoilLenz™ Chemometrics Engine v4.2 | ISO Standard Environmental Testing
        </div>
      </div>
    </footer>
  );
}
