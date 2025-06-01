#!/bin/bash

# Check for patch argument
if [ -z "$1" ]; then
  echo "Usage: $0 <patch>"
  exit 1
fi

# if [ -z "$2" ]; then
#   echo "Usage: $0 <patch> <pob-tag>"
#   exit 1
# fi

# accepts patch like 3.25.0 as arg 1
PATCH=$1
# POB_TAG=$2

# if data/patch doesn't exist, make those dirs
if ! [ -d "./data/" ]; then
    mkdir "./data"
fi

if ! [ -d "./data/$PATCH" ]; then
    mkdir "./app/data/$PATCH"
fi

# get the tree data from ggg if we don't have it already
if ! [ -f "./data/$PATCH/data.json" ]; then
    curl -L -o "./data/$PATCH/data.json" "https://raw.githubusercontent.com/grindinggear/skilltree-export/$PATCH.0/data.json"
fi

for jewel_type in BrutalRestraint MilitantFaith LethalPride ElegantHubris
do
    if ! [ -f "./data/$PATCH/$jewel_type" ]; then
        curl -L -o "./data/$PATCH/$jewel_type" "https://raw.githubusercontent.com/Regisle/TimelessJewelData/main/Data/$jewel_type"
    fi
done

# GV needs to be unzipped
if ! [ -f "./data/$PATCH/GloriousVanity" ]; then
    curl -L -o "./data/$PATCH/GloriousVanity.zip" "https://raw.githubusercontent.com/Regisle/TimelessJewelData/main/Data/GloriousVanity.zip" && pigz -z -d "./app/data/$PATCH/GloriousVanity.zip"
fi

# node_indices.csv
if ! [ -f "./data/$PATCH/node_indices.csv" ]; then
    curl -L -o "./data/$PATCH/node_indices.csv" "https://raw.githubusercontent.com/Regisle/TimelessJewelData/main/Data/node_indices.csv"
fi

# files that we convert from lua
if ! [ -f "./data/$PATCH/LegionPassives.json" ]; then
    # if not, get from the pob repo and then convert it from lua
    curl -L -o "./data/$PATCH/LegionPassives.lua" "https://raw.githubusercontent.com/PathOfBuildingCommunity/PathOfBuilding/master/src/Data/TimelessJewelData/LegionPassives.lua" && lua5.3 convert.lua "./app/data/$PATCH/LegionPassives" && rm "./app/data/$PATCH/LegionPassives.lua"
fi

echo "Starting poll.py..."
# ./venv/bin/python3 poll.py

# TODO all of this needs to be done while considering user and umask stuff
# btw curl can fail to download these and I think it would really behoove me to do some error handling