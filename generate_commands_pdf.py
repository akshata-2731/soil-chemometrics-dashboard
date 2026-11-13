"""
SoiLENZ Complete Technical Documentation with Dedicated Commands List
Generates a comprehensive PDF document containing full system specifications,
the complete BLE & UI command tables, and calculation engines.
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
            self.setFont("Helvetica", 8.5)
            self.setFillColor(colors.HexColor("#555555"))
            
            # Header
            self.drawString(40, 805, "Arkashine SoiLENZ — Complete Commands Specification & Algorithmic Engine")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(40, 797, 572, 797)
            
            # Footer
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(572, 30, page_text)
            self.drawString(40, 30, "CONFIDENTIAL & PROPRIETARY — ARKASHINE INNOVATIONS PVT LTD")
            self.line(40, 40, 572, 40)
            self.restoreState()

    pdf_filename = "SoiLENZ_Commands_and_Calculations_Guide.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1A2B4C"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=12
    )
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=4
    )
    table_text = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1A202C")
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#FFFFFF")
    )
    code_inline = ParagraphStyle(
        'CodeInline',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0D3880")
    )
    code_block = ParagraphStyle(
        'FormulaCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0D3880"),
        backColor=colors.HexColor("#EDF2F7"),
        borderPadding=5,
        spaceBefore=4,
        spaceAfter=6
    )

    story = []

    # Title Banner
    story.append(Paragraph("Arkashine SoiLENZ System Guide", title_style))
    story.append(Paragraph("Complete Technical Architecture, Dedicated Commands Reference Table & Calculation Engines", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceAfter=10))

    # Section 1: Overview
    story.append(Paragraph("1. System Architecture & Topology", h1_style))
    story.append(Paragraph(
        "The Arkashine SoiLENZ platform operates in two interchangeable configurations: "
        "<b>(1) An interactive touch appliance</b> running Pygame (800×400 resolution) with on-screen virtual keyboards, "
        "and <b>(2) A headless Bluetooth Low Energy (BLE) GATT server</b> (device name: <code>ArkaShine-Soil</code>) "
        "exposing a full bidirectional JSON control protocol. Both modes interface with identical sensory hardware: "
        "an ADS1115 16-bit ADC (Ch 0: pH probe, Ch 1: EC probe), an 18-channel AS7265X tri-spectral sensor (410nm to 940nm), "
        "an AS7331 UV sensor (UVA, UVB, UVC), dual mixing motors (GPIO 17 & 27), an automatic pouring servo (GPIO 12 PWM), "
        "and a thermal ESC/POS slip printer on <code>/dev/serial0</code> (9600 baud).", body_style
    ))

    # Section 2: Complete BLE Command Table
    story.append(Paragraph("2. Dedicated BLE GATT Protocol Commands List", h1_style))
    story.append(Paragraph(
        "All commands are transmitted as UTF-8 encoded JSON strings via GATT Service UUID "
        "<code>12345678-1234-1234-1234-1234567890ab</code> and Characteristic UUID <code>abcd1234-5678-1234-5678-1234567890ab</code>. "
        "Below is the complete reference table of all active commands:", body_style
    ))

    ble_cmd_data = [
        [Paragraph("Category", table_header), 
         Paragraph("JSON Request (Client &rarr; Device)", table_header), 
         Paragraph("JSON Response / Notification", table_header), 
         Paragraph("Parameters & Action Triggered", table_header)],
        
        [Paragraph("<b>Handshake</b>", table_text),
         Paragraph("<code>{\"HANDSHAKE\": \"HELLO\"}</code>", code_inline),
         Paragraph("<code>{\"HANDSHAKE\": \"ACK\"}</code>", code_inline),
         Paragraph("Verifies active Bluetooth connection.", table_text)],

        [Paragraph("<b>Version</b>", table_text),
         Paragraph("<code>{\"CHECKVERSION\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"CHECKVERSION\": \"OK\", \"current\": \"1.1.x\"}</code>", code_inline),
         Paragraph("Reads software version from version_info.json.", table_text)],

        [Paragraph("<b>System Info</b>", table_text),
         Paragraph("<code>{\"GETSYSTEMINFO\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"GETSYSTEMINFO\": \"OK\", \"version\": ..., \"device_id\": ..., \"serial_no\": ..., \"update_state\": {...}}</code>", code_inline),
         Paragraph("Returns device config, serial number, and active state snapshot.", table_text)],

        [Paragraph("<b>Motor Start</b>", table_text),
         Paragraph("<code>{\"SOILTEST\": \"START\"}</code>", code_inline),
         Paragraph("<code>{\"SOILTEST\": \"STARTED\"}</code><br/>&darr;<br/><code>{\"SOILTEST\": \"MIXING_COMPLETED\"}</code>", code_inline),
         Paragraph("Pulses GPIO 17 & 27 HIGH for 200ms, sets LOW, and signals completion.", table_text)],

        [Paragraph("<b>Motor Stop</b>", table_text),
         Paragraph("<code>{\"SOILTEST\": \"STOP\"}</code>", code_inline),
         Paragraph("<code>{\"SOILTEST\": \"STOPPED\"}</code>", code_inline),
         Paragraph("Forces GPIO 17 & 27 LOW immediately; aborts mixing thread.", table_text)],

        [Paragraph("<b>Motor Status</b>", table_text),
         Paragraph("<code>{\"CHECKSOILMOTORSTATUS\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"SOILMOTORSTATUS\": \"RUNNING\"}</code> or <code>\"STOPPED\"</code>", code_inline),
         Paragraph("Queries current motor state machine variable.", table_text)],

        [Paragraph("<b>Sensor Read</b>", table_text),
         Paragraph("<code>{\"SOILSENSOR\": \"READ\"}</code>", code_inline),
         Paragraph("<code>{\"SOILSENSORSTATUS\": \"READING\"}</code><br/>&darr;<br/><code>{\"SOILSENSORSTATUS\": \"SENSOR_READING_DONE\"}</code>", code_inline),
         Paragraph("Runs 20-sample optical test (AS7265X + AS7331), executes Ridge ML inference, syncs to Cloud API /api/add_data/.", table_text)],

        [Paragraph("<b>Sensor Status</b>", table_text),
         Paragraph("<code>{\"CHECKSOILSENSORSTATUS\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"SOILSENSORSTATUS\": \"READING\"}</code> or <code>\"STOPPED\"</code>", code_inline),
         Paragraph("Queries optical sensor acquisition status.", table_text)],

        [Paragraph("<b>Get Results</b>", table_text),
         Paragraph("<code>{\"SOILRESULT\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"FINALSOILRESULT\": {\"OC\": ..., \"N\": ..., \"P\": ..., \"K\": ..., \"Ca\": ..., \"Mg\": ..., \"S\": ..., \"Fe\": ..., \"Mn\": ..., \"Cu\": ..., \"Zn\": ..., \"B\": ..., \"ph\": ..., \"ec\": ...}}</code>", code_inline),
         Paragraph("Returns 12 nutrient levels + pH + EC cached in latest_result.", table_text)],

        [Paragraph("<b>Print Slip</b>", table_text),
         Paragraph("<code>{\"SOILPRINT\": \"START\", \"farmer_name\": \"...\", \"farmer_phone\": \"...\", \"ph\": 6.8, \"ec\": 1.2, \"latitude\": ..., \"longitude\": ...}</code>", code_inline),
         Paragraph("<code>{\"SOILPRINT\": \"DONE\"}</code><br/>or<br/><code>{\"SOILPRINT\": \"ERROR\", \"message\": \"...\"}</code>", code_inline),
         Paragraph("Updates farmer info, prints slip via ESC/POS on /dev/serial0 with Low/Med/High ratings, and cuts paper.", table_text)],

        [Paragraph("<b>Single Calibrate</b>", table_text),
         Paragraph("<code>{\"SOILCALIBRATE\": \"START\", \"nutrient\": \"N\", \"point\": \"mid\"}</code>", code_inline),
         Paragraph("<code>{\"SOILCALIBRATION\": \"CAPTURING\"}</code><br/>&darr;<br/><code>{\"SOILCALIBRATION\": \"COMPLETED\"}</code>", code_inline),
         Paragraph("Captures 30 optical samples for the nutrient; saves vector to soil_calibration.json.", table_text)],

        [Paragraph("<b>Cancel Calibrate</b>", table_text),
         Paragraph("<code>{\"SOILCALIBRATE\": \"CANCEL\"}</code>", code_inline),
         Paragraph("<code>{\"SOILCALIBRATION\": \"CANCEL_REQUESTED\"}</code>", code_inline),
         Paragraph("Sets cancel flag, turns off sensor LEDs, and aborts loop.", table_text)],

        [Paragraph("<b>List Calibrate</b>", table_text),
         Paragraph("<code>{\"SOILCALIBRATE\": \"LIST\"}</code>", code_inline),
         Paragraph("<code>{\"SOILCALIBRATIONDATA\": \"OK\", \"saved_points\": {...}}</code>", code_inline),
         Paragraph("Returns list of saved calibration points for each nutrient.", table_text)],

        [Paragraph("<b>Batch Calibrate</b>", table_text),
         Paragraph("<code>{\"SOILCALIBRATION\": \"START\", \"nutrients\": [\"N\",\"P\",\"K\"], \"point\": \"min\"}</code>", code_inline),
         Paragraph("<code>{\"SOILCALIBRATION\": \"STARTED\"}</code><br/>&darr;<br/><code>{\"SOILCALIBRATION\": \"COMPLETED\"}</code>", code_inline),
         Paragraph("Batch calibration across multiple nutrients. Streams live progress and spectrum every 5 loops.", table_text)],

        [Paragraph("<b>Stop Batch</b>", table_text),
         Paragraph("<code>{\"SOILCALIBRATION\": \"STOP\"}</code>", code_inline),
         Paragraph("<code>{\"SOILCALIBRATION\": \"STOPPED\"}</code>", code_inline),
         Paragraph("Terminates batch calibration thread.", table_text)],

        [Paragraph("<b>Cal Data Get</b>", table_text),
         Paragraph("<code>{\"SOILCALIBRATIONDATA\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"SOILCALIBRATIONDATA\": \"OK\", \"summary\": {...}, \"file\": \"soil_calibration.json\"}</code>", code_inline),
         Paragraph("Returns complete database structure snapshot.", table_text)],

        [Paragraph("<b>Cal Status</b>", table_text),
         Paragraph("<code>{\"SOILCALIBRATIONSTATUS\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"SOILCALIBRATION\": \"CAPTURING\", \"sample\": n, \"total\": 30, \"percent\": ...}</code>", code_inline),
         Paragraph("Returns live sample index and progress percentage.", table_text)],

        [Paragraph("<b>OTA Check</b>", table_text),
         Paragraph("<code>{\"VERSIONUPDATE\": \"START\"}</code><br/>(Stage 1: Check)", code_inline),
         Paragraph("<code>{\"CHECKUPDATE\": \"AVAILABLE\", \"latest\": \"...\"}</code> or <code>{\"CHECKUPDATE\": \"UP_TO_DATE\"}</code>", code_inline),
         Paragraph("Queries Arkashine API to determine if update exists.", table_text)],

        [Paragraph("<b>OTA Install</b>", table_text),
         Paragraph("<code>{\"VERSIONUPDATE\": \"START\"}</code><br/>(Stage 2: Install)", code_inline),
         Paragraph("<code>{\"VERSIONUPDATE\": \"STARTED\"}</code>", code_inline),
         Paragraph("Downloads update.zip, unzips, skips user data, and restarts app.", table_text)],

        [Paragraph("<b>OTA Status</b>", table_text),
         Paragraph("<code>{\"VERSIONUPDATE\": \"STATUS\"}</code>", code_inline),
         Paragraph("<code>{\"VERSIONUPDATE\": \"STATUS\", \"stage\": \"Downloading\", \"percent\": ..., \"bytes_downloaded\": ...}</code>", code_inline),
         Paragraph("Streams download and installation progress.", table_text)],

        [Paragraph("<b>OTA Cancel</b>", table_text),
         Paragraph("<code>{\"UPDATE\": \"CANCEL\"}</code> or <code>{\"VERSIONUPDATE\": \"FORSESTOP\"}</code>", code_inline),
         Paragraph("<code>{\"UPDATE\": \"CANCEL_REQUESTED\"}</code> / <code>{\"VERSIONUPDATE\": \"CANCELLED\"}</code>", code_inline),
         Paragraph("Cancels download, removes partial files, resets state.", table_text)]
    ]

    t_cmds = Table(ble_cmd_data, colWidths=[68, 140, 150, 174])
    t_cmds.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F7FAFC")]),
    ]))
    story.append(t_cmds)
    story.append(PageBreak())

    # Section 3: UI Workflow Reference
    story.append(Paragraph("3. Interactive UI Workflow Reference (Touch Appliance)", h1_style))
    story.append(Paragraph(
        "For appliance operation via the 800×400 LCD touch display, navigation follows a fixed screen-by-screen sequence:", body_style
    ))

    ui_data = [
        [Paragraph("Screen", table_header), Paragraph("State Name", table_header), Paragraph("Drawing Function", table_header), Paragraph("Operational Actions & Logic", table_header)],
        [Paragraph("1", table_text), Paragraph("logo", code_inline), Paragraph("draw_logo()", code_inline), Paragraph("3s alpha fade-in. Forward &rarr; QR code; Settings &rarr; Recalibration.", table_text)],
        [Paragraph("2", table_text), Paragraph("qr_code", code_inline), Paragraph("draw_qr_code()", code_inline), Paragraph("Displays registration QR code image (sudha_qr.png).", table_text)],
        [Paragraph("3", table_text), Paragraph("software_update_check", code_inline), Paragraph("draw_software_update_page()", code_inline), Paragraph("Cloud API check. YES &rarr; Download & install; NO &rarr; Test selection.", table_text)],
        [Paragraph("4", table_text), Paragraph("test_selection", code_inline), Paragraph("draw_test_selection_page()", code_inline), Paragraph("Selects Soil Test (Screen 5) or Water Test (pH & TDS).", table_text)],
        [Paragraph("5", table_text), Paragraph("test_calibration_std_2", code_inline), Paragraph("draw_test_calibration_std_2()", code_inline), Paragraph("Selects Calibration Mode (JSON-1) or Actual Soil Mode (JSON-2).", table_text)],
        [Paragraph("6", table_text), Paragraph("page_user_details", code_inline), Paragraph("draw_page_user_details()", code_inline), Paragraph("Farmer Name (virtual QWERTY), Phone (numeric), Language, State, Crop.", table_text)],
        [Paragraph("7", table_text), Paragraph("page5", code_inline), Paragraph("draw_page5()", code_inline), Paragraph("Soil + DI water prep; Motor 1 (GPIO 17) runs 60s; samples pH & EC ADC.", table_text)],
        [Paragraph("8", table_text), Paragraph("page6", code_inline), Paragraph("draw_page6()", code_inline), Paragraph("Displays pH (Acidic/Neutral/Basic) and EC (dS/m) with raw voltages.", table_text)],
        [Paragraph("9", table_text), Paragraph("page10", code_inline), Paragraph("draw_page10()", code_inline), Paragraph("40ml extractant addition; Motor 2 (GPIO 27) runs 60s reaction.", table_text)],
        [Paragraph("10", table_text), Paragraph("page11", code_inline), Paragraph("draw_page11()", code_inline), Paragraph("Pouring Servo (GPIO 12 PWM 0&deg; to 90&deg;); 190s settling countdown.", table_text)],
        [Paragraph("11", table_text), Paragraph("page22", code_inline), Paragraph("draw_page22()", code_inline), Paragraph("SENSOR button triggers 20-sample optical test (AS7265X + AS7331).", table_text)],
        [Paragraph("12", table_text), Paragraph("page24", code_inline), Paragraph("draw_page24()", code_inline), Paragraph("Primary Results: OC (%), N, P2O5, K2O (kg/ha), Ca (meq/100g).", table_text)],
        [Paragraph("13", table_text), Paragraph("page24_extra", code_inline), Paragraph("draw_page24_extra()", code_inline), Paragraph("Secondary Results: Mg, S, Fe, Mn, Cu, Zn, B + direct Print button.", table_text)],
        [Paragraph("14", table_text), Paragraph("page21", code_inline), Paragraph("draw_page21()", code_inline), Paragraph("3-column summary: GPS location, crop, pH, EC, NPK, chemical recipes.", table_text)],
        [Paragraph("15", table_text), Paragraph("language_selection", code_inline), Paragraph("draw_language_selection_page()", code_inline), Paragraph("Selects print language; sends ESC/POS ASCII or PIL bitmap image to printer.", table_text)]
    ]
    t_ui = Table(ui_data, colWidths=[40, 110, 130, 252])
    t_ui.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F7FAFC")]),
    ]))
    story.append(t_ui)
    story.append(Spacer(1, 10))

    # Section 4: Calculation Logic
    story.append(Paragraph("4. Core Calculation Engines & Formulas", h1_style))

    # pH Calculation
    story.append(Paragraph("A. Soil pH Calculation Engine", h2_style))
    ph_code = (
        "1. ADC Noise Filtering (stable_voltage):\n"
        "   - Acquire 25 samples on ADS1115 Ch0 (20ms delays)\n"
        "   - Rejection: keep values where |v - median| < 0.05V\n"
        "   - Outlier Trim: remove 2 lowest and 2 highest; average middle 21\n\n"
        "2. Soil-Shifted Calibration Matrix (build_soil_ph_lookup):\n"
        "   V8 = V7 + ((8.0 - 7.0) / (9.0 - 7.0)) * (V9 - V7)\n"
        "   Soil V4 is set to V8; table generated from 4.00 to 9.00 in 0.01 steps\n\n"
        "3. Piecewise Interpolation:\n"
        "   pH = pH1 + (V - V1) * (pH2 - pH1) / (V2 - V1)\n\n"
        "4. Asymptotic Exponential Soft Clamping:\n"
        "   If pH < 4.4:  pH_clamped = 4.4 - (4.4 - 4.0) * (1 - exp(-(4.4 - pH)))\n"
        "   If pH > 7.75: pH_clamped = 7.75 + (7.5 - 7.75) * (1 - exp(-(pH - 7.75)))\n\n"
        "5. Slurry Correction Offset (apply_correction):\n"
        "   If pH < 7.0 (Acidic): pH_final = pH + 1.5\n"
        "   If pH >= 7.0 (Alkaline): pH_final = pH - 3.0"
    )
    story.append(Paragraph(ph_code.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_block))

    # EC Calculation
    story.append(Paragraph("B. Electrical Conductivity (EC) Calculation Engine", h2_style))
    ec_code = (
        "1. Sampling: 20 samples on ADS1115 Ch1; drop top/bottom 2; average middle 16\n\n"
        "2. Piecewise Linear Transfer Function:\n"
        "   Range 1 (0.0V - 0.9V):  EC = 0.0 + 1.4333 * V           (Slope = 1.29 / 0.9)\n"
        "   Range 2 (1.0V - 1.9V):  EC = 1.3 + 0.8889 * (V - 1.0)   (Slope = 0.8 / 0.9)\n"
        "   Range 3 (2.0V - 2.9V):  EC = 2.2 + 4.2222 * (V - 2.0)   (Slope = 3.8 / 0.9)\n\n"
        "   Clamping: V < 0V -> 0 dS/m | 0.9V-1.0V -> 1.29 dS/m | 1.9V-2.0V -> 2.1 dS/m | > 2.9V -> 6.0 dS/m"
    )
    story.append(Paragraph(ec_code.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_block))

    story.append(PageBreak())

    # ML Nutrient Prediction
    story.append(Paragraph("C. Spectral ML Nutrient Inference Engine", h2_style))
    ml_code = (
        "Input: 21 Optical Features [A410..W860 (18 channels) + UVA, UVB, UVC]\n\n"
        "1. Forced Range Constraints (FORCE_RANGE):\n"
        "   Phosphorus (P): [2.0, 22.0] kg/ha    | Iron (Fe):     [4.5, 10.0] ppm\n"
        "   Calcium (Ca):    [5.0, 10.0] meq/100g | Nitrogen (N):  [125.0, 500.0] kg/ha\n\n"
        "2. Ridge Inference Pipeline (for other nutrients):\n"
        "   X_scaled = scaler.transform(X)\n"
        "   pred_class = classifier.predict(X_scaled)[0]\n"
        "   pred_val = random.uniform(lo + 0.05*range, hi - 0.05*range) within model class rules\n\n"
        "3. Tanh Soft Clamping (soft_clamp):\n"
        "   For Calcium: val = val / 2.0\n"
        "   z = (val - lo) / (hi - lo)\n"
        "   t = tanh(z / 3.0)\n"
        "   frac = 0.20 + 0.60 * ((t + 1) / 2)  [Low]\n"
        "   frac = 0.10 + 0.80 * ((t + 1) / 2)  [Med]\n"
        "   frac = 0.15 + 0.75 * ((t + 1) / 2)  [High]\n"
        "   Output = lo + max(0.05, min(0.95, frac)) * (hi - lo)"
    )
    story.append(Paragraph(ml_code.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_block))

    # Fertilizer RDF
    story.append(Paragraph("D. Fertilizer Recommendation (RDF) Formulas", h2_style))
    fert_code = (
        "1. Baseline Multipliers:\n"
        "   - Low Rating  (N < 280, P < 22.9, K < 141):   Adjusted = RDF * 1.25 (+25%)\n"
        "   - Medium      (280-560, 22.9-56.3, 141-336): Adjusted = RDF * 1.00 (Normal)\n"
        "   - High Rating (N > 560, P > 56.3, K > 336):   Adjusted = RDF * 0.75 (-25%)\n\n"
        "2. Commercial Chemical Conversions:\n"
        "   MOP (kg/ha)  = (Adjusted_K / 60) * 100\n"
        "   DAP (kg/ha)  = (Adjusted_P / 46) * 100\n"
        "   N_from_DAP   = DAP * 0.18\n"
        "   Urea (kg/ha) = ((Adjusted_N - N_from_DAP) / 46) * 100\n\n"
        "3. Micronutrient Amendment Recipes:\n"
        "   - Sulphur (S < 30 ppm):      Add Elemental Sulphur 20 kg/ha\n"
        "   - Iron (Fe < 8.5 ppm):       Add FeSO4 10 kg/ha (4 kg/acre)\n"
        "   - Manganese (Mn < 7.0 ppm):  Add MnSO4 10 kg/ha (4 kg/acre)\n"
        "   - Copper (Cu < 0.8 ppm):     Add CuSO4 10 kg/ha (4 kg/acre)\n"
        "   - Zinc (Zn < 1.2 ppm):       Add ZnSO4 10 kg/ha (4 kg/acre)\n"
        "   - Boron (B < 0.9 ppm):       Add Borax 5 kg/ha"
    )
    story.append(Paragraph(fert_code.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_block))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Generated Complete Commands Guide PDF: {os.path.abspath(pdf_filename)}")

if __name__ == "__main__":
    generate_pdf()
