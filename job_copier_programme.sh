#!/bin/bash
# Route File Copier - Copy route-specific and common R0 files
# Usage: ./route_file_copier.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Text formatting
NORMAL='\033[0m'
BOLD='\033[1m'
DIM='\033[2'
UNDERLINE='\033[4m'

# Configuration
SOURCE_DIR="/home/ishikawa/Documents/Test_1/"
DEST_DIR="/home/ishikawa/Documents/Test_2/"

# Get route number from user
echo -e "${YELLOW}${BOLD}${UNDERLINE}Welcome to Emitter File Transfer${NC}${NORMAL}"
echo -e "R0 files will copy automatically, just enter the route you are flying"
read -p "Please Enter Route number: " route_number

# Validate input
if ! [[ "$route_number" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}${BOLD}Error: ${NORMAL}${NC}Route number must be a positive integer"
    exit 1
fi

# Check directories exist
if [[ ! -d "$SOURCE_DIR" ]] || [[ ! -d "$DEST_DIR" ]]; then
    echo -e "${RED}${BOLD}Error: ${NORMAL}${NC}Source or destination directory does not exist"
    exit 1
fi

# Copy R0 files
echo -e "${YELLOW}Copying R0 files...${NC}"
cp -v "$SOURCE_DIR"R0* "$DEST_DIR" || true

# Copy route-specific files
echo -e "${YELLOW}Copying Route$route_number files...${NC}"
cp -v "$SOURCE_DIR"R${route_number}* "$DEST_DIR" || true

echo -e "${GREEN}${BOLD}Files copied successfully for Route ${NORMAL}${NC}$route_number"
