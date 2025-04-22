#!/bin/bash

# Script to run the gim2vtec.v2b.scr command inside the Docker container

# Check if correct number of arguments is provided
if [ "$#" -ne 3 ]; then
    echo '{"status": "error", "message": "Usage: ./run_vtec.sh <start_date: YYYY-MM-DDTHH:MM:SS> <end_date: YYYY-MM-DDTHH:MM:SS> <station_id>"}'
    exit 1
fi

# Input parameters
START_DATETIME=$1
END_DATETIME=$2
STATION_PARAM=$3

# Extract date components using `cut`
START_YEAR=$(echo $START_DATETIME | cut -d'-' -f1)
START_MONTH=$(echo $START_DATETIME | cut -d'-' -f2)
START_DAY=$(echo $START_DATETIME | cut -d'-' -f3 | cut -d'T' -f1)

END_YEAR=$(echo $END_DATETIME | cut -d'-' -f1)
END_MONTH=$(echo $END_DATETIME | cut -d'-' -f2)
END_DAY=$(echo $END_DATETIME | cut -d'-' -f3 | cut -d'T' -f1)

# Other fixed variables
IMAGE_NAME="ionsat/tools-v5"
SCRIPT_PATH="./w/bin/gim2vtec.v2b.scr"
OUTPUT_DIR="VTECvsTIME"
CODE="uqrg"
SOME_VALUE=120
EXECUTION_PATH="$START_YEAR$START_MONTH$START_DAY-$END_YEAR$END_MONTH$END_DAY-$STATION_PARAM"
SINGLE_CHAR="n"
DESCRIPTION="VTECvsTIME_extraction"


# Path to the output directory
TARGET_PATH="./target/$EXECUTION_PATH/VTECvsTIME_from_GIM.$CODE.$SOME_VALUE"

EXT=".$STATION_PARAM"

# Find any .at13 file in the output directory
FILE=$(find "$TARGET_PATH" -type f -name "*$EXT" | head -n 1)
if [ -n "$FILE" ]; then
    echo "{\"status\": \"success\", \"message\": \"Output file already exists\", \"file\": \"$FILE\"}"
    exit 0
fi

# Run Docker with mounted volume and the command
DOCKER_OUTPUT=$(docker run --mount type=bind,source="$(pwd)"/target,target=/root/run \
    $IMAGE_NAME \
    $SCRIPT_PATH \
    $OUTPUT_DIR \
    $START_YEAR $START_MONTH $START_DAY \
    $END_YEAR $END_MONTH $END_DAY \
    $CODE $SOME_VALUE \
    run/$EXECUTION_PATH $SINGLE_CHAR \
    $DESCRIPTION $STATION_PARAM 2>&1)

# Find any .at13 file in the output directory
FILE=$(find "$TARGET_PATH" -type f -name "*$EXT" | head -n 1)

if [ -n "$FILE" ]; then
    echo "{\"status\": \"success\", \"message\": \"Output file created successfully\", \"file\": \"$FILE\"}"
else
    echo "{\"status\": \"error\", \"message\": \"$DOCKER_OUTPUT\"}"
fi