# Soil Chemometrics & Spectroscopic Multi-Model Intelligence Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite-61dafb.svg)](https://react.dev/)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7.svg)](https://soil-chemometrics-dashboard.onrender.com)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

A high-throughput, non-destructive soil nutrient quantification platform that couples **21-channel diffuse reflectance spectroscopy (UV-Vis-NIR: 200 nm – 940 nm)** with an ensemble of **76 Machine Learning pipelines** and **51 deterministic mathematical calibration logics**.

---

## 🌟 Key Features

- **76 Pre-Trained Chemometric & ML Architectures:** Benchmarks PLSR, Support Vector Regression (SVR), ExtraTrees, Random Forest, Kernel Ridge, LightGBM, and Hybrid Multi-Stage Stacking pipelines across 12 target nutrients.
- **Two-Stage Classifier-Regressor Engine:** Classifies soil samples into concentration tiers (Deficient, Optimal, High) before dispatching to specialized regressors with physics-based soft-clamping.
- **Multi-Nutrient Coverage (12 Targets):**
  - **Macro-Nutrients:** Organic Carbon (`OC`), Nitrogen (`N`), Phosphorus (`P` / $P_2O_5$), Potassium (`K` / $K_2O$).
  - **Secondary & Micro-Nutrients:** Calcium (`Ca`), Magnesium (`Mg`), Sulfur (`S`), Iron (`Fe`), Manganese (`Mn`), Copper (`Cu`), Zinc (`Zn`), Boron (`B`), plus optional `pH` and `EC`.
- **Ranked Multi-Model Leaderboard:** Automatically arranges algorithms from highest to lowest accuracy per nutrient, flagging 75% pass rates, Average Accuracy %, and Mean Absolute Error (MAE).
- **Interactive Actual vs. Predicted Visualizations:** Real-time scatter plots with ideal 1:1 reference diagonals and sequential line comparison curves.
- **Automated Excel Reporting:** Exports publication-ready workbooks containing summary leaderboards, champion models, raw sample predictions, and embedded scatter charts.

---

## 🔬 Sensor Hardware & Optical Specification

The platform ingests raw spectral readings from 21 discrete optical bandpass filters:

| Spectral Region | Wavelength Channels (nm) |
| :--- | :--- |
| **Visible & Violet** | `nm_410`, `nm_435`, `nm_460`, `nm_485`, `nm_510`, `nm_535`, `nm_560`, `nm_585`, `nm_610`, `nm_645`, `nm_680` |
| **Near-Infrared (NIR)** | `nm_705`, `nm_730`, `nm_760`, `nm_810`, `nm_860`, `nm_900`, `nm_940` |
| **Ultraviolet (UV)** | `nm_320`, `nm_280`, `nm_200` |

---

## 📂 Project Architecture

```
soil-chemometrics-dashboard/
├── app.py                     # Flask REST API, prediction engine & SPA router
├── requirements.txt           # Production Python dependencies
├── history.db                 # SQLite local audit log of runs & predictions
├── models/                    # 76 ML model architectures and pre-trained weights (.pkl, .joblib)
├── logics/                    # 51 mathematical calibration definitions and JS implementations
│   ├── definitions/           # JSON schema files for calibration formulas
│   └── implementations/       # Mathematical logic scripts
├── calibration/               # Zero-standardization & reference calibration data
├── data/                      # Reference soil sample datasets (data.xlsx)
├── frontend/                  # React + Vite application source
│   ├── dist/                  # Production-built static assets (served by Flask)
│   ├── src/                   # React components, pages, and chart modules
│   │   ├── pages/             # MultiModelScreen, ModeBatch, ModeSingle, ModeAll12, etc.
│   │   └── components/        # Recharts interactive graphs, footers, themes
│   └── package.json           # Frontend dependencies
└── test_reports/              # Generated Excel validation reports & scatter workbooks
```

---

## 🚀 Getting Started Locally

### Prerequisites
- **Python:** 3.10 or higher
- **Node.js:** v18 or higher (optional, for editing the React frontend)
- **Git**

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/akshata-2731/soil-chemometrics-dashboard.git
   cd soil-chemometrics-dashboard
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```
   Open your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000).

---

## 🛠️ Building the Frontend (Optional)

If you modify files inside `frontend/src/`, recompile the production bundle:

```bash
cd frontend
npm install
npm run build
cd ..
```
The compiled files are automatically output to `frontend/dist/` and served directly by Flask.

---

## ☁️ Deployment on Render

This repository is pre-configured for zero-configuration deployment on [Render](https://render.com):

1. Link your repository `soil-chemometrics-dashboard` on Render.
2. Select **Web Service** with the following settings:
   - **Environment:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300
     ```
3. Set the instance type to **Starter** or higher (minimum 1GB RAM recommended for multi-model loading).

---

## 📊 Input Data Formatting

To evaluate models or run predictions via Excel upload:
- **Columns 1 to 21:** `nm_410`, `nm_435`, `nm_460`, ..., `nm_200` (Raw spectral reflectance values).
- **Nutrient Ground Truth Columns (for testing accuracy):** `OC`, `N`, `P2O5`, `K2O`, `Ca`, `Mg`, `SO4`, `Fe`, `Mn`, `Cu`, `Zn`, `B`.
- **Sample Identifier:** `Sample_ID` or `Sample #`.

---

## 📄 License & Proprietary Notice

All rights reserved. This software, including its pre-trained chemometric weight files, calibration coefficients, and two-stage soft-clamping algorithms, is proprietary intellectual property. Unauthorized copying, reverse engineering, or redistribution is strictly prohibited.
