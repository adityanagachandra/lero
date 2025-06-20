"""
LeRobot Dataset Editor Module

This module provides functionality for editing and managing LeRobot datasets
for robot imitation learning.
"""

from .core import LeRobotDatasetEditor
from .metadata import MetadataManager
from .operations import DatasetOperations
from .cli import CLIHandler

__version__ = "0.3.0"

__all__ = [
    'LeRobotDatasetEditor',
    'MetadataManager', 
    'DatasetOperations',
    'CLIHandler'
]