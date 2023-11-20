#!/bin/bash

# Usage: ./get_kp_data.sh start_date end_date format
# Example: ./get_kp_data.sh 2023-11-06 2023-11-07 txt
# Output Result Path: ./output/kp_index
# Output Result Name: ${start_date}_to_${end_date}.${output_format}
# Output Formats: [print, txt, json]

# Read start and end dates from the input parameters
start_date=$(date -d "$1" +%Y%m%d)
end_date=$(date -d "$2" +%Y%m%d)
output_format=$3

# Function to validate date format
validate_date() {
    if [[ $1 =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        # Check if the date is valid
        date -d "$1" > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo "Error: The date format is correct, but the date is invalid." >&2
            exit 1
        fi
    else
        echo "Error: The date format is invalid. Please use YYYY-MM-DDTHH:MM:SS." >&2
        exit 1
    fi
}

# Function to validate output type
validate_output_type() {
    if [[ ! $1 =~ ^(print|txt|json)$ ]]; then
        echo "Error: Output type must be 'txt' or 'json'." >&2
        exit 1
    fi
}

# Validate start date
validate_date "$1"

# Validate end date
validate_date "$2"

# Validate output type
validate_output_type "$3"

# The URL of the dataset
DATA_URL="https://kp.gfz-potsdam.de/app/files/Kp_ap_Ap_SN_F107_since_1932.txt"

# Local file path relative to the script's directory
LOCAL_FILE_PATH="$(dirname "$0")/dataset/Kp_ap_Ap_SN_F107_since_1932.txt"

# Output file path relative to the script's directory
OUTPUT_DIR="$(dirname "$0")/output/kp_index"
OUTPUT_FILE="$OUTPUT_DIR/"$1"_to_"$2".$output_format"

# Create output directory if it does not exist
mkdir -p "$OUTPUT_DIR"

# Function to filter lines based on the date range and print each Kp value with a timestamp
filter_data() {
    if [ "$output_format" == "print" ]; then
	# Filtering data and print to the screen
        echo "--------Kp Index---------"
	echo "UTC ISO TS          Kp"
        awk -v start="$start_date" -v end="$end_date" '
        BEGIN { FS = " "; }
        {
            # Format the date from the file as YYYYMMDD
            current_date = $1 $2 $3;
            gsub("-", "", current_date);
            if (current_date >= start && current_date <= end) {
                for (i = 1; i <= 8; i++) {
                    printf("%s-%s-%sT%02d:00:00 %s\n", $1, $2, $3, (i-1)*3, $(7+i));
                }
            }
        }' "$LOCAL_FILE_PATH"
    elif [ "$output_format" == "txt" ]; then
        # Filtering data and outputting as text
        awk -v start="$start_date" -v end="$end_date" '
        BEGIN { FS = " "; }
        {
            # Format the date from the file as YYYYMMDD
            current_date = $1 $2 $3;
            gsub("-", "", current_date);
            if (current_date >= start && current_date <= end) {
                for (i = 1; i <= 8; i++) {
                    printf("%s-%s-%sT%02d:00:00 %s\n", $1, $2, $3, (i-1)*3, $(7+i));
                }
            }
        }' "$LOCAL_FILE_PATH" > "$OUTPUT_FILE"
    elif [ "$output_format" == "json" ]; then
        # Start JSON array
        echo "{\"start\":\"$1\", \"end\":\"$2\", \"results\":[" > "$OUTPUT_FILE"
        # Filtering data and appending to JSON array
        awk -v start="$start_date" -v end="$end_date" '
        BEGIN { FS = " "; ORS = ""; first = 1; }
        {
            # Format the date from the file as YYYYMMDD
            current_date = $1 $2 $3;
            gsub("-", "", current_date);
            if (current_date >= start && current_date <= end) {
                for (i = 1; i <= 8; i++) {
                    if (!first) print ",";
                    print "{\"timestamp\":\"" $1 "-" $2 "-" $3 "T" sprintf("%02d", (i-1)*3) ":00:00\",\"value\":\"" $(7+i) "\"}";
                    first = 0;
                }
            }
        }' "$LOCAL_FILE_PATH" >> "$OUTPUT_FILE"
        # End JSON array
        echo "]}" >> "$OUTPUT_FILE"
    else
        echo "Unknown output format: $output_format"
        exit 1
    fi
}

# Function to download the file
download_file() {
    # echo "Downloading the latest dataset..."
    curl -o "$LOCAL_FILE_PATH" "$DATA_URL"
}

# Check if the local file exists
if [ -f "$LOCAL_FILE_PATH" ]; then
    # Get the size of the local file
    LOCAL_SIZE=$(stat -c %s "$LOCAL_FILE_PATH")

    # Get the size of the remote file
    REMOTE_SIZE=$(curl -sI "$DATA_URL" | grep -i Content-Length | awk '{print $2}' | tr -d '\r')

    # Compare the local and remote file sizes
    if [ "$REMOTE_SIZE" != "$LOCAL_SIZE" ]; then
        download_file
    fi
else
    # The local file doesn't exist, so download it
    download_file
fi

# Call the function to filter the data based on the date range
filter_data "$start_date" "$end_date"
if [ "$output_format" != "print" ]; then
    echo "Data filtered and stored in $OUTPUT_FILE"
fi
