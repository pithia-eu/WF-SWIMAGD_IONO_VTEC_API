# Data Retrieval Scripts for WF-NOA 1

This repository contains three scripts for retrieving various types of data. Each script is tailored for specific data retrieval purposes as detailed below.

## 1. Get Kp Index Data (`get_kp_data.sh`)

### Description
This Bash script fetches geomagnetic Kp index data for a specified date range.

### Usage
```./get_kp_data.sh [start_date] [end_date] [format]```

- **start_date:** Start date in YYYY-MM-DD format.
- **end_date:** End date in YYYY-MM-DD format.
- **format:** Output format (options: `print`, `txt`, `json`).

#### Example
```./get_kp_data.sh 2023-11-06 2023-11-07 txt```

#### Output
The results are saved in the `./output/kp_index` directory with the filename format `${start_date}_to_${end_date}.${output_format}`.

---

## 2. Get Bmag Data (`get_bmag_data.py`)

### Description
This Python script retrieves magnetic field data (Bmag, Bx, By, Bz) for a given start and end datetime.

### Usage
```python get_bmag_data.py [start_datetime] [end_datetime]```

- **start_datetime:** Start datetime in ISO format (YYYY-MM-DDTHH:MM:SS).
- **end_datetime:** End datetime in ISO format (YYYY-MM-DDTHH:MM:SS).

#### Example
```python get_bmag_data.py 2021-01-01T00:00:00 2021-01-02T00:00:00```

#### Output
Prints the results to the console in the format: UTC ISO Timestamp, Bmag, Bx, By, Bz.

---

## 3. Get SAO Metadata (`get_sao_metadata.py`)

### Description
This Python script fetches SAO metadata for specified stations and characteristics within a given datetime range.

### Usage
```python3 get_sao_metadata.py [start_datetime] [end_datetime] [stations] [characteristics]```

- **start_datetime:** Start datetime in ISO format (YYYY-MM-DDTHH:MM:SS).
- **end_datetime:** End datetime in ISO format (YYYY-MM-DDTHH:MM:SS).
- **stations:** List of station codes, separated by commas.
- **characteristics:** List of characteristic codes, separated by commas.

#### Example
```python3 get_sao_metadata.py 2023-11-06T12:00:00 2023-11-06T13:00:00 AT138,DB049 foF2,foF1```

#### Output
Prints the results to the console in the format: UTC ISO Timestamp, Station, Characteristics.

---

### Requirements
- For Bash scripts: A Unix-like environment with Bash.
- For Python scripts: Python 3.x with the required modules (`httpx`, `pandas`, `ciso8601`).

### Installation
- Ensure Python 3.x is installed.
- Install required Python modules: `pip install httpx pandas ciso8601`.

---
