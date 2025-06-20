#!/bin/bash

# batch_copy_episodes.sh
# 
# This script demonstrates how to copy multiple episodes with new instructions
# using the LeRobot Dataset Editor.
#
# Usage:
#   ./batch_copy_episodes.sh <dataset_path> <episode_numbers> <instruction>
#
# Example:
#   ./batch_copy_episodes.sh /path/to/dataset "1,3,5,7" "Pick up the red block"
#
# Licensed under the Apache License 2.0

set -e  # Exit on any error

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 <dataset_path> <episode_numbers> <instruction>"
    echo ""
    echo "Arguments:"
    echo "  dataset_path     Path to the LeRobot dataset directory"
    echo "  episode_numbers  Comma-separated list of episode numbers (e.g., '1,3,5,7')"
    echo "  instruction      New instruction text for copied episodes"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/dataset '1,3,5' 'Pick up the red block'"
    echo "  $0 /path/to/dataset '10,20,30' 'Place the object in the container'"
    echo ""
    echo "Options:"
    echo "  --dry-run        Preview operations without making changes"
    echo "  --help          Show this help message"
}

# Function to validate dataset path
validate_dataset() {
    local dataset_path="$1"
    
    if [[ ! -d "$dataset_path" ]]; then
        print_error "Dataset directory does not exist: $dataset_path"
        return 1
    fi
    
    if [[ ! -d "$dataset_path/meta" ]]; then
        print_error "Invalid dataset: meta directory not found in $dataset_path"
        return 1
    fi
    
    if [[ ! -f "$dataset_path/meta/info.json" ]]; then
        print_error "Invalid dataset: info.json not found in $dataset_path/meta"
        return 1
    fi
    
    return 0
}

# Function to validate episode numbers
validate_episode_numbers() {
    local episode_numbers="$1"
    
    # Check if episode_numbers contains only digits and commas
    if [[ ! "$episode_numbers" =~ ^[0-9,]+$ ]]; then
        print_error "Invalid episode numbers format. Use comma-separated numbers (e.g., '1,3,5')"
        return 1
    fi
    
    return 0
}

# Function to check if lero module exists
check_editor_script() {
    local script_dir
    script_dir="$(dirname "$(dirname "$(realpath "$0")")")"
    local editor_module="$script_dir/lero"
    
    if [[ ! -d "$editor_module" ]]; then
        print_error "lero module not found at $editor_module"
        print_error "Please ensure this script is run from the examples directory of the project"
        return 1
    fi
    
    echo "$editor_module"
    return 0
}

# Function to get dataset episode count
get_episode_count() {
    local dataset_path="$1"
    local editor_module="$2"
    
    # Get episode count from dataset summary
    local summary_output
    summary_output=$(python -m lero "$dataset_path" --summary 2>/dev/null | grep "Total episodes:" | cut -d: -f2 | tr -d ' ')
    
    if [[ -z "$summary_output" ]]; then
        print_error "Could not determine episode count from dataset"
        return 1
    fi
    
    echo "$summary_output"
    return 0
}

# Function to copy episodes with new instruction
copy_episodes() {
    local dataset_path="$1"
    local episode_numbers="$2"
    local instruction="$3"
    local editor_module="$4"
    local dry_run="$5"
    
    # Convert comma-separated string to array
    IFS=',' read -ra episodes <<< "$episode_numbers"
    
    local total_episodes=${#episodes[@]}
    local current=0
    local success_count=0
    local error_count=0
    
    print_info "Starting batch copy operation for $total_episodes episodes"
    print_info "New instruction: \"$instruction\""
    
    if [[ "$dry_run" == "true" ]]; then
        print_warning "DRY RUN MODE - No actual changes will be made"
    fi
    
    echo ""
    
    # Process each episode
    for episode in "${episodes[@]}"; do
        current=$((current + 1))
        
        # Remove any whitespace
        episode=$(echo "$episode" | tr -d ' ')
        
        print_info "[$current/$total_episodes] Processing episode $episode..."
        
        # Build command
        local cmd="python -m lero \"$dataset_path\" --copy $episode --instruction \"$instruction\""
        if [[ "$dry_run" == "true" ]]; then
            cmd="$cmd --dry-run"
        fi
        
        # Execute command
        if eval "$cmd"; then
            if [[ "$dry_run" == "true" ]]; then
                print_success "Episode $episode: Dry run completed successfully"
            else
                print_success "Episode $episode: Copied successfully with new instruction"
            fi
            success_count=$((success_count + 1))
        else
            print_error "Episode $episode: Copy operation failed"
            error_count=$((error_count + 1))
        fi
        
        echo ""
    done
    
    # Print summary
    echo "=================================="
    print_info "Batch copy operation completed"
    print_success "Successful operations: $success_count"
    
    if [[ $error_count -gt 0 ]]; then
        print_error "Failed operations: $error_count"
    fi
    
    echo "=================================="
    
    return $error_count
}

# Main function
main() {
    local dataset_path=""
    local episode_numbers=""
    local instruction=""
    local dry_run="false"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run="true"
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            -*)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                if [[ -z "$dataset_path" ]]; then
                    dataset_path="$1"
                elif [[ -z "$episode_numbers" ]]; then
                    episode_numbers="$1"
                elif [[ -z "$instruction" ]]; then
                    instruction="$1"
                else
                    print_error "Too many arguments"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Validate required arguments
    if [[ -z "$dataset_path" || -z "$episode_numbers" || -z "$instruction" ]]; then
        print_error "Missing required arguments"
        show_usage
        exit 1
    fi
    
    # Validate inputs
    if ! validate_dataset "$dataset_path"; then
        exit 1
    fi
    
    if ! validate_episode_numbers "$episode_numbers"; then
        exit 1
    fi
    
    # Check for editor module
    local editor_module
    if ! editor_module=$(check_editor_script); then
        exit 1
    fi
    
    # Get episode count for validation
    print_info "Validating dataset and checking episode count..."
    local total_episodes
    if ! total_episodes=$(get_episode_count "$dataset_path" "$editor_module"); then
        exit 1
    fi
    
    print_info "Dataset contains $total_episodes episodes"
    
    # Validate episode numbers against dataset
    IFS=',' read -ra episodes <<< "$episode_numbers"
    for episode in "${episodes[@]}"; do
        episode=$(echo "$episode" | tr -d ' ')
        if [[ $episode -ge $total_episodes ]]; then
            print_error "Episode $episode is out of range (dataset has $total_episodes episodes, valid range: 0-$((total_episodes-1)))"
            exit 1
        fi
    done
    
    # Show configuration
    echo ""
    print_info "Configuration:"
    echo "  Dataset path: $dataset_path"
    echo "  Episodes to copy: $episode_numbers"
    echo "  New instruction: \"$instruction\""
    echo "  Dry run mode: $dry_run"
    echo ""
    
    # Confirm operation (unless dry run)
    if [[ "$dry_run" == "false" ]]; then
        echo -n "Proceed with batch copy operation? [y/N]: "
        read -r confirmation
        if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
            print_info "Operation cancelled by user"
            exit 0
        fi
        echo ""
    fi
    
    # Perform the copy operations
    if copy_episodes "$dataset_path" "$episode_numbers" "$instruction" "$editor_module" "$dry_run"; then
        if [[ "$dry_run" == "true" ]]; then
            print_success "Dry run completed successfully - use without --dry-run to perform actual operations"
        else
            print_success "All copy operations completed successfully"
        fi
        exit 0
    else
        print_error "Some operations failed - check the output above for details"
        exit 1
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi