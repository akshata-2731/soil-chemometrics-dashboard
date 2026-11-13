"""
SoiLENZ BLE Firmware Daemon Technical Documentation & Algorithm PDF Generator
Generates a complete, publication-quality PDF document detailing the BLE peripheral codebase.
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
            self.drawString(54, 800, "Arkashine SoiLENZ — BLE Firmware Daemon Specification")
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(54, 792, 558, 792)
            
            # Footer
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(558, 36, page_text)
            self.drawString(54, 36, "CONFIDENTIAL & PROPRIETARY — ARKASHINE INNOVATIONS PVT LTD")
            self.line(54, 48, 558, 48)
            self.restoreState()

    pdf_filename = "SoiLENZ_BLE_Firmware_Documentation.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

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
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=5
    )
    code_style = ParagraphStyle(
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
    bullet_style = ParagraphStyle(
        'BulletPoint',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    story = []

    # Title Header
    story.append(Paragraph("Arkashine SoiLENZ BLE Firmware", title_style))
    story.append(Paragraph("Headless Daemon Architecture, BLE JSON Protocol & Algorithmic Engine", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1A365D"), spaceAfter=14))

    # Section 1: Overview
    story.append(Paragraph("1. System Architecture & Headless Peripheral Topology", h1_style))
    story.append(Paragraph(
        "This software component serves as a headless background daemon running an asynchronous GATT server "
        "named <b>ArkaShine-Soil</b> via the <code>bless</code> library. It facilitates bidirectional control from mobile applications "
        "(iOS/Android) over a unified JSON-over-BLE protocol. The daemon controls physical dual mixing motors (GPIO 17 & 27), "
        "drives an 18-channel AS7265X spectral sensor and AS7331 UV sensor, performs multi-point soil calibration, "
        "runs machine learning nutrient inference, formats thermal slips via an ESC/POS printer on <code>/dev/serial0</code>, "
        "and handles background Over-The-Air (OTA) updates.", body_style
    ))

    ble_table = [
        [Paragraph("<b>Parameter</b>", body_style), Paragraph("<b>Specification</b>", body_style), Paragraph("<b>Function / Capabilities</b>", body_style)],
        [Paragraph("Device Name", body_style), Paragraph("ArkaShine-Soil", body_style), Paragraph("Advertised BLE peripheral name", body_style)],
        [Paragraph("Service UUID", body_style), Paragraph("12345678-1234-1234-1234-1234567890ab", body_style), Paragraph("Primary GATT Service UUID", body_style)],
        [Paragraph("Characteristic UUID", body_style), Paragraph("abcd1234-5678-1234-5678-1234567890ab", body_style), Paragraph("Read, Write, WriteWithoutResponse, Notify", body_style)],
        [Paragraph("Thermal Printer", body_style), Paragraph("Serial /dev/serial0 (9600 baud)", body_style), Paragraph("Hardware ESC/POS thermal printing with paper cut", body_style)],
        [Paragraph("Actuator Drivers", body_style), Paragraph("GPIO 17 (M1) & GPIO 27 (M2)", body_style), Paragraph("200ms pulsed mixing motor activation", body_style)],
        [Paragraph("Spectral Sensor", body_style), Paragraph("AS7265X I2C 0x49 + AS7331 I2C 0x74", body_style), Paragraph("21 total optical channels (410nm to 940nm + 3 UV)", body_style)]
    ]
    t_ble = Table(ble_table, colWidths=[110, 170, 224])
    t_ble.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_ble)
    story.append(Spacer(1, 10))

    # Section 2: Command Reference
    story.append(Paragraph("2. Complete BLE JSON Command Specification", h1_style))

    commands = [
        ("A. Handshake & System Telemetry",
         "• <code>{'HANDSHAKE': 'HELLO'}</code> &rarr; <code>{'HANDSHAKE': 'ACK'}</code>: Confirms BLE link.<br/>"
         "• <code>{'CHECKVERSION': 'GET'}</code> &rarr; <code>{'CHECKVERSION': 'OK', 'current': '...'}</code>: Queries software version.<br/>"
         "• <code>{'GETSYSTEMINFO': 'GET'}</code> &rarr; <code>{'GETSYSTEMINFO': 'OK', 'version': '...', 'device_id': '...', 'serial_no': '...', 'update_state': {...}}</code>: Full hardware snapshot."),
        ("B. Mixing Motor Control (`SOILTEST`)",
         "• <code>{'SOILTEST': 'START'}</code>: Spawns worker thread, drives GPIO 17 & 27 HIGH for 200ms, then LOW. Sends <code>{'SOILTEST': 'MIXING_COMPLETED'}</code>.<br/>"
         "• <code>{'SOILTEST': 'STOP'}</code>: Forces motors LOW immediately, notifies <code>{'SOILTEST': 'STOPPED'}</code>.<br/>"
         "• <code>{'CHECKSOILMOTORSTATUS': 'GET'}</code>: Returns current motor status (<code>RUNNING</code> or <code>STOPPED</code>)."),
        ("C. Soil Spectral Sensor & Inference (`SOILSENSOR`)",
         "• <code>{'SOILSENSOR': 'READ'}</code>: Starts 20-sample optical test (AS7265X + AS7331), logs features to CSV, executes ML models, caches farmer pH/EC, uploads payload to cloud API, and notifies <code>{'SOILSENSORSTATUS': 'SENSOR_READING_DONE'}</code>.<br/>"
         "• <code>{'SOILRESULT': 'GET'}</code>: Returns latest prediction map: <code>{'FINALSOILRESULT': {'OC': ..., 'N': ..., 'P': ..., 'K': ..., 'Ca': ..., 'Mg': ..., 'S': ..., 'Fe': ..., 'Mn': ..., 'Cu': ..., 'Zn': ..., 'B': ..., 'ph': ..., 'ec': ...}}</code>.<br/>"
         "• <code>{'CHECKSOILSENSORSTATUS': 'GET'}</code>: Returns sensor acquisition state."),
        ("D. Thermal Receipt Printing (`SOILPRINT`)",
         "• <code>{'SOILPRINT': 'START', 'farmer_name': '...', 'farmer_phone': '...', 'ph': 6.8, 'ec': 1.2, 'latitude': ..., 'longitude': ...}</code>: "
         "Updates thread-safe farmer registry, formats receipt slip on <code>/dev/serial0</code> with standard ranges, Low/Med/High ratings for all 12 nutrients, and issues cut command."),
        ("E. Optical Multi-Nutrient Calibration (`SOILCALIBRATE` & `SOILCALIBRATION`)",
         "• <code>{'SOILCALIBRATE': 'START', 'nutrient': 'N', 'point': 'mid'}</code>: Calibrates single nutrient level.<br/>"
         "• <code>{'SOILCALIBRATION': 'START', 'nutrients': ['N', 'P', 'K'], 'point': 'min'}</code>: Calibrates batch of nutrients across standard points (<code>blank</code>, <code>min</code>, <code>mid</code>, <code>max</code>). Runs 30 loops, streams live progress and channel spectrum over BLE every 5 loops, and writes to <code>soil_calibration.json</code>.<br/>"
         "• <code>{'SOILCALIBRATE': 'LIST'}</code> / <code>{'SOILCALIBRATIONDATA': 'GET'}</code>: Returns database summary.<br/>"
         "• <code>{'SOILCALIBRATE': 'CANCEL'}</code> / <code>{'SOILCALIBRATION': 'STOP'}</code>: Aborts calibration safely."),
        ("F. Over-The-Air (OTA) Updates (`VERSIONUPDATE`)",
         "• <code>{'VERSIONUPDATE': 'START'}</code>: Checks server API. If update available, reports <code>{'CHECKUPDATE': 'AVAILABLE'}</code>; on second invocation, initiates background streaming download, zip extraction, and file installation.<br/>"
         "• <code>{'VERSIONUPDATE': 'STATUS'}</code>: Returns live download percentage, bytes transferred, and stage.<br/>"
         "• <code>{'UPDATE': 'CANCEL'}</code> / <code>{'VERSIONUPDATE': 'FORSESTOP'}</code>: Cancels update process safely.")
    ]

    for title, desc in commands:
        story.append(Paragraph(title, h2_style))
        story.append(Paragraph(desc, body_style))

    story.append(PageBreak())

    # Section 3: Sensor Driver Logic
    story.append(Paragraph("3. Optical Sensor Register Drivers & Multi-Loop Acquisition", h1_style))
    story.append(Paragraph(
        "The spectral acquisition system uses low-level I2C commands across two multi-channel sensor chips:", body_style
    ))
    story.append(Paragraph("<b>1. AS7265X Tri-Spectral Sensor (I2C 0x49):</b><br/>"
                           "• Configures sub-devices 0x00, 0x01, 0x02 with integration time 0x3F (176.4ms) and gain 16x.<br/>"
                           "• Measurement sequence: LEDs enabled via V_REG_LED_CONTROL (0x07) | 0x09; 100ms settling; One-shot Mode 3 triggered; "
                           "polls control register until data-ready bit flags; reads 6 IEEE-754 32-bit floats per chip (18 total).<br/>"
                           "• Channels: A(410nm), B(435nm), C(460nm), D(485nm), E(510nm), F(535nm), G(560nm), H(585nm), "
                           "I(645nm), J(705nm), K(900nm), L(940nm), R(610nm), S(680nm), T(730nm), U(760nm), V(810nm), W(860nm).", body_style))
    story.append(Paragraph("<b>2. AS7331 UV Sensor (I2C 0x74):</b><br/>"
                           "• Gain: 512X; Integration Time: 128ms.<br/>"
                           "• Reads UVA, UVB, UVC with irradiance scaling:<br/>"
                           "<code>UVA_irr = UVA * 0.166 | UVB_irr = UVB * 0.185 | UVC_irr = UVC * 0.388 (&mu;W/cm&sup2;)</code>", code_style))

    # Section 4: Machine Learning Engine
    story.append(Paragraph("4. Machine Learning Nutrient Prediction & Soft Clamping Engine", h1_style))
    story.append(Paragraph(
        "Inference transforms the 21-channel optical vector using pre-trained Ridge regression bundles loaded from "
        "<code>/home/soil/models/*.pkl</code>.", body_style
    ))
    
    ml_desc = (
        "1. Forced Agronomic Range Rules (FORCE_RANGE):\n"
        "   - Phosphorus (P):  Constrained to [2.0, 22.0] kg/ha\n"
        "   - Iron (Fe):        Constrained to [4.5, 10.0] ppm\n"
        "   - Calcium (Ca):     Constrained to [5.0, 10.0] meq/100g\n"
        "   - Nitrogen (N):     Constrained to [125.0, 500.0] kg/ha\n\n"
        "2. Ridge Regression Inference Pipeline:\n"
        "   - X_scaled = scaler.transform(X_21_channels)\n"
        "   - pred_class = classifier.predict(X_scaled)[0]\n"
        "   - pred_val   = random.uniform(lo + 0.05*range, hi - 0.05*range) within model class bounds\n\n"
        "3. Hyperbolic Tangent Soft Clamping (soft_clamp):\n"
        "   - For Calcium:  val = val / 2.0\n"
        "   - z = (val - lo) / (hi - lo)\n"
        "   - t = tanh(z / 3.0)\n"
        "   - If Low:  frac = 0.20 + 0.60 * ((t + 1) / 2)\n"
        "   - If Med:  frac = 0.10 + 0.80 * ((t + 1) / 2)\n"
        "   - If High: frac = 0.15 + 0.75 * ((t + 1) / 2)\n"
        "   - frac = max(0.05, min(0.95, frac))\n"
        "   - Final Value = lo + frac * (hi - lo)"
    )
    story.append(Paragraph(ml_desc.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    # Section 5: Standards Table
    story.append(Paragraph("5. Agronomic Thresholds & Thermal Slip Specifications", h1_style))
    
    standards_table = [
        [Paragraph("<b>Nutrient</b>", body_style), Paragraph("<b>Low</b>", body_style), Paragraph("<b>Medium</b>", body_style), Paragraph("<b>High</b>", body_style), Paragraph("<b>Slip Label</b>", body_style), Paragraph("<b>Range</b>", body_style)],
        [Paragraph("OC (%)", body_style), Paragraph("&lt; 0.50", body_style), Paragraph("0.50 - 0.75", body_style), Paragraph("&gt; 0.75", body_style), Paragraph("OC(0.5-0.75%):", body_style), Paragraph("0-1.0 %", body_style)],
        [Paragraph("N (kg/ha)", body_style), Paragraph("&lt; 280", body_style), Paragraph("280 - 560", body_style), Paragraph("&gt; 560", body_style), Paragraph("N(280-560kg/ha):", body_style), Paragraph("125-800 kg/ha", body_style)],
        [Paragraph("P (kg/ha)", body_style), Paragraph("&lt; 22.9", body_style), Paragraph("22.9 - 56.3", body_style), Paragraph("&gt; 56.3", body_style), Paragraph("P(22.9-56.3kg/ha):", body_style), Paragraph("1-200 kg/ha", body_style)],
        [Paragraph("K (kg/ha)", body_style), Paragraph("&lt; 144", body_style), Paragraph("144 - 336", body_style), Paragraph("&gt; 336", body_style), Paragraph("K(144-336kg/ha):", body_style), Paragraph("20-1000 kg/ha", body_style)],
        [Paragraph("Ca (meq)", body_style), Paragraph("&lt; 1.5", body_style), Paragraph("1.5 - 5.0", body_style), Paragraph("&gt; 5.0", body_style), Paragraph("Ca(1.5-5.0meq):", body_style), Paragraph("1-100 meq", body_style)],
        [Paragraph("Mg (meq)", body_style), Paragraph("&lt; 1.0", body_style), Paragraph("1.0 - 3.0", body_style), Paragraph("&gt; 3.0", body_style), Paragraph("Mg(1.0-3.0meq):", body_style), Paragraph("1-50 meq", body_style)],
        [Paragraph("S (ppm)", body_style), Paragraph("&lt; 10", body_style), Paragraph("10 - 20", body_style), Paragraph("&gt; 20", body_style), Paragraph("S(10-20ppm):", body_style), Paragraph("2-250 ppm", body_style)],
        [Paragraph("Fe (ppm)", body_style), Paragraph("&lt; 4.5", body_style), Paragraph("4.5 - 10.0", body_style), Paragraph("&gt; 10.0", body_style), Paragraph("Fe(4.5-10ppm):", body_style), Paragraph("1-50 ppm", body_style)],
        [Paragraph("Mn (ppm)", body_style), Paragraph("&lt; 2.0", body_style), Paragraph("2.0 - 4.0", body_style), Paragraph("&gt; 4.0", body_style), Paragraph("Mn(2.0-4.0ppm):", body_style), Paragraph("1-25 ppm", body_style)],
        [Paragraph("Cu (ppm)", body_style), Paragraph("&lt; 0.2", body_style), Paragraph("0.2 - 0.4", body_style), Paragraph("&gt; 0.4", body_style), Paragraph("Cu(0.2-0.4ppm):", body_style), Paragraph("0.1-10 ppm", body_style)],
        [Paragraph("Zn (ppm)", body_style), Paragraph("&lt; 0.6", body_style), Paragraph("0.6 - 1.2", body_style), Paragraph("&gt; 1.2", body_style), Paragraph("Zn(0.6-1.2ppm):", body_style), Paragraph("0.2-10 ppm", body_style)],
        [Paragraph("B (ppm)", body_style), Paragraph("&lt; 0.5", body_style), Paragraph("0.5 - 1.0", body_style), Paragraph("&gt; 1.0", body_style), Paragraph("B(0.5-1ppm):", body_style), Paragraph("0.1-10 ppm", body_style)],
        [Paragraph("pH", body_style), Paragraph("&lt; 6.5", body_style), Paragraph("6.5 - 7.3", body_style), Paragraph("&gt; 7.3", body_style), Paragraph("pH (6.5-7.3) :", body_style), Paragraph("0-14", body_style)],
        [Paragraph("EC (dS/m)", body_style), Paragraph("&lt; 0.8", body_style), Paragraph("0.8 - 1.6", body_style), Paragraph("&gt; 1.6", body_style), Paragraph("EC (0.8-1.6 dS/m):", body_style), Paragraph("0-10 dS/m", body_style)]
    ]
    t_std = Table(standards_table, colWidths=[70, 60, 75, 60, 120, 119])
    t_std.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_std)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Generated BLE PDF Documentation: {os.path.abspath(pdf_filename)}")

if __name__ == "__main__":
    generate_pdf()
