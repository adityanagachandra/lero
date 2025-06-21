# LERO - LeRobot dataset Operations toolkit

**LERO (LeRobot dataset Operations toolkit)** is a comprehensive toolkit for editing and managing LeRobot datasets for robot imitation learning. LERO provides powerful tools for LeRobot dataset editing, efficiently handling LeRobot format datasets consisting of Parquet files, MP4 videos, and metadata with a modern, modular architecture.

![demo](media/lero-demo-movie.gif)

## Features

### Core Functionality
- **Dataset Overview**: Display episode count, task count, and dataset statistics
- **Episode Management**: View episode details and list episodes with advanced filtering
- **Episode Deletion**: Delete specified episodes with automatic renumbering
- **Episode Copying**: Duplicate episodes with new instructions
- **Dry Run Mode**: Preview operations before executing them
- **Multi-Camera Support**: Handle multiple camera video files seamlessly

### GUI Features
- **Interactive Episode Viewer**: Visual episode browser with video playback
- **Real-time Joint Angle Visualization**: Unified graph showing all robot joints
- **Synchronized Playback**: Video and joint data synchronized with timeline controls
- **Multi-Camera Display**: Support for multiple camera views with automatic layout
- **Variable Speed Playback**: Adjustable playback speed (0.1x to 10x)

![GUI Screenshot](media/screen_image.png)
*Interactive GUI showing synchronized video playback and joint angle visualization*

### Advanced Features
- **Modular Architecture**: Clean, maintainable codebase with separated concerns
- **Comprehensive Validation**: Dataset integrity checking and validation
- **Performance Optimized**: Efficient file operations and memory usage
- **Error Recovery**: Robust error handling with detailed diagnostics

## Dataset Structure

This tool supports LeRobot datasets with the following structure:

```
dataset_root/
├── data/                     # Parquet files (robot state data)
│   ├── chunk-000/
│   │   ├── episode_000000.parquet
│   │   └── ...
│   └── ...
├── videos/                   # MP4 video files
│   ├── chunk-000/
│   │   ├── observation.images.laptop/
│   │   │   ├── episode_000000.mp4
│   │   │   └── ...
│   │   └── observation.images.phone/
│   │       └── ...
│   └── ...
└── meta/                     # Metadata
    ├── info.json            # Dataset information
    ├── episodes.jsonl       # Episode metadata
    ├── tasks.jsonl          # Task descriptions
    └── stats.json           # Statistics data
```

## Installation

### Using uv (Recommended)

```bash
# Setup project with core dependencies
uv sync

# Install with GUI support
uv sync --group gui

# Install with development tools
uv sync --group dev

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### Using pip

```bash
# Core dependencies
pip install pandas pyarrow

# GUI dependencies (optional)
pip install matplotlib opencv-python Pillow

# Development dependencies (optional)  
pip install pytest black isort mypy
```

## Usage

### Basic Usage

```bash
# Display dataset overview
lero /path/to/dataset

# Show detailed summary with statistics
lero /path/to/dataset --summary
```

### Episode Display

```bash
# List episodes (default 10 episodes)
lero /path/to/dataset --list

# Display specific range (10 episodes starting from episode 20)
lero /path/to/dataset --list 10 --list-start 20

# Show specific episode details
lero /path/to/dataset --episode 5

# Include data sample in display
lero /path/to/dataset --episode 5 --show-data
```

### Episode Operations

```bash
# Delete episode 5 (remaining episodes are automatically renumbered)
lero /path/to/dataset --delete 5

# Dry run deletion (preview what would be deleted)
lero /path/to/dataset --delete 5 --dry-run

# Copy episode 3 with new instruction (added to the end of the dataset)
lero /path/to/dataset --copy 3 --instruction "Move the block to the left"

# Dry run copy
lero /path/to/dataset --copy 3 --instruction "New task" --dry-run
```

### GUI Mode

```bash
# Launch interactive GUI viewer
lero /path/to/dataset --gui

# Launch GUI with specific episode
lero /path/to/dataset --gui --episode 5

# Direct GUI launch  
python -m lero.gui.viewer /path/to/dataset --episode 5
```

## Command Line Arguments

### Display Options
| Argument | Description |
|----------|-------------|
| `dataset_path` | Path to the dataset root directory (required) |
| `--summary` | Display detailed dataset summary |
| `--list [N]` | List episodes (default 10) |
| `--list-start N` | Starting index for episode listing |
| `--episode N` | Show details of specific episode |
| `--show-data` | Include data sample when displaying episode |

### Edit Operations
| Argument | Description |
|----------|-------------|
| `--delete N` | Delete specified episode and renumber remaining episodes |
| `--copy N` | Copy specified episode with new instruction |
| `--instruction "text"` | New instruction for copied episode (required with --copy) |
| `--dry-run` | Preview operations without making changes |

### GUI Options
| Argument | Description |
|----------|-------------|
| `--gui` | Launch interactive GUI viewer for episodes |

## Architecture

### Modular Design

The project follows a clean, modular architecture:

```
lero/
├── __init__.py           # Package entry point
├── __main__.py           # Main module entry point
├── dataset_editor/       # Core dataset editing module
│   ├── __init__.py       # Module entry point
│   ├── constants.py      # Configuration and constants
│   ├── metadata.py       # Metadata management (MetadataManager)
│   ├── file_utils.py     # File system operations (FileSystemManager)
│   ├── operations.py     # Dataset operations (DatasetOperations)
│   ├── display.py        # Display formatting (DisplayFormatter)
│   ├── cli.py           # CLI handling (CLIHandler)
│   └── core.py          # Main API (LeRobotDatasetEditor)
└── gui/                 # GUI components module
    ├── __init__.py       # GUI module entry point
    ├── constants.py      # GUI configuration
    ├── data_handler.py   # Data processing utilities
    ├── video_component.py # Video display component
    ├── plot_component.py # Joint angle plotting
    ├── controls.py      # UI controls and panels
    └── viewer.py        # Main GUI application
```

### Key Components

- **MetadataManager**: Handles all metadata file operations
- **FileSystemManager**: Manages file system operations and path generation
- **DatasetOperations**: Core dataset manipulation logic
- **DisplayFormatter**: Consistent formatting for all output
- **CLIHandler**: Comprehensive command-line interface
- **LeRobotDatasetEditor**: Main API for external usage

## Feature Details

### Episode Deletion

When deleting an episode, the following operations are performed automatically:

1. Delete the target episode's Parquet file
2. Delete all camera videos for the target episode
3. Renumber subsequent episodes (shift up)
4. Update metadata (`episodes.jsonl`, `info.json`)
5. Maintain chunk-based file structure
6. Clean up empty directories

### Episode Copying

When copying an episode, the following operations are performed:

1. Copy the source episode's Parquet file
2. Copy all camera videos for the source episode
3. Set the copy destination to the last episode number
4. Add new task description to `tasks.jsonl`
5. Update episode indices in copied Parquet data
6. Update all metadata files appropriately

### GUI Features

The interactive GUI provides:

- **Multi-camera video playback** with synchronized timeline
- **Unified joint angle visualization** showing all 6 robot joints
- **Variable speed playback** from 0.1x to 10x speed
- **Frame-accurate navigation** with timeline scrubber
- **Episode switching** within the GUI
- **Performance optimizations** for smooth playback

### Dry Run Mode

Using the `--dry-run` option allows you to preview:

- List of files to be deleted or copied
- Source and destination file paths for operations
- Range of episodes to be renumbered after operations
- File size and storage impact estimates

## Robot Support

Currently optimized for:

- **SO-100 Robot**: 6-DOF robotic arm with gripper
  - Joint names: shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
  - Automatic joint data extraction from `observation.state` column
  - Multi-camera support (laptop, phone, etc.)

The architecture is extensible to support additional robot types.

## Performance Considerations

- **Chunk-based file organization**: Efficient handling of large datasets
- **Lazy loading**: Metadata loaded on-demand
- **Optimized video playback**: Frame skipping during high-speed playback
- **Memory efficient**: Streaming data processing where possible
- **Parallel operations**: Concurrent file operations when safe

## Important Notes

- **Backup Recommended**: Always create backups before editing datasets
- **Large Datasets**: Operations may take time with large datasets (progress indicators provided)
- **Chunk Structure**: Supports 1000-episode chunks; other chunk sizes are not supported
- **Concurrent Execution**: Do not run multiple tools on the same dataset simultaneously
- **GUI Dependencies**: GUI features require additional packages (install with `--group gui`)

## Development

### Dependencies

#### Core Dependencies
- Python 3.8+
- pandas: For reading and writing Parquet files
- pyarrow: For Parquet file support

#### GUI Dependencies (Optional)
- matplotlib: For joint angle plotting
- opencv-python: For video processing
- Pillow: For image handling
- tkinter: For GUI framework (usually included with Python)

#### Development Dependencies (Optional)
- pytest: For testing
- black: For code formatting
- isort: For import sorting
- mypy: For type checking

### Project Structure

```
.
├── lero/                    # Main package directory
│   ├── dataset_editor/      # Core dataset editing module
│   ├── gui/                 # GUI components module
│   ├── __init__.py          # Package entry point
│   └── __main__.py          # Module entry point
├── examples/                # Example scripts and documentation
├── media/                   # Screenshots and assets
├── tests/                   # Test suite
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── LICENSE                  # Apache 2.0 license
```

### Development Setup

```bash
# Install with all dependencies
uv sync --group dev --group gui

# Run tests
uv run pytest

# Code formatting
uv run black .
uv run isort .

# Type checking
uv run mypy lero/

# Run the tool in development
lero --help
```

### API Usage

```python
from lero import LeRobotDatasetEditor

# Initialize editor
editor = LeRobotDatasetEditor("/path/to/dataset")

# Get dataset information
episode_count = editor.count_episodes()
episode_info = editor.get_episode_info(5)
summary = editor.get_statistics()

# Perform operations
editor.delete_episode(5, dry_run=True)  # Preview deletion
editor.copy_episode_with_new_instruction(3, "New task")

# Launch GUI programmatically
from lero.gui import launch_episode_viewer
launch_episode_viewer("/path/to/dataset", episode_index=5)
```

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Contributing

Bug reports and feature requests are welcome via GitHub Issues. Pull requests are also welcome.

### Contributing Guidelines

1. Follow the existing code style (black, isort)
2. Add type hints for new functions
3. Include docstrings for public APIs
4. Add tests for new functionality
5. Update documentation as needed

## Changelog

### v0.3.0
- **Major Architecture Refactor**: Modular design with separated concerns
- **GUI Episode Viewer**: Interactive video and joint angle visualization
- **Enhanced CLI**: Comprehensive command-line interface with validation
- **Performance Improvements**: Optimized file operations and memory usage
- **Robust Error Handling**: Better error messages and recovery
- **Dataset Validation**: Integrity checking and validation tools
- **SO-100 Robot Support**: Optimized for SO-100 6-DOF robotic arm
- **Dry Run Enhancements**: More detailed preview capabilities
- **Documentation**: Comprehensive documentation and examples

### Previous Versions
- **v0.2.0**: Episode deletion with automatic renumbering
- **v0.1.0**: Basic dataset overview and episode display functionality