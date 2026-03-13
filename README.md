# 🥊 UFC Stats Web Scraper & Data Pipeline

This repository contains a suite of Python scripts designed to extract, clean, and process the complete [UFC Stats](http://ufcstats.com) database. 

The goal of this pipeline is to create high-quality, **Machine Learning-ready** datasets containing the complete history of fights and fighter profiles from UFC 1 (1993) up to 2026.

## 🏗️ Project Architecture

The pipeline is divided into four main scripts, which should be executed sequentially to ensure data integrity:

### 1. Fight Extraction (`ComnbatScrapingMMA.py`)
Scrapes all events and fights in UFC history.
* **Resilience:** Features a checkpointing system (memory) that reads the existing CSV and skips already downloaded fights, ideal for long extractions or internet disconnections.
* **Inline Cleaning:** Immediately converts strike fractions (e.g., "26 of 45") into separate *Landed* and *Attempted* numerical columns, and calculates the total fight time in pure seconds.
* **Output:** `ufc_gold_dataset.csv`

### 2. Chronological Sorting (`sortCombats.py`)
Converts event dates to `Datetime` format and sorts the fight dataset from oldest to newest.
* **Importance:** A crucial step to prevent *Data Leakage* in the future predictive modeling phase.
* **Output:** `ufc_gold_dataset_final.csv`

### 3. Fighter Extraction (`ufc_fighters_scraper.py`)
Visits the alphabetical directory and extracts the biometric profile and career statistics (SLpM, SApM, TD Def, etc.) of over 4,400 fighters.
* **Optimization:** Uses optimized parameters (`page=all`) to drastically reduce the number of server requests and speed up the process.
* **Output:** `ufc_fighters_profiles.csv`

### 4. Biometric Cleaning (`SortFighters.py`)
Handles missing data and standardizes physical metrics for mathematical calculations.
* **Null Handling:** Converts strings like `--` (common in fighters from the 90s) into actual Pandas `NaN`s for future imputation.
* **Output:** `ufc_fighters_final.csv`

---

## 🚀 How to Run

**1. Install dependencies:**
pip install requests beautifulsoup4 pandas numpy

**1. Run the Scripts:**
python CombatScrapingMMA.py
python FighterScrapingMMA.py
python sortCombats.py
python sortFighters.py
