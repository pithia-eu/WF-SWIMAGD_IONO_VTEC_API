import tempfile
import uuid
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import subprocess
import json
import os
import zipfile
from datetime import datetime, timedelta
from io import StringIO, BytesIO
from enum import Enum
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator, MaxNLocator
import numpy as np

class OutputFormat(str, Enum):
    zip = "zip"
    json = "json"


class Stations(str, Enum):
    AT138 = "AT138"
    DB049 = "DB049"
    EA036 = "EA036"
    EB040 = "EB040"
    JR055 = "JR055"
    PQ052 = "PQ052"
    RL052 = "RL052"
    RO041 = "RO041"
    SO148 = "SO148"
    TR170 = "TR170"

# Define the colors for each characteristic
CHAR_COLORS = {
    'b0IRI': '#C04F15',
    'fbEs': '#FF0000',
    'foE': '#0F9ED5',
    'foEs': '#4EA72E',
    'foF2': '#156082',
    'hE': '#0F9ED5',
    'hEs': '#4EA72E',
    'hF2': '#6D1582',
    'mufD': '#D86ECC',
    'phF2lyr': '#156082',
    'scHgtF2pk': '#0D3512'
}

# Define the set of valid stations and characteristics for the SAO metadata API
VALID_STATIONS = {
    'AT138', 'DB049', 'EA036', 'EB040', 'JR055', 'PQ052', 'RL052', 'RO041', 'SO148', 'TR170'
}
SORTED_VALID_STATIONS = ','.join(sorted(VALID_STATIONS))
VALID_CHARACTERISTICS = {
    'b0IRI', 'fbEs', 'ff', 'foE', 'foEs', 'foF2', 'hE', 'hEs', 'hF2', 'mufD', 'phF2lyr', 'scHgtF2pk'
    #'foF1', 'mD', 'fmin',  'fminF', 'fminE',  'fxI', 'hF''zmE', 'yE', 'qf', 'qe', 'downF', 'downE', 'downEs',  'fe', 'd', 'fMUF''hfMUF', 'delta_foF2', 'foEp', 'fhF', 'fhF2', 'foF1p', 'phF1lyr', 'zhalfNm', 'foF2p', 'fminEs', 'yF2', 'yF1', 'tec', 'b1IRI', 'd1IRI', 'foEa', 'hEa', 'foP', 'hP',  'typeEs'
}

SORTED_VALID_CHARACTERISTICS = ','.join(sorted(VALID_CHARACTERISTICS))

FREQ_CHARACTERISTICS = {
    'fbEs', 'foE', 'foEs', 'foF2', 'mufD'
}

HEIGHT_CHARACTERISTICS = {
    'b0IRI', 'hE', 'hEs', 'hF2', 'phF2lyr', 'scHgtF2pk'
}

SORTED_BOTH_CHARACTERISTICS = ','.join(sorted(FREQ_CHARACTERISTICS.union(HEIGHT_CHARACTERISTICS)))

# Get the full path to the directory containing the FastAPI script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the full path to the directory containing the NOA Workflow scripts
workflow_dir = script_dir.replace('/api', '')
app = FastAPI(
    openapi_tags=[
        # {"name": "Status","description": "Get the status of the NOA Workflow API."},
        #{"name": "Get KP Data","description": "Download the KP data for a given date range."},
        #{"name": "Get BMAG Data","description": "Download the BMAG data for a given datetime range."},
        #{"name": "Get SAO Metadata","description": "Download the SAO metadata for a given datetime range."},
        {
            "name": "Run Workflow",
            "description": "Run the SWIMAGD_IONO workflow and Download the compress results (KP data, B data, and SAO metadata) in either ZIP or JSON format."
        },
        {
            "name": "Plot Data",
            "description": "Plot the KP data, B data, and SAO metadata for selected station"
        }
    ],
    title="SWIMAGD_IONO Workflow API",
    description="The SWIMAGD_IONO workflow provides: <br /><br />(a) Geomagnetic three-hourly (T00:00:00, T03:00:00, …, T21:00:00) Kp index​; <br />(b) DSCOVR mission Magdata records (Bmag, Bx, By, Bz) as part of the SWIF model Data Collection; <br />(c) Distinct ionospheric characteristics (SAO records) for 10 European Digisonde stations (AT138, EA036, EB040, DB049, JR055, PQ052, RL052, RO041, SO148, TR170).",
    version="1.1.0",
    root_path="/wf-swimagd_iono"
)

# Configure CORS for all domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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
@app.get("/", summary="Get the status of the SWIMAGD_IONO Workflow API.", description="Returns the status of the SWIMAGD_IONO Workflow API.", tags=["Status"], include_in_schema=False)
async def get_status():
    return {"status": "ok",
            "message": "The SWIMAGD_IONO Workflow API is running.",
            "version": "1.0.0",
            "api_dir": script_dir,
            "workflow_dir": workflow_dir}

# Run the workflow workflow_dir/get_kp_data.sh script
# Example: /download_kp_data/?start_date=2023-11-06&end_date=2023-11-07
@app.get("/download_kp_data/", response_class=StreamingResponse, summary="Download the KP data for a given date range.", description="Download the KP data for a given date range.", tags=["Get KP Data"], include_in_schema=False)
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
@app.get("/download_bmag_data/", response_class=StreamingResponse, summary="Download the BMAG data for a given datetime range.", description="Download the BMAG data for a given datetime range.", tags=["Get BMAG Data"], include_in_schema=False)
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
@app.get("/download_sao_metadata_zip/", response_class=StreamingResponse, summary="Download the SAO metadata for a given datetime range.", description="Download the SAO metadata for a given datetime range.", tags=["Get SAO Metadata"], include_in_schema=False)
async def download_sao_metadata_zip(start_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2023-01-01T00:00:00 "),end_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2023-01-01T00:00:00"), stations: str = Query(..., description=f"Comma-separated list of stations, e.g. AT138,DB049. Full list of valid stations: {VALID_STATIONS}"), characteristics: str = Query(..., description=f"Comma-separated list of characteristics, e.g. foF2,foE. Full list of valid characteristics: {VALID_CHARACTERISTICS}")):
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
    # Create a temporary file to store the ZIP content
    with tempfile.NamedTemporaryFile(delete=False) as temp_zip_file:
        temp_zip_file.write(zip_buffer.getvalue())
    zip_filename = f"sao_metadata_{start_datetime}_{end_datetime}.zip"

    headers = {
        'Content-Disposition': f'attachment; filename="{zip_filename}"'
    }
    # Use FileResponse to return the ZIP file
    return FileResponse(temp_zip_file.name, media_type="application/octet-stream", headers=headers)


# Define the new `run_workflow` API
@app.get("/run_workflow/", response_class=StreamingResponse, responses={200: {"content": {"application/octet-stream": {}},"description": "**Important:** When selecting the 'zip' format, please remember to rename the downloaded file to have the extension '*.zip' before opening it.\n\n",}},summary="Run the SWIMAGD_IONO workflow.", description="Return KP data, B data, and SAO metadata, and optionally compress the results into a single ZIP file or receive them in JSON format.\n\n"+"**Important:** When selecting the 'zip' format, please remember to rename the downloaded file to have the extension '*.zip' before opening it.\n\n", tags=["Run Workflow"])
async def run_workflow(start_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2024-01-01T00:00:00 "), end_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2024-01-01T00:00:00"), stations: str = Query(..., description=f"Comma-separated list of stations, e.g. AT138,DB049. Full list of valid stations: {SORTED_VALID_STATIONS}"), characteristics: str = Query(..., description=f"Comma-separated list of characteristics, e.g. foF2,foE. Full list of valid characteristics: b0IRI,fbEs,ff,foE,foEs,foF2,hE,hEs,hF2,mufD,phF2lyr,scHgtF2pk, where phF2ly=hmF2."),format: OutputFormat = Query(..., description="The format of the output file. Valid values are 'zip' and 'json'.")):
    error_message = {"error":""}
    # Remove any whitespace from the stations and characteristics
    stations = stations.replace(' ', '')
    characteristics = characteristics.replace(' ', '')
    # Sort the stations and characteristics a-z
    stations = ','.join(sorted(stations.split(',')))
    characteristics = ','.join(sorted(characteristics.split(',')))
    
    # Validate the inputs
    if not validate_datetimes(start_datetime, end_datetime):
        error_message['error']="Invalid datetime range. Ensure the start datetime is before the end datetime and the format is YYYY-MM-DDTHH:MM:SS."
        return JSONResponse(
            status_code=200, content=error_message)
    if not set(stations.split(',')).issubset(VALID_STATIONS):
        error_message['error']=f"One or more stations are invalid. Here is the list of valid stations: {','.join(VALID_STATIONS)}"
        return JSONResponse(status_code=200, content=error_message)
    if not set(characteristics.split(',')).issubset(VALID_CHARACTERISTICS):
        error_message['error']=f"One or more characteristics are invalid. Here is the list of valid characteristics: {','.join(VALID_CHARACTERISTICS)}"
        return JSONResponse(status_code=200, content=error_message)
    
    # Workflow Step 1: Get KP data
    kp_script_path = f'{workflow_dir}/get_kp_data.sh'
    # Convert the start and end datetimes to dates
    start_date = start_datetime.split('T')[0]
    # Add one day to the end date to ensure the end date is included in the results
    end_date = (datetime.strptime(end_datetime.split('T')[0], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    # Execute the shell script and capture the output
    try:
        process = subprocess.Popen(
            [kp_script_path, start_date, end_date, 'print-csv'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_message['error'] = stderr.decode()  # Parse the JSON error message
            # Return the error message as json in the response, instead of raising an exception
            return JSONResponse(status_code=200, content=error_message)
    except subprocess.CalledProcessError as e:
        error_message['error'] = str(e)
        return JSONResponse(status_code=200, content=error_message)
    # Create CSV files in memory for kp data
    try:
        kp_filename = f"kp_{start_datetime.replace(':','-')}_{end_datetime.replace(':','-')}.csv"
        kp_file = StringIO(stdout.decode())
        kp_file.seek(0)
    except Exception as e:
        error_message['error'] = f"Error processing output: {str(e)}"
        return JSONResponse(status_code=200, content=error_message)
    # Remove the rows that timestamp is not in the requested datetime range, start_datetime <= timestamp <= end_datetime
    try:
        kp_df = pd.read_csv(kp_file, sep=',', header=0, index_col=0)
        # Convert the index to datetime with the format YYYY-MM-DDTHH:MM:SS
        kp_df.index = pd.to_datetime(kp_df.index).strftime('%Y-%m-%dT%H:%M:%S')
        kp_df = kp_df.loc[start_datetime:end_datetime]
        kp_file = StringIO(kp_df.to_csv())
        kp_file.seek(0)
    except Exception as e:
        error_message['error'] = f"Error processing output: {str(e)}"
        return JSONResponse(status_code=200, content=error_message)
    
    # Workflow Step 2: Get BMAG data
    bmag_script_path = f'{workflow_dir}/get_bmag_data.py'
    command = ['python3', bmag_script_path, start_datetime, end_datetime]
    # Execute the script and capture the output
    try:
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        stdout, stderr = process.stdout, process.stderr
        
        if process.returncode != 0:
            error_message['error'] = stderr.decode()  # Parse the JSON error message
            return JSONResponse(status_code=200, content=error_message)
    except subprocess.CalledProcessError as e:
        error_message['error'] = json.loads(e.stdout)
        return JSONResponse(status_code=200, content=error_message)
    # Create CSV files in memory for bmag data
    try:
        bmag_filename = f"b_{start_datetime.replace(':','-')}_{end_datetime.replace(':','-')}.csv"
        bmag_file = StringIO(stdout)
        bmag_file.seek(0)
    except Exception as e:
        error_message['error'] = f"Error processing output: {str(e)}"
        return JSONResponse(status_code=200, content=error_message)
        #raise HTTPException(status_code=400, detail=f"Error processing output: {str(e)}")
    
    # Workflow Step 3: Get SAO metadata
    sao_script_path = f'{workflow_dir}/get_sao_metadata.py'
    command = ['python3', sao_script_path, start_datetime, end_datetime, stations, characteristics]
    # Execute the script and capture the output
    try:
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        stdout, stderr = process.stdout, process.stderr
        
        if process.returncode != 0:
            error_message['error'] = stderr.decode()
            return JSONResponse(status_code=200, content=error_message)
        
    except subprocess.CalledProcessError as e:
        error_message['error'] = json.loads(e.stdout)
        return JSONResponse(status_code=200, content=error_message)
    # Create CSV files in memory for each station
    try:
        # Create CSV files in memory for each station
        station_files = {}
        for line in process.stdout.splitlines():
            if line.startswith("station_csv_filename:"):
                filename = line.split("'")[1].split(",")[0].replace(':','-').strip()
                station_files[filename] = StringIO()
            elif line:
                station_files[filename].write(line + '\n')
    except Exception as e:
        error_message['error'] = f"Error processing output: {str(e)}"
        return JSONResponse(status_code=200, content=error_message)
    
    if format == OutputFormat.json:
        # Convert to json from csv, first row is header, keys are separated by comma, data is from second row, values are separated by comma
        kp_json = pd.read_csv(kp_file, sep=',', header=0, index_col=0).to_json(orient='index')
        bmag_json = pd.read_csv(bmag_file, sep=',', header=0, index_col=0).to_json(orient='index')
        sao_json = {}
        for filename, file in station_files.items():
            file.seek(0)
            # Only get the station name from the filename
            filename = filename.split('_')[0]
            sao_json[filename] = json.loads(pd.read_csv(file, sep=',', header=0, index_col=0, usecols=lambda column: column != 'station').to_json(orient='index'))
        # Construct the final json response
        response_json = {
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'stations': stations,
            'characteristics': characteristics,
            'data':{
                'kp_data': json.loads(kp_json),
                'b_data': json.loads(bmag_json),
                'sao_metadata': sao_json
            }
        }
        # Return the json response
        headers = {
            'Content-Disposition': f'attachment; filename="SWIMAGD_IONO_Workflow_{start_datetime}_{end_datetime}.json"',
            'Content-Type': 'application/json'
        }
        return StreamingResponse(iter([json.dumps(response_json)]), headers=headers)
    
    if format == OutputFormat.zip:
        # Workflow Step 4: Create ZIP file, add files to it, and return it as a streaming response
        # The zip file structure will be: kp_filename, bmag_filename, for each station, stroed in the sao/ directory
        # Create a ZIP file in memory
        try:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add the KP data file
                zipf.writestr(kp_filename, kp_file.getvalue())
                # Add the BMAG data file
                zipf.writestr(bmag_filename, bmag_file.getvalue())
                # Add the SAO metadata files
                for filename, file in station_files.items():
                    file.seek(0)
                    zipf.writestr(f"sao/{filename}", file.getvalue())
        except Exception as e:
            error_message['error'] = f"Error processing output: {str(e)}"
            return JSONResponse(status_code=200, content=error_message)

        # Prepare the ZIP file for download
        zip_buffer.seek(0)
        # Create a temporary file to store the ZIP content
        with tempfile.NamedTemporaryFile(delete=False) as temp_zip_file:
            temp_zip_file.write(zip_buffer.getvalue())
            
        zip_filename = f"SWIMAGD_IONO_Workflow_{start_datetime}_{end_datetime}.zip"

        headers = {
            'Content-Disposition': f'attachment; filename="{zip_filename}"'
        }
        # Use FileResponse to return the ZIP file
        return FileResponse(temp_zip_file.name, media_type="application/octet-stream", headers=headers)


# Define the 'plot_data' API
@app.get("/plot_data/", response_class=StreamingResponse, summary="Plot the KP data, B data, and SAO metadata for selected station.", description="Plot the KP data, B data, and SAO metadata.", tags=["Plot Data"])
async def plot_data(date_of_interest: str = Query(..., description="Date in the format 'YYYY-MM-DD', e.g. 2023-01-01"), station: Stations = Query(..., description=f"Select a station"), characteristics: str = Query(..., description=f"Comma-separated list of characteristics, e.g. foF2,foE. Full list of valid characteristics: b0IRI,fbEs,foE,foEs,foF2,hE,hEs,hF2,mufD,phF2lyr,scHgtF2pk, where phF2ly=hmF2.")):
    error_message = {"error":""}
    # Remove any whitespace from the characteristics
    characteristics = characteristics.replace(' ', '')
    # Sort the stations and characteristics a-z
    characteristics = ','.join(sorted(characteristics.split(',')))
    
    # Validate the inputs
    if not set(characteristics.split(',')).issubset(FREQ_CHARACTERISTICS.union(HEIGHT_CHARACTERISTICS)):
        error_message['error']=f"One or more characteristics are invalid. Here is the list of valid characteristics: {SORTED_BOTH_CHARACTERISTICS}"
        return JSONResponse(status_code=200, content=error_message)
    # Validate the date of interest
    try:
        datetime.strptime(date_of_interest, '%Y-%m-%d')
    except ValueError:
        error_message['error']="Invalid date format. Ensure the format is YYYY-MM-DD."
        return JSONResponse(status_code=200, content=error_message)
    
    # Generate start_datetime and end_datetime from date_of_interest, which include the previous day data, and the next day data, at time 00:00:00
    start_datetime = (datetime.strptime(date_of_interest, '%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S')
    end_datetime = (datetime.strptime(date_of_interest, '%Y-%m-%d') + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%S')
    # Construct the X Axis in Array, with 5 minutes interval, from start_datetime to end_datetime
    
    # Get the KP data
    kp_script_path = f'{workflow_dir}/get_kp_data.sh'
    # Convert the start and end datetimes to dates
    start_date = start_datetime.split('T')[0]
    # Add one day to the end date to ensure the end date is included in the results
    end_date = end_datetime.split('T')[0]
    # Execute the shell script and capture the output
    try:
        process = subprocess.Popen(
            [kp_script_path, start_date, end_date, 'print-csv'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_message['error'] = stderr.decode()  # Parse the JSON error message
            # Return the error message as json in the response, instead of raising an exception
            return JSONResponse(status_code=200, content=error_message)
    except subprocess.CalledProcessError as e:
        error_message['error'] = str(e)
        return JSONResponse(status_code=200, content=error_message)
    # 3 Hours range KP data, so we need to get the timestamp with the format YYYY-MM-DDTHH:MM:SS
    x_axis = pd.date_range(start_datetime, end_datetime, freq='3h')
    # Get the KP data for the date of interest, fill the kp_y_axis with the kp value, if the timestamp is not in the x_axis, fill the value with 0
    try:
        kp_df = pd.read_csv(StringIO(stdout.decode()), sep=',', header=0, index_col=0)
        kp_df.index = pd.to_datetime(kp_df.index).strftime('%Y-%m-%dT%H:%M:%S')
        kp_y_axis = []
        for timestamp in x_axis.strftime('%Y-%m-%dT%H:%M:%S'):
            if timestamp in kp_df.index:
                kp_y_axis.append(kp_df.loc[timestamp, 'Kp'])
            else:
                kp_y_axis.append(0)
    except Exception as e:
        error_message['error'] = f"Error processing output: {str(e)}"
        return JSONResponse(status_code=200, content=error_message)
    
    fig,(ax_b,ax_kp, ax_freq, ax_height) = plt.subplots(4,1, figsize=(16,9), dpi=100)
    # For all the subplots, set the x-axis range from start_datetime-2 hours to end_datetime+2 hours, need to convert the string to datetime
    start_datetime_offset = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M:%S') - timedelta(hours=2)
    end_datetime_offset = datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M:%S') + timedelta(hours=2)
    ax_b.set_xlim(start_datetime_offset, end_datetime_offset)
    ax_kp.set_xlim(start_datetime_offset, end_datetime_offset)
    
    # Calculate the major tick positions
    major_ticks = pd.date_range(datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M:%S'), periods=7, freq='12h')
    for ax in (ax_b, ax_kp, ax_freq, ax_height):
        ax.set_xticks(major_ticks)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        # Set the minor ticks to be every 1 hour
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
        # Plot the x-axis with grey color, linewidth 0.5, from top to bottom
        ax.xaxis.grid(True, which='major', color='grey', linestyle='-', linewidth=0.5)
        # Plot the x-axis for minor ticks without any text
        ax.xaxis.grid(True, which='minor', color='lightgrey', linestyle='-', linewidth=0.5)
        # Make all the lines in the plot to be under the grid lines, not cover the data
        ax.set_axisbelow(True)
        # if is ax_height, use customed x-axis label, format as 00:00:00, new line, Jan 01, 2023
        if ax == ax_height:
            ax.set_xticklabels([datetime.strftime(x, '%H:%M:%S\n%b %d, %Y') for x in major_ticks])
    # Plot the KP data using bar chart, skip the timestamp with 0 value
    ax_kp.bar(x_axis, kp_y_axis, width=0.04, color='#156082', label='Kp')
    # Set the kp y-axis range from min to max of kp_y_axis offset by 0.5
    ax_kp.set_ylim(0, max(kp_y_axis)+0.5)
    # Set the major ticks, maximum 5 ticks
    ax_kp.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
    # Draw the horizontal line at each major tick position
    ax_kp.yaxis.grid(True, linestyle='-', linewidth=0.5)
    
    ax_kp.set_ylabel('Kp-index')
    ax_kp.set_title(f'Geomagnetic three-hourly Kp-index')
    # Get the BMAG data
    bmag_script_path = f'{workflow_dir}/get_bmag_data.py'
    command = ['python3', bmag_script_path, start_datetime, end_datetime]
    # Execute the script and capture the output
    try:
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        stdout, stderr = process.stdout, process.stderr
        
        if process.returncode != 0:
            error_message['error'] = stderr.decode()  # Parse the JSON error message
            return JSONResponse(status_code=200, content=error_message)
    except subprocess.CalledProcessError as e:
        error_message['error'] = e.stdout
        return JSONResponse(status_code=200, content=error_message)
    # 1 hour range BMAG data, so we need to get the timestamp with the format YYYY-MM-DDTHH:MM:SS
    x_axis = pd.date_range(start_datetime, end_datetime, freq='1h')
    # Get the BMAG data for the date of interest, fill the bmag_y_axis with the bmag value, if the timestamp is not in the x_axis, fill the value with 0
    try:
        b_df = pd.read_csv(StringIO(stdout), sep=',', header=0, index_col=0)
        b_df.index = pd.to_datetime(b_df.index).strftime('%Y-%m-%dT%H:%M:%S')
        bmag_y_axis = []
        bx_y_axis = []
        by_y_axis = []
        bz_y_axis = []
        for timestamp in x_axis.strftime('%Y-%m-%dT%H:%M:%S'):
            if timestamp in b_df.index:
                bmag_y_axis.append(b_df.loc[timestamp, 'bmag'])
                bx_y_axis.append(b_df.loc[timestamp, 'bx'])
                by_y_axis.append(b_df.loc[timestamp, 'by'])
                bz_y_axis.append(b_df.loc[timestamp, 'bz'])
            else:
                bmag_y_axis.append(0)
                bx_y_axis.append(0)
                by_y_axis.append(0)
                bz_y_axis.append(0)
    except Exception as e:
        error_message['error'] = f"Error processing output: {str(e)}"
        return JSONResponse(status_code=200, content=error_message)

    # bmag line style is solid bold, bx line style is dash, by line style is dot, bz line style is solid thin, all in black color
    ax_b.plot(x_axis, bmag_y_axis, label='Bmag', linestyle='-', linewidth=4, color='black')
    ax_b.plot(x_axis, bx_y_axis, label='Bx', linestyle='--', linewidth=3, color='black')
    ax_b.plot(x_axis, by_y_axis, label='By', linestyle=':', linewidth=2, color='black')
    ax_b.plot(x_axis, bz_y_axis, label='Bz', linestyle='-', linewidth=1, color='black')
    # Set the y-axis range from min to max of all bmag_y_axis, bx_y_axis, by_y_axis, bz_y_axis offset by 20% of the axis height, auto scale
    ax_b.set_ylim(min(bmag_y_axis+bx_y_axis+by_y_axis+bz_y_axis)-1, max(bmag_y_axis+bx_y_axis+by_y_axis+bz_y_axis)+int(0.4*(max(bmag_y_axis+bx_y_axis+by_y_axis+bz_y_axis)-min(bmag_y_axis+bx_y_axis+by_y_axis+bz_y_axis))))
    # Set the major ticks, maximum 5 ticks
    ax_b.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
    # Draw the horizontal line at each major tick position
    ax_b.yaxis.grid(True, linestyle='-', linewidth=0.5)
    ax_b.set_ylabel('Bmag, Bx, By, Bz [nT]')
    # Fix the legend position to the top right corner
    ax_b.legend(ncol=4, loc='upper right')
    ax_b.set_title(f'DSCOVR mission Magdata records')
    
    # Get the SAO metadata
    sao_script_path = f'{workflow_dir}/get_sao_metadata.py'
    selected_station = station.value
    command = ['python3', sao_script_path, start_datetime, end_datetime, selected_station, characteristics]
    # Execute the script and capture the output
    try:
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        stdout, stderr = process.stdout, process.stderr
        
        if process.returncode != 0:
            error_message['error'] = stderr.decode()
            return JSONResponse(status_code=200, content=error_message)
        
    except subprocess.CalledProcessError as e:
        error_message['error'] = json.loads(e.stdout)
        return JSONResponse(status_code=200, content=error_message)
    # x_axis is 5 minutes interval, from start_datetime to end_datetime
    x_axis = pd.date_range(start_datetime, end_datetime, freq='5min')
    # Check the characteristics, depending which type of characteristics frequency or height, create the y_axis arrays group by type
    freq_y_characteristics = []
    height_y_characteristics = []
    for characteristic in characteristics.split(','):
        if characteristic in FREQ_CHARACTERISTICS:
            freq_y_characteristics.append(characteristic)
        if characteristic in HEIGHT_CHARACTERISTICS:
            height_y_characteristics.append(characteristic)
    
    sao_df = pd.DataFrame()
    try:
        # Need to skip the first line, which is the file name
        sao_df = pd.read_csv(StringIO(stdout), sep=',', header=0, index_col=0, skiprows=1)
        sao_df.index = pd.to_datetime(sao_df.index)
    except Exception as e:
        error_message['error'] = f"Error processing output: {str(e)}"
    sao_df_x_axis = pd.to_datetime(sao_df.index)
    x_axis = pd.to_datetime(x_axis)
    
    # Union the sao_df index with the x_axis, reordering the sao_df_index from earliest to latest
    new_x_axis = x_axis.union(sao_df_x_axis).sort_values()
    # Load the new_sao_df with the cnew sao_df_x_axis, fill the missing value with np.nan
    new_sao_df = sao_df.reindex(new_x_axis).fillna(np.nan)
    # Replace the value in new_sao_df with the value from sao_df with the same index
    new_sao_df = new_sao_df.combine_first(sao_df)
    print(f"New x-axis size: {len(x_axis)} U {len(sao_df_x_axis)} = {len(new_x_axis)}")

    
    # Set the x-axis range from sao_df index min to max, with 1 second interval
    ax_freq.set_xlim(start_datetime_offset, end_datetime_offset)
    ax_height.set_xlim(start_datetime_offset, end_datetime_offset)
    ax_freq.set_ylabel(f'Frequencies [MHz]')
    ax_freq.set_title(f'{selected_station} - Ionospheric characteristics - frequencies: {",".join(freq_y_characteristics)} [MHz]')
    # Hide the x-axis tick labels
    # plt.setp(ax_freq.get_xticklabels(), visible=False)
    ax_height.set_ylabel(f'Heights [km]')
    ax_height.set_title(f'{selected_station} - Ionospheric characteristics - heights: {",".join(height_y_characteristics)} [km]')
    if sao_df.empty==False:
        if len(freq_y_characteristics) > 0:
            # Plot the frequency characteristics
            for characteristic in freq_y_characteristics:
                ax_freq.plot(new_x_axis.values,new_sao_df[characteristic].values,linestyle="",label=characteristic,linewidth=1, color=CHAR_COLORS[characteristic], marker='o', markersize=1, alpha=0.7)
            # Leave some space at the top of the plot, set the bottom of the plot to 0
            ax_freq.set_ylim(bottom=0, top=ax_freq.get_ylim()[1]+10)
            # Add major ticks to the Y-axis, maximum 5 ticks
            ax_freq.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
            # For each locator, include both major and minor ticks, and draw the grid lines
            ax_freq.yaxis.grid(True, linestyle='-', linewidth=0.5)
            # Make the marker in the legend to be bigger
            ax_freq.legend(ncol=len(freq_y_characteristics), loc='upper right', markerscale=2)
            # Display the legend in columns, all columns in one row
            
            
        else:
            ax_freq.text(0.5, 0.5, f"No data available for the selected station ({selected_station}), date period ({start_datetime} - {end_datetime}), and characteristics ({','.join(freq_y_characteristics)})", horizontalalignment='center', verticalalignment='center', transform=ax_freq.transAxes)
        if len(height_y_characteristics) > 0:
            # Plot the height characteristics
            for characteristic in height_y_characteristics:
                ax_height.plot(new_x_axis.values,new_sao_df[characteristic].values,linestyle="",label=characteristic,linewidth=1, color=CHAR_COLORS[characteristic], marker='o', markersize=1, alpha=0.7)
            
            # Leave some space at the top of the plot
            ax_height.set_ylim(top=ax_height.get_ylim()[1]+100)
            # Add major ticks to the Y-axis, maximum 5 ticks
            ax_height.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
            # For each tick, draw a horizontal line
            ax_height.yaxis.grid(True, linestyle='-', linewidth=0.5)
            # Make the marker in the legend to be bigger
            ax_height.legend(ncol=len(height_y_characteristics), loc='upper right', markerscale=2)
        else:
            ax_height.text(0.5, 0.5, f"No data available for the selected station ({selected_station}), date period ({start_datetime} - {end_datetime}), and characteristics ({','.join(height_y_characteristics)})", horizontalalignment='center', verticalalignment='center', transform=ax_height.transAxes)
    else:
        # Add text to the plot, no data available for the selected station, date_of_interest, and characteristics
        ax_freq.text(0.5, 0.5, f"No data available for the selected station ({selected_station}), date period ({start_datetime} - {end_datetime}), and characteristics ({','.join(freq_y_characteristics)})", horizontalalignment='center', verticalalignment='center', transform=ax_freq.transAxes)
        # Add text to the plot, no data available for the selected station, date_of_interest, and characteristics
        ax_height.text(0.5, 0.5, f"No data available for the selected station ({selected_station}), date period ({start_datetime} - {end_datetime}), and characteristics ({','.join(height_y_characteristics)})", horizontalalignment='center', verticalalignment='center', transform=ax_height.transAxes)
    
    plt.tight_layout()
    # Save the plot to a temporary file, png format, filename is station_date_of_interest_characteristics_seperated_by_-.png
    plot_filename = f"{selected_station}_{date_of_interest}_{characteristics.replace(',','-')}.png"
    plt.savefig(f'/tmp/{plot_filename}')
    plt.close()
    # Return the output as a FileResponse
    headers = {
        'Content-Disposition': f'attachment; filename="{plot_filename}"'
    }
    return FileResponse(f"/tmp/{plot_filename}", media_type="image/png", headers=headers)
    
    