# Urban GNSS Risk Assessment Using High-Definition 3D City Models

**Validating the 'Building-First' Hypothesis in Dense Urban Environments**

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

## 🛠 Prerequisites

To reproduce this study, you need the following environment:

### 1. Software
* **Python 3.10+**
* **QGIS 3.40 LTR** (Required for spatial processing steps)

### 2. Python Libraries
Install the required dependencies:
```bash
pip install -r requirements.txt
