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
    
    @staticmethod
    def display_tasks_list(tasks: List[Dict[str, Any]], episodes: List[Dict[str, Any]] = None) -> None:
        """
        Display a comprehensive list of all tasks in the dataset with associated episodes.
        
        Args:
            tasks: List of task dictionaries
            episodes: List of episode dictionaries (optional)
        """
        if not tasks:
            print("\n=== Tasks ===")
            print("No tasks found in dataset.")
            return
        
        # Debug information (can be removed later)
        import os
        if os.environ.get('LERO_DEBUG'):
            print(f"\n=== DEBUG: Tasks ({len(tasks)}) ===")
            for i, task in enumerate(tasks):
                print(f"  Task {i}: {task}")
            print(f"\n=== DEBUG: Episodes ({len(episodes) if episodes else 0}) ===")
            if episodes:
                for i, episode in enumerate(episodes):
                    print(f"  Episode {i}: {episode}")
            print("=== END DEBUG ===\n")
        
        # Create mapping of task_index to episode indices
        task_to_episodes = {}
        if episodes:
            for episode in episodes:
                # Try multiple ways to get task index
                task_idx = episode.get('task_index')
                episode_idx = episode.get('episode_index')
                
                # If task_index is not available, try to match by task text
                if task_idx is None:
                    # Check for single task field
                    episode_task = episode.get('task')
                    if episode_task:
                        # Find matching task by text
                        for task in tasks:
                            if task.get('task') == episode_task:
                                task_idx = task.get('task_index')
                                break
                    
                    # Check for tasks array (plural)
                    episode_tasks = episode.get('tasks')
                    if episode_tasks and isinstance(episode_tasks, list) and len(episode_tasks) > 0:
                        episode_task = episode_tasks[0]  # Use first task in the array
                        # Find matching task by text (with fuzzy matching for minor differences)
                        for task in tasks:
                            task_text = task.get('task', '')
                            # Try exact match first
                            if task_text == episode_task:
                                task_idx = task.get('task_index')
                                break
                            # Try fuzzy match (handle singular/plural differences)
                            if task_text.lower().replace('plates', 'plate') == episode_task.lower().replace('plates', 'plate'):
                                task_idx = task.get('task_index')
                                break
                
                if task_idx is not None and episode_idx is not None:
                    if task_idx not in task_to_episodes:
                        task_to_episodes[task_idx] = []
                    task_to_episodes[task_idx].append(episode_idx)
        
        print(f"\n=== Tasks ({len(tasks)} total) ===")
        
        for task in tasks:
            task_index = task.get('task_index', 'Unknown')
            task_text = task.get('task', 'Unknown task')
            
            # Get associated episodes
            episode_indices = task_to_episodes.get(task_index, [])
            episode_count = len(episode_indices)
            
            if episode_indices:
                episode_indices.sort()
                if len(episode_indices) <= 5:
                    episodes_str = f" ({episode_count} episodes: {', '.join(map(str, episode_indices))})"
                else:
                    first_few = ', '.join(map(str, episode_indices[:3]))
                    episodes_str = f" ({episode_count} episodes: {first_few}... +{len(episode_indices)-3} more)"
            else:
                episodes_str = " (0 episodes)"
            
            print(f"Task {task_index:3}: {task_text}{episodes_str}")


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