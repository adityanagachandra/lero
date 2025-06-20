"""
Dataset operations for episode management.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from .metadata import MetadataManager
from .file_utils import FileSystemManager
from .constants import (
    ErrorMessages, SuccessMessages, DEFAULT_FRAME_LENGTH, DEFAULT_TASK_LIST
)


class DatasetOperations:
    """Handles dataset operations like delete, copy, and episode management."""
    
    def __init__(self, dataset_path: Path):
        """
        Initialize dataset operations.
        
        Args:
            dataset_path: Path to the dataset root directory
        """
        self.dataset_path = dataset_path
        self.metadata = MetadataManager(dataset_path)
        self.file_manager = FileSystemManager(dataset_path)
    
    def get_episode_info(self, episode_index: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific episode.
        
        Args:
            episode_index: Index of the episode to retrieve
            
        Returns:
            Dictionary containing episode information
        """
        total_episodes = self.metadata.get_episode_count()
        if episode_index < 0 or episode_index >= total_episodes:
            raise ValueError(ErrorMessages.EPISODE_OUT_OF_RANGE.format(
                index=episode_index, max_range=total_episodes-1
            ))
        
        # Get episode metadata
        episode_meta = self.metadata.get_episode_metadata(episode_index)
        if not episode_meta:
            episode_meta = {
                "episode_index": episode_index, 
                "length": DEFAULT_FRAME_LENGTH, 
                "tasks": DEFAULT_TASK_LIST
            }
        
        # Get file paths
        video_features = self.metadata.get_video_features()
        paths = self.file_manager.get_episode_file_paths(episode_index, video_features)
        existence = self.file_manager.check_episode_files_exist(paths)
        
        # Extract task descriptions
        task_descriptions = episode_meta.get("tasks", DEFAULT_TASK_LIST)
        
        return {
            "episode_index": episode_index,
            "length": episode_meta.get("length", DEFAULT_FRAME_LENGTH),
            "tasks": task_descriptions,
            "data_file": paths['data'],
            "video_files": paths['videos'],
            "data_exists": existence['data'],
            "videos_exist": existence['videos']
        }
    
    def delete_episode(self, episode_index: int, dry_run: bool = False) -> bool:
        """
        Delete a specific episode and renumber all subsequent episodes.
        
        Args:
            episode_index: Index of the episode to delete
            dry_run: If True, only show what would be deleted without actually deleting
            
        Returns:
            True if successful, False otherwise
        """
        total_episodes = self.metadata.get_episode_count()
        if episode_index < 0 or episode_index >= total_episodes:
            print(ErrorMessages.EPISODE_OUT_OF_RANGE.format(
                index=episode_index, max_range=total_episodes-1
            ))
            return False
        
        try:
            episode_info = self.get_episode_info(episode_index)
            
            if dry_run:
                self._show_delete_dry_run(episode_index, episode_info, total_episodes)
                return True
            
            print(f"\nDeleting episode {episode_index}...")
            
            # Delete files
            video_features = self.metadata.get_video_features()
            paths = self.file_manager.get_episode_file_paths(episode_index, video_features)
            deleted_files = self.file_manager.delete_episode_files(paths)
            
            for file_path in deleted_files:
                print(f"Deleted: {file_path}")
            
            # Renumber subsequent episodes
            self._renumber_episodes_after_deletion(episode_index, total_episodes)
            
            # Update metadata
            self.metadata.remove_episode(episode_index)
            self.metadata.save_metadata()
            
            # Clean up empty directories
            self.file_manager.cleanup_empty_directories()
            
            print(SuccessMessages.EPISODE_DELETED.format(index=episode_index))
            return True
            
        except Exception as e:
            print(ErrorMessages.EPISODE_DELETE_ERROR.format(index=episode_index, error=e))
            return False
    
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
        total_episodes = self.metadata.get_episode_count()
        if source_episode_index < 0 or source_episode_index >= total_episodes:
            print(ErrorMessages.EPISODE_OUT_OF_RANGE.format(
                index=source_episode_index, max_range=total_episodes-1
            ))
            return False
        
        try:
            source_info = self.get_episode_info(source_episode_index)
            target_index = total_episodes
            
            if dry_run:
                self._show_copy_dry_run(source_episode_index, target_index, source_info, new_instruction)
                return True
            
            print(f"\nCopying episode {source_episode_index} to episode {target_index} with new instruction...")
            
            # Get file paths
            video_features = self.metadata.get_video_features()
            source_paths = self.file_manager.get_episode_file_paths(source_episode_index, video_features)
            target_paths = self.file_manager.get_episode_file_paths(target_index, video_features)
            
            # Copy files
            copied_files = self.file_manager.copy_episode_files(source_paths, target_paths)
            
            for file_path in copied_files:
                print(f"Copied to: {file_path}")
            
            # Update episode indices in the copied parquet file
            if target_paths['data'].exists():
                self._update_episode_indices_in_parquet(target_paths['data'], target_index)
            
            # Add new task and update metadata
            task_index = self.metadata.add_or_get_task(new_instruction)
            self.metadata.add_episode(target_index, source_info['length'], [new_instruction])
            self.metadata.save_metadata()
            
            print(SuccessMessages.EPISODE_COPIED.format(
                source=source_episode_index, 
                target=target_index, 
                instruction=new_instruction
            ))
            return True
            
        except Exception as e:
            print(ErrorMessages.EPISODE_COPY_ERROR.format(index=source_episode_index, error=e))
            return False
    
    def _show_delete_dry_run(self, episode_index: int, episode_info: Dict[str, Any], total_episodes: int) -> None:
        """Show what would be deleted in a dry run."""
        print(f"\n=== {SuccessMessages.DRY_RUN_DELETE.format(index=episode_index)} ===")
        print(f"Data file: {episode_info['data_file']}")
        
        for video_key, video_path in episode_info['video_files'].items():
            print(f"Video file ({video_key}): {video_path}")
        
        print(f"\nWould renumber episodes {episode_index + 1}-{total_episodes - 1}")
    
    def _show_copy_dry_run(self, source_index: int, target_index: int, source_info: Dict[str, Any], instruction: str) -> None:
        """Show what would be copied in a dry run."""
        print(f"\n=== {SuccessMessages.DRY_RUN_COPY.format(source=source_index, target=target_index)} ===")
        print(f"Source data file: {source_info['data_file']}")
        
        for video_key, video_path in source_info['video_files'].items():
            print(f"Source video file ({video_key}): {video_path}")
        
        print(f"New instruction: {instruction}")
    
    def _renumber_episodes_after_deletion(self, deleted_index: int, total_episodes: int) -> None:
        """
        Renumber all episodes after the deleted episode index.
        
        Args:
            deleted_index: Index of the deleted episode
            total_episodes: Total number of episodes before deletion
        """
        video_features = self.metadata.get_video_features()
        
        # Renumber data files and video files
        for current_index in range(deleted_index + 1, total_episodes):
            new_index = current_index - 1
            self.file_manager.renumber_episode_files(current_index, new_index, video_features)
    
    def _update_episode_indices_in_parquet(self, parquet_path: Path, new_episode_index: int) -> None:
        """
        Update episode indices in a parquet file.
        
        Args:
            parquet_path: Path to the parquet file
            new_episode_index: New episode index to set
        """
        try:
            df = pd.read_parquet(parquet_path)
            if 'episode_index' in df.columns:
                df['episode_index'] = new_episode_index
                df.to_parquet(parquet_path, index=False)
        except Exception as e:
            print(f"Warning: Could not update episode indices in {parquet_path}: {e}")
    
    def get_dataset_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the dataset.
        
        Returns:
            Dictionary containing dataset summary
        """
        summary = self.metadata.get_dataset_summary()
        summary['dataset_path'] = str(self.dataset_path)
        return summary
    
    def count_episodes(self) -> int:
        """
        Count the total number of episodes in the dataset.
        
        Returns:
            Number of episodes
        """
        return self.metadata.get_episode_count()
    
    def reload_metadata(self) -> None:
        """Reload metadata from disk."""
        self.metadata._load_metadata()