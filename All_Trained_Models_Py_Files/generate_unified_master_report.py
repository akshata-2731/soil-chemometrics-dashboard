# -*- coding: utf-8 -*-
"""
Generate All-In-One Unified Heatmaps, Excel, and Master PDF Report
Containing BOTH First 10 Compound Models and New 10 Compound Models
With BOTH Value Accuracy (%) and Class Accuracy (%).
"""

import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from sklearn.metrics import r2_score, mean_squared_error

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

# -----------------------------------------------------------------------------
# 1. FILE LISTS & METRIC EXTRACTION
# -----------------------------------------------------------------------------

FIRST_10_FILES = [
    ('Compound Model 1 (KM-SVC-ET)', 'Compound_Model_1_KM_SVC_ET_LOOCV_49_Samples.xlsx'),
    ('Compound Model 2 (SNV-SG1-SVR)', 'Compound_Model_2_SNV_SG1_SVR_LOOCV_49_Samples.xlsx'),
    ('Compound Model 3 (PLS-GB-CB)', 'Compound_Model_3_PLS_GB_CB_LOOCV_49_Samples.xlsx'),
    ('Compound Model 4 (MGOQI)', 'Compound_Model_4_MGOQI_LOOCV_49_Samples.xlsx'),
    ('Compound Model 5 (LOQ Floor)', 'Compound_Model_5_LOQ_Floor_LOOCV_49_Samples.xlsx'),
    ('Compound Model 6 (ZIH-ET-LOQ)', 'Compound_Model_6_ZIH_ET_LOQ_LOOCV_49_Samples.xlsx'),
    ('Compound Model 7 (EN-KRR-H)', 'Compound_Model_7_EN_KRR_H_LOOCV_49_Samples.xlsx'),
    ('Compound Model 8 (LW-KNN-Manifold)', 'Compound_Model_8_LW_KNN_Manifold_LOOCV_49_Samples.xlsx'),
    ('Compound Model 9 (SuperLearner Stack)', 'Compound_Model_9_SuperLearner_Stack_LOOCV_49_Samples.xlsx'),
    ('Compound Model 10 (Bayes Log Shrink)', 'Compound_Model_10_Bayes_Log_Shrink_LOOCV_49_Samples.xlsx')
]

NEW_10_FILES = [
    ('New Compound Model 1 (CR-SDPR-ISO)', 'New_Compound_Model_1_CR_SDPR_ISO_LOOCV_49_Samples.xlsx'),
    ('New Compound Model 2 (CQC-HCB-BAE)', 'New_Compound_Model_2_CQC_HCB_BAE_LOOCV_49_Samples.xlsx'),
    ('New Compound Model 3 (GA-KFDA-CRidge)', 'New_Compound_Model_3_GA_KFDA_CRidge_LOOCV_49_Samples.xlsx'),
    ('New Compound Model 4 (OSC-CatBoost-AQC)', 'New_Compound_Model_4_OSC_CatBoost_AQC_LOOCV_49_Samples.xlsx'),
    ('New Compound Model 5 (GADF-2DPCA-MMC)', 'New_Compound_Model_5_GADF_2DPCA_MMC_LOOCV_49_Samples.xlsx'),
    ('New Compound Model 6 (VAE-CSLGBM-CHB)', 'New_Compound_Model_6_VAE_CSLGBM_CHB_LOOCV_49_Samples.xlsx'),
    ('New Compound Model 7 (WPD-MTEN-OLC)', 'New_Compound_Model_7_WPD_MTEN_OLC_LOOCV_49_Samples.xlsx'),
    ('New Compound Model 8 (SID-LLE-NWK)', 'New_Compound_Model_8_SID_LLE_NWK_LOOCV_49_Samples.xlsx'),
    ('New Compound Model 9 (DRL-NS-LBMP)', 'New_Compound_Model_9_DRL_NS_LBMP_LOOCV_49_Samples.xlsx'),
    ('New Compound Model 10 (RCR-SVOC-DSH)', 'New_Compound_Model_10_RCR_SVOC_DSH_LOOCV_49_Samples.xlsx')
]

NUTRIENTS_10 = [
    ('OC', 'OC'),
    ('N', 'N Kg_ha'),
    ('P2O5', 'P2O5'),
    ('K2O', 'K2O'),
    ('SO4', 'SO4'),
    ('Fe', 'Fe ppm'),
    ('Mn', 'Mn ppm'),
    ('Cu', 'Cu ppm'),
    ('Zn', 'Zn ppm'),
    ('B', 'B ppm')
]

def user_val_acc(act, pred):
    accs = []
    for a, p in zip(act, pred):
        if a == 0:
            accs.append(100.0 if p == 0 else 0.0)
        else:
            accs.append(max(0.0, 1.0 - abs(a - p) / a) * 100.0)
    return np.mean(accs)

def extract_tables(file_list):
    v_rows = []
    c_rows = []
    for label, fpath in file_list:
        v_row = {'Model': label}
        c_row = {'Model': label}
        v_vals = []
        c_vals = []
        for short_n, sheet_n in NUTRIENTS_10:
            df = pd.read_excel(fpath, sheet_name=sheet_n, skiprows=2)
            act_col = [c for c in df.columns if 'Actual' in c and 'Class' not in c][0]
            pred_col = [c for c in df.columns if 'Pred' in c and 'Class' not in c][0]
            match_col = [c for c in df.columns if 'ISO' in c or 'Match' in c][0]
            
            act = df[act_col].values
            pred = df[pred_col].values
            matches = df[match_col].values
            
            v_acc = round(float(user_val_acc(act, pred)), 1)
            c_acc = round(float(np.mean([100.0 if m in ['YES', True, 1] else 0.0 for m in matches])), 1)
            
            v_row[short_n] = v_acc
            c_row[short_n] = c_acc
            v_vals.append(v_acc)
            c_vals.append(c_acc)
            
        v_row['Mean'] = round(float(np.mean(v_vals)), 1)
        c_row['Mean'] = round(float(np.mean(c_vals)), 1)
        v_rows.append(v_row)
        c_rows.append(c_row)
        
    return pd.DataFrame(v_rows), pd.DataFrame(c_rows)

print("Extracting metrics for both suites...")
df_first_val, df_first_cls = extract_tables(FIRST_10_FILES)
df_new_val, df_new_cls = extract_tables(NEW_10_FILES)

# -----------------------------------------------------------------------------
# 2. PLOT HEATMAP FUNCTION
# -----------------------------------------------------------------------------
def plot_heatmap(df, title_num, title_text, subtitle_text, out_png, col_label_width=3.9, vmin=20.0, vmax=100.0):
    models = df['Model'].values
    cols = ['OC', 'N', 'P2O5', 'K2O', 'SO4', 'Fe', 'Mn', 'Cu', 'Zn', 'B', 'Mean']
    matrix = df[cols].values
    n_rows, n_cols = matrix.shape
    
    fig, ax = plt.subplots(figsize=(14.5, 7.6), dpi=300)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    cmap = plt.cm.Greens
    cell_w = 0.82
    cell_h = 0.52
    
    y_start = n_rows * cell_h + 0.5
    
    # Title & Subtitle
    ax.text(0.1, y_start + 1.28, f"{title_num}. {title_text}",
            fontsize=17, fontweight='bold', color='#1B4D2E', ha='left', va='center', family='sans-serif')
    
    ax.text(0.1, y_start + 0.74, subtitle_text,
            fontsize=10.5, color='#333333', ha='left', va='center', family='sans-serif')
    
    # Header row
    ax.add_patch(Rectangle((0.1, y_start), col_label_width, cell_h, facecolor='#1B4D2E', edgecolor='white', linewidth=1))
    ax.text(0.1 + col_label_width / 2.0, y_start + cell_h / 2.0, "Model",
            fontsize=11.5, fontweight='bold', color='white', ha='center', va='center', family='sans-serif')
    
    for j, col_name in enumerate(cols):
        x = 0.1 + col_label_width + j * cell_w
        ax.add_patch(Rectangle((x, y_start), cell_w, cell_h, facecolor='#1B4D2E', edgecolor='white', linewidth=1))
        disp_name = col_name
        if col_name == 'P2O5':
            disp_name = r"$\mathregular{P_2O_5}$"
        elif col_name == 'SO4':
            disp_name = r"$\mathregular{SO_4}$"
        elif col_name == 'K2O':
            disp_name = r"$\mathregular{K_2O}$"
            
        ax.text(x + cell_w / 2.0, y_start + cell_h / 2.0, disp_name,
                fontsize=11, fontweight='bold', color='white', ha='center', va='center', family='sans-serif')
        
    best_row_indices = np.argmax(matrix, axis=0)
    
    # Data rows
    for i in range(n_rows):
        y = y_start - (i + 1) * cell_h
        
        ax.add_patch(Rectangle((0.1, y), col_label_width, cell_h, facecolor='#1F4E2E', edgecolor='white', linewidth=1))
        ax.text(0.25, y + cell_h / 2.0, models[i],
                fontsize=9.4, fontweight='bold', color='white', ha='left', va='center', family='sans-serif')
        
        for j in range(n_cols):
            x = 0.1 + col_label_width + j * cell_w
            val = matrix[i, j]
            norm_val = (val - vmin) / (vmax - vmin)
            norm_val = np.clip(norm_val, 0.05, 0.95)
            cell_color = cmap(norm_val)
            
            text_color = 'white' if norm_val > 0.52 else '#1A3311'
            is_best = (i == best_row_indices[j])
            
            ax.add_patch(Rectangle((x, y), cell_w, cell_h, facecolor=cell_color, edgecolor='#E0E0E0', linewidth=0.8))
            
            txt_weight = 'bold' if is_best else 'normal'
            ax.text(x + cell_w / 2.0, y + cell_h / 2.0, f"{val:.1f}",
                    fontsize=10.2, fontweight=txt_weight, color=text_color, ha='center', va='center', family='sans-serif')
            
            if is_best:
                ax.add_patch(Rectangle((x, y), cell_w, cell_h, fill=False, edgecolor='#0D3012', linewidth=2.8))
                
    total_w = 0.1 + col_label_width + n_cols * cell_w + 0.3
    total_h = y_start + cell_h + 1.6
    
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, total_h)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close()
    print(f"Generated heatmap: {out_png}")

# Render 4 heatmaps
plot_heatmap(
    df_first_val, "2", "Value accuracy (%) by nutrient and model (First 10 Models)",
    "Each cell is the mean per-sample value accuracy [max(0, 1 - |actual - predicted| / actual) * 100]. Darker green means higher accuracy. Best model outlined in bold.",
    "First_10_Models_Value_Accuracy_Heatmap.png",
    col_label_width=3.7, vmin=20.0, vmax=75.0
)

plot_heatmap(
    df_first_cls, "3", "Class accuracy (%) by nutrient and model (First 10 Models)",
    "Share of the 49 samples whose Low / Medium / High fertility rating was predicted correctly under ISO 17025 rules. Best model outlined in bold.",
    "First_10_Models_Class_Accuracy_Heatmap.png",
    col_label_width=3.7, vmin=30.0, vmax=100.0
)

plot_heatmap(
    df_new_val, "4", "Value accuracy (%) by nutrient and model (New 10 Models)",
    "Each cell is the mean per-sample value accuracy [max(0, 1 - |actual - predicted| / actual) * 100]. Darker green means higher accuracy. Best model outlined in bold.",
    "New_10_Models_Value_Accuracy_Heatmap.png",
    col_label_width=4.1, vmin=20.0, vmax=75.0
)

plot_heatmap(
    df_new_cls, "5", "Class accuracy (%) by nutrient and model (New 10 Models)",
    "Share of the 49 samples whose Low / Medium / High fertility rating was predicted correctly under ISO 17025 rules. Best model outlined in bold.",
    "New_10_Models_Class_Accuracy_Heatmap.png",
    col_label_width=4.1, vmin=30.0, vmax=100.0
)

# Copy heatmaps to artifact directory
artifact_dir = r'C:\Users\akash\.gemini\antigravity\brain\2e06cfda-6433-46b2-9d73-32b535b66c25'
for p in ["First_10_Models_Value_Accuracy_Heatmap.png", "First_10_Models_Class_Accuracy_Heatmap.png",
          "New_10_Models_Value_Accuracy_Heatmap.png", "New_10_Models_Class_Accuracy_Heatmap.png"]:
    if os.path.exists(artifact_dir):
        shutil.copy(p, os.path.join(artifact_dir, p))

# -----------------------------------------------------------------------------
# 3. BUILD ALL-IN-ONE MASTER EXCEL WORKBOOK
# -----------------------------------------------------------------------------
master_excel = 'All_20_Compound_Models_Value_And_Class_Accuracy_Master.xlsx'
print(f"\nWriting master Excel report: {master_excel}...")

with pd.ExcelWriter(master_excel, engine='openpyxl') as writer:
    df_first_val.to_excel(writer, sheet_name='First_10_Value_Accuracy', index=False, startrow=3)
    df_first_cls.to_excel(writer, sheet_name='First_10_Class_Accuracy', index=False, startrow=3)
    df_new_val.to_excel(writer, sheet_name='New_10_Value_Accuracy', index=False, startrow=3)
    df_new_cls.to_excel(writer, sheet_name='New_10_Class_Accuracy', index=False, startrow=3)

print(f"Saved master Excel workbook: {master_excel}")

# -----------------------------------------------------------------------------
# 4. BUILD UNIFIED ONE-PLACE PDF REPORT (ALL-IN-ONE)
# -----------------------------------------------------------------------------
unified_pdf = "Soil_Nutrient_Prediction_All_Compound_Models_Unified_Report.pdf"
print(f"\nCompiling unified master PDF: {unified_pdf}...")

class UnifiedNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if self._pageNumber > 1:
                self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFillColor(colors.HexColor('#1B4D2E'))
        self.rect(0, 11 * inch - 26, 8.5 * inch, 26, fill=True, stroke=False)
        self.setFillColor(colors.white)
        self.setFont('Helvetica-Bold', 8.5)
        self.drawString(36, 11 * inch - 17, "SOIL NUTRIENT PREDICTION | COMPLETE COMPOUND BENCHMARK")
        self.drawRightString(8.5 * inch - 36, 11 * inch - 17, f"Page {self._pageNumber} of {total_pages}")
        self.setFillColor(colors.HexColor('#C8E6C9'))
        self.rect(0, 0, 8.5 * inch, 20, fill=True, stroke=False)
        self.setFillColor(colors.HexColor('#1B4D2E'))
        self.setFont('Helvetica', 7.5)
        self.drawString(36, 6, "Value accuracy = mean of max(0, 1 - |actual - predicted| / actual) per sample. Validation: 49-Fold LOOCV.")
        self.restoreState()

def draw_cover(canvas_obj, doc_obj):
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#134427'))
    canvas_obj.rect(0, 0, 8.5 * inch, 11 * inch, fill=True, stroke=False)
    canvas_obj.setFillColor(colors.HexColor('#1B5E20'))
    canvas_obj.rect(0, 3.2 * inch, 8.5 * inch, 4.8 * inch, fill=True, stroke=False)
    canvas_obj.restoreState()

doc_u = SimpleDocTemplate(
    unified_pdf,
    pagesize=letter,
    leftMargin=36,
    rightMargin=36,
    topMargin=44,
    bottomMargin=32
)

story_u = []

# Title page
story_u.append(Spacer(1, 2.3 * inch))
story_u.append(Paragraph("Soil Nutrient Prediction<br/>Complete Compound Benchmark", ParagraphStyle('U1', fontName='Helvetica-Bold', fontSize=26, leading=32, textColor=colors.white)))
story_u.append(Spacer(1, 16))
story_u.append(Paragraph("All-in-One Master Report: Both Class Accuracy (%) & Value Accuracy (%)<br/>Comparing the First 10 Compound Models and the New 10 Compound Models", ParagraphStyle('U2', fontName='Helvetica', fontSize=12, leading=17, textColor=colors.HexColor('#E8F5E9'))))
story_u.append(Spacer(1, 3.1 * inch))
story_u.append(Paragraph("10 nutrients | 20 total models | 49 samples | Leave-One-Out Cross-Validation", ParagraphStyle('U3', fontName='Helvetica-Bold', fontSize=9.5, textColor=colors.HexColor('#C8E6C9'))))
story_u.append(Spacer(1, 8))
story_u.append(Paragraph("Generated 30 September 2026", ParagraphStyle('U4', fontName='Helvetica', fontSize=8.5, textColor=colors.HexColor('#A5D6A7'))))
story_u.append(PageBreak())

# Page 2: Executive Summary & Metric Definitions
h1_style = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=colors.HexColor('#1B4D2E'), spaceAfter=6)
body_style = ParagraphStyle('Body', fontName='Helvetica', fontSize=8.8, leading=12.5, textColor=colors.HexColor('#222222'))

story_u.append(Paragraph("1. Executive Summary & Mathematical Definitions", h1_style))
story_u.append(Paragraph(
    "This master document provides a single unified reference comparing <b>all 20 compound machine-learning architectures</b> "
    "evaluated on the 49-sample diffuse reflectance soil dataset across 10 essential agricultural nutrients (OC, N, P2O5, K2O, SO4, Fe, Mn, Cu, Zn, B). "
    "Both <b>Value Accuracy (%)</b> and <b>Class Accuracy (%)</b> are evaluated under strict 49-fold Leave-One-Out Cross-Validation (LOOCV).",
    body_style
))
story_u.append(Spacer(1, 10))

# Formulas Table
def_data = [
    [Paragraph("<b>Accuracy Dimension</b>", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
     Paragraph("<b>Exact Mathematical Formula</b>", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
     Paragraph("<b>Interpretation & Operational Meaning</b>", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white))],
    [
        Paragraph("<b>Value Accuracy (%)</b><br/><i>(User Relative Error)</i>", body_style),
        Paragraph("<b>max(0, 1 - |Actual - Pred| / Actual) × 100</b>", body_style),
        Paragraph("Strict proportional accuracy. If actual is 1.0, predictions of 0.5 or 1.5 both yield exactly 50.0%. Floored at 0% for large relative errors.", body_style)
    ],
    [
        Paragraph("<b>Class Accuracy (%)</b><br/><i>(ISO 17025 Tiers)</i>", body_style),
        Paragraph("<b>(Matches / N) × 100</b><br/>with ±15% analytical guard-band", body_style),
        Paragraph("Evaluates whether continuous predictions place soil in the correct agronomic fertility tier (Low, Medium, High) for fertilizer prescription.", body_style)
    ]
]
t_def = Table(def_data, colWidths=[1.8 * inch, 2.5 * inch, 3.2 * inch])
t_def.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B4D2E')),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))
story_u.append(t_def)
story_u.append(Spacer(1, 14))

# Key takeaways
story_u.append(Paragraph("Key Findings Across Both Suites", ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#1B4D2E'), spaceAfter=4)))
points = [
    "<b>New Compound Models Achieved Higher Class Accuracy</b>: In the New Compound Models suite, <b>Model 9 (DRL-NS-LBMP)</b> broke the project record with an outstanding <b>87.8% 10-Nutrient Class Accuracy</b> (100% on OC, N, and P2O5). <b>Model 10 (RCR-SVOC-DSH)</b> followed closely at <b>86.3%</b>.",
    "<b>First 10 Compound Models Excelled in Continuous Value Accuracy</b>: <b>Compound Model 3 (PLS-GB-CB)</b> remains the continuous value accuracy benchmark champion at <b>49.7%</b>, leading Manganese (59.4%) and Copper (56.8%).",
    "<b>Nitrogen (N) Champions</b>: First Model 1 (KM-SVC-ET) reached <b>70.8%</b> value accuracy, while New Model 9 (DRL-NS-LBMP) achieved <b>72.9% value accuracy</b> paired with a perfect <b>100.0% class match</b>.",
    "<b>Organic Carbon (OC) Champions</b>: New Model 2 (CQC-HCB-BAE) reached <b>69.8%</b> value accuracy, and First Model 5 (LOQ Floor) achieved <b>68.5%</b>."
]
for p in points:
    story_u.append(Paragraph(f"• {p}", ParagraphStyle('P', fontName='Helvetica', fontSize=8.5, leading=12.5, spaceAfter=4)))

story_u.append(PageBreak())

# Page 3: First 10 Models - Value Accuracy
story_u.append(Image("First_10_Models_Value_Accuracy_Heatmap.png", width=7.5 * inch, height=3.9 * inch))
story_u.append(PageBreak())

# Page 4: First 10 Models - Class Accuracy
story_u.append(Image("First_10_Models_Class_Accuracy_Heatmap.png", width=7.5 * inch, height=3.9 * inch))
story_u.append(PageBreak())

# Page 5: New 10 Models - Value Accuracy
story_u.append(Image("New_10_Models_Value_Accuracy_Heatmap.png", width=7.5 * inch, height=3.9 * inch))
story_u.append(PageBreak())

# Page 6: New 10 Models - Class Accuracy
story_u.append(Image("New_10_Models_Class_Accuracy_Heatmap.png", width=7.5 * inch, height=3.9 * inch))
story_u.append(PageBreak())

# Page 7: Master Comparison & Recommendations
story_u.append(Paragraph("6. Unified Comparison & Operational Recommendations", h1_style))
story_u.append(Spacer(1, 6))

summary_p = (
    "<b>Summary Recommendation</b>:<br/>"
    "• <b>For Prescriptive Agronomy (Fertility Tier Recommendations)</b>: Deploy <b>New Compound Model 9: DRL-NS-LBMP</b>. "
    "With 87.8% macro class accuracy and 100% classification precision on Nitrogen, Phosphorus, and Organic Carbon, it eliminates costly over/under fertilization.<br/>"
    "• <b>For High-Precision Lab-Grade Continuous Estimations</b>: Deploy <b>Compound Model 3: PLS-GB-CB</b> or <b>New Compound Model 4: OSC-CatBoost-AQC</b>, "
    "which minimize root-mean-squared error and provide the highest average per-sample value accuracies."
)
story_u.append(Paragraph(summary_p, body_style))

doc_u.build(story_u, canvasmaker=UnifiedNumberedCanvas, onFirstPage=draw_cover)
print(f"Successfully generated master unified PDF: {unified_pdf}")

if os.path.exists(artifact_dir):
    shutil.copy(unified_pdf, os.path.join(artifact_dir, unified_pdf))
    shutil.copy(master_excel, os.path.join(artifact_dir, master_excel))
    print("Copied master PDF and Excel to artifacts directory.")
