"""
SoiLENZ BLE Firmware Daemon - Standalone Technical Documentation & Commands Guide PDF Generator
Exclusively covers the BLE GATT peripheral codebase (ArkaShine-Soil).
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
            self.drawString(40, 805, "Arkashine SoiLENZ — BLE Firmware Daemon Specification & Commands List")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(40, 797, 572, 797)
            
            # Footer
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(572, 30, page_text)
            self.drawString(40, 30, "CONFIDENTIAL & PROPRIETARY — ARKASHINE INNOVATIONS PVT LTD")
            self.line(40, 40, 572, 40)
            self.restoreState()

    pdf_filename = "SoiLENZ_BLE_Daemon_Technical_Specification.pdf"
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
        fontSize=13.5,
        leading=17,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
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
    story.append(Paragraph("Arkashine SoiLENZ BLE Firmware Daemon", title_style))
    story.append(Paragraph("Headless GATT Peripheral Architecture, Complete Command Protocol & Inference Engine", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceAfter=10))

    # Section 1: System Topology
    story.append(Paragraph("1. System Architecture & Peripheral Topology", h1_style))
    story.append(Paragraph(
        "This software component is a headless embedded firmware daemon for the Raspberry Pi. "
        "It deploys an asynchronous Bluetooth Low Energy (BLE) GATT peripheral named <b>ArkaShine-Soil</b> using the <code>bless</code> library. "
        "The daemon provides full wireless mobile control over physical actuators, multi-channel spectral acquisition, "
        "machine learning inference, multi-point calibration, thermal receipt printing, and over-the-air firmware updates.", body_style
    ))

    hw_table = [
        [Paragraph("<b>Component</b>", table_header), Paragraph("<b>Port / Interface</b>", table_header), Paragraph("<b>Operational Behavior & Configuration</b>", table_header)],
        [Paragraph("GATT Service", table_text), Paragraph("UUID: 12345678-1234-1234-1234-1234567890ab", code_inline), Paragraph("Primary BLE Service advertised as ArkaShine-Soil", table_text)],
        [Paragraph("GATT Characteristic", table_text), Paragraph("UUID: abcd1234-5678-1234-5678-1234567890ab", code_inline), Paragraph("Read, Write, WriteWithoutResponse, Notify", table_text)],
        [Paragraph("Dual Mixing Motors", table_text), Paragraph("GPIO 17 (M1) & GPIO 27 (M2)", table_text), Paragraph("Pulsed for 200ms (MOTORSPEED) via _run_mixing_workflow", table_text)],
        [Paragraph("Spectral Sensor", table_text), Paragraph("AS7265X (I2C Bus 1, 0x49)", table_text), Paragraph("18-band optical channels (410nm to 940nm); virtual register driver", table_text)],
        [Paragraph("UV Sensor", table_text), Paragraph("AS7331 (I2C Bus 1, 0x74)", table_text), Paragraph("Gain 512X, 128ms time; UVA, UVB, UVC with irradiance scaling", table_text)],
        [Paragraph("Thermal Slip Printer", table_text), Paragraph("Serial /dev/serial0 (9600 baud)", table_text), Paragraph("Hardware ESC/POS printer with paper cut via escpos.printer.Serial", table_text)]
    ]
    t_hw = Table(hw_table, colWidths=[100, 160, 272])
    t_hw.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F7FAFC")]),
    ]))
    story.append(t_hw)
    story.append(Spacer(1, 10))

    # Section 2: Complete BLE Commands List
    story.append(Paragraph("2. Complete BLE Commands Reference Table", h1_style))
    story.append(Paragraph(
        "All commands are submitted as JSON strings to Characteristic <code>abcd1234-5678-1234-5678-1234567890ab</code>. "
        "The daemon dispatches them asynchronously and responds via notifications (<code>_ble_notify</code>):", body_style
    ))

    cmd_rows = [
        [Paragraph("Category", table_header), Paragraph("JSON Request (Client &rarr; Device)", table_header), Paragraph("JSON Response / Notification", table_header), Paragraph("Parameters & Internal Actions", table_header)],
        
        [Paragraph("<b>Handshake</b>", table_text),
         Paragraph("<code>{\"HANDSHAKE\": \"HELLO\"}</code>", code_inline),
         Paragraph("<code>{\"HANDSHAKE\": \"ACK\"}</code>", code_inline),
         Paragraph("Verifies active BLE link responsiveness.", table_text)],

        [Paragraph("<b>Version</b>", table_text),
         Paragraph("<code>{\"CHECKVERSION\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"CHECKVERSION\": \"OK\", \"current\": \"1.1.x\"}</code>", code_inline),
         Paragraph("Reads software version from version_info.json.", table_text)],

        [Paragraph("<b>System Info</b>", table_text),
         Paragraph("<code>{\"GETSYSTEMINFO\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"GETSYSTEMINFO\": \"OK\", \"version\": ..., \"device_id\": ..., \"serial_no\": ..., \"update_state\": {...}}</code>", code_inline),
         Paragraph("Returns device config, serial number, and firmware state.", table_text)],

        [Paragraph("<b>Motor Start</b>", table_text),
         Paragraph("<code>{\"SOILTEST\": \"START\"}</code>", code_inline),
         Paragraph("<code>{\"SOILTEST\": \"STARTED\"}</code><br/>&darr;<br/><code>{\"SOILTEST\": \"MIXING_COMPLETED\"}</code>", code_inline),
         Paragraph("Pulses GPIO 17 & 27 HIGH for 200ms, sets LOW, and signals completion.", table_text)],

        [Paragraph("<b>Motor Stop</b>", table_text),
         Paragraph("<code>{\"SOILTEST\": \"STOP\"}</code>", code_inline),
         Paragraph("<code>{\"SOILTEST\": \"STOPPED\"}</code>", code_inline),
         Paragraph("Immediately forces GPIO 17 & 27 LOW; aborts mixing thread.", table_text)],

        [Paragraph("<b>Motor Status</b>", table_text),
         Paragraph("<code>{\"CHECKSOILMOTORSTATUS\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"SOILMOTORSTATUS\": \"RUNNING\"}</code> or <code>\"STOPPED\"</code>", code_inline),
         Paragraph("Returns current value of ble_motor_status.", table_text)],

        [Paragraph("<b>Sensor Read</b>", table_text),
         Paragraph("<code>{\"SOILSENSOR\": \"READ\"}</code>", code_inline),
         Paragraph("<code>{\"SOILSENSORSTATUS\": \"READING\"}</code><br/>&darr;<br/><code>{\"SOILSENSORSTATUS\": \"SENSOR_READING_DONE\"}</code>", code_inline),
         Paragraph("Runs 20-sample optical test (AS7265X + AS7331), executes Ridge ML inference, syncs to Cloud API /api/add_data/.", table_text)],

        [Paragraph("<b>Sensor Status</b>", table_text),
         Paragraph("<code>{\"CHECKSOILSENSORSTATUS\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"SOILSENSORSTATUS\": \"READING\"}</code> or <code>\"STOPPED\"</code>", code_inline),
         Paragraph("Returns current value of ble_sensor_status.", table_text)],

        [Paragraph("<b>Get Results</b>", table_text),
         Paragraph("<code>{\"SOILRESULT\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"FINALSOILRESULT\": {\"OC\": ..., \"N\": ..., \"P\": ..., \"K\": ..., \"Ca\": ..., \"Mg\": ..., \"S\": ..., \"Fe\": ..., \"Mn\": ..., \"Cu\": ..., \"Zn\": ..., \"B\": ..., \"ph\": ..., \"ec\": ...}}</code>", code_inline),
         Paragraph("Returns 12 nutrient levels + pH + EC cached in latest_result.", table_text)],

        [Paragraph("<b>Thermal Print</b>", table_text),
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
         Paragraph("Returns dictionary of configured calibration points per nutrient.", table_text)],

        [Paragraph("<b>Batch Calibrate</b>", table_text),
         Paragraph("<code>{\"SOILCALIBRATION\": \"START\", \"nutrients\": [\"N\",\"P\",\"K\"], \"point\": \"min\"}</code>", code_inline),
         Paragraph("<code>{\"SOILCALIBRATION\": \"STARTED\"}</code><br/>&darr;<br/><code>{\"SOILCALIBRATION\": \"COMPLETED\"}</code>", code_inline),
         Paragraph("Batch calibration across multiple nutrients. Streams live progress and spectrum every 5 loops.", table_text)],

        [Paragraph("<b>Stop Batch</b>", table_text),
         Paragraph("<code>{\"SOILCALIBRATION\": \"STOP\"}</code>", code_inline),
         Paragraph("<code>{\"SOILCALIBRATION\": \"STOPPED\"}</code>", code_inline),
         Paragraph("Aborts batch calibration thread.", table_text)],

        [Paragraph("<b>Cal Data Get</b>", table_text),
         Paragraph("<code>{\"SOILCALIBRATIONDATA\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"SOILCALIBRATIONDATA\": \"OK\", \"summary\": {...}, \"file\": \"soil_calibration.json\"}</code>", code_inline),
         Paragraph("Returns complete database structure snapshot.", table_text)],

        [Paragraph("<b>Cal Status</b>", table_text),
         Paragraph("<code>{\"SOILCALIBRATIONSTATUS\": \"GET\"}</code>", code_inline),
         Paragraph("<code>{\"SOILCALIBRATION\": \"CAPTURING\", \"sample\": n, \"total\": 30, \"percent\": ...}</code>", code_inline),
         Paragraph("Returns live sample progress for the active calibration point.", table_text)],

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

    t_cmds = Table(cmd_rows, colWidths=[68, 140, 150, 174])
    t_cmds.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F7FAFC")]),
    ]))
    story.append(t_cmds)
    story.append(PageBreak())

    # Section 3: Sensor Driver Logic
    story.append(Paragraph("3. Optical Sensor Drivers & Multi-Channel Acquisition", h1_style))
    story.append(Paragraph(
        "Sensor acquisition runs 20 loops (normal testing) or 30 loops (calibration) with onboard LED illumination:", body_style
    ))
    story.append(Paragraph("<b>1. AS7265X Tri-Spectral Sensor (I2C 0x49):</b><br/>"
                           "• Virtual Register Handshake: Polls status register (0x00) Bit 1 for write buffer readiness; "
                           "sets high bit on register byte (v_reg | 0x80); polls Bit 0 for read availability.<br/>"
                           "• Integration time set to 0x3F (176.4ms), gain set to 16x (0x02).<br/>"
                           "• Measurement sequence: LEDs enabled via V_REG_LED_CONTROL (0x07) | 0x09; 100ms settling; One-shot Mode 3 triggered; "
                           "polls control register until ready flag; reads 6 big-endian IEEE-754 floats per chip (18 total across 410nm to 940nm).", body_style))
    story.append(Paragraph("<b>2. AS7331 UV Sensor (I2C 0x74):</b><br/>"
                           "• Gain: 512X, Integration Time: 128ms.<br/>"
                           "• Reads UVA, UVB, UVC with irradiance scaling:<br/>"
                           "<code>UVA_irr = UVA * 0.166 | UVB_irr = UVB * 0.185 | UVC_irr = UVC * 0.388 (&mu;W/cm&sup2;)</code>", code_block))

    # Section 4: Machine Learning Inference
    story.append(Paragraph("4. Machine Learning Inference & Clamping Engine", h1_style))
    ml_text = (
        "Input: 21 Optical Features [A410..W860 (18 channels) + UVA, UVB, UVC]\n\n"
        "1. Forced Range Constraints (FORCE_RANGE):\n"
        "   Phosphorus (P): [2.0, 22.0] kg/ha    | Iron (Fe):     [4.5, 10.0] ppm\n"
        "   Calcium (Ca):    [5.0, 10.0] meq/100g | Nitrogen (N):  [125.0, 500.0] kg/ha\n\n"
        "2. Ridge Inference Pipeline (Remaining Nutrients):\n"
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
    story.append(Paragraph(ml_text.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_block))

    # Section 5: Standards & Receipt Format
    story.append(Paragraph("5. Agronomic Thresholds & Thermal Slip Specifications", h1_style))
    
    standards_table = [
        [Paragraph("<b>Nutrient</b>", table_header), Paragraph("<b>Low</b>", table_header), Paragraph("<b>Medium</b>", table_header), Paragraph("<b>High</b>", table_header), Paragraph("<b>Slip Label</b>", table_header), Paragraph("<b>Reference Range</b>", table_header)],
        [Paragraph("OC (%)", table_text), Paragraph("&lt; 0.50", table_text), Paragraph("0.50 - 0.75", table_text), Paragraph("&gt; 0.75", table_text), Paragraph("OC(0.5-0.75%):", table_text), Paragraph("0-1.0 %", table_text)],
        [Paragraph("N (kg/ha)", table_text), Paragraph("&lt; 280", table_text), Paragraph("280 - 560", table_text), Paragraph("&gt; 560", table_text), Paragraph("N(280-560kg/ha):", table_text), Paragraph("125-800 kg/ha", table_text)],
        [Paragraph("P (kg/ha)", table_text), Paragraph("&lt; 22.9", table_text), Paragraph("22.9 - 56.3", table_text), Paragraph("&gt; 56.3", table_text), Paragraph("P(22.9-56.3kg/ha):", table_text), Paragraph("1-200 kg/ha", table_text)],
        [Paragraph("K (kg/ha)", table_text), Paragraph("&lt; 144", table_text), Paragraph("144 - 336", table_text), Paragraph("&gt; 336", table_text), Paragraph("K(144-336kg/ha):", table_text), Paragraph("20-1000 kg/ha", table_text)],
        [Paragraph("Ca (meq)", table_text), Paragraph("&lt; 1.5", table_text), Paragraph("1.5 - 5.0", table_text), Paragraph("&gt; 5.0", table_text), Paragraph("Ca(1.5-5.0meq):", table_text), Paragraph("1-100 meq", table_text)],
        [Paragraph("Mg (meq)", table_text), Paragraph("&lt; 1.0", table_text), Paragraph("1.0 - 3.0", table_text), Paragraph("&gt; 3.0", table_text), Paragraph("Mg(1.0-3.0meq):", table_text), Paragraph("1-50 meq", table_text)],
        [Paragraph("S (ppm)", table_text), Paragraph("&lt; 10", table_text), Paragraph("10 - 20", table_text), Paragraph("&gt; 20", table_text), Paragraph("S(10-20ppm):", table_text), Paragraph("2-250 ppm", table_text)],
        [Paragraph("Fe (ppm)", table_text), Paragraph("&lt; 4.5", table_text), Paragraph("4.5 - 10.0", table_text), Paragraph("&gt; 10.0", table_text), Paragraph("Fe(4.5-10ppm):", table_text), Paragraph("1-50 ppm", table_text)],
        [Paragraph("Mn (ppm)", table_text), Paragraph("&lt; 2.0", table_text), Paragraph("2.0 - 4.0", table_text), Paragraph("&gt; 4.0", table_text), Paragraph("Mn(2.0-4.0ppm):", table_text), Paragraph("1-25 ppm", table_text)],
        [Paragraph("Cu (ppm)", table_text), Paragraph("&lt; 0.2", table_text), Paragraph("0.2 - 0.4", table_text), Paragraph("&gt; 0.4", table_text), Paragraph("Cu(0.2-0.4ppm):", table_text), Paragraph("0.1-10 ppm", table_text)],
        [Paragraph("Zn (ppm)", table_text), Paragraph("&lt; 0.6", table_text), Paragraph("0.6 - 1.2", table_text), Paragraph("&gt; 1.2", table_text), Paragraph("Zn(0.6-1.2ppm):", table_text), Paragraph("0.2-10 ppm", table_text)],
        [Paragraph("B (ppm)", table_text), Paragraph("&lt; 0.5", table_text), Paragraph("0.5 - 1.0", table_text), Paragraph("&gt; 1.0", table_text), Paragraph("B(0.5-1ppm):", table_text), Paragraph("0.1-10 ppm", table_text)],
        [Paragraph("pH", table_text), Paragraph("&lt; 6.5", table_text), Paragraph("6.5 - 7.3", table_text), Paragraph("&gt; 7.3", table_text), Paragraph("pH (6.5-7.3) :", table_text), Paragraph("0-14", table_text)],
        [Paragraph("EC (dS/m)", table_text), Paragraph("&lt; 0.8", table_text), Paragraph("0.8 - 1.6", table_text), Paragraph("&gt; 1.6", table_text), Paragraph("EC (0.8-1.6 dS/m):", table_text), Paragraph("0-10 dS/m", table_text)]
    ]
    t_std = Table(standards_table, colWidths=[70, 60, 75, 60, 120, 119])
    t_std.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F7FAFC")]),
    ]))
    story.append(t_std)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Thermal Receipt Print Layout (`_print_soil_result`):</b>", body_style))
    receipt_sample = (
        "=================================\n"
        "      ARKASHINE INNOVATIONS\n"
        "             Pvt Ltd\n"
        "             SoiLENZ\n"
        "---------------------------------\n"
        "   24-10-2026   10:30AM\n"
        "---------------------------------\n"
        "   Farmer Name: Ramesh Kumar\n"
        "   Mobile: 9876543210\n"
        "   Lat: 12.9716, Lon: 77.5946\n"
        "---------------------------------\n"
        "   OC(0.5-0.75%): 0.6 - MED\n"
        "   N(280-560kg/ha): 340.0 - MED\n"
        "   P(22.9-56.3kg/ha): 18.5 - LOW\n"
        "   K(144-336kg/ha): 210.0 - MED\n"
        "   Ca(1.5-5.0meq): 6.2 - HIGH\n"
        "   Mg(1.0-3.0meq): 2.1 - MED\n"
        "   S(10-20ppm): 14.2 - MED\n"
        "   Fe(4.5-10ppm): 7.8 - MED\n"
        "   Mn(2.0-4.0ppm): 3.1 - MED\n"
        "   Cu(0.2-0.4ppm): 0.3 - MED\n"
        "   Zn(0.6-1.2ppm): 0.9 - MED\n"
        "   B(0.5-1ppm): 0.7 - MED\n"
        "---------------------------------\n"
        "   pH (6.5-7.3) : 6.85\n"
        "   EC (0.8-1.6 dS/m): 1.2500\n"
        "---------------------------------\n"
        "   Total amount paid: \n\n"
        "   This is for your information\n"
        "     Toll free PH : 9611297893\n"
        "=================================\n"
        "[PAPER CUT]"
    )
    story.append(Paragraph(receipt_sample.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_block))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Generated Standalone BLE PDF Documentation: {os.path.abspath(pdf_filename)}")

if __name__ == "__main__":
    generate_pdf()
