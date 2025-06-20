"""
File system utilities for dataset operations.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from .constants import (
    CHUNK_SIZE, DATA_DIR, VIDEOS_DIR, CHUNK_PATTERN, 
    EPISODE_PATTERN, PARQUET_EXT, VIDEO_EXT
)


class FileSystemManager:
    """Manages file system operations for dataset files."""
    
    def __init__(self, dataset_path: Path):
        """
        Initialize file system manager.
        
        Args:
            dataset_path: Path to the dataset root directory
        """
        self.dataset_path = dataset_path
        self.data_path = dataset_path / DATA_DIR
        self.videos_path = dataset_path / VIDEOS_DIR
    
    def get_episode_file_paths(self, episode_index: int, video_features: Dict[str, dict]) -> Dict[str, Path]:
        """
        Get file paths for a specific episode.
        
        Args:
            episode_index: Index of the episode
            video_features: Dictionary of video features from metadata
            
        Returns:
            Dictionary containing file paths
        """
        chunk = episode_index // CHUNK_SIZE
        episode_name = EPISODE_PATTERN.format(episode=episode_index)
        chunk_name = CHUNK_PATTERN.format(chunk=chunk)
        
        paths = {}
        
        # Data file path
        paths['data'] = self.data_path / chunk_name / f"{episode_name}{PARQUET_EXT}"
        
        # Video file paths
        paths['videos'] = {}
        for video_key in video_features.keys():
            video_path = self.videos_path / chunk_name / video_key / f"{episode_name}{VIDEO_EXT}"
            paths['videos'][video_key] = video_path
        
        return paths
    
    def check_episode_files_exist(self, paths: Dict[str, Path]) -> Dict[str, bool]:
        """
        Check if episode files exist.
        
        Args:
            paths: Dictionary of file paths
            
        Returns:
            Dictionary indicating which files exist
        """
        existence = {}
        
        # Check data file
        existence['data'] = paths['data'].exists()
        
        # Check video files
        existence['videos'] = {}
        for video_key, video_path in paths['videos'].items():
            existence['videos'][video_key] = video_path.exists()
        
        return existence
    
    def delete_episode_files(self, paths: Dict[str, Path]) -> List[str]:
        """
        Delete episode files.
        
        Args:
            paths: Dictionary of file paths to delete
            
        Returns:
            List of deleted file paths
        """
        deleted_files = []
        
        # Delete data file
        if paths['data'].exists():
            paths['data'].unlink()
            deleted_files.append(str(paths['data']))
        
        # Delete video files
        for video_key, video_path in paths['videos'].items():
            if video_path.exists():
                video_path.unlink()
                deleted_files.append(str(video_path))
        
        return deleted_files
    
    def copy_episode_files(self, source_paths: Dict[str, Path], target_paths: Dict[str, Path]) -> List[str]:
        """
        Copy episode files from source to target.
        
        Args:
            source_paths: Dictionary of source file paths
            target_paths: Dictionary of target file paths
            
        Returns:
            List of copied file paths
        """
        copied_files = []
        
        # Copy data file
        if source_paths['data'].exists():
            target_paths['data'].parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source_paths['data']), str(target_paths['data']))
            copied_files.append(str(target_paths['data']))
        
        # Copy video files
        for video_key, source_video_path in source_paths['videos'].items():
            target_video_path = target_paths['videos'][video_key]
            if source_video_path.exists():
                target_video_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(source_video_path), str(target_video_path))
                copied_files.append(str(target_video_path))
        
        return copied_files
    
    def renumber_episode_files(self, old_index: int, new_index: int, video_features: Dict[str, dict]) -> bool:
        """
        Renumber episode files from old index to new index.
        
        Args:
            old_index: Current episode index
            new_index: New episode index
            video_features: Dictionary of video features
            
        Returns:
            True if successful, False otherwise
        """
        try:
            old_paths = self.get_episode_file_paths(old_index, video_features)
            new_paths = self.get_episode_file_paths(new_index, video_features)
            
            # Move data file
            if old_paths['data'].exists():
                new_paths['data'].parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_paths['data']), str(new_paths['data']))
            
            # Move video files
            for video_key, old_video_path in old_paths['videos'].items():
                new_video_path = new_paths['videos'][video_key]
                if old_video_path.exists():
                    new_video_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(old_video_path), str(new_video_path))
            
            return True
        except Exception as e:
            print(f"Error renumbering episode {old_index} to {new_index}: {e}")
            return False
    
    def get_episode_size_info(self, paths: Dict[str, Path]) -> Dict[str, int]:
        """
        Get size information for episode files.
        
        Args:
            paths: Dictionary of file paths
            
        Returns:
            Dictionary containing file sizes in bytes
        """
        sizes = {}
        
        # Data file size
        if paths['data'].exists():
            sizes['data'] = paths['data'].stat().st_size
        else:
            sizes['data'] = 0
        
        # Video file sizes
        sizes['videos'] = {}
        total_video_size = 0
        for video_key, video_path in paths['videos'].items():
            if video_path.exists():
                size = video_path.stat().st_size
                sizes['videos'][video_key] = size
                total_video_size += size
            else:
                sizes['videos'][video_key] = 0
        
        sizes['total_video'] = total_video_size
        sizes['total'] = sizes['data'] + total_video_size
        
        return sizes
    
    def cleanup_empty_directories(self) -> None:
        """Clean up empty chunk directories."""
        # Clean up empty data chunk directories
        for chunk_dir in self.data_path.iterdir():
            if chunk_dir.is_dir() and not any(chunk_dir.iterdir()):
                chunk_dir.rmdir()
        
        # Clean up empty video chunk directories
        for chunk_dir in self.videos_path.iterdir():
            if chunk_dir.is_dir():
                # Check if any video subdirectories have files
                has_files = False
                for video_dir in chunk_dir.iterdir():
                    if video_dir.is_dir() and any(video_dir.iterdir()):
                        has_files = True
                        break
                
                if not has_files:
                    # Remove empty video subdirectories first
                    for video_dir in chunk_dir.iterdir():
                        if video_dir.is_dir():
                            video_dir.rmdir()
                    # Remove empty chunk directory
                    chunk_dir.rmdir()