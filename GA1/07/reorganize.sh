#!/usr/bin/env bash
# Run inside the extracted files_to_reorganize/ folder.
set -euo pipefail

# Collect the list first, so files we move into new folders aren't picked up again
mapfile -d '' files < <(find . -type f -name '*.txt' -print0)

for f in "${files[@]}"; do
  rel="${f#./}"                                   # archive/part 2/file09.txt
  category=$(grep -m1 '^category:' "$f" | sed 's/^category:[[:space:]]*//; s/[[:space:]]*$//')
  [ -n "$category" ] || { echo "no category: $rel"; continue; }
  mkdir -p "$category"
  mv -n -- "$f" "$category/$(printf '%s' "$rel" | tr '/' '-')"
done

find . -type f | LC_ALL=C sort | sha256sum | cut -d' ' -f1
