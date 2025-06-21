"""
Core dataset editor functionality.
"""

from pathlib import Path
from typing import Dict, Any
from .operations import DatasetOperations
from .display import DisplayFormatter


class LeRobotDatasetEditor:
    """Main class for editing and managing LeRobot datasets."""
    
    def __init__(self, dataset_path: str):
        """
        Initialize the dataset editor.
        
        Args:
            dataset_path: Path to the root directory of the LeRobot dataset
        """
        self.dataset_path = Path(dataset_path)
        self.operations = DatasetOperations(self.dataset_path)
    
    def count_episodes(self) -> int:
        """
        Count the total number of episodes in the dataset.
        
        Returns:
            Number of episodes
        """
        return self.operations.count_episodes()
    
    def get_episode_info(self, episode_index: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific episode.
        
        Args:
            episode_index: Index of the episode to retrieve
            
        Returns:
            Dictionary containing episode information
        """
        return self.operations.get_episode_info(episode_index)
    
    def display_episode(self, episode_index: int, show_data_sample: bool = False) -> None:
        """
        Display information about a specific episode.
        
        Args:
            episode_index: Index of the episode to display
            show_data_sample: Whether to show a sample of the data
        """
        episode_info = self.get_episode_info(episode_index)
        DisplayFormatter.display_episode(episode_info, show_data_sample)
    
    def list_episodes(self, start: int = 0, count: int = 10) -> None:
        """
        List episodes with basic information.
        
        Args:
            start: Starting episode index
            count: Number of episodes to list
        """
        DisplayFormatter.list_episodes(self.operations, start, count)
    
    def dataset_summary(self) -> None:
        """Display a summary of the dataset."""
        summary = self.operations.get_dataset_summary()
        tasks = self.operations.metadata.tasks
        DisplayFormatter.display_dataset_summary(summary, tasks)
    
    def list_tasks(self) -> None:
        """Display a list of all tasks in the dataset."""
        tasks = self.operations.metadata.tasks
        episodes = self.operations.metadata.episodes
        DisplayFormatter.display_tasks_list(tasks, episodes)
    
    def delete_episode(self, episode_index: int, dry_run: bool = False) -> bool:
        """
        Delete a specific episode and renumber all subsequent episodes.
        
        Args:
            episode_index: Index of the episode to delete
            dry_run: If True, only show what would be deleted without actually deleting
            
        Returns:
            True if successful, False otherwise
        """
        return self.operations.delete_episode(episode_index, dry_run)
    
    def copy_episode_with_new_instruction(self, source_episode_index: int, new_instruction: str, dry_run: bool = False) -> bool:
        """
        Copy an episode with a new instruction and place it at the end of the dataset.
        
        Args:
            source_episode_index: Index of the episode to copy
            new_instruction: New instruction text for the copied episode
            dry_run: If True, only show what would be copied without actually copying
            
        Returns:
            True if successful, False otherwise
        """
        return self.operations.copy_episode_with_new_instruction(source_episode_index, new_instruction, dry_run)
    
    def reload_metadata(self) -> None:
        """Reload metadata from disk (useful after external changes)."""
        self.operations.reload_metadata()
    
    def get_dataset_path(self) -> Path:
        """
        Get the dataset path.
        
        Returns:
            Path to the dataset
        """
        return self.dataset_path
    
    def validate_dataset(self) -> Dict[str, Any]:
        """
        Validate the dataset structure and return validation results.
        
        Returns:
            Dictionary containing validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "episode_count": 0,
            "missing_files": [],
            "orphaned_files": []
        }
        
        try:
            total_episodes = self.count_episodes()
            validation_results["episode_count"] = total_episodes
            
            # Check each episode
            for i in range(total_episodes):
                try:
                    episode_info = self.get_episode_info(i)
                    
                    # Check for missing data files
                    if not episode_info['data_exists']:
                        validation_results["missing_files"].append(str(episode_info['data_file']))
                        validation_results["warnings"].append(f"Episode {i}: Missing data file")
                    
                    # Check for missing video files
                    for video_key, exists in episode_info['videos_exist'].items():
                        if not exists:
                            video_path = episode_info['video_files'][video_key]
                            validation_results["missing_files"].append(str(video_path))
                            validation_results["warnings"].append(f"Episode {i}: Missing video file {video_key}")
                
                except Exception as e:
                    validation_results["errors"].append(f"Episode {i}: {str(e)}")
                    validation_results["valid"] = False
            
        except Exception as e:
            validation_results["errors"].append(f"Dataset validation failed: {str(e)}")
            validation_results["valid"] = False
        
        return validation_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get detailed statistics about the dataset.
        
        Returns:
            Dictionary containing dataset statistics
        """
        stats = {
            "total_episodes": self.count_episodes(),
            "total_tasks": len(self.operations.metadata.tasks),
            "episodes_with_data": 0,
            "episodes_with_videos": 0,
            "total_frames": 0,
            "file_sizes": {
                "total_data_size": 0,
                "total_video_size": 0,
                "total_size": 0
            }
        }
        
        # Calculate detailed statistics
        for i in range(stats["total_episodes"]):
            try:
                episode_info = self.get_episode_info(i)
                
                if episode_info['data_exists']:
                    stats["episodes_with_data"] += 1
                
                if any(episode_info['videos_exist'].values()):
                    stats["episodes_with_videos"] += 1
                
                # Add frame count if available
                length = episode_info['length']
                if isinstance(length, int):
                    stats["total_frames"] += length
                
                # Get file sizes
                video_features = self.operations.metadata.get_video_features()
                paths = self.operations.file_manager.get_episode_file_paths(i, video_features)
                sizes = self.operations.file_manager.get_episode_size_info(paths)
                
                stats["file_sizes"]["total_data_size"] += sizes["data"]
                stats["file_sizes"]["total_video_size"] += sizes["total_video"]
                stats["file_sizes"]["total_size"] += sizes["total"]
                
            except Exception as e:
                print(f"Warning: Could not get statistics for episode {i}: {e}")
        
        return stats