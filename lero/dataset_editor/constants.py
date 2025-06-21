"""
Constants and configuration for the dataset editor.
"""


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
    INVALID_DATASET_PATH = "Error: Invalid dataset path: {path}"

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

# Terminal color constants
class Colors:
    """ANSI color codes for terminal output."""
    # Basic colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    
    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    
    # Reset
    RESET = "\033[0m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"

# Color utility functions
import os
import sys

def supports_color() -> bool:
    """Check if the terminal supports color output."""
    # Check if running in a terminal
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False
    
    # Check for NO_COLOR environment variable
    if os.environ.get('NO_COLOR'):
        return False
    
    # Check for FORCE_COLOR environment variable
    if os.environ.get('FORCE_COLOR'):
        return True
    
    # Check TERM environment variable
    term = os.environ.get('TERM', '').lower()
    if 'color' in term or term in ['xterm', 'xterm-256color', 'screen', 'tmux']:
        return True
    
    # Windows terminal support
    if sys.platform == 'win32':
        try:
            import colorama
            return True
        except ImportError:
            return False
    
    return True

def colorize(text: str, color: str = "", reset: bool = True) -> str:
    """
    Apply color to text if color support is available.
    
    Args:
        text: Text to colorize
        color: Color code from Colors class
        reset: Whether to add reset code at the end
        
    Returns:
        Colorized text or plain text if colors not supported
    """
    if not supports_color():
        return text
    
    if not color:
        return text
    
    result = f"{color}{text}"
    if reset:
        result += Colors.RESET
    
    return result

# Predefined color functions for common uses
def header(text: str) -> str:
    """Format text as a header (bold blue)."""
    return colorize(text, Colors.BOLD + Colors.BLUE)

def success(text: str) -> str:
    """Format text as success message (green)."""
    return colorize(text, Colors.GREEN)

def warning(text: str) -> str:
    """Format text as warning (yellow)."""
    return colorize(text, Colors.YELLOW)

def error(text: str) -> str:
    """Format text as error (red)."""
    return colorize(text, Colors.RED)

def info(text: str) -> str:
    """Format text as info (cyan)."""
    return colorize(text, Colors.CYAN)

def highlight(text: str) -> str:
    """Format text as highlighted (bold)."""
    return colorize(text, Colors.BOLD)

def dim(text: str) -> str:
    """Format text as dimmed."""
    return colorize(text, Colors.DIM)