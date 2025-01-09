#!/bin/bash

DIR="./data/accounts"
echo -e "Public_key\tRunning_Time"

for file in "$DIR"/*; do
    if [[ -f $file ]]; then
        email=$(awk -F= '/^Public_key=/{print $2}' "$file")
        earnings=$(awk -F= '/^Running_Time=/{print $2}' "$file")
        if [[ -n $email && -n $earnings ]]; then
            echo -e "$email\t$earnings"
        fi
    fi
done