#!/usr/bin/env bash
set -euo pipefail

files=(
    "BrutalRestraint.zip"
    "ElegantHubris.zip"
    "HeroicTragedy.zip"
    "LethalPride.zip"
    "MilitantFaith.zip"
)

for file in "${files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "Skipping '$file' (not found)"
        continue
    fi

    outfile="${file%.zip}"

    echo "Decompressing '$file' -> '$outfile'..."
    pigz -d -z < "$file" > "$outfile"

    echo "Deleting '$file'..."
    rm -f "$file"
done

# Multipart archives (prefixes only, without the .partN suffix).
multipart_prefixes=(
#    "GloriousVanity.zip"
    "AbyssAmanamu.zip"
    "AbyssKurgal.zip"
    "AbyssTecrod.zip"
    "AbyssUlaman.zip"
    "AbyssZorath.zip"
)

  declare -A abyss_map
  abyss_map["AbyssAmanamu.zip"]="DestructiveAspiration"
  abyss_map["AbyssKurgal.zip"]="BalefulDominion"
  abyss_map["AbyssTecrod.zip"]="FesteringVengeance"
  abyss_map["AbyssUlaman.zip"]="ExtinguishingGrasp"
  abyss_map["AbyssZorath.zip"]="ReclaimedMalevolence"

# Concatenate and decompress multipart archives.
for prefix in "${multipart_prefixes[@]}"; do
    if [[ -v abyss_map["$prefix"] ]]; then
        outfile="${abyss_map["$prefix"]}"
    else
        outfile="${prefix}"
    fi

    # Collect existing part files up to .part10
    parts=()
    for i in {0..10}; do
        file="${prefix}.part${i}"
        [[ -f "$file" ]] && parts+=("$file")
    done

    # Check if we found at least one part file
    if [ ${#parts[@]} -eq 0 ]; then
        echo "No part files found for prefix '$prefix'. Skipping..."
        continue
    fi

    echo "Decompressing multipart archive for '$prefix' (${#parts[@]} parts found) -> '$outfile'..."

    # Decompress only the files that exist
    cat "${parts[@]}" | pigz -d -z > "$outfile"

    echo "Deleting multipart files..."
    rm -f "${parts[@]}"
done

echo "Done."