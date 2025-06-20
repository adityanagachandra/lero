"""
Constants and configuration for the GUI components.
"""

# GUI Layout Constants
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
MAX_VIDEO_SIZE = 300

# Playback Constants
DEFAULT_PLAYBACK_SPEED = 1.0
MIN_PLAYBACK_SPEED = 0.1
MAX_PLAYBACK_SPEED = 10.0
BASE_FPS = 60  # Target FPS for playback
MIN_DELAY_MS = 1  # Minimum delay between frames in milliseconds
VIDEO_UPDATE_SPEED_THRESHOLD = 2.0  # Skip video updates above this speed

# Font Settings
DEFAULT_FONT_SIZE = 12
LABEL_FONT = ('TkDefaultFont', 12, 'bold')
PLOT_TITLE_FONT_SIZE = 14
PLOT_LABEL_FONT_SIZE = 12
PLOT_TICK_FONT_SIZE = 10
LEGEND_FONT_SIZE = 10

# Robot Joint Constants
SO100_JOINT_NAMES = [
    'main_shoulder_pan', 
    'main_shoulder_lift', 
    'main_elbow_flex',
    'main_wrist_flex', 
    'main_wrist_roll', 
    'main_gripper'
]

MAX_JOINTS_DISPLAY = 6

# Plot Colors for Joint Angles
JOINT_COLORS = [
    '#1f77b4',  # Blue
    '#ff7f0e',  # Orange
    '#2ca02c',  # Green
    '#d62728',  # Red
    '#9467bd',  # Purple
    '#8c564b'   # Brown
]

# UI Icons/Emojis
ICON_CHART = "📊"
ICON_TARGET = "🎯"
ICON_FILM = "🎬"

# Data Extraction Keywords
JOINT_KEYWORDS = ['joint', 'position', 'angle', 'state']
NUMERIC_DTYPES = ['float64', 'float32', 'int64', 'int32']