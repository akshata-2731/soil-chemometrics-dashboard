# Soil Chemometrics & Multi-Model Intelligence Dashboard
## Non-Technical User Guide & Testing Manual

---

## 📌 1. Overview: What This Dashboard Does

The **Soil Chemometrics Dashboard** is a scientific software platform that analyzes soil health **without slow, destructive wet-chemistry laboratory procedures**. 

By taking optical sensor readings across **21 light wavelength bands (UV, Visible, Near-Infrared)**, the software instantly predicts the concentrations of **12 key soil macro- and micronutrients** using an array of **76 Machine Learning models** and **51 mathematical calibration formulas**.

### Core Capabilities:
* **Instant Multi-Nutrient Assessment:** Evaluates Organic Carbon (`OC`), Nitrogen (`N`), Phosphorus (`P`), Potassium (`K`), Calcium (`Ca`), Magnesium (`Mg`), Sulfur (`S`), Iron (`Fe`), Manganese (`Mn`), Copper (`Cu`), Zinc (`Zn`), and Boron (`B`).
* **Multi-Model Tournament:** Runs multiple algorithms in parallel and ranks them from **highest accuracy to lowest accuracy** for each specific nutrient.
* **Accuracy Verification:** Compares the model's predictions directly against laboratory reference standards and applies a **75% accuracy pass threshold**.
* **Visual Diagnostics:** Displays interactive Actual vs. Predicted scatter graphs with ideal 1:1 reference lines.
* **Excel Reports:** Generates downloadable Excel workbooks with embedded charts.

---

## 📁 2. Input Data Preparation: What the File Must Look Like

To test your samples on the dashboard, upload an **Excel file (`.xlsx`)**. 

Each **row represents one soil sample**, and the **columns contain your sensor readings and lab references**.

```
[ Sample ID ] ──► [ 21 Spectral Columns (nm_...) ] ──► [ Laboratory Reference Columns (OC, N, P, K...) ]
```

### A. The 21 Optical Sensor Columns (Required)
Every sample must have readings for the 21 physical optical filters:
* **Violet & Visible:** `nm_410`, `nm_435`, `nm_460`, `nm_485`, `nm_510`, `nm_535`, `nm_560`, `nm_585`, `nm_610`, `nm_645`, `nm_680`
* **Near-Infrared (NIR):** `nm_705`, `nm_730`, `nm_760`, `nm_810`, `nm_860`, `nm_900`, `nm_940`
* **Ultraviolet (UV):** `nm_320`, `nm_280`, `nm_200`

### B. The 12 Nutrient Reference Columns (For Accuracy Evaluation)
To calculate accuracy, the system reads reference values from standard laboratory headers:

| Nutrient | Accepted Column Headers in Excel | Measurement Unit |
| :--- | :--- | :--- |
| **Organic Carbon** | `OC`, `OC%`, `OC (%)`, `Organic Carbon` | Percentage (`%`) |
| **Nitrogen** | `N`, `N Kg/ha`, `N (kg/ha)`, `Nitrogen` | `Kg/ha` |
| **Phosphorus** | `P`, `P2O5`, `P₂O₅`, `Phosphate`, `P (ppm)` | `ppm` or Oxide form |
| **Potassium** | `K`, `K2O`, `K₂O`, `Potash`, `K (kg/ha)` | `Kg/ha` or Oxide form |
| **Calcium** | `Ca`, `Ca (meq)`, `Ca (meq/100g)` | `meq/100g` |
| **Magnesium** | `Mg`, `Mg (meq)`, `Mg (meq/100g)` | `meq/100g` |
| **Sulfur** | `S`, `SO4`, `SO₄`, `Sulfate`, `S (ppm)` | `ppm` |
| **Iron** | `Fe`, `Fe (ppm)`, `Iron` | `ppm` |
| **Manganese** | `Mn`, `Mn (ppm)`, `Manganese` | `ppm` |
| **Copper** | `Cu`, `Cu (ppm)`, `Copper` | `ppm` |
| **Zinc** | `Zn`, `Zn (ppm)`, `Zinc` | `ppm` |
| **Boron** | `B`, `B (ppm)`, `Boron` | `ppm` |

> If a sample is missing values for a few nutrients, the platform automatically evaluates only the nutrients present in your sheet.

---

## 🧭 3. Navigation & Dashboard Screens

At the top of the interface, the navigation bar allows you to switch between different operating modes:

1. **🔬 Multi-Model Run (Test All):** The primary benchmarking screen. Evaluates and ranks algorithms side-by-side, generates Actual vs. Predicted curves, and exports summary reports.
2. **📦 Batch (Multi-Sample):** For production lab technicians. Upload an entire batch of field samples to get a single consolidated soil health card.
3. **🎯 Single Nutrient:** Focused deep-dive on one specific element (e.g., analyzing only Potassium or Zinc).
4. **🌿 All 12 Nutrients:** High-throughput screen predicting all 12 elements simultaneously for quick sample screening.
5. **⚙️ Calibration & Zero-Set:** Standardizes optical sensors using reference white tiles and dark-current baselines to ensure zero sensor drift.
6. **📜 History & Audit Logs:** A tamper-evident database log of all previous testing sessions and sample runs.

---

## 🧪 4. Step-by-Step Testing Walkthrough

Follow these simple steps on the **Multi-Model Run** screen:

### Step 1: Choose Execution Mode & Origin
* **Dataset Origin:**
  * Select **"🆕 New Test Data (Unseen)"** when uploading fresh field samples to evaluate generalization.
  * Select **"🔄 Same Trained Data"** when testing the calibration fit.
* **Algorithm Selection:**
  * **⚡ Run All ML Algorithms Once:** Runs all 76 models (best on local high-performance machines).
  * **📐 Run All Mathematical Logics Once:** Runs the 51 deterministic formula calibrations.
  * **🎯 Select Specific Models / Logics (Recommended for Fast Cloud Testing):** Pick 4–10 top models (e.g. `B01_PLSR`, `B07_3D_SVR`, `B09_BayesianRidge`, `B28_BoundaryBuffer`) for rapid 15-second execution.

### Step 2: Set the Accuracy Pass Threshold
* Adjust the slider (default: **75%**).
* Any sample where the error is under 25% is marked **`PASS`**; if the error exceeds 25%, it is marked **`FAIL`**.

### Step 3: Choose Target Nutrients
* Click **"★ All Nutrients"** to evaluate all 12 elements simultaneously.
* Alternatively, click individual nutrient buttons (e.g., `OC`, `P`, `K`) to focus on specific targets.

### Step 4: Upload & Execute
* Click **Choose File** and select your `.xlsx` spreadsheet.
* Click **🚀 Execute Models / Logics**.

---

## 📊 5. How to Read and Interpret the Results

Once computation finishes, the results are presented in four coordinated sections:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. NUTRIENT SELECTOR TABS  [OC] [N] [P] [K] [Ca] [Mg] ...   │
├─────────────────────────────────────────────────────────────┤
│ 2. CHAMPION MODEL SPOTLIGHT (👑 #1 Model for active nutrient)│
├─────────────────────────────────────────────────────────────┤
│ 3. ACTUAL VS PREDICTED INTERACTIVE GRAPH (Scatter / Line)   │
├─────────────────────────────────────────────────────────────┤
│ 4. RANKED LEADERBOARD TABLE (Highest Accuracy ──► Lowest)   │
└─────────────────────────────────────────────────────────────┘
```

### 1. Nutrient Quick-Switch Tabs
* Click any nutrient pill (**`OC`**, **`N`**, **`P`**, **`K`**, etc.) to immediately isolate and inspect that nutrient.
* Each button displays the champion model's top accuracy (e.g. `Top: 91.4%`).

### 2. Champion Spotlight Banner (👑 #1 Model)
* Highlights the best-performing algorithm for the selected nutrient, detailing its **Average Accuracy %**, **Pass Rate %**, and **Mean Absolute Error (MAE)**.

### 3. Actual vs. Predicted Graphs
* **Scatter Plot:** Each dot represents one soil sample. The closer the dots lie to the dashed diagonal line (1:1 Ideal line), the closer the prediction is to laboratory perfection.
* **Line with Points:** Displays the laboratory reference line (Green) side-by-side with the algorithm's prediction line (Blue) across all samples.

### 4. Model Accuracy Leaderboard Table
All evaluated models are sorted from **Highest Accuracy to Lowest Accuracy**:
* **Rank (🥇 #1, 🥈 #2, 🥉 #3...):** Performance hierarchy.
* **Accuracy Progress Bar:**
  * 🟢 **Green (≥ 85%):** Excellent accuracy.
  * 🔵 **Blue (75% – 84%):** Optimal / Passed standard threshold.
  * 🟡 **Amber (60% – 74%):** Moderate accuracy.
  * 🔴 **Red (< 60%):** Sub-optimal.
* **Pass Rate %:** Percentage of samples meeting the $\ge 75\%$ accuracy requirement.
* **MAE (Mean Absolute Error):** Average unit deviation from laboratory wet chemistry.
* **Inspect Action:** Click **"Inspect"** on any model to instantly load its specific curve into the graph.

---

## 📥 6. Exporting Excel Reports

Click the green button **"📥 Download Excel Report with Scatter Graphs"** in the top right header:

The exported Excel file includes:
1. **`Best Models Per Nutrient` Sheet:** Summary of the #1 champion model for each element.
2. **`Summary Leaderboard` Sheet:** Pre-sorted rankings of all model-nutrient combinations.
3. **`All Predictions` Sheet:** Raw sample-by-sample predictions, actuals, error margins, and individual Pass/Fail statuses.
4. **`Graph sheets`:** Dedicated sheets per nutrient with auto-generated native Excel scatter charts.
