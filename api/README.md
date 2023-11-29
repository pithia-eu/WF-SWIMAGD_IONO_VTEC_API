# NOA Workflow API

## Overview

The NOA Workflow API provides a set of endpoints to interact with the NOA Workflow scripts. These scripts allow you to download various data sets related to NOA.

## Features

- Get the status of the NOA Workflow API.
- Download KP data for a given date range.
- Download BMAG data for a given datetime range.
- Download SAO metadata for a given datetime range.

## Prerequisites

Before using this API, ensure you have the following prerequisites:

- Python 3.6+
- FastAPI
- Pydantic
- Various system dependencies as required by the NOA Workflow scripts.

## Installation

1. Clone the repository:
     ```shell
     git clone https://github.com/pithia-eu/WF-NOA1.git
     cd api
     ```

2. Install the required dependencies:
     ```shell
     pip install -r requirements.txt
     ```

3. Run the FastAPI application:
     ```shell
     uvicorn apis:app --host 0.0.0.0 --port 8000 --reload
     ```
4. Open a web browser to access the API's Swagger UI documentation.
    ```shell
    localhost:8000/docs#
    ```

## API Endpoints

### Get API Status

- URL: /
- Method: GET
- Description: Get the status of the NOA Workflow API.
- Response:
    ```json
    {
         "status": "ok",
         "message": "The NOA Workflow API is running.",
         "version": "1.0.0",
         "api_dir": "path_to_api_directory",
         "workflow_dir": "path_to_workflow_scripts_directory"
    }
    ```

### Download KP Data

- URL: /download_kp_data/
- Method: GET
- Description: Download KP data for a given date range.
- Query Parameters:
    - start_date (string, required): Start date in the format 'YYYY-MM-DD'.
    - end_date (string, required): End date in the format 'YYYY-MM-DD'.
- Response: CSV file containing KP data for the specified date range.

### Download BMAG Data

- URL: /download_bmag_data/
- Method: GET
- Description: Download BMAG data for a given datetime range.
- Query Parameters:
    - start_datetime (string, required): Start datetime in the format 'YYYY-MM-DDTHH:MM:SS'.
    - end_datetime (string, required): End datetime in the format 'YYYY-MM-DDTHH:MM:SS'.
- Response: CSV file containing BMAG data for the specified datetime range.

### Download SAO Metadata (ZIP)

- URL: /download_sao_metadata_zip/
- Method: GET
- Description: Download SAO metadata for a given datetime range as a ZIP file.
- Query Parameters:
    - start_datetime (string, required): Start datetime in the format 'YYYY-MM-DDTHH:MM:SS'.
    - end_datetime (string, required): End datetime in the format 'YYYY-MM-DDTHH:MM:SS'.
    - stations (string, required): Comma-separated list of stations, e.g., 'AT138,DB049'.
    - characteristics (string, required): Comma-separated list of characteristics, e.g., 'foF2,foF1'.
- Response: ZIP file containing SAO metadata for the specified datetime range, stations, and characteristics.

## Usage

1. Start the FastAPI application as described in the Installation section.

2. Use a tool like curl, Postman, or your preferred HTTP client to make requests to the API endpoints as described in the API Endpoints section.

3. Retrieve data files and information as needed for your research or analysis.
