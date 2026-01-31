# Urban GNSS Risk Assessment Using High-Definition 3D City Models

**Urban GNSS Risk Assessment Using High-Definition 3D City Models: Validating the "Building-First" Hypothesis and the Necessity of Infrastructure Integration**

This repository contains the source code, QGIS processing scripts, and data pipeline for the research paper presented at **Pacific PNT 2026**.

---

## 📖 Abstract (IMRAD)

### **Introduction**
Standard 3D city maps often prioritize buildings ("Building-First" hypothesis) while overlooking civil infrastructure like highway viaducts. This study investigates whether these standard models are sufficient for GNSS risk assessment in dense urban canyons like Shibuya, Tokyo.

### **Methods**
We conducted a field experiment at **45 stratified sites** (Open/Street/Alley) in a 500m x 500m area of Shibuya. We compared:
1.  **Baseline:** Risk estimation using standard Building-Only 3D models.
2.  **Proposed:** A Hybrid Override Logic integrating infrastructure data.
Ground truth data was collected using a **Google Pixel 8** (Raw GNSS Logs).

### **Results**
Standard models failed to detect risks at critical locations, such as **Site A11**, which lies directly beneath a highway viaduct but was classified as "Open Sky." The proposed hybrid method significantly improved risk prediction accuracy (**AUC improved from 0.68 to 0.89**).

### **Discussion**
We demonstrate that geometry-only approaches using standard building data are insufficient for urban air mobility and autonomous navigation. Infrastructure layers are critical for accurate signal degradation modeling.

---

## 📡 Data Collection Protocol

 The raw GNSS logs in `data/raw/` were collected under strict conditions:

* **Device:** Google Pixel 8 (Android 16)
* **Software:** Google GNSS Logger v3.0.0.1
* **Mounting:** Tripod-mounted at **1.5m height** (Screen facing zenith)
* **Constellations:** GPS (L1/L5), QZSS (L1/L5), Galileo (E1/E5a), BeiDou, GLONASS
* **Duration:** 5 minutes 30 seconds per site
* **Dates:** January 10–14, 2026 (11:00 - 14:00 JST)
* **Location:** Shibuya, Tokyo (500m x 500m AOI)

---

## 🛠 Prerequisites Reproduction Steps

To reproduce this study, you need the following environment:

### 1. Software
* **Python 3.10+**
* **QGIS 3.40 LTR** (Required for spatial processing steps)

### 2. Python Libraries
Install the required dependencies:

```bash
pip install -r requirements.txt
```
---



## 🚀 Reproduction Steps

This workflow consists of two parts: **Spatial Processing (QGIS)** and **Data Analysis (Python)**.

### Step 1: Spatial Processing (QGIS)
This step generates the risk maps and geometric features from raw 3D data.

1. **Setup Project:**
   - Open QGIS and create a new project.
   - Set Project CRS to **EPSG:6677** (JGD2011 / Tokyo).
   - Load all layers from `data_qgis/raw/` into the project.

2. **Generate Risk Raster Layers:**
   Open the QGIS Python Console and run the scripts in the following order:
   - `src_qgis/bld_height3m_layer.py`
   - `src_qgis/bld_height5m_layer.py`
   - `src_qgis/open_street_alley_threshold_layer.py`
   - `src_qgis/svf_risk_localmax_layer.py`

3. **Process Site Data:**
   - Load the layer: `data_qgis/processed/PNT_sites_raw.gpkg`
   - Run script: `src_qgis/for_PNT_sites_raw.py`
  
### Step 2: Analysis Pipeline (Python)

This step processes the GNSS logs and evaluates the risk models statistically.

> **Note:** Ensure `data/` folder contains the downloaded datasets.

Run the scripts in the following order from the terminal:

1. **Baseline Analysis (Phase 1)**
   ```bash
   python src/01_baseline_phase1/run_baseline.py
   ```
2. **Proposed Method & Simulation (Phase 2)**
   ```bash
   python src/02_proposed_phase2/step2_1_dop_sim.py
   python src/02_proposed_phase2/step2_2_evaluate_methods.py
   ```
3. **Statistical Validation (Phase 3)**
   ```bash
   python src/03_statistical_validation/run_bootstrap_test.py
   ```
## 📂 Directory Structure

* `data/`: GNSS logs and CSV datasets.
* `data_qgis/`: Spatial data (Geopackages, TIFs).
* `src/`: Main analysis Python scripts.
* `src_qgis/`: Python scripts for QGIS Console.
* `experiments/`: Output directory for reproduction results.

---

## ✉️ Contact

* **Author:** Rito Yamasaki
* **Affiliation:** Furuhashi Lab, School of Global Studies and Collaboration, Aoyama Gakuin University
* **Note:** For questions or feedback, please open an [Issue](https://github.com/your-username/PacificPNT_GitHub/issues) in this repository.
   
