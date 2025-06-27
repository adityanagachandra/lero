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
        
        # Check if the data file exists - this is critical for episode access
        if not existence['data']:
            raise ValueError(f"Episode {episode_index} data file not found: {paths['data']}")
        
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
    
    def merge_datasets(self, source_datasets: List[Path], output_path: Path, task_mapping: Optional[Dict[str, str]] = None, dry_run: bool = False) -> bool:
        """
        Merge multiple datasets into a single dataset.
        
        Args:
            source_datasets: List of paths to source datasets
            output_path: Path where the merged dataset will be created
            task_mapping: Optional mapping from original task names to new task names
            dry_run: If True, only show what would be merged without actually merging
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if dry_run:
                return self._show_merge_dry_run(source_datasets, output_path, task_mapping)
            
            print(f"\nMerging {len(source_datasets)} datasets into {output_path}...")
            
            # Create output directory structure
            self._create_output_directory_structure(output_path)
            
            # Initialize merged metadata
            merged_info = self._initialize_merged_info()
            merged_episodes = []
            merged_tasks = {}
            
            episode_offset = 0
            task_id_offset = 0
            
            # Process each source dataset
            for i, source_path in enumerate(source_datasets):
                print(f"Processing dataset {i+1}/{len(source_datasets)}: {source_path}")
                
                source_ops = DatasetOperations(source_path)
                source_summary = source_ops.get_dataset_summary()
                
                # Copy episodes from source to output
                episodes_copied = self._copy_episodes_to_merged_dataset(
                    source_ops, output_path, episode_offset, task_id_offset, task_mapping
                )
                
                # Update metadata
                source_episodes = source_ops.metadata.get_all_episodes()
                source_tasks = source_ops.metadata.get_all_tasks()
                
                self._merge_episodes_metadata(merged_episodes, source_episodes, episode_offset, task_mapping)
                self._merge_tasks_metadata(merged_tasks, source_tasks, task_id_offset, task_mapping)
                
                episode_offset += len(source_episodes)
                task_id_offset += len(source_tasks)
                
                print(f"Copied {episodes_copied} episodes from {source_path}")
            
            # Update merged info with final counts
            merged_info["total_episodes"] = episode_offset
            merged_info["total_tasks"] = len(merged_tasks)
            
            # Save merged metadata
            self._save_merged_metadata(output_path, merged_info, merged_episodes, merged_tasks)
            
            print(f"\nSuccessfully merged {len(source_datasets)} datasets into {output_path}")
            print(f"Total episodes: {episode_offset}")
            print(f"Total tasks: {len(merged_tasks)}")
            
            return True
            
        except Exception as e:
            print(f"Error merging datasets: {e}")
            return False
    
    def _show_merge_dry_run(self, source_datasets: List[Path], output_path: Path, task_mapping: Optional[Dict[str, str]]) -> bool:
        """Show what would be merged in a dry run."""
        print(f"\n=== DRY RUN: Merging {len(source_datasets)} datasets ===")
        print(f"Output path: {output_path}")
        
        total_episodes = 0
        all_tasks = set()
        
        for i, source_path in enumerate(source_datasets):
            try:
                source_ops = DatasetOperations(source_path)
                summary = source_ops.get_dataset_summary()
                episodes = summary.get('episode_count', 0)
                tasks = summary.get('task_names', [])
                
                print(f"\nDataset {i+1}: {source_path}")
                print(f"  Episodes: {episodes}")
                print(f"  Tasks: {', '.join(tasks) if tasks else 'None'}")
                
                total_episodes += episodes
                all_tasks.update(tasks)
                
            except Exception as e:
                print(f"  Error reading dataset: {e}")
                return False
        
        print(f"\nSummary:")
        print(f"  Total episodes: {total_episodes}")
        print(f"  Unique tasks: {len(all_tasks)}")
        
        if task_mapping:
            print(f"  Task mapping:")
            for old_task, new_task in task_mapping.items():
                print(f"    '{old_task}' -> '{new_task}'")
        
        return True
    
    def _create_output_directory_structure(self, output_path: Path) -> None:
        """Create the directory structure for the merged dataset."""
        output_path.mkdir(parents=True, exist_ok=True)
        (output_path / "meta").mkdir(exist_ok=True)
        (output_path / "data" / "chunk-000").mkdir(parents=True, exist_ok=True)
        (output_path / "videos" / "chunk-000").mkdir(parents=True, exist_ok=True)
    
    def _initialize_merged_info(self) -> Dict[str, Any]:
        """Initialize info.json for the merged dataset."""
        return {
            "codebase_version": "0.1.0",
            "data_path": "data",
            "video_path": "videos",
            "features": {},
            "total_episodes": 0,
            "total_tasks": 0,
            "robot_type": "merged",
            "fps": 30
        }
    
    def _copy_episodes_to_merged_dataset(self, source_ops: 'DatasetOperations', output_path: Path, 
                                       episode_offset: int, task_id_offset: int, 
                                       task_mapping: Optional[Dict[str, str]]) -> int:
        """Copy episodes from source dataset to merged dataset."""
        source_episodes = source_ops.metadata.get_all_episodes()
        video_features = source_ops.metadata.get_video_features()
        episodes_copied = 0
        
        for episode in source_episodes:
            source_index = episode['episode_index']
            target_index = source_index + episode_offset
            
            # Get source file paths
            source_paths = source_ops.file_manager.get_episode_file_paths(source_index, video_features)
            
            # Create target file paths in the merged dataset
            output_file_manager = FileSystemManager(output_path)
            target_paths = output_file_manager.get_episode_file_paths(target_index, video_features)
            
            # Copy files
            if source_paths['data'].exists():
                # Copy and update episode indices in parquet file
                target_paths['data'].parent.mkdir(parents=True, exist_ok=True)
                df = pd.read_parquet(source_paths['data'])
                if 'episode_index' in df.columns:
                    df['episode_index'] = target_index
                df.to_parquet(target_paths['data'], index=False)
                
                # Copy video files
                for video_key, source_video_path in source_paths['videos'].items():
                    if source_video_path.exists():
                        target_video_path = target_paths['videos'][video_key]
                        target_video_path.parent.mkdir(parents=True, exist_ok=True)
                        import shutil
                        shutil.copy2(source_video_path, target_video_path)
                
                episodes_copied += 1
        
        return episodes_copied
    
    def _merge_episodes_metadata(self, merged_episodes: List[Dict], source_episodes: List[Dict], 
                               episode_offset: int, task_mapping: Optional[Dict[str, str]]) -> None:
        """Merge episode metadata with offset adjustments."""
        for episode in source_episodes:
            merged_episode = episode.copy()
            merged_episode['episode_index'] = episode['episode_index'] + episode_offset
            
            # Apply task mapping if provided
            if task_mapping and 'tasks' in merged_episode:
                mapped_tasks = []
                for task in merged_episode['tasks']:
                    mapped_tasks.append(task_mapping.get(task, task))
                merged_episode['tasks'] = mapped_tasks
            
            merged_episodes.append(merged_episode)
    
    def _merge_tasks_metadata(self, merged_tasks: Dict, source_tasks: Dict, 
                            task_id_offset: int, task_mapping: Optional[Dict[str, str]]) -> None:
        """Merge task metadata with ID offset adjustments."""
        for task_id, task_info in source_tasks.items():
            new_task_id = str(int(task_id) + task_id_offset)
            task_name = task_info.get('task', task_info.get('instruction', ''))
            
            # Apply task mapping if provided
            if task_mapping and task_name in task_mapping:
                task_name = task_mapping[task_name]
            
            merged_tasks[new_task_id] = {
                "task": task_name,
                "instruction": task_name
            }
    
    def _save_merged_metadata(self, output_path: Path, info: Dict[str, Any], 
                            episodes: List[Dict], tasks: Dict[str, Any]) -> None:
        """Save merged metadata to the output dataset."""
        import json
        
        # Save info.json
        with open(output_path / "meta" / "info.json", 'w') as f:
            json.dump(info, f, indent=2)
        
        # Save episodes.jsonl
        with open(output_path / "meta" / "episodes.jsonl", 'w') as f:
            for episode in episodes:
                f.write(json.dumps(episode) + '\n')
        
        # Save tasks.jsonl
        with open(output_path / "meta" / "tasks.jsonl", 'w') as f:
            for task_id, task_info in tasks.items():
                task_data = {"task_index": int(task_id), **task_info}
                f.write(json.dumps(task_data) + '\n')
    
    def filter_dataset(self, output_path: Path, exclude_features: Optional[List[str]] = None, 
                      include_features: Optional[List[str]] = None, frame_range: Optional[tuple] = None,
                      dry_run: bool = False) -> bool:
        """
        Filter dataset by excluding/including specific features and create a new dataset.
        
        Args:
            output_path: Path where the filtered dataset will be created
            exclude_features: List of feature names to exclude
            include_features: List of feature names to include (exclusive with exclude_features)
            frame_range: Tuple of (start_frame, end_frame) to filter frames
            dry_run: If True, only show what would be filtered without actually filtering
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if dry_run:
                return self._show_filter_dry_run(output_path, exclude_features, include_features, frame_range)
            
            print(f"\nFiltering dataset from {self.dataset_path} to {output_path}...")
            
            # Create output directory structure
            self._create_output_directory_structure(output_path)
            
            # Get all features from source dataset
            all_features = self._get_all_features()
            
            # Determine which features to keep
            features_to_keep = self._determine_features_to_keep(all_features, exclude_features, include_features)
            
            print(f"Keeping {len(features_to_keep)} out of {len(all_features)} features")
            
            # Filter episodes
            source_episodes = self.metadata.get_all_episodes()
            filtered_count = 0
            
            for episode in source_episodes:
                episode_index = episode['episode_index']
                success = self._filter_episode_data(
                    episode_index, output_path, features_to_keep, frame_range
                )
                if success:
                    filtered_count += 1
            
            # Create filtered metadata
            filtered_info = self._create_filtered_info(all_features, features_to_keep)
            filtered_episodes = self._create_filtered_episodes(source_episodes, frame_range)
            source_tasks = self.metadata.get_all_tasks()
            
            # Save filtered metadata
            self._save_merged_metadata(output_path, filtered_info, filtered_episodes, source_tasks)
            
            print(f"\nSuccessfully filtered dataset to {output_path}")
            print(f"Filtered {filtered_count} episodes")
            print(f"Excluded features: {set(all_features) - set(features_to_keep)}")
            
            return True
            
        except Exception as e:
            print(f"Error filtering dataset: {e}")
            return False
    
    def _show_filter_dry_run(self, output_path: Path, exclude_features: Optional[List[str]], 
                           include_features: Optional[List[str]], frame_range: Optional[tuple]) -> bool:
        """Show what would be filtered in a dry run."""
        print(f"\n=== DRY RUN: Filtering dataset ===")
        print(f"Source: {self.dataset_path}")
        print(f"Output: {output_path}")
        
        all_features = self._get_all_features()
        features_to_keep = self._determine_features_to_keep(all_features, exclude_features, include_features)
        features_to_exclude = set(all_features) - set(features_to_keep)
        
        print(f"\nTotal features: {len(all_features)}")
        print(f"Features to keep: {len(features_to_keep)}")
        print(f"Features to exclude: {len(features_to_exclude)}")
        
        if features_to_exclude:
            print(f"\nExcluded features:")
            for feature in sorted(features_to_exclude):
                print(f"  - {feature}")
        
        if features_to_keep:
            print(f"\nKept features:")
            for feature in sorted(features_to_keep):
                print(f"  - {feature}")
        
        if frame_range:
            print(f"\nFrame range filter: {frame_range[0]}-{frame_range[1]}")
        
        episode_count = self.metadata.get_episode_count()
        print(f"\nEpisodes to process: {episode_count}")
        
        return True
    
    def _get_all_features(self) -> List[str]:
        """Get all feature names from the dataset."""
        features = []
        if self.metadata.info and "features" in self.metadata.info:
            features = list(self.metadata.info["features"].keys())
        return features
    
    def _determine_features_to_keep(self, all_features: List[str], exclude_features: Optional[List[str]], 
                                  include_features: Optional[List[str]]) -> List[str]:
        """Determine which features to keep based on include/exclude lists."""
        if include_features is not None:
            # Include mode: only keep specified features
            return [f for f in include_features if f in all_features]
        elif exclude_features is not None:
            # Exclude mode: keep all except specified features
            return [f for f in all_features if f not in exclude_features]
        else:
            # No filtering: keep all features
            return all_features.copy()
    
    def _filter_episode_data(self, episode_index: int, output_path: Path, 
                           features_to_keep: List[str], frame_range: Optional[tuple]) -> bool:
        """Filter data for a single episode."""
        try:
            # Get source file paths
            video_features = self.metadata.get_video_features()
            source_paths = self.file_manager.get_episode_file_paths(episode_index, video_features)
            
            # Read source parquet data
            if not source_paths['data'].exists():
                print(f"Warning: Episode {episode_index} data file not found")
                return False
            
            df = pd.read_parquet(source_paths['data'])
            
            # Apply frame range filter
            if frame_range:
                start_frame, end_frame = frame_range
                df = df[(df['frame_index'] >= start_frame) & (df['frame_index'] <= end_frame)]
            
            # Filter columns to keep only desired features
            columns_to_keep = ['episode_index', 'frame_index', 'timestamp']
            for feature in features_to_keep:
                if feature in df.columns:
                    columns_to_keep.append(feature)
            
            filtered_df = df[columns_to_keep]
            
            # Save filtered parquet data
            output_file_manager = FileSystemManager(output_path)
            target_paths = output_file_manager.get_episode_file_paths(episode_index, {})
            target_paths['data'].parent.mkdir(parents=True, exist_ok=True)
            filtered_df.to_parquet(target_paths['data'], index=False)
            
            # Copy video files for kept video features
            video_features_to_keep = {k: v for k, v in video_features.items() if k in features_to_keep}
            if video_features_to_keep:
                target_video_paths = output_file_manager.get_episode_file_paths(episode_index, video_features_to_keep)
                for video_key, source_video_path in source_paths['videos'].items():
                    if video_key in features_to_keep and source_video_path.exists():
                        target_video_path = target_video_paths['videos'][video_key]
                        target_video_path.parent.mkdir(parents=True, exist_ok=True)
                        import shutil
                        shutil.copy2(source_video_path, target_video_path)
            
            return True
            
        except Exception as e:
            print(f"Error filtering episode {episode_index}: {e}")
            return False
    
    def _create_filtered_info(self, all_features: List[str], features_to_keep: List[str]) -> Dict[str, Any]:
        """Create filtered info.json with only kept features."""
        # Start with original info
        filtered_info = self.metadata.info.copy() if self.metadata.info else {}
        
        # Filter features
        if "features" in filtered_info:
            original_features = filtered_info["features"]
            filtered_features = {k: v for k, v in original_features.items() if k in features_to_keep}
            filtered_info["features"] = filtered_features
        
        return filtered_info
    
    def _create_filtered_episodes(self, source_episodes: List[Dict], frame_range: Optional[tuple]) -> List[Dict]:
        """Create filtered episodes metadata."""
        filtered_episodes = []
        for episode in source_episodes:
            filtered_episode = episode.copy()
            
            # Adjust episode length if frame range is applied
            if frame_range:
                start_frame, end_frame = frame_range
                original_length = episode.get('length', 0)
                new_length = min(end_frame - start_frame + 1, original_length)
                filtered_episode['length'] = new_length
            
            filtered_episodes.append(filtered_episode)
        
        return filtered_episodes