# -*- coding: utf-8 -*-
"""
================================================================================
RAINBOW SPECTRAL INTENSITY GRAPH (Y-AXIS INTENSITY MAPPED TO RAINBOW COLORS)
================================================================================
Plots the spectral reflectance signature where the color of the curve, markers,
and vertical gradient fill directly correspond to the Y-axis intensity change
using a vibrant rainbow spectrum (Violet -> Blue -> Cyan -> Green -> Yellow -> Orange -> Red).
================================================================================
"""

import os
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from scipy.interpolate import PchipInterpolator

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.2

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    data_file = os.path.join(script_dir, 'data.xlsx')
    output_png = os.path.join(script_dir, 'rainbow_intensity_spectral_graph.png')
    
    artifact_dir = r"C:\Users\akash\.gemini\antigravity\brain\2e06cfda-6433-46b2-9d73-32b535b66c25"
    artifact_png = os.path.join(artifact_dir, 'rainbow_intensity_spectral_graph.png')

    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    wavelengths = np.array([int(c.replace('nm_', '')) for c in spec_cols])
    
    # Sort physically from 200 nm to 940 nm
    sort_idx = np.argsort(wavelengths)
    sorted_wl = wavelengths[sort_idx]
    sorted_cols = np.array(spec_cols)[sort_idx]
    
    # Sample 1 (Image 1) and Sample 15 (Image 2)
    s1_y = df.loc[0, sorted_cols].values.astype(float)
    s15_y = df.loc[14, sorted_cols].values.astype(float)

    # High-resolution interpolation using shape-preserving PCHIP
    wl_fine = np.linspace(sorted_wl.min(), sorted_wl.max(), 1200)
    pchip_s1 = PchipInterpolator(sorted_wl, s1_y)
    y_fine_s1 = pchip_s1(wl_fine)

    pchip_s15 = PchipInterpolator(sorted_wl, s15_y)
    y_fine_s15 = pchip_s15(wl_fine)

    # Colormap and Normalization for Y-Axis Intensity
    # Rainbow spectrum: Violet/Blue (low) -> Green/Yellow (mid) -> Red (high)
    cmap = plt.cm.turbo  # Vibrant, perceptual, high-contrast rainbow colormap
    norm = Normalize(vmin=0, vmax=1800)

    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)
    fig.patch.set_facecolor('#FAFAFA')
    ax.set_facecolor('#FFFFFF')

    # 1. Background Vertical Rainbow Gradient Fill Under the Curve
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path

    # Create polygon path under the s1 curve
    verts = [(wl_fine[0], 0)] + list(zip(wl_fine, y_fine_s1)) + [(wl_fine[-1], 0)]
    path = Path(verts)
    patch = PathPatch(path, facecolor='none', edgecolor='none')
    ax.add_patch(patch)

    # Vertical rainbow gradient mapped to Y intensity
    gradient_y = np.linspace(0, 1800, 300)[:, None]
    im = ax.imshow(gradient_y, extent=[sorted_wl.min(), sorted_wl.max(), 0, 1800],
                   origin='lower', cmap=cmap, norm=norm, aspect='auto', alpha=0.35)
    im.set_clip_path(patch)

    # 2. Rainbow Line Collection for Sample 1
    # Create segments for multi-colored line based on Y intensity
    points = np.array([wl_fine, y_fine_s1]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    lc_s1 = LineCollection(segments, cmap=cmap, norm=norm, linewidth=4.0, zorder=5)
    lc_s1.set_array(y_fine_s1)
    ax.add_collection(lc_s1)

    # 3. Add Sample 15 (Image 2) as a dashed comparison line
    points_s15 = np.array([wl_fine, y_fine_s15]).T.reshape(-1, 1, 2)
    segments_s15 = np.concatenate([points_s15[:-1], points_s15[1:]], axis=1)
    lc_s15 = LineCollection(segments_s15, cmap=cmap, norm=norm, linewidth=2.5, linestyle='--', alpha=0.85, zorder=4)
    lc_s15.set_array(y_fine_s15)
    ax.add_collection(lc_s15)

    # 4. Scatter Plot of the 21 Discrete Sensor Wavelengths (Sample 1)
    sc = ax.scatter(sorted_wl, s1_y, c=s1_y, cmap=cmap, norm=norm, 
                    s=80, edgecolors='#1B2631', linewidth=1.5, zorder=6)

    # Scatter markers for Sample 15
    ax.scatter(sorted_wl, s15_y, c=s15_y, cmap=cmap, norm=norm, 
               s=55, marker='s', edgecolors='#1B2631', linewidth=1.2, alpha=0.85, zorder=6)

    # 5. Label Major Peaks and Valleys with exact intensity values
    annotations = [
        (410, s1_y[list(sorted_wl).index(410)], "410 nm\n1709.5", 70, 'bottom'),
        (460, s1_y[list(sorted_wl).index(460)], "460 nm\n1471.3", 70, 'bottom'),
        (535, s1_y[list(sorted_wl).index(535)], "535 nm\n1107.5", 70, 'bottom'),
        (730, s1_y[list(sorted_wl).index(730)], "730 nm\n650.8", 70, 'bottom'),
        (940, s1_y[list(sorted_wl).index(940)], "940 nm\n362.0", 70, 'bottom'),
        (680, s1_y[list(sorted_wl).index(680)], "680 nm\n44.1", 90, 'bottom'),
        (705, s1_y[list(sorted_wl).index(705)], "705 nm\n18.0", 170, 'bottom'),
    ]

    for wl, val, text, y_offset, va in annotations:
        ax.annotate(text, xy=(wl, val), xytext=(wl, val + y_offset),
                    arrowprops=dict(arrowstyle='->', color='#2C3E50', lw=1.2),
                    ha='center', va=va,
                    fontsize=8.5, fontweight='bold', color='#1B2631',
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='#FFFFFF', edgecolor='#BDC3C7', alpha=0.92, lw=0.8))

    # Formatting axes and labels
    ax.set_title('Spectral Reflectance Curve with Rainbow Intensity Gradient (Y-Axis Mapping)', 
                 fontsize=15, fontweight='bold', pad=15, color='#0D233A')
    ax.set_xlabel('Wavelength λ (nm)', fontsize=12, fontweight='bold', labelpad=8, color='#1B2631')
    ax.set_ylabel('Spectral Intensity (Counts)', fontsize=12, fontweight='bold', labelpad=8, color='#1B2631')
    
    ax.set_xticks(sorted_wl)
    ax.set_xticklabels(sorted_wl, rotation=45, fontsize=9, fontweight='medium')
    ax.set_xlim(185, 955)
    ax.set_ylim(-30, 1950)
    
    ax.grid(True, linestyle=':', alpha=0.55, color='#95A5A6')

    # Add Colorbar for Y-Axis Rainbow Intensity
    cbar = fig.colorbar(im, ax=ax, orientation='vertical', pad=0.02, aspect=28)
    cbar.set_label('Spectral Intensity (Y-Axis Rainbow Scale)', fontsize=11, fontweight='bold', labelpad=10, color='#1B2631')
    cbar.ax.tick_params(labelsize=9.5)
    cbar.outline.set_edgecolor('#333333')
    cbar.outline.set_linewidth(1.0)

    # Custom Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='#E74C3C', lw=3.5, label='Sample 1 (Image 1: nm_410 = 1709.5) [Solid]'),
        Line2D([0], [0], color='#3498DB', lw=2.5, linestyle='--', label='Sample 15 (Image 2: nm_410 = 1333.2) [Dashed]'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#F39C12', markeredgecolor='#1B2631', markersize=8, label='21 Discrete Sensor Wavelengths')
    ]
    ax.legend(handles=legend_elements, loc='upper right', framealpha=0.95, facecolor='#FFFFFF', edgecolor='#BDC3C7', fontsize=9.5)

    plt.tight_layout()
    plt.savefig(output_png, bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"Saved rainbow intensity spectral graph to: {output_png}")
    shutil.copy(output_png, artifact_png)
    print(f"Copied to artifact directory: {artifact_png}")

if __name__ == '__main__':
    main()
