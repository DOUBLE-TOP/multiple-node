#!/bin/bash

DIR="./data/accounts"

# Print the header with nice formatting
echo -e "Public_key\t\t\t\tRunning_Time"
echo -e "-----------------------------------------------------"

# Collect data to create a structured format for column
output=""

for file in "$DIR"/*; do
    if [[ -f $file ]]; then
        email=$(awk -F= '/^Public_key=/{print $2}' "$file")
        earnings=$(awk -F= '/^Running_Time=/{print $2}' "$file")
        if [[ -n $email && -n $earnings ]]; then
            output+="$email\t$earnings\n"
        fi
    fi
done

# Use column to format the output and sort by Total_Earnings
echo -e "$output" | sort -k2,2n | column -t -s $'\t'