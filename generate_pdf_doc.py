"""
SoiLENZ Technical Documentation & Calculation Engine PDF Generator
Generates a complete, publication-quality PDF document detailing the working codebase.
"""

import sys
import os

def generate_pdf():
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
        )
        from reportlab.pdfgen import canvas
    except ImportError:
        print("ReportLab is not installed. Installing reportlab...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
        )
        from reportlab.pdfgen import canvas

    class NumberedCanvas(canvas.Canvas):
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
                self.draw_page_number(num_pages)
                super().showPage()
            super().save()

        def draw_page_number(self, page_count):
            self.saveState()
            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor("#555555"))
            
            # Header
            self.drawString(54, 800, "Arkashine SoiLENZ — Working Code & Algorithm Specification")
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(54, 792, 558, 792)
            
            # Footer
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(558, 36, page_text)
            self.drawString(54, 36, "CONFIDENTIAL & PROPRIETARY — ARKASHINE INNOVATIONS PVT LTD")
            self.line(54, 48, 558, 48)
            self.restoreState()

    pdf_filename = "SoiLENZ_Working_Code_Documentation.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1A2B4C"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=15
    )
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6
    )
    code_style = ParagraphStyle(
        'FormulaCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0D3880"),
        backColor=colors.HexColor("#EDF2F7"),
        borderPadding=5,
        spaceBefore=4,
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'BulletPoint',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    story = []

    # Title Block
    story.append(Paragraph("Arkashine SoiLENZ System", title_style))
    story.append(Paragraph("Working Codebase Technical & Algorithmic Architecture Document", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1A365D"), spaceAfter=14))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary & Hardware Topology", h1_style))
    story.append(Paragraph(
        "The Arkashine SoiLENZ embedded soil analyzer operates on a Raspberry Pi using a Pygame 800×400 graphical touch interface. "
        "The physical system integrates an ADS1115 16-bit analog-to-digital converter (ADC) for pH and Electrical Conductivity (EC), "
        "an 18-channel AS7265X tri-spectral sensor, a 3-channel AS7331 UV sensor, dual mixing motors, an automated pouring servo mechanism, "
        "and a 9600-baud thermal ESC/POS printer. This document details exclusively the operational components of the codebase, "
        "omitting legacy or inactive routines.", body_style
    ))

    hw_table_data = [
        [Paragraph("<b>Subsystem</b>", body_style), Paragraph("<b>Hardware / Interface</b>", body_style), Paragraph("<b>Function in Working Code</b>", body_style)],
        [Paragraph("pH ADC", body_style), Paragraph("ADS1115 (Ch 0, I2C)", body_style), Paragraph("10-sample stable median voltage measurement", body_style)],
        [Paragraph("EC ADC", body_style), Paragraph("ADS1115 (Ch 1, I2C)", body_style), Paragraph("20-sample trimmed mean voltage measurement", body_style)],
        [Paragraph("Spectral Sensor", body_style), Paragraph("AS7265X (I2C 0x49)", body_style), Paragraph("18-band optical spectrum (410nm to 940nm)", body_style)],
        [Paragraph("UV Sensor", body_style), Paragraph("AS7331 (I2C 0x74)", body_style), Paragraph("UVA (320nm), UVB (280nm), UVC (200nm)", body_style)],
        [Paragraph("Mixing Motors", body_style), Paragraph("GPIO 17 & GPIO 27", body_style), Paragraph("Motor 1 (water prep), Motor 2 (extractant reaction)", body_style)],
        [Paragraph("Decanting Servo", body_style), Paragraph("GPIO 12 (50Hz PWM)", body_style), Paragraph("Rotates 0° to 90° for liquid transfer", body_style)],
        [Paragraph("Thermal Printer", body_style), Paragraph("Serial /dev/ttyS0 (9600)", body_style), Paragraph("Native ESC/POS (English) & PIL bitmap (Regional)", body_style)]
    ]
    t_hw = Table(hw_table_data, colWidths=[110, 140, 254])
    t_hw.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_hw)
    story.append(Spacer(1, 10))

    # Screen by Screen
    story.append(Paragraph("2. Operational Screen-by-Screen Breakdown", h1_style))
    
    screens = [
        ("Screen 1: Splash & Brand Launch (`logo`)",
         "Initial power-on screen displaying company branding with a smooth 3000ms alpha fade-in. After 3 seconds, forward navigation arrow appears to proceed to QR verification, and a settings icon provides direct access to 100-test recalibration."),
        ("Screen 2: QR Authentication Screen (`qr_code`)",
         "Displays device registration QR code ('sudha_qr.png') verifying device authenticity. Forward button advances to software version check."),
        ("Screen 3: Software Update Check (`software_update_check`)",
         "Connects to the Arkashine API ('/versions/api/check-active-version/') to compare installed version against cloud release. 'YES' downloads zip, extracts updates, and launches recalibration if needed; 'NO' proceeds to test selection."),
        ("Screen 4: Test Type Selection (`test_selection`)",
         "Presents cards for 'Soil Test (14 Parameters)' and 'Water Test'. Choosing Soil Test routes to soil mode selection."),
        ("Screen 5: Soil Mode Selection (`test_calibration_std_2`)",
         "Allows switching between 'Calibration Test' (using buffer reference file 'calibration_edit.json') and 'Actual Soil Test' (using soil-adjusted matrix 'ph_soil_cal.json')."),
        ("Screen 6: Farmer & Crop Demographics (`page_user_details`)",
         "Collects farmer name via on-screen alpha virtual keyboard, mobile number via numeric virtual keyboard, language from 10 Indian regional languages, state (filtering crop choices), and target crop."),
        ("Screen 7: DI Water Preparation & Motor 1 (`page5`)",
         "Instructs user to place 5g soil + DI water into Tub 1. Activating ON runs Motor 1 on GPIO 17 for 60s. Upon completion, ADC channels 0 and 1 are sampled for pH and EC."),
        ("Screen 8: Initial Soil Sensor Readings (`page6`)",
         "Displays live pH (with Acidic/Neutral/Basic classification) and Electrical Conductivity (in dS/m) alongside raw probe voltages."),
        ("Screen 9: Chemical Extractant & Motor 2 (`page10`)",
         "Prompts addition of 40ml chemical extractant reagent. ON activates Motor 2 on GPIO 27 for a 60-second reaction period."),
        ("Screen 10: Automatic Decanting Servo (`page11`)",
         "Rotates servo motor on GPIO 12 smoothly from 0° to 90° to decant prepared supernatant into the spectral optical chamber, then begins a 190-second settling countdown."),
        ("Screen 11: Optical Spectral Sensor Acquisition (`page22`)",
         "Pressing 'SENSOR' runs soil_test(): illuminates multi-wavelength LED bulbs, averages 20 samples from 18 AS7265X channels and 3 AS7331 UV channels, and saves raw records to 'soil_sensor_log.csv'."),
        ("Screen 12: Soil Results Set 1 — Primary Nutrients (`page24`)",
         "Executes pre-trained Ridge regression models to predict Organic Carbon (OC %), Nitrogen (N kg/ha), Phosphorus (P2O5 kg/ha), Potassium (K kg/ha), and Calcium (Ca meq/100g) with Low/Medium/High/Deficient ratings."),
        ("Screen 13: Soil Results Set 2 — Secondary & Micronutrients (`page24_extra`)",
         "Displays Magnesium (Mg), Sulphur (S), Iron (Fe), Manganese (Mn), Copper (Cu), Zinc (Zn), and Boron (B) with corresponding chemical amendment advisories. Contains direct 'PRINT RECEIPT' button."),
        ("Screen 14: Comprehensive Summary & Recommendations (`page21`)",
         "3-column agronomic dashboard showing GPS coordinates, reverse-geocoded location, crop, pH, EC, NPK dosage, and corrective chemical recipes."),
        ("Screen 15: Print Language Selection (`language_selection`)",
         "Allows selecting receipt output language. Translates and compiles either native ESC/POS commands or dynamic PIL-generated bitmap images sent to the thermal printer.")
    ]

    for title, desc in screens:
        story.append(Paragraph(title, h2_style))
        story.append(Paragraph(desc, body_style))

    story.append(PageBreak())

    # Calculation Logics
    story.append(Paragraph("3. Mathematical & Algorithmic Logic", h1_style))
    
    # pH Engine
    story.append(Paragraph("A. Soil pH Calculation Engine", h2_style))
    story.append(Paragraph(
        "Soil pH is derived from ADS1115 Channel 0 using a 5-stage algorithm that accounts for noise filtering, "
        "soil suspension matrix shift, piecewise linear interpolation, asymptotic soft clamping, and chemical slurry correction.", body_style
    ))
    story.append(Paragraph("<b>1. Voltage Sampling & Noise Rejection (stable_voltage):</b><br/>"
                           "25 ADC readings are acquired at 20ms intervals. The median voltage M is determined. "
                           "Readings deviating by more than 0.05V from M are discarded. The top 2 and bottom 2 values are trimmed, "
                           "and the remaining values are averaged.", body_style))
    story.append(Paragraph("<b>2. Soil-Shifted Calibration Matrix (build_soil_ph_lookup):</b><br/>"
                           "Pure standard buffer calibration points are shifted to account for colloidal soil suspension effects. "
                           "The voltage corresponding to pH 8 is interpolated from Buffer 7 (V7) and Buffer 9 (V9):<br/>"
                           "<code>V8 = V7 + ((8.0 - 7.0) / 2.0) * (V9 - V7)</code><br/>"
                           "pH 4 is re-anchored to V8, and all lookup points between 4.00 and 9.00 are linearly interpolated in steps of 0.01.", code_style))
    story.append(Paragraph("<b>3. Piecewise Interpolation & Soft Clamping:</b><br/>"
                           "Between bounding calibration points (V1, pH1) and (V2, pH2):<br/>"
                           "<code>pH = pH1 + (V - V1) * (pH2 - pH1) / (V2 - V1)</code><br/>"
                           "Asymptotic exponential limits constrain values to physically meaningful soil boundaries [4.0, 7.5]:<br/>"
                           "<code>If pH &lt; 4.4: pH = 4.4 - (4.4 - 4.0) * (1 - exp(-(4.4 - pH)))</code><br/>"
                           "<code>If pH &gt; 7.75: pH = 7.75 + (7.5 - 7.75) * (1 - exp(-(pH - 7.75)))</code>", code_style))
    story.append(Paragraph("<b>4. Slurry Offset Correction (apply_correction):</b><br/>"
                           "<code>If pH &lt; 7.0 (Acidic): pH_final = pH + 1.5</code><br/>"
                           "<code>If pH &gt;= 7.0 (Alkaline): pH_final = pH - 3.0</code>", code_style))

    # EC Engine
    story.append(Paragraph("B. Electrical Conductivity (EC) Calculation Engine", h2_style))
    story.append(Paragraph(
        "ADS1115 Channel 1 samples the EC electrode. 20 samples are acquired with the two highest and lowest readings discarded. "
        "The resulting mean voltage is mapped to Electrical Conductivity in dS/m using a piecewise calibrated transfer function:", body_style
    ))
    ec_formula = (
        "Range 1 (0.0V to 0.9V)  -> Slope = (1.29 - 0.0) / (0.9 - 0.0) = 1.4333\n"
        "   EC = 0.0 + 1.4333 * (V - 0.0)\n\n"
        "Range 2 (1.0V to 1.9V)  -> Slope = (2.10 - 1.3) / (1.9 - 1.0) = 0.8889\n"
        "   EC = 1.3 + 0.8889 * (V - 1.0)\n\n"
        "Range 3 (2.0V to 2.9V)  -> Slope = (6.00 - 2.2) / (2.9 - 2.0) = 4.2222\n"
        "   EC = 2.2 + 4.2222 * (V - 2.0)\n\n"
        "Clamping: V < 0V -> 0 dS/m; 0.9V-1.0V -> 1.29 dS/m; 1.9V-2.0V -> 2.1 dS/m; > 2.9V -> 6.0 dS/m"
    )
    story.append(Paragraph(ec_formula.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    # ML Nutrient Engine
    story.append(Paragraph("C. Spectral ML Nutrient Inference Engine", h2_style))
    story.append(Paragraph(
        "Nutrient prediction utilizes 21 spectral features [A(410nm) through L(940nm) + UVA, UVB, UVC]. "
        "Each nutrient is evaluated via pre-trained model bundles ('models/*.pkl') containing a StandardScaler, "
        "a Classifier (predicting 'Low', 'Med', or 'High'), and a bank of class-specific Ridge regressors.", body_style
    ))
    ml_formula = (
        "1. Standard Scaling:  X_scaled = scaler.transform(X_21_features)\n"
        "2. Class Prediction:  pred_class = classifier.predict(X_scaled)[0]\n"
        "3. Ridge Regression:  pred_val = regressors[pred_class].predict(X_scaled)[0]\n"
        "4. Deterministic Soft Clamp (soft_clamp):\n"
        "   - Calcium: pred_val = pred_val / 2.0\n"
        "   - Low Class:   clamped to [lo + 0.20 * range, lo + 0.95 * range]\n"
        "   - Med Class:   clamped to [lo + 0.05 * range, hi - 0.05 * range]\n"
        "   - High Class:  proportional mapping for micronutrients (B, Fe, Mn)"
    )
    story.append(Paragraph(ml_formula.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Spacer(1, 10))

    # Fertilizer RDF
    story.append(Paragraph("D. Fertilizer Recommendation (RDF) & Chemical Split", h2_style))
    story.append(Paragraph(
        "The system adjusts recommended fertilizer doses based on tested fertility status and calculates commercial fertilizer quantities:", body_style
    ))

    fert_table = [
        [Paragraph("<b>Parameter</b>", body_style), Paragraph("<b>Low Threshold</b>", body_style), Paragraph("<b>Medium Threshold</b>", body_style), Paragraph("<b>High Threshold</b>", body_style), Paragraph("<b>RDF Multiplier</b>", body_style)],
        [Paragraph("Nitrogen (N)", body_style), Paragraph("&lt; 280 kg/ha", body_style), Paragraph("280 - 560 kg/ha", body_style), Paragraph("&gt; 560 kg/ha", body_style), Paragraph("Low: +25% | Med: 0% | High: -25%", body_style)],
        [Paragraph("Phosphorus (P2O5)", body_style), Paragraph("&lt; 22.9 kg/ha", body_style), Paragraph("22.9 - 56.3 kg/ha", body_style), Paragraph("&gt; 56.3 kg/ha", body_style), Paragraph("Low: +25% | Med: 0% | High: -25%", body_style)],
        [Paragraph("Potassium (K2O)", body_style), Paragraph("&lt; 141 kg/ha", body_style), Paragraph("141 - 336 kg/ha", body_style), Paragraph("&gt; 336 kg/ha", body_style), Paragraph("Low: +25% | Med: 0% | High: -25%", body_style)]
    ]
    t_fert = Table(fert_table, colWidths=[100, 90, 100, 90, 124])
    t_fert.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_fert)
    story.append(Spacer(1, 8))

    fert_calc_code = (
        "Commercial Fertilizer Calculations:\n"
        "1. MOP Requirement (60% K2O):\n"
        "   MOP (kg/ha) = (Adjusted_K / 60) * 100\n\n"
        "2. DAP Requirement (46% P2O5, 18% N):\n"
        "   DAP (kg/ha) = (Adjusted_P / 46) * 100\n"
        "   N_from_DAP  = DAP * 0.18\n\n"
        "3. Urea Requirement (46% N):\n"
        "   Urea (kg/ha) = ((Adjusted_N - N_from_DAP) / 46) * 100"
    )
    story.append(Paragraph(fert_calc_code.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Paragraph("<b>Micronutrient Amendment Recipes:</b>", body_style))
    story.append(Paragraph("• <b>Sulphur (S &lt; 30 ppm):</b> Add Elemental Sulphur 20 kg/ha.", bullet_style))
    story.append(Paragraph("• <b>Iron (Fe &lt; 8.5 ppm):</b> Add FeSO4 10 kg/ha (4 kg/acre).", bullet_style))
    story.append(Paragraph("• <b>Manganese (Mn &lt; 7.0 ppm):</b> Add MnSO4 10 kg/ha (4 kg/acre).", bullet_style))
    story.append(Paragraph("• <b>Copper (Cu &lt; 0.8 ppm):</b> Add CuSO4 10 kg/ha (4 kg/acre).", bullet_style))
    story.append(Paragraph("• <b>Zinc (Zn &lt; 1.2 ppm):</b> Add ZnSO4 10 kg/ha (4 kg/acre).", bullet_style))
    story.append(Paragraph("• <b>Boron (B &lt; 0.9 ppm):</b> Add Borax/Boron 5 kg/ha.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Generated PDF Documentation: {os.path.abspath(pdf_filename)}")

if __name__ == "__main__":
    generate_pdf()
