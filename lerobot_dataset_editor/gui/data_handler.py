"""
Data handling utilities for processing robot dataset information.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, List
from .constants import SO100_JOINT_NAMES, JOINT_KEYWORDS, NUMERIC_DTYPES


class JointDataExtractor:
    """Handles extraction and processing of joint data from robot datasets."""
    
    @staticmethod
    def extract_joint_data(episode_data: pd.DataFrame) -> Tuple[Optional[np.ndarray], List[str]]:
        """
        Extract joint angle data from episode dataframe.
        
        Args:
            episode_data: DataFrame containing episode data
            
        Returns:
            Tuple of (joint_data_array, joint_names) or (None, []) if no data found
        """
        joint_data = None
        joint_names = SO100_JOINT_NAMES.copy()
        
        # Primary method: Extract from observation.state column
        if 'observation.state' in episode_data.columns:
            joint_data = JointDataExtractor._extract_from_observation_state(episode_data)
            if joint_data is not None:
                return joint_data, joint_names
        
        # Fallback: Look for individual joint columns
        joint_data, joint_names = JointDataExtractor._extract_from_individual_columns(episode_data)
        
        return joint_data, joint_names
    
    @staticmethod
    def _extract_from_observation_state(episode_data: pd.DataFrame) -> Optional[np.ndarray]:
        """Extract joint data from observation.state column."""
        try:
            joint_arrays = []
            for _, row in episode_data.iterrows():
                state = row['observation.state']
                if isinstance(state, np.ndarray) and len(state) >= 6:
                    joint_arrays.append(state[:6])  # Take first 6 joints
                elif hasattr(state, '__len__') and len(state) >= 6:
                    joint_arrays.append(list(state)[:6])
            
            if joint_arrays:
                return np.array(joint_arrays)  # Shape: (timesteps, 6)
        except Exception as e:
            print(f"Error extracting joint data from observation.state: {e}")
        
        return None
    
    @staticmethod
    def _extract_from_individual_columns(episode_data: pd.DataFrame) -> Tuple[Optional[np.ndarray], List[str]]:
        """Extract joint data from individual columns as fallback."""
        joint_columns = []
        for col in episode_data.columns:
            if any(keyword in col.lower() for keyword in JOINT_KEYWORDS):
                if episode_data[col].dtype in NUMERIC_DTYPES:
                    joint_columns.append(col)
        
        if joint_columns:
            joint_data = episode_data[joint_columns[:6]].values  # Limit to 6 joints
            joint_names = joint_columns[:6]
            return joint_data, joint_names
        
        return None, []
    
    @staticmethod
    def get_joint_value_range(joint_data: np.ndarray) -> Tuple[float, float]:
        """
        Calculate the overall value range for all joints.
        
        Args:
            joint_data: Array of shape (timesteps, num_joints)
            
        Returns:
            Tuple of (min_value, max_value)
        """
        if joint_data is None or len(joint_data) == 0:
            return 0.0, 1.0
        
        y_min = joint_data.min()
        y_max = joint_data.max()
        y_range = y_max - y_min
        
        if y_range > 0:
            # Add 10% padding
            padding = 0.1 * y_range
            return y_min - padding, y_max + padding
        else:
            # Handle case where all values are the same
            return y_min - 1.0, y_max + 1.0


class DatasetInfoFormatter:
    """Handles formatting of dataset information for display."""
    
    @staticmethod
    def format_episode_info(episode_info: dict) -> str:
        """
        Format episode information for display.
        
        Args:
            episode_info: Dictionary containing episode information
            
        Returns:
            Formatted string for display
        """
        from .constants import ICON_CHART, ICON_TARGET
        
        tasks_str = ', '.join(episode_info['tasks'][:2])
        if len(episode_info['tasks']) > 2:
            tasks_str += f" (+{len(episode_info['tasks']) - 2} more)"
        elif not episode_info['tasks']:
            tasks_str = "No tasks"
        
        return f"{ICON_CHART} Length: {episode_info['length']} frames | {ICON_TARGET} Tasks: {tasks_str}"
    
    @staticmethod
    def format_frame_info(current_frame: int, total_frames: int) -> str:
        """
        Format frame information for display.
        
        Args:
            current_frame: Current frame number (0-indexed)
            total_frames: Total number of frames
            
        Returns:
            Formatted string for display
        """
        from .constants import ICON_FILM
        
        return f"{ICON_FILM} Frame: {current_frame + 1}/{total_frames}"
    
    @staticmethod
    def format_speed_info(speed: float) -> str:
        """
        Format playback speed for display.
        
        Args:
            speed: Playback speed multiplier
            
        Returns:
            Formatted string for display
        """
        return f"{speed:.1f}x"