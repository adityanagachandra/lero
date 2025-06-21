# Examples

This directory contains sample scripts demonstrating how to use the LeRobot Dataset Editor in various scenarios.

## Available Examples

### 1. Batch Episode Creation

- **`batch_copy_episodes.sh`**: Shell script to copy multiple episodes with new instructions
- **`batch_copy_episodes.py`**: Python script equivalent with enhanced error handling and logging
- **`batch_matrix_copy.sh`**: Shell script for matrix-style copying (multiple episodes × multiple instructions)
- **`batch_matrix_copy.py`**: Python script for advanced matrix-style batch copying with detailed logging

### 2. Dataset Analysis

- **`analyze_dataset.py`**: Comprehensive dataset analysis and statistics generation
- **`validate_dataset.py`**: Dataset validation and integrity checking

### 3. Automation Scripts

- **`automated_cleanup.py`**: Automated dataset cleanup and optimization
- **`export_episode_info.py`**: Export episode information to various formats

## Detailed Usage Examples

### Matrix Batch Copying

The new matrix batch copy scripts allow you to copy multiple episodes with multiple instructions efficiently:

```bash
# Copy episodes 1,2,10,15 with both "put the block" and "catch the block" instructions
./examples/batch_matrix_copy.sh /path/to/dataset "1,2,10,15" "put the block,catch the block"

# Python version with dry-run
python examples/batch_matrix_copy.py /path/to/dataset \
    --episodes "1,2,10,15" \
    --instructions "put the block,catch the block" \
    --dry-run

# With range specification and multiple instructions
./examples/batch_matrix_copy.sh /path/to/dataset "1-5,10" "task A,task B,task C"
```

**Processing Order**: For episodes [1,2,10,15] and instructions ["put the block", "catch the block"]:
1. Episode 1 with "put the block"
2. Episode 2 with "put the block"  
3. Episode 10 with "put the block"
4. Episode 15 with "put the block"
5. Episode 1 with "catch the block"
6. Episode 2 with "catch the block"
7. Episode 10 with "catch the block"
8. Episode 15 with "catch the block"

### Basic Batch Copying

```bash
# Copy specific episodes with single instruction
./examples/batch_copy_episodes.sh /path/to/dataset "1,3,5" "Pick up the red block"

# Python version with enhanced logging
python examples/batch_copy_episodes.py /path/to/dataset \
    --episodes "1,3,5" \
    --instruction "Pick up the red block" \
    --log-level DEBUG
```

### Dataset Analysis

```bash
# Analyze dataset structure and statistics
python examples/analyze_dataset.py /path/to/dataset

# Validate dataset integrity
python examples/validate_dataset.py /path/to/dataset
```

## Common Options

Most scripts support these common options:

- `--dry-run`: Preview operations without making changes
- `--log-level`: Set logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `--stop-on-error`: Stop processing if any operation fails
- `--help`: Show detailed usage information

## Usage

Each example includes detailed comments and usage instructions. Most scripts can be run with:

```bash
# Shell scripts
./examples/script_name.sh

# Python scripts  
python examples/script_name.py
```

See individual script documentation for specific requirements and options.