import os,sys
import uuid
import ciso8601
import httpx
import io
import orjson
import pandas as pd
from datetime import timedelta

BASE_URL = 'https://electron.space.noa.gr/swif/api/v2/'


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
        print(f'Upon request Connection Error: {e}')
        raise e
    except httpx.ConnectTimeout as e:
        print(f'Upon request Connection Timeout: {e}')
        raise e
    except httpx.ReadTimeout as e:
        print(f'Upon request Read Timeout: {e}')
        raise e
    except Exception as e:
        print(f'C Unable to complete API request {e}')
        raise httpx.RequestError(e.__str__())

    return resp


def request(start, end):
    client = None
    csv = None
    try:
        client = httpx.Client(
            transport=httpx.HTTPTransport(retries=3), base_url=BASE_URL,
            headers=None, params=None, timeout=httpx.Timeout(30, read=30)
        )
        df = getdf(client, '/swifdb/solardb/magdata_df', params=dict(start=start, end=end))
        df = df[['timestamp', 'bmag', 'bx', 'by', 'bz']]
        print("--------Bmag Index---------")
        print("UTC ISO TS          Bmag    Bx      By      Bz")
        for index, row in df.iterrows():
            timestamp = row['timestamp'].strftime('%Y-%m-%dT%H:%M:%S') if pd.notnull(row['timestamp']) else 'NaN'
            
            # Check and round each value if it's not NaN
            bmag = round(row['bmag'], 3) if pd.notnull(row['bmag']) else 'NaN'
            bx = round(row['bx'], 3) if pd.notnull(row['bx']) else 'NaN'
            by = round(row['by'], 3) if pd.notnull(row['by']) else 'NaN'
            bz = round(row['bz'], 3) if pd.notnull(row['bz']) else 'NaN'

            print(timestamp, bmag, bx, by, bz)
    except Exception as e:
        print(f'Unable to connect to API {e}')
        raise httpx.RequestError(e.__str__())
    finally:
        try:
            client.close()
        except:
            pass

    return csv


def main(argv):
    if len(argv) < 3:
        print("Usage: get_bmag_data.py start_datetime end_datetime")
        return
    try:
        # Try to parse the start and end dates using the ciso8601 library
        start = ciso8601.parse_datetime(argv[1])
        end = ciso8601.parse_datetime(argv[2])

        # Check if the dates are in the correct format and valid
        if not (start and end):
            raise ValueError("The provided dates are not in the correct format or are invalid.")

        # Check the difference between the dates
        if (end - start) >= timedelta(days=365):
            raise ValueError("The difference between start and end dates must be less than 365 days.")

        # Call the request function and print the results
        request(start.isoformat(), end.isoformat())

    except ValueError as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    # INPUT1: start datetime, INPUT2: end datetime
    # Read start and end dates from the input parameters
    # Example: python get_bmag_data.py 2021-01-01T00:00:00 2021-01-02T00:00:00
    # start = ciso8601.parse_datetime(sys.argv[1])
    # end = ciso8601.parse_datetime(sys.argv[2])
    # OUTPUT: print the results: UTC ISO TS, Bmag, Bx, By, Bz
    sys.exit(main(sys.argv))