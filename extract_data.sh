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
    "GloriousVanity.zip"
)

# Concatenate and decompress multipart archives.
for prefix in "${multipart_prefixes[@]}"; do
    outfile="${prefix%.zip}"

    echo "Decompressing multipart archive '${prefix}.part0'...'.part4' -> '$outfile'..."

    cat "${prefix}".part{0..4} | pigz -d -z > "$outfile"

    echo "Deleting multipart files..."
    rm -f "${prefix}".part{0..4}
done

echo "Done."