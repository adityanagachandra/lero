"""
Display utilities for dataset information.
"""

import pandas as pd
from typing import Dict, Any, List
from .constants import MAX_TASKS_DISPLAY, MAX_TASKS_SUMMARY


class DisplayFormatter:
    """Handles formatting and display of dataset information."""
    
    @staticmethod
    def display_episode(episode_info: Dict[str, Any], show_data_sample: bool = False) -> None:
        """
        Display information about a specific episode.
        
        Args:
            episode_info: Dictionary containing episode information
            show_data_sample: Whether to show a sample of the data
        """
        episode_index = episode_info['episode_index']
        
        print(f"\n=== Episode {episode_index} ===")
        print(f"Length: {episode_info['length']} frames")
        
        tasks_str = ', '.join(episode_info['tasks']) if episode_info['tasks'] else 'No tasks'
        print(f"Tasks: {tasks_str}")
        
        print(f"Data file: {episode_info['data_file']}")
        print(f"Data exists: {episode_info['data_exists']}")
        
        print("\nVideo files:")
        for video_key, video_path in episode_info['video_files'].items():
            exists = episode_info['videos_exist'][video_key]
            status = 'EXISTS' if exists else 'MISSING'
            print(f"  {video_key}: {video_path} ({status})")
        
        # Show data sample if requested and file exists
        if show_data_sample and episode_info['data_exists']:
            if not DisplayFormatter._show_data_sample(episode_info['data_file']):
                raise ValueError("Failed to read data file")
    
    @staticmethod
    def _show_data_sample(data_file_path) -> bool:
        """Show a sample of the data file."""
        try:
            df = pd.read_parquet(data_file_path)
            print(f"\nData Sample (first 5 rows of {len(df)} total):")
            print(df.head().to_string())
            return True
        except Exception as e:
            print(f"\nError reading data file: {e}")
            return False
    
    @staticmethod
    def list_episodes(operations, start: int = 0, count: int = 10) -> None:
        """
        List episodes with basic information.
        
        Args:
            operations: DatasetOperations instance
            start: Starting episode index
            count: Number of episodes to list
        """
        total_episodes = operations.count_episodes()
        end = min(start + count, total_episodes)
        
        print(f"\n=== Episodes {start}-{end-1} (Total: {total_episodes}) ===")
        
        for i in range(start, end):
            try:
                episode_info = operations.get_episode_info(i)
                tasks_str = ', '.join(episode_info['tasks'][:MAX_TASKS_DISPLAY])
                if len(episode_info['tasks']) > MAX_TASKS_DISPLAY:
                    tasks_str += f" (+{len(episode_info['tasks'])-MAX_TASKS_DISPLAY} more)"
                
                print(f"Episode {i:6d}: {episode_info['length']:4} frames | {tasks_str}")
            except Exception as e:
                print(f"Episode {i:6d}: Error - {e}")
    
    @staticmethod
    def display_dataset_summary(summary: Dict[str, Any], tasks: List[Dict[str, Any]]) -> None:
        """
        Display a summary of the dataset.
        
        Args:
            summary: Dictionary containing dataset summary
            tasks: List of task dictionaries
        """
        print(f"\n=== Dataset Summary ===")
        print(f"Dataset Path: {summary['dataset_path']}")
        print(f"Total episodes: {summary['total_episodes']}")
        print(f"Total frames: {summary.get('total_frames', 'Unknown')}")
        print(f"Total tasks: {summary['total_tasks']}")
        print(f"Robot type: {summary.get('robot_type', 'Unknown')}")
        print(f"FPS: {summary.get('fps', 'Unknown')}")
        print(f"Codebase version: {summary.get('codebase_version', 'Unknown')}")
        
        print(f"\nAvailable tasks: {len(tasks)}")
        for i, task in enumerate(tasks[:MAX_TASKS_SUMMARY]):
            task_index = task.get('task_index', i)
            task_text = task.get('task', 'Unknown task')
            print(f"  {task_index}: {task_text}")
        
        if len(tasks) > MAX_TASKS_SUMMARY:
            print(f"  ... and {len(tasks) - MAX_TASKS_SUMMARY} more tasks")


class ErrorDisplay:
    """Handles display of error messages."""
    
    @staticmethod
    def show_error(message: str) -> None:
        """
        Show an error message.
        
        Args:
            message: Error message to display
        """
        print(f"Error: {message}")
    
    @staticmethod
    def show_validation_error(field: str, value: Any, expected: str) -> None:
        """
        Show a validation error message.
        
        Args:
            field: Field name that failed validation
            value: Value that failed validation
            expected: Description of expected value
        """
        print(f"Validation Error: {field} '{value}' is invalid. Expected: {expected}")


class ProgressDisplay:
    """Handles display of progress information."""
    
    @staticmethod
    def show_operation_start(operation: str, details: str = "") -> None:
        """
        Show the start of an operation.
        
        Args:
            operation: Name of the operation
            details: Additional details about the operation
        """
        print(f"\n{operation}...")
        if details:
            print(f"Details: {details}")
    
    @staticmethod
    def show_operation_progress(step: str) -> None:
        """
        Show progress of an operation.
        
        Args:
            step: Description of the current step
        """
        print(f"  {step}")
    
    @staticmethod
    def show_operation_complete(operation: str, result: str = "") -> None:
        """
        Show completion of an operation.
        
        Args:
            operation: Name of the operation
            result: Result of the operation
        """
        print(f"{operation} completed.")
        if result:
            print(f"Result: {result}")


class TableFormatter:
    """Handles table formatting for structured data display."""
    
    @staticmethod
    def format_episode_table(episodes_info: List[Dict[str, Any]]) -> str:
        """
        Format episodes information as a table.
        
        Args:
            episodes_info: List of episode information dictionaries
            
        Returns:
            Formatted table string
        """
        if not episodes_info:
            return "No episodes found."
        
        # Create header
        header = f"{'Episode':>8} | {'Frames':>8} | {'Data':>6} | {'Videos':>7} | Tasks"
        separator = "-" * len(header)
        
        lines = [header, separator]
        
        for episode_info in episodes_info:
            episode_idx = episode_info['episode_index']
            length = episode_info['length']
            data_status = "✓" if episode_info['data_exists'] else "✗"
            
            # Count existing videos
            video_count = sum(1 for exists in episode_info['videos_exist'].values() if exists)
            total_videos = len(episode_info['videos_exist'])
            video_status = f"{video_count}/{total_videos}"
            
            # Format tasks
            tasks = episode_info['tasks'][:2]  # Show first 2 tasks
            tasks_str = ', '.join(tasks)
            if len(episode_info['tasks']) > 2:
                tasks_str += f" (+{len(episode_info['tasks'])-2})"
            
            line = f"{episode_idx:>8} | {length:>8} | {data_status:>6} | {video_status:>7} | {tasks_str}"
            lines.append(line)
        
        return "\n".join(lines)