import tempfile
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

class OutputFormat(str, Enum):
    csv = "csv"
    zip = "zip"
    json = "json"
    
    
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
            "description": "Run the SWIMAGD_IONO workflow and Download the compress results (KP data, BMAG data, and SAO metadata) in either csv, ZIP or JSON format."
        },
    ],
    title="SWIMAGD_IONO Workflow API",
    description="A REST API for running the SWIMAGD_IONO (SOLAR WIND MAGNETOSPHERE DRIVEN IONOSPHERIC RESPONSE) Workflow scripts.<br /><br />"+"This is a workflow with three Data Collections: <br />(a) ActivityIndicator: Collection of Kp, ap, and Ap indices by GFZ, with F10.7 from DRAO and Sn from WSC SILSO, <br />(b) SWIF Model, and <br />(c) European Ionosonde Network DIAS (European Digital upper Atmosphere Server) collection. <br /><br />More specifically, the SWIMAGD_IONO workflow provides: <br />(a) planetary 3-hour-range (T00:00:00, T03:00:00, ... , T21:00:00) index Kp, <br />(b) DSCOVR mission Magdata records (Bmag, Bx, By, Bz)), and <br />(c) distinct ionospheric characteristics (SAO records) for 10 European Digisonde stations (AT138, EB040, RO041, RL052, PQ052, JR055, EA036, DB049, SO148, TR170).",
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
@app.get("/run_workflow/", response_class=StreamingResponse, responses={200: {"content": {"application/octet-stream": {}},"description": "**Important:** When selecting the 'zip' format, please remember to rename the downloaded file to have the extension '*.zip' before opening it.\n\n",}},summary="Run the SWIMAGD_IONO workflow.", description="Return KP data, BMAG data, and SAO metadata, and optionally compress the results into a single ZIP file or receive them in JSON format.\n\n"+"**Important:** When selecting the 'zip' format, please remember to rename the downloaded file to have the extension '*.zip' before opening it.\n\n", tags=["Run Workflow"])
async def run_workflow(start_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2023-01-01T00:00:00 "), end_datetime: str = Query(..., description="Datetime in the format 'YYYY-MM-DDTHH:MM:SS', e.g. 2023-01-01T00:00:00"), stations: str = Query(..., description=f"Comma-separated list of stations, e.g. AT138,DB049. Full list of valid stations: {SORTED_VALID_STATIONS}"), characteristics: str = Query(..., description=f"Comma-separated list of characteristics, e.g. foF2,foE. Full list of valid characteristics: {SORTED_VALID_CHARACTERISTICS}"),format: OutputFormat = Query(..., description="The format of the output file. Valid values are 'csv', 'zip' and 'json'.")):
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
        csv_header = ['Kp', 'bmag', 'bx', 'by', 'bz']
        for station in stations.split(','):
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
        # Fill the SAO metadata
        for filename, file in station_files.items():
            file.seek(0)
            # Only get the station name from the filename
            station = filename.split('_')[0]
            sao_df = pd.read_csv(file, sep=',', header=0, index_col=0, usecols=lambda column: column != 'station')
            sao_df.index = pd.to_datetime(sao_df.index).strftime('%Y-%m-%dT%H:%M:%S')
            for timestamp in sao_df.index:
                if timestamp in df.index:
                    df.loc[timestamp, station+'_station'] = station
                    for characteristic in sao_df.columns:
                        df.loc[timestamp, station+'_'+characteristic] = sao_df.loc[timestamp, characteristic]
        # Fill the empty values with empty string
        df.fillna('', inplace=True)
        # Convert the dataframe to csv
        csv_file = StringIO(df.to_csv())
        csv_file.seek(0)
        if format == OutputFormat.csv:
            # Return the output as a streaming response
            headers = {
                'Content-Disposition': f'attachment; filename="SWIMAGD_IONO_Workflow_{start_datetime}_{end_datetime}.csv"',
                'Content-Type': 'text/csv'
            }
            return StreamingResponse(iter([csv_file.getvalue()]), headers=headers)
    
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
    