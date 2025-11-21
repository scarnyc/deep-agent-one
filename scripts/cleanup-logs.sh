#!/bin/bash
# Cleanup old log files while preserving recent ones
#
# Description:
#   Deletes old log files from out/logs/backend/ and out/logs/frontend/ directories
#   while ensuring a minimum number of recent logs are always kept.
#
# Usage:
#   ./scripts/cleanup-logs.sh
#
# Configuration:
#   DAYS_TO_KEEP=7       # Delete logs older than 7 days
#   MIN_FILES_TO_KEEP=10 # Always keep at least 10 most recent logs
#
# Requirements:
#   - out/logs/backend/ and/or out/logs/frontend/ directories exist
#
# Behavior:
#   - Interactive: Asks for confirmation before deleting
#   - Shows files to be deleted with size and modification date
#   - Calculates total space to be freed
#   - Preserves minimum number of recent files regardless of age
#
# Safety:
#   - Never deletes ALL logs (keeps MIN_FILES_TO_KEEP)
#   - Shows detailed preview before deletion
#   - Requires explicit confirmation
#
# Output:
#   - Lists files to be deleted
#   - Shows total space to be freed
#   - Summary of remaining logs
#
# Examples:
#   ./scripts/cleanup-logs.sh                 # Interactive cleanup
#
# Advanced:
#   Edit script to change DAYS_TO_KEEP or MIN_FILES_TO_KEEP

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
DAYS_TO_KEEP=7
MIN_FILES_TO_KEEP=10

# Navigate to project root (script is in scripts/ directory)
cd "$(dirname "$0")/.."

echo -e "${BLUE}Deep Agent AGI - Log Cleanup${NC}"
echo ""

# Function to cleanup logs in a directory
cleanup_directory() {
    local log_dir=$1
    local service_name=$2

    if [ ! -d "$log_dir" ]; then
        echo -e "${YELLOW}Directory $log_dir does not exist, skipping${NC}"
        return
    fi

    echo -e "${BLUE}Cleaning up ${service_name} logs...${NC}"

    # Count total log files
    total_files=$(find "$log_dir" -name "*.log" -type f 2>/dev/null | wc -l | tr -d ' ')

    if [ "$total_files" -eq 0 ]; then
        echo -e "${GREEN}No log files found in $log_dir${NC}"
        return
    fi

    echo "Total log files: $total_files"

    # Find files older than DAYS_TO_KEEP
    old_files=$(find "$log_dir" -name "*.log" -type f -mtime +${DAYS_TO_KEEP} 2>/dev/null)
    old_files_count=$(echo "$old_files" | grep -c "\.log$" || echo "0")

    if [ "$old_files_count" -eq 0 ]; then
        echo -e "${GREEN}No log files older than ${DAYS_TO_KEEP} days${NC}"
        return
    fi

    # Calculate how many files we can safely delete
    files_after_deletion=$((total_files - old_files_count))

    if [ "$files_after_deletion" -lt "$MIN_FILES_TO_KEEP" ]; then
        # Need to keep some old files to maintain minimum count
        files_to_delete=$((total_files - MIN_FILES_TO_KEEP))

        if [ "$files_to_delete" -le 0 ]; then
            echo -e "${YELLOW}Keeping all files to maintain minimum of ${MIN_FILES_TO_KEEP} files${NC}"
            return
        fi

        echo -e "${YELLOW}Found $old_files_count old files, but will only delete $files_to_delete to keep minimum ${MIN_FILES_TO_KEEP} files${NC}"

        # Get oldest files to delete (sorted by modification time)
        files_to_remove=$(find "$log_dir" -name "*.log" -type f -printf '%T+ %p\n' | sort | head -n "$files_to_delete" | cut -d' ' -f2-)
    else
        echo "Found $old_files_count log files older than ${DAYS_TO_KEEP} days"
        files_to_remove="$old_files"
    fi

    # Show files that will be deleted
    echo ""
    echo -e "${YELLOW}Files to be deleted:${NC}"
    echo "$files_to_remove" | while read -r file; do
        if [ -n "$file" ]; then
            file_date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null | cut -d'.' -f1)
            file_size=$(du -h "$file" | cut -f1)
            echo "  - $(basename "$file") (${file_size}, modified: ${file_date})"
        fi
    done

    # Calculate total size to be freed
    total_size=$(echo "$files_to_remove" | while read -r file; do
        if [ -n "$file" ] && [ -f "$file" ]; then
            stat -f "%z" "$file" 2>/dev/null || stat -c "%s" "$file" 2>/dev/null
        fi
    done | awk '{s+=$1} END {print s}')

    if [ -z "$total_size" ]; then
        total_size=0
    fi

    total_size_human=$(echo "$total_size" | awk '
        function human(x) {
            if (x < 1024) return x " B"
            x /= 1024
            if (x < 1024) return sprintf("%.2f KB", x)
            x /= 1024
            if (x < 1024) return sprintf("%.2f MB", x)
            x /= 1024
            return sprintf("%.2f GB", x)
        }
        {print human($1)}
    ')

    echo ""
    echo -e "${BLUE}Total space to be freed: ${total_size_human}${NC}"
    echo ""

    # Ask for confirmation
    read -p "Proceed with deletion? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        deleted_count=0
        echo "$files_to_remove" | while read -r file; do
            if [ -n "$file" ] && [ -f "$file" ]; then
                rm "$file"
                deleted_count=$((deleted_count + 1))
            fi
        done
        echo -e "${GREEN}✓ Cleanup complete for ${service_name}${NC}"
    else
        echo -e "${YELLOW}Cleanup cancelled${NC}"
    fi

    echo ""
}

# Cleanup backend logs
cleanup_directory "out/logs/backend" "backend"

# Cleanup frontend logs
cleanup_directory "out/logs/frontend" "frontend"

# Show final summary
echo -e "${BLUE}Final Summary:${NC}"
backend_count=$(find out/logs/backend -name "*.log" -type f 2>/dev/null | wc -l | tr -d ' ')
frontend_count=$(find out/logs/frontend -name "*.log" -type f 2>/dev/null | wc -l | tr -d ' ')

echo "Remaining log files:"
echo "  Backend:  $backend_count files"
echo "  Frontend: $frontend_count files"

echo ""
echo -e "${GREEN}Log cleanup complete!${NC}"
