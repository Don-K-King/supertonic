#!/usr/bin/env bash
set -euo pipefail

voice_dir="${SUPERTONIC_VOICE_DIR:-$(pwd)/voices/custom}"
base_url="${SUPERTONIC_BASE_URL:-http://supertonic-tts:7788}"
overwrite="${SUPERTONIC_IMPORT_OVERWRITE:-true}"
network="${SUPERTONIC_DOCKER_NETWORK:-evido-live-translate}"
use_docker="${SUPERTONIC_IMPORT_USE_DOCKER:-1}"
curl_image="${SUPERTONIC_CURL_IMAGE:-curlimages/curl:8.7.1}"

if [[ ! -d "$voice_dir" ]]; then
  echo "Voice directory not found: $voice_dir" >&2
  exit 1
fi

shopt -s nullglob
voice_files=("$voice_dir"/*.json)
if (( ${#voice_files[@]} == 0 )); then
  echo "No custom Supertonic voice JSON files found in $voice_dir"
  exit 0
fi

for voice_file in "${voice_files[@]}"; do
  voice_name="$(basename "$voice_file")"
  import_url="${base_url%/}/v1/styles/import?overwrite=${overwrite}"
  echo "Importing $voice_name"

  if [[ "$use_docker" == "1" ]]; then
    docker run --rm \
      --network "$network" \
      -v "$voice_dir:/voices/custom:ro" \
      "$curl_image" \
      -fsS \
      -X POST "$import_url" \
      -H "Content-Type: application/json" \
      --data-binary "@/voices/custom/$voice_name"
  else
    curl \
      -fsS \
      -X POST "$import_url" \
      -H "Content-Type: application/json" \
      --data-binary "@$voice_file"
  fi
done

echo "Imported ${#voice_files[@]} custom Supertonic voice file(s)."
