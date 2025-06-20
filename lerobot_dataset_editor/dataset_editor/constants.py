"""
Constants and configuration for the dataset editor.
"""

from pathlib import Path
from typing import List

# File and directory constants
CHUNK_SIZE = 1000  # Episodes per chunk
DATA_DIR = "data"
VIDEOS_DIR = "videos"
META_DIR = "meta"

# Metadata file names
INFO_FILE = "info.json"
EPISODES_FILE = "episodes.jsonl"
TASKS_FILE = "tasks.jsonl"
STATS_FILE = "stats.json"
EPISODES_STATS_FILE = "episodes_stats.jsonl"

# File patterns
CHUNK_PATTERN = "chunk-{chunk:03d}"
EPISODE_PATTERN = "episode_{episode:06d}"
PARQUET_EXT = ".parquet"
VIDEO_EXT = ".mp4"

# Data types
SUPPORTED_VIDEO_DTYPES = ["video"]
NUMERIC_DTYPES = ["float64", "float32", "int64", "int32"]

# Default values
DEFAULT_FRAME_LENGTH = "Unknown"
DEFAULT_TASK_LIST = []

# Error messages
class ErrorMessages:
    DATASET_NOT_FOUND = "Dataset info file not found at {path}"
    EPISODE_OUT_OF_RANGE = "Episode index {index} out of range (0-{max_range})"
    INVALID_EPISODE_NUMBER = "Please enter a valid episode number"
    INSTRUCTION_REQUIRED = "--instruction is required when using --copy"
    EPISODE_DELETE_ERROR = "Error deleting episode {index}: {error}"
    EPISODE_COPY_ERROR = "Error copying episode {index}: {error}"
    GUI_DEPENDENCIES_MISSING = "GUI dependencies not available.\nInstall with: uv sync --group gui"
    INVALID_DATASET_PATH = "Invalid dataset path: {path}"

# Success messages
class SuccessMessages:
    EPISODE_DELETED = "Successfully deleted episode {index} and renumbered remaining episodes"
    EPISODE_COPIED = "Successfully copied episode {source} to episode {target} with new instruction: '{instruction}'"
    DRY_RUN_DELETE = "DRY RUN: Would delete episode {index}"
    DRY_RUN_COPY = "DRY RUN: Would copy episode {source} to {target}"

# Display constants
MAX_TASKS_DISPLAY = 2
MAX_TASKS_SUMMARY = 5
MAX_COLUMNS_DISPLAY = 10