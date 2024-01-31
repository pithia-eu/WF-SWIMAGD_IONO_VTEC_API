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

class OutputFormat(str, Enum):
    csv = "csv"
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
    'b0IRI': 'red',
    'fbEs': 'blue',
    'ff': 'green',
    'foE': 'orange',
    'foEs': 'purple',
    'foF2': 'brown',
    'hE': 'pink',
    'hEs': 'gray',
    'hF2': 'olive',
    'mufD': 'cyan',
    'phF2lyr': 'magenta',
    'scHgtF2pk': 'yellow'
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
            "description": "Run the SWIMAGD_IONO workflow and Download the compress results (KP data, B data, and SAO metadata) in either csv, ZIP or JSON format."
        },
        {
            "name": "Plot Data",
            "description": "Plot the KP data, B data, and SAO metadata for selected station"
        }
    ],
    title="SWIMAGD_IONO Workflow API",
    description="The SWIMAGD_IONO workflow provides: <br /><br />(a) Planetary 3-hour-range (T00:00:00, T03:00:00, …, T21:00:00) Kp-index; <br />(b) DSCOVR mission Magdata records (Bmag, Bx, By, Bz) as part of the SWIF model Data Collection; <br />(c) Distinct ionospheric characteristics (SAO records) for 10 European Digisonde stations (AT138, EA036, EB040, DB049, JR055, PQ052, RL052, RO041, SO148, TR170).",
    version="1.1.0",
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
async def run_workflow(start_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2023-01-01T00:00:00 "), end_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2023-01-01T00:00:00"), stations: str = Query(..., description=f"Comma-separated list of stations, e.g. AT138,DB049. Full list of valid stations: {SORTED_VALID_STATIONS}"), characteristics: str = Query(..., description=f"Comma-separated list of characteristics, e.g. foF2,foE. Full list of valid characteristics: b0IRI,fbEs,ff,foE,foEs,foF2,hE,hEs,hF2,mufD,phF2lyr,scHgtF2pk, where phF2ly=hmF2."),format: OutputFormat = Query(..., description="The format of the output file. Valid values are 'csv', 'zip' and 'json'.")):
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
    
    if format == OutputFormat.csv:
        # Merge all the data into 1 csv file, which is order by timmestamp, the header could be timestamp, kp, bmag, bx, by, bz, station1, characteristic1, characteristic2, station2, characteristic1, characteristic2 ... We can get the row timestamp from the first station file, and search the timestamp in the other files, if the timestamp is not in the file, we can fill the value with empty string
        null_value = "9999"
        csv_header = ['Kp', 'bmag', 'bx', 'by', 'bz']
        for station in stations.split(','):
            if format != OutputFormat.csv:
                csv_header.append(station+'_station')
            for characteristic in characteristics.split(','):
                csv_header.append(station+'_'+characteristic)
        # Create a dataframe with the header, and set timestamp as index, timestamp is build from start_datetime to end_datetime with 5 minutes interval
        start_datetime = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M:%S')
        end_datetime = datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M:%S')
        index = pd.date_range(start_datetime, end_datetime, freq='5min')
        index = index.strftime('%Y-%m-%dT%H:%M:%S')
        df = pd.DataFrame(columns=csv_header, index=index)
        # Give the index a name
        df.index.name = 'timestamp'
        # Fill the dataframe with data
        # Fill the KP data
        kp_df = pd.read_csv(kp_file, sep=',', header=0, index_col=0)
        kp_df.index = pd.to_datetime(kp_df.index).strftime('%Y-%m-%dT%H:%M:%S')
        # Fill the KP data if have the timestamp in the dataframe, or fill the empty string
        # The KP data is 3-hour-range (T00:00:00, T03:00:00, ... , T21:00:00), so we need to get the timestamp with the format YYYY-MM-DDTHH:MM:SS
        for timestamp in kp_df.index:
            if timestamp in df.index:
                df.loc[timestamp, 'Kp'] = kp_df.loc[timestamp, 'Kp']
        
        # Fill the BMAG data
        bmag_df = pd.read_csv(bmag_file, sep=',', header=0, index_col=0)
        bmag_df.index = pd.to_datetime(bmag_df.index).strftime('%Y-%m-%dT%H:%M:%S')
        # The bmag data is 1-hour-range (T00:00:00, T01:00:00, ... , T23:00:00), so we need to get the timestamp with the format YYYY-MM-DDTHH:MM:SS
        for timestamp in bmag_df.index:
            if timestamp in df.index:
                df.loc[timestamp, 'bmag'] = bmag_df.loc[timestamp, 'bmag']
                df.loc[timestamp, 'bx'] = bmag_df.loc[timestamp, 'bx']
                df.loc[timestamp, 'by'] = bmag_df.loc[timestamp, 'by']
                df.loc[timestamp, 'bz'] = bmag_df.loc[timestamp, 'bz']
        remaining_stations = stations.split(',')
        # Fill the SAO metadata
        for filename, file in station_files.items():
            file.seek(0)
            # Only get the station name from the filename
            station = filename.split('_')[0]
            sao_df = pd.read_csv(file, sep=',', header=0, index_col=0, usecols=lambda column: column != 'station')
            sao_df.index = pd.to_datetime(sao_df.index).strftime('%Y-%m-%dT%H:%M:%S')
            for timestamp in df.index:
                if timestamp in sao_df.index:
                    if format != OutputFormat.csv:
                        df.loc[timestamp, station+'_station'] = station
                    for characteristic in sao_df.columns:
                        # if the value is not empty, fill the value to the dataframe. or fill with 9999
                        df.loc[timestamp, station+'_'+characteristic] = sao_df.loc[timestamp, characteristic] if pd.notnull(sao_df.loc[timestamp, characteristic]) else null_value
                else:
                    if format != OutputFormat.csv:
                        df.loc[timestamp, station+'_station'] = station
                    for characteristic in characteristics.split(','):
                        df.loc[timestamp, station+'_'+characteristic] = null_value
            # Remove the station from the remaining_stations
            remaining_stations.remove(station)
        # Fill the remaining stations with 9999
        for station in remaining_stations:
            for timestamp in df.index:
                if format != OutputFormat.csv:
                    df.loc[timestamp, station+'_station'] = station
                for characteristic in characteristics.split(','):
                    df.loc[timestamp, station+'_'+characteristic] = null_value
        # Fill the empty values with empty string
        df.fillna('', inplace=True)
        # Convert the dataframe to csv
        csv_file = StringIO(df.to_csv())
        csv_file.seek(0)
        # Return the output as a FileResponse
        filename = f"SWIMAGD_IONO_Workflow_{start_datetime}_{end_datetime}_{stations.replace(',','_')}.csv"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/csv'
        }
        # save the csv file to a temporary file
        temp_csv_file = tempfile.NamedTemporaryFile(delete=False)
        temp_csv_file.write(csv_file.getvalue().encode())
        temp_csv_file.close()
        # Use FileResponse to return the csv file
        return FileResponse(temp_csv_file.name, media_type="text/csv", headers=headers)
    
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
@app.get("/plot_data/", response_class=StreamingResponse, summary="Plot the KP data, B data, and SAO metadata for selected station.", description="Plot the KP data, BMAG data, and SAO metadata.", tags=["Plot Data"])
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
    x_axis = pd.date_range(start_datetime, end_datetime, freq='3H')
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

    # Plot the KP data using bar chart, skip the timestamp with 0 value
    ax_kp.bar(x_axis, kp_y_axis, width=0.04, color='blue', label='Kp')
    # Set the kp y-axis range from min to max of kp_y_axis offset by 0.5
    ax_kp.set_ylim(min(kp_y_axis)-0.5, max(kp_y_axis)+0.5)
    ax_kp.set_ylabel('Kp-index')
    ax_kp.set_title(f'Planetary 3-hour-range Kp-index')
    # Add the legend at the bottom
    # ax_kp.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=4)
    # Hide the x-axis tick labels
    plt.setp(ax_kp.get_xticklabels(), visible=False)
    
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
        error_message['error'] = json.loads(e.stdout)
        return JSONResponse(status_code=200, content=error_message)
    # 1 hour range BMAG data, so we need to get the timestamp with the format YYYY-MM-DDTHH:MM:SS
    x_axis = pd.date_range(start_datetime, end_datetime, freq='1H')
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
    # Set the bmag y-axis range from min to max of all bmag_y_axis, bx_y_axis, by_y_axis, bz_y_axis offset by 1
    ax_b.set_ylim(min(bmag_y_axis+bx_y_axis+by_y_axis+bz_y_axis)-2, max(bmag_y_axis+bx_y_axis+by_y_axis+bz_y_axis)+2)
    # Plot the 0 line for y-axis, grey color, linewidth 0.5
    ax_b.axhline(y=0, color='grey', linewidth=0.5, linestyle='--')
    ax_b.set_ylabel('Bmag, Bx, By, Bz [nT]')
    ax_b.set_title(f'DSCOVR mission Magdata records')
    # Add the legend
    ax_b.legend(ncol=4)
    # Hide the x-axis tick labels
    plt.setp(ax_b.get_xticklabels(), visible=False)
    
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
    # x_axis is 5 minutes interval
    x_axis = pd.date_range(start_datetime, end_datetime, freq='5min')
    # Check the characteristics, depending which type of characteristics frequency or height, create the y_axis arrays group by type
    freq_y_axis = {}
    height_y_axis = {}
    freq_y_characteristics = []
    height_y_characteristics = []
    for characteristic in characteristics.split(','):
        if characteristic in FREQ_CHARACTERISTICS:
            freq_y_axis[characteristic] = []
            freq_y_characteristics.append(characteristic)
        if characteristic in HEIGHT_CHARACTERISTICS:
            height_y_axis[characteristic] = []
            height_y_characteristics.append(characteristic)
    print(freq_y_axis, height_y_axis)
    
    sao_df = pd.DataFrame()
    try:
        # Need to skip the first line, which is the file name
        sao_df = pd.read_csv(StringIO(stdout), sep=',', header=0, index_col=0, skiprows=1)
        sao_df.index = pd.to_datetime(sao_df.index).strftime('%Y-%m-%dT%H:%M:%S')
        
        # Fill the y_axis arrays with the sao_df data, if the timestamp is not in the x_axis, fill the value with 0
        for timestamp in x_axis.strftime('%Y-%m-%dT%H:%M:%S'):
            if timestamp in sao_df.index:
                for characteristic in characteristics.split(','):
                    if characteristic in FREQ_CHARACTERISTICS:
                        freq_y_axis[characteristic].append(sao_df.loc[timestamp, characteristic] if pd.notnull(sao_df.loc[timestamp, characteristic]) else float('nan'))
                    if characteristic in HEIGHT_CHARACTERISTICS:
                        height_y_axis[characteristic].append(sao_df.loc[timestamp, characteristic] if pd.notnull(sao_df.loc[timestamp, characteristic]) else float('nan'))
            else:
                for characteristic in characteristics.split(','):
                    if characteristic in FREQ_CHARACTERISTICS:
                        freq_y_axis[characteristic].append(0)
                    if characteristic in HEIGHT_CHARACTERISTICS:
                        height_y_axis[characteristic].append(0)
    except Exception as e:
        error_message['error'] = f"Error processing output: {str(e)}"
    ax_freq.set_ylabel(f'Frequencies [MHz]')
    ax_freq.set_title(f'{selected_station} - Ionospheric characteristics - frequencies: {",".join(freq_y_characteristics)} [MHz]')
    # Hide the x-axis tick labels
    plt.setp(ax_freq.get_xticklabels(), visible=False)
    ax_height.set_ylabel(f'Heights [km]')
    ax_height.set_title(f'{selected_station} - Ionospheric characteristics - heights: {",".join(height_y_characteristics)} [km]')
    # Show the x-axis tick lables, and reformat the timestamp to show as 1 Jan 2024 00:00:00
    ax_height.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y %H:%M:%S'))
    if sao_df.empty==False:
        if len(freq_y_characteristics) > 0:
        # Plot the frequency characteristics
            for characteristic in freq_y_characteristics:
                ax_freq.plot(x_axis, freq_y_axis[characteristic], label=characteristic, linestyle='-', linewidth=2, color=CHAR_COLORS[characteristic])
            # Place the legend at the Top Right corner
            ax_freq.legend(ncol=len(freq_y_characteristics), loc='upper right')
            # Leave some space at the top of the plot
            ax_freq.set_ylim(top=ax_freq.get_ylim()[1]+10)
            
        else:
            ax_freq.text(0.5, 0.5, f"No data available for the selected station ({selected_station}), date period ({start_datetime} - {end_datetime}), and characteristics ({','.join(freq_y_characteristics)})", horizontalalignment='center', verticalalignment='center', transform=ax_freq.transAxes)
        if len(height_y_characteristics) > 0:
            # Plot the height characteristics
            for characteristic in height_y_characteristics:
                ax_height.plot(x_axis, height_y_axis[characteristic], label=characteristic, linestyle='-', linewidth=2, color=CHAR_COLORS[characteristic])
            ax_height.legend(ncol=len(height_y_characteristics), loc='upper right')
            # Leave some space at the top of the plot
            ax_height.set_ylim(top=ax_height.get_ylim()[1]+100)
        else:
            ax_height.text(0.5, 0.5, f"No data available for the selected station ({selected_station}), date period ({start_datetime} - {end_datetime}), and characteristics ({','.join(height_y_characteristics)})", horizontalalignment='center', verticalalignment='center', transform=ax_height.transAxes)
    else:
        # Add text to the plot, no data available for the selected station, date_of_interest, and characteristics
        ax_freq.text(0.5, 0.5, f"No data available for the selected station ({selected_station}), date period ({start_datetime} - {end_datetime}), and characteristics ({','.join(freq_y_characteristics)})", horizontalalignment='center', verticalalignment='center', transform=ax_freq.transAxes)
        # Add text to the plot, no data available for the selected station, date_of_interest, and characteristics
        ax_height.text(0.5, 0.5, f"No data available for the selected station ({selected_station}), date period ({start_datetime} - {end_datetime}), and characteristics ({','.join(height_y_characteristics)})", horizontalalignment='center', verticalalignment='center', transform=ax_height.transAxes)
    
    plt.tight_layout()
    # Save the plot to a temporary file, use uuid as the filename, png format
    plot_filename = str(uuid.uuid4())+'.png'
    plt.savefig(f'/tmp/{plot_filename}')
    plt.close()
    # Return the output as a FileResponse
    headers = {
        'Content-Disposition': f'attachment; filename="{plot_filename}"'
    }
    return FileResponse(f"/tmp/{plot_filename}", media_type="image/png", headers=headers)
    
    