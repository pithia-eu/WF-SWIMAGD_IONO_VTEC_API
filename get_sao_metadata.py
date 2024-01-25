import os,sys
import uuid
import ciso8601
import httpx
import io
import orjson
import pandas as pd
from datetime import timedelta

BASE_URL = 'https://electron.space.noa.gr/ionostream/api/v2/'
# Define the set of valid stations and characteristics
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

def print_error_and_exit(error_message):
    """Prints the error message in JSON format and exits."""
    print(f'{{"error":"{error_message}"}}')
    sys.exit(1)

def validate_arguments(stations, characteristics):
    # Check if provided stations and characteristics are valid
    if not set(stations).issubset(VALID_STATIONS):
        print_error_and_exit(f'One or more stations are invalid. Here is the list of valid stations: {VALID_STATIONS}')
    if not set(characteristics).issubset(VALID_CHARACTERISTICS):
        print_error_and_exit(f'One or more characteristics are invalid. Here is the list of valid characteristics: {VALID_CHARACTERISTICS}')

def getdf(client, endpoint, params=None, headers=None):
    resp = None
    content_type = None
    try:
        with io.BytesIO() as bf:
            with client.stream('GET', endpoint, headers=headers, params=params) as r:
                headers_ = dict(r.headers.raw)
                total = int(headers_[b"content-length"])
                content_type = headers_[b"content-type"].decode('utf-8')
                isocstream = bool(content_type == 'application/octet-stream')
                for chunk in r.iter_bytes():
                    bf.write(chunk)
                    num_bytes_downloaded = r.num_bytes_downloaded
            bf.seek(0)
            if isocstream:
                resp = pd.read_parquet(bf, engine='pyarrow')
            else:
                resp = bf.getvalue()

            if isocstream:
                resp['id'] = resp['id'].apply(lambda _: uuid.UUID(_))
            else:
                resp = orjson.loads(resp.decode('utf-8'))
    except httpx.ConnectError as e:
        print_error_and_exit(f'Upon request Connection Error: {e}')
        raise e
    except httpx.ConnectTimeout as e:
        print_error_and_exit(f'Upon request Connection Timeout: {e}')
    except httpx.ReadTimeout as e:
        print_error_and_exit(f'Upon request Read Timeout: {e}')
    except Exception as e:
        print_error_and_exit(f'Unable to complete API request: {e}')

    return resp


def request(params, stations, characteristics):
    client = None
    try:
        client = httpx.Client(
            transport=httpx.HTTPTransport(retries=3), base_url=BASE_URL,
            headers=None, params=None, timeout=httpx.Timeout(30, read=30)
        )
        df = getdf(client, '/idb/saodf', params=params)
        df_grouped = df.groupby('ursi_code')
        # Generate the zip file name
        # Format the timestamp to the '%Y-%m-%dT%H:%M:%S' format
        for station, group in df_grouped:
            # Genearate the filename
            # Format the timestamp to the '%Y-%m-%dT%H:%M:%S' format
            filename = f"station_csv_filename:'{station}_{params[0][1].strftime('%Y-%m-%dT%H:%M:%S')}_{params[1][1].strftime('%Y-%m-%dT%H:%M:%S')}.csv'"
            print(filename)
            header_to_print = ['timestamp,station']
            header_to_print.extend(f',{char}' for char in characteristics)
            # Combine the headers into a single string, and remove empty spaces
            header_to_print = ''.join(header_to_print).replace(' ', '')
            print(header_to_print)
            for index, row in group.iterrows():
                data_to_print = [row['timestamp'].strftime('%Y-%m-%dT%H:%M:%S'), ',',row['ursi_code']]
                data_to_print.extend(f',{row[char]}' for char in characteristics if char in row)
                # Combine the data into a single string, and remove empty spaces
                data_to_print = ''.join(data_to_print).replace(' ', '')
                print(data_to_print)
            print()
    except Exception as e:
        print_error_and_exit(f'Unable to connect to API: {e}')
    finally:
        try:
            client.close()
        except:
            pass


def main(argv):
    if len(argv) < 4:
        print_error_and_exit("Usage: get_sao_metadata.py start_datetime end_datetime station1,station2 characteristic1,characteristic2")
    try:
        # Try to parse the start and end dates using the ciso8601 library
        start = ciso8601.parse_datetime(argv[1])
        end = ciso8601.parse_datetime(argv[2])

        # Check if the dates are in the correct format and valid
        if not (start and end):
            print_error_and_exit("The provided dates are not in the correct format or are invalid.")

        # Check the difference between the dates
        if (end - start) >= timedelta(days=365):
            print_error_and_exit("The difference between start and end dates must be less than 365 days.")
        
        stations = argv[3].split(',')  # Split comma-separated stations
        characteristics = argv[4].split(',')  # Split comma-separated characteristics
        
        # Validate the stations and characteristics
        validate_arguments(stations, characteristics)
        
        # Create the params list
        params = [
            ('start', start),
            ('end', end),
        ]
        # Add stations to params
        for station in stations:
            params.append(('stations', station))
        # Add characteristics to params
        for characteristic in characteristics:
            params.append(('characteristics', characteristic))
        # Add ordering attributes
        params.extend([
            ('order_attrs', 'station'),
            ('order_attrs', 'timestamp'),
            ('order_by', 'asc')
        ])

        # Call the request function and print the results
        request(params, stations, characteristics)

    except ValueError as e:
        print_error_and_exit(str(e))


if __name__ == '__main__':
    sys.exit(main(sys.argv))
