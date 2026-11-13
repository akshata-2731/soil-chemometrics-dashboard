# -*- coding: utf-8 -*-
"""
================================================================================
SPECTRAL VISUALIZATION SCRIPT: 21 VIS-NIR-UV WAVELENGTHS (49 SOIL SAMPLES)
================================================================================
Generates publication-grade spectral reflectance plots for the uploaded samples
(Sample 1 from Image 1 and Sample 15 from Image 2) and the full 49-sample library:
  1. Continuous Physical Spectrum (200 nm to 940 nm) with UV, VIS, and NIR zones.
  2. Channel-by-Channel Readout in Sensor Column Order.
  3. Full Soil Library Population Envelope (all 49 samples).
================================================================================
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import shutil

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.0

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    data_file = os.path.join(script_dir, 'data.xlsx')
    output_png = os.path.join(script_dir, 'spectral_graph_wavelengths.png')
    
    # Destination in artifact directory
    artifact_dir = r"C:\Users\akash\.gemini\antigravity\brain\2e06cfda-6433-46b2-9d73-32b535b66c25"
    artifact_png = os.path.join(artifact_dir, 'spectral_graph_wavelengths.png')

    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    
    # Extract numerical wavelengths
    raw_wavelengths = [int(c.replace('nm_', '')) for c in spec_cols]
    
    # Sort by physical wavelength
    sort_idx = np.argsort(raw_wavelengths)
    sorted_wl = np.array(raw_wavelengths)[sort_idx]
    sorted_cols = np.array(spec_cols)[sort_idx]
    
    # Extract data
    all_spectra_sorted = df[sorted_cols].values
    all_spectra_raw_order = df[spec_cols].values
    
    mean_spectrum_sorted = np.mean(all_spectra_sorted, axis=0)
    std_spectrum_sorted = np.std(all_spectra_sorted, axis=0)
    
    # Sample 1 (Row 0, Image 1)
    s1_sorted = df.loc[0, sorted_cols].values
    s1_raw = df.loc[0, spec_cols].values
    
    # Sample 15 (Row 14, Image 2)
    s15_sorted = df.loc[14, sorted_cols].values
    s15_raw = df.loc[14, spec_cols].values

    # Setup 2x2 multi-panel layout
    fig = plt.figure(figsize=(16, 12), dpi=300)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1.0], hspace=0.32, wspace=0.22)
    
    # =========================================================================
    # PANEL 1 (Top Span): Continuous Physical Spectral Curve (200 - 940 nm)
    # =========================================================================
    ax1 = fig.add_subplot(gs[0, :])
    
    # Optical bands background shading
    ax1.axvspan(190, 380, color='#8E44AD', alpha=0.08, label='Ultraviolet (UV: 200-380 nm)')
    ax1.axvspan(380, 750, color='#2ECC71', alpha=0.07, label='Visible Light (VIS: 380-750 nm)')
    ax1.axvspan(750, 960, color='#E74C3C', alpha=0.08, label='Near-Infrared (NIR: 750-940 nm)')
    
    # Population Shading (+/- 1 STD)
    ax1.fill_between(sorted_wl, 
                     mean_spectrum_sorted - std_spectrum_sorted, 
                     mean_spectrum_sorted + std_spectrum_sorted, 
                     color='#7F8C8D', alpha=0.20, label='Soil Library Mean ± 1 SD (N=49)')
    
    # Population Mean
    ax1.plot(sorted_wl, mean_spectrum_sorted, color='#2C3E50', linestyle='--', linewidth=2.0, label='Soil Library Mean (N=49)')
    
    # Sample 1 (Uploaded Image 1)
    ax1.plot(sorted_wl, s1_sorted, color='#1F77B4', marker='o', markersize=7, linewidth=2.6, 
             label='Sample 1 (Image 1: nm_410=1709.45, nm_460=1471.25)')
    
    # Sample 15 (Uploaded Image 2)
    ax1.plot(sorted_wl, s15_sorted, color='#D62728', marker='s', markersize=7, linewidth=2.6, 
             label='Sample 15 (Image 2: nm_410=1333.15, nm_460=1209.15)')
    
    # Peak labels
    peaks = [(410, s1_sorted[list(sorted_wl).index(410)], 'Peak 410 nm\n(Violet)'),
             (460, s1_sorted[list(sorted_wl).index(460)], 'Peak 460 nm\n(Blue)'),
             (535, s1_sorted[list(sorted_wl).index(535)], 'Peak 535 nm\n(Green)'),
             (730, s1_sorted[list(sorted_wl).index(730)], 'Peak 730 nm\n(Red Edge)'),
             (940, s1_sorted[list(sorted_wl).index(940)], 'Peak 940 nm\n(NIR Water/OH)')]
             
    for wl_p, val_p, text_p in peaks:
        ax1.annotate(text_p, xy=(wl_p, val_p), xytext=(wl_p, val_p + 140),
                     arrowprops=dict(facecolor='#1F77B4', shrink=0.08, width=1.0, headwidth=5),
                     ha='center', fontsize=9, fontweight='bold', color='#1A5276',
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='#EBF5FB', edgecolor='#AED6F1', alpha=0.9))

    ax1.set_title('Continuous Spectral Reflectance Signature Across Physical Wavelengths (200 nm – 940 nm)', 
                  fontsize=14, fontweight='bold', pad=12, color='#1B2631')
    ax1.set_xlabel('Wavelength λ (nm)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Spectral Intensity / Raw Counts', fontsize=12, fontweight='bold')
    ax1.set_xticks(sorted_wl)
    ax1.set_xticklabels(sorted_wl, rotation=45, fontsize=9)
    ax1.set_xlim(185, 955)
    ax1.set_ylim(-20, 2050)
    ax1.grid(True, linestyle=':', alpha=0.6, color='#BDC3C7')
    ax1.legend(loc='upper right', framealpha=0.95, facecolor='#FFFFFF', edgecolor='#BDC3C7', fontsize=9.5)

    # =========================================================================
    # PANEL 2 (Bottom-Left): Channel Sequence in Sensor Column Order
    # =========================================================================
    ax2 = fig.add_subplot(gs[1, 0])
    
    x_indices = np.arange(len(spec_cols))
    bar_width = 0.38
    
    ax2.bar(x_indices - bar_width/2, s1_raw, width=bar_width, color='#1F77B4', alpha=0.85, label='Sample 1 (Image 1)')
    ax2.bar(x_indices + bar_width/2, s15_raw, width=bar_width, color='#D62728', alpha=0.85, label='Sample 15 (Image 2)')
    
    ax2.set_title('Readout Profile in Table Column Order (nm_410 → nm_200)', 
                  fontsize=12, fontweight='bold', pad=10, color='#1B2631')
    ax2.set_xlabel('Sensor Channel (As Ordered in Uploaded Image)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Spectral Intensity', fontsize=11, fontweight='bold')
    ax2.set_xticks(x_indices)
    ax2.set_xticklabels(spec_cols, rotation=65, ha='right', fontsize=8.5)
    ax2.set_ylim(0, 1950)
    ax2.grid(True, axis='y', linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right', fontsize=9.5, framealpha=0.95)

    # =========================================================================
    # PANEL 3 (Bottom-Right): Full Soil Library Envelope (N=49)
    # =========================================================================
    ax3 = fig.add_subplot(gs[1, 1])
    
    # Plot all 49 background samples
    for i in range(len(df)):
        ax3.plot(sorted_wl, all_spectra_sorted[i], color='#BDC3C7', linewidth=0.8, alpha=0.45)
    # Re-plot last one for label
    ax3.plot([], [], color='#BDC3C7', linewidth=1.2, label='Other 47 Soil Samples')
    
    # Highlighted user samples
    ax3.plot(sorted_wl, s1_sorted, color='#1F77B4', marker='o', markersize=5, linewidth=2.2, label='Sample 1 (Image 1)')
    ax3.plot(sorted_wl, s15_sorted, color='#D62728', marker='s', markersize=5, linewidth=2.2, label='Sample 15 (Image 2)')
    ax3.plot(sorted_wl, mean_spectrum_sorted, color='#27AE60', linestyle='--', linewidth=2.0, label='Library Mean')
    
    ax3.set_title('Sample Profiles within Full 49-Sample Soil Library', 
                  fontsize=12, fontweight='bold', pad=10, color='#1B2631')
    ax3.set_xlabel('Physical Wavelength λ (nm)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Spectral Intensity', fontsize=11, fontweight='bold')
    ax3.set_xticks([200, 320, 460, 535, 645, 730, 860, 940])
    ax3.set_xlim(185, 955)
    ax3.set_ylim(-20, 2050)
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.legend(loc='upper right', fontsize=9.5, framealpha=0.95)

    # Global Super Title
    fig.suptitle('VIS-NIR-UV Spectral Reflectance Profiles for 21 Sensor Wavelengths', 
                 fontsize=16, fontweight='heavy', y=0.98, color='#0D233A')

    plt.savefig(output_png, bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"Saved spectral graph to: {output_png}")
    
    # Copy to artifacts directory
    shutil.copy(output_png, artifact_png)
    print(f"Copied spectral graph to artifacts: {artifact_png}")

if __name__ == '__main__':
    main()
