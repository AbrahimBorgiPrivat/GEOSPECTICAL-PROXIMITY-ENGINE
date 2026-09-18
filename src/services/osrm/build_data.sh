#!/bin/bash
set -e

BUILD_TARGETS=(
  "car|denmark|denmark.osm.pbf|denmark.osrm"
  "foot|denmark|denmark.osm.pbf|denmark.osrm"
  "bicycle|denmark|denmark.osm.pbf|denmark.osrm"
)

for TARGET in "${BUILD_TARGETS[@]}"; do
  IFS='|' read -r PROFILE_NAME OUTPUT_DIR_NAME MAP_FILENAME OSRM_FILENAME <<< "$TARGET"
  # --- CONFIG ---------------------------------------------------------
  MAP_FILE="./data/maps/$MAP_FILENAME"
  OSRM_DIR="./data/osrm/$OUTPUT_DIR_NAME"
  MAPS_DIR="./data/maps"
  PROFILE="${PROFILE_NAME}.lua"
  echo "=== OSRM build script ==="
  echo "Working directory: $(pwd)"
  echo "Using map file:    $MAP_FILE"
  echo "Output dir:        $OSRM_DIR"
  echo "Profile:           $PROFILE"
  echo ""
  if [ ! -f "$MAP_FILE" ]; then
    echo "ERROR: Map file $MAP_FILE not found!"
    echo "Make sure you have downloaded it to: $(pwd)/$MAPS_DIR"
    exit 1
  fi
  mkdir -p "$OSRM_DIR" 

  #  OS DETECTION 
  OS=$(uname -s | tr '[:upper:]' '[:lower:]')
  echo "Detected OS: $OS"
  if [[ "$OS" == *"mingw"* || "$OS" == *"msys"* || "$OS" == *"cygwin"* ]]; then
      echo "Running on Windows (Git Bash detected). Applying Windows path fixes..."
      export MSYS_NO_PATHCONV=1
      export MSYS2_ARG_CONV_EXCL="*"
      OSRM_DATA_MOUNT="$(cygpath -w "$(pwd)/$OSRM_DIR")"
      MAPS_MOUNT="$(cygpath -w "$(pwd)/$MAPS_DIR")"
  else
      echo "Running on Linux/macOS. Using POSIX paths."
      OSRM_DATA_MOUNT="$(pwd)/$OSRM_DIR"
      MAPS_MOUNT="$(pwd)/$MAPS_DIR"
  fi
  echo "Mounting OSRM data from: $OSRM_DATA_MOUNT"
  echo "Mounting Maps from:      $MAPS_MOUNT"
  echo ""

  #  EXTRACT 
  echo "=== Extracting map with $PROFILE profile ==="
  docker run -t --rm \
    -v "$OSRM_DATA_MOUNT:/data" \
    -v "$MAPS_MOUNT:/maps" \
    osrm/osrm-backend \
    osrm-extract -p "/opt/$PROFILE" "/maps/$MAP_FILENAME"
  find "$MAPS_DIR" -maxdepth 1 ! -name "*.osm.pbf" -type f -exec mv {} "$OSRM_DIR" \;

  # PARTITION
  echo "=== Partitioning ==="
  docker run -t --rm \
    -v "$OSRM_DATA_MOUNT:/data" \
    osrm/osrm-backend \
    osrm-partition "/data/$OSRM_FILENAME"
  #  CUSTOMIZE 
  echo "=== Customizing ==="
  docker run -t --rm \
    -v "$OSRM_DATA_MOUNT:/data" \
    osrm/osrm-backend \
    osrm-customize "/data/$OSRM_FILENAME"

  echo "=== OSRM data has been created successfully ==="
  echo "Files are in: $(pwd)/data/osrm"
done

echo "=== All OSRM profiles built successfully ==="
echo "Files are in: $(pwd)/data/osrm"
