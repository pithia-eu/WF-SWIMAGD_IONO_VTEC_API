from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
import subprocess
import json
import os
import glob
import shutil
import zipfile
from datetime import datetime
from io import StringIO, BytesIO

# Define the set of valid stations and characteristics for the SAO metadata API
VALID_STATIONS = {
    'AT138', 'DB049', 'EA036', 'EB040', 'JR055', 'PQ052', 'RL052', 'RO041', 'SO148', 'TR170'
}
VALID_CHARACTERISTICS = {
    'foF2', 'foF1', 'mD', 'mufD', 'fmin', 'foEs', 'fminF', 'fminE', 'foE', 'fxI', 'hF', 'hF2',
    'hE', 'hEs', 'zmE', 'yE', 'qf', 'qe', 'downF', 'downE', 'downEs', 'ff', 'fe', 'd', 'fMUF',
    'hfMUF', 'delta_foF2', 'foEp', 'fhF', 'fhF2', 'foF1p', 'phF2lyr', 'phF1lyr', 'zhalfNm',
    'foF2p', 'fminEs', 'yF2', 'yF1', 'tec', 'scHgtF2pk', 'b0IRI', 'b1IRI', 'd1IRI', 'foEa',
    'hEa', 'foP', 'hP', 'fbEs', 'typeEs'
}

# Get the full path to the directory containing the FastAPI script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the full path to the directory containing the NOA Workflow scripts
workflow_dir = script_dir.replace('/api', '')
app = FastAPI(
    openapi_tags=[
        {
            "name": "Status",
            "description": "Get the status of the NOA Workflow API."
        },
        {
            "name": "Get KP Data",
            "description": "Download the KP data for a given date range."
        },
        {
            "name": "Get BMAG Data",
            "description": "Download the BMAG data for a given datetime range."
        },
        {
            "name": "Get SAO Metadata",
            "description": "Download the SAO metadata for a given datetime range."
        }
    ],
    title="SWIMAGD_IONO Workflow API",
    description="A REST API for running the SWIMAGD_IONO (SOLAR WIND MAGNETOSPHERE DRIVEN IONOSPHERIC RESPONSE) Workflow scripts.",
    version="1.0.0",
)

class ExecuteRequest(BaseModel):
    date: str

# Validate the date range
def validate_dates(start_date_str, end_date_str):
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        if start_date > end_date:
            return False
    except ValueError:
        return False
    return True

# Validate the datetime range
def validate_datetimes(start_datetime_str, end_datetime_str):
    try:
        start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M:%S')
        end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M:%S')
        if start_datetime > end_datetime:
            return False
    except ValueError:
        return False
    return True

# Get the status of the NOA Workflow API
@app.get("/", summary="Get the status of the NOA Workflow API.", description="Returns the status of the NOA Workflow API.", tags=["Status"])
async def get_status():
    return {"status": "ok",
            "message": "The NOA Workflow API is running.",
            "version": "1.0.0",
            "api_dir": script_dir,
            "workflow_dir": workflow_dir}

# Run the workflow workflow_dir/get_kp_data.sh script
# Example: /download_kp_data/?start_date=2023-11-06&end_date=2023-11-07
@app.get("/download_kp_data/", response_class=StreamingResponse, summary="Download the KP data for a given date range.", description="Download the KP data for a given date range.", tags=["Get KP Data"])
async def download_kp_data(start_date: str = Query(..., description="Date in the format 'YYYY-MM-DD', e.g 2023-01-20"), end_date: str = Query(..., description="Date in the format 'YYYY-MM-DD', e.g. 2023-01-20")):
    # Validate the date range
    if not validate_dates(start_date, end_date):
        raise HTTPException(status_code=400, detail="Invalid date range. Ensure the start date is before the end date and the format is YYYY-MM-DD.")

    script_path = f'{workflow_dir}/get_kp_data.sh'
    # Execute the shell script and capture the output
    try:
        process = subprocess.Popen(
            [script_path, start_date, end_date, 'print-csv'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode()  # Parse the JSON error message
            raise HTTPException(status_code=500, detail=error_message)

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Construct the filename
    filename = f"kp_{start_date}_{end_date}.csv"

    # Return the output as a streaming response
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': 'text/csv'
    }
    return StreamingResponse(iter([stdout]), headers=headers)

# Run the workflow workflow_dir/get_bmag_data.py script
# Example: /download_bmag_data/?start_datetime=2023-11-06T00:00:00&end_datetime=2023-11-07T00:00:00
@app.get("/download_bmag_data/", response_class=StreamingResponse, summary="Download the BMAG data for a given datetime range.", description="Download the BMAG data for a given datetime range.", tags=["Get BMAG Data"])
async def download_bmag_data(start_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2023-01-01T00:00:00 "),end_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2023-01-01T00:00:00")):
    # Validate the datetime range
    if not validate_datetimes(start_datetime, end_datetime):
        raise HTTPException(status_code=400, detail="Invalid datetime range. Ensure the start datetime is before the end datetime and the format is YYYY-MM-DDTHH:MM:SS.")
    
    # Construct the command to run the Python script
    script_path = f'{workflow_dir}/get_bmag_data.py'
    command = ['python3', script_path, start_datetime, end_datetime]

    # Execute the script and capture the output
    try:
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        stdout, stderr = process.stdout, process.stderr
        
        if process.returncode != 0:
            error_message = stderr.decode()  # Parse the JSON error message
            raise HTTPException(status_code=500, detail=error_message)
    except subprocess.CalledProcessError as e:
        error_detail = json.loads(e.stdout)
        raise HTTPException(status_code=500, detail=error_detail)

    # Construct the filename for the downloadable file
    filename = f"bmag_{start_datetime}_{end_datetime}.csv"

    # Return the output as a streaming response
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': 'text/csv'
    }
    return StreamingResponse(iter([stdout]), headers=headers)

# Run the workflow workflow_dir/get_sao_metadata.py script
# Example: /download_sao_metadata_zip/?start_datetime=2023-11-06T00:00:00&end_datetime=2023-11-07T00:00:00&stations=AT138,DB049&characteristics=foF2,foF1
@app.get("/download_sao_metadata_zip/", response_class=StreamingResponse, summary="Download the SAO metadata for a given datetime range.", description="Download the SAO metadata for a given datetime range.", tags=["Get SAO Metadata"])
async def download_sao_metadata_zip(start_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2023-01-01T00:00:00 "),end_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2023-01-01T00:00:00"), stations: str = Query(..., description=f"Comma-separated list of stations, e.g. AT138,DB049. Full list of valid stations: {VALID_STATIONS}"), characteristics: str = Query(..., description=f"Comma-separated list of characteristics, e.g. foF2,foF1. Full list of valid characteristics: {VALID_CHARACTERISTICS}")):
    # Validate the datetime range
    if not validate_datetimes(start_datetime, end_datetime):
        raise HTTPException(status_code=400, detail="Invalid datetime range. Ensure the start datetime is before the end datetime and the format is YYYY-MM-DDTHH:MM:SS.")
    
    # Construct the command to run the Python script
    script_path = f'{workflow_dir}/get_sao_metadata.py'
    command = ['python3', script_path, start_datetime, end_datetime, stations, characteristics]

    # Execute the script and capture the output
    try:
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        stdout, stderr = process.stdout, process.stderr
        
        if process.returncode != 0:
            error_message = stderr.decode()  # Parse the JSON error message
            raise HTTPException(status_code=500, detail=error_message)
        
    except subprocess.CalledProcessError as e:
        error_detail = json.loads(e.stdout)
        raise HTTPException(status_code=500, detail=error_detail)

    try:
        # Create CSV files in memory for each station
        station_files = {}
        for line in process.stdout.splitlines():
            if line.startswith("station_csv_filename:"):
                filename = line.split("'")[1].split(",")[0].strip()
                station_files[filename] = StringIO()
            elif line:
                station_files[filename].write(line + '\n')

        # Create a ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, file in station_files.items():
                file.seek(0)
                zipf.writestr(filename, file.getvalue())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing output: {str(e)}")

    # Prepare the ZIP file for download
    zip_buffer.seek(0)
    zip_filename = f"sao_metadata_{start_datetime}_{end_datetime}.zip"

    # Return the ZIP content as a streaming response
    headers = {
        'Content-Disposition': f'attachment; filename="{zip_filename}"',
        'Content-Type': 'application/zip'
    }
    return StreamingResponse(zip_buffer, media_type="application/octet-stream", headers=headers)