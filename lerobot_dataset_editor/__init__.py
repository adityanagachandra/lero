#!/usr/bin/env python3
"""
LeRobot Dataset Editor

A comprehensive tool for editing and managing LeRobot datasets for robot imitation learning.

This package provides functionality for:
- Loading and editing LeRobot datasets
- Episode management (delete, copy, modify)
- GUI interface for visual dataset browsing
- Batch operations and automation

Licensed under the Apache License 2.0
"""

__version__ = "0.3.0"

from .dataset_editor.core import LeRobotDatasetEditor

__all__ = ["LeRobotDatasetEditor"]