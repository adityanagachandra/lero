#!/usr/bin/env python3
"""
LERO - LeRobot dataset Operations toolkit - Main Entry Point

This is the main entry point for LERO (LeRobot dataset Operations toolkit).
The actual implementation has been modularized for better maintainability.
"""

__version__ = "0.3.0"

import sys
from .dataset_editor.cli import main

# Re-export main classes for backward compatibility
from .dataset_editor.core import LeRobotDatasetEditor
from .dataset_editor.metadata import MetadataManager
from .dataset_editor.operations import DatasetOperations

__all__ = ['LeRobotDatasetEditor', 'MetadataManager', 'DatasetOperations']

if __name__ == "__main__":
    sys.exit(main())