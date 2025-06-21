"""
Metadata management for LeRobot datasets.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from .constants import (
    META_DIR, INFO_FILE, EPISODES_FILE, TASKS_FILE,
    ErrorMessages
)


class MetadataManager:
    """Manages dataset metadata including info, episodes, and tasks."""
    
    def __init__(self, dataset_path: Path):
        """
        Initialize metadata manager.
        
        Args:
            dataset_path: Path to the dataset root directory
        """
        self.dataset_path = dataset_path
        self.meta_path = dataset_path / META_DIR
        self.info: Optional[Dict[str, Any]] = None
        self.episodes: List[Dict[str, Any]] = []
        self.tasks: List[Dict[str, Any]] = []
        
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load all metadata from disk."""
        self._load_info()
        self._load_episodes()
        self._load_tasks()
    
    def _load_info(self) -> None:
        """Load dataset info from info.json."""
        info_path = self.meta_path / INFO_FILE
        if info_path.exists():
            with open(info_path, 'r') as f:
                self.info = json.load(f)
        else:
            raise FileNotFoundError(ErrorMessages.DATASET_NOT_FOUND.format(path=info_path))
    
    def _load_episodes(self) -> None:
        """Load episodes metadata from episodes.jsonl."""
        episodes_path = self.meta_path / EPISODES_FILE
        self.episodes = []
        
        if episodes_path.exists():
            with open(episodes_path, 'r') as f:
                for line in f:
                    if line.strip():
                        self.episodes.append(json.loads(line.strip()))
    
    def _load_tasks(self) -> None:
        """Load tasks from tasks.jsonl."""
        tasks_path = self.meta_path / TASKS_FILE
        self.tasks = []
        
        if tasks_path.exists():
            with open(tasks_path, 'r') as f:
                for line in f:
                    if line.strip():
                        self.tasks.append(json.loads(line.strip()))
    
    def save_metadata(self) -> None:
        """Save all metadata to disk."""
        self._save_info()
        self._save_episodes()
        self._save_tasks()
    
    def _save_info(self) -> None:
        """Save info.json to disk."""
        if self.info:
            info_path = self.meta_path / INFO_FILE
            info_path.parent.mkdir(parents=True, exist_ok=True)
            with open(info_path, 'w') as f:
                json.dump(self.info, f, indent=2)
    
    def _save_episodes(self) -> None:
        """Save episodes.jsonl to disk."""
        episodes_path = self.meta_path / EPISODES_FILE
        episodes_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(episodes_path, 'w') as f:
            for episode in sorted(self.episodes, key=lambda x: x.get("episode_index", 0)):
                f.write(json.dumps(episode) + '\n')
    
    def _save_tasks(self) -> None:
        """Save tasks.jsonl to disk."""
        tasks_path = self.meta_path / TASKS_FILE
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(tasks_path, 'w') as f:
            for task in sorted(self.tasks, key=lambda x: x.get("task_index", 0)):
                f.write(json.dumps(task) + '\n')
    
    def get_episode_count(self) -> int:
        """
        Get the total number of episodes.
        
        Returns:
            Number of episodes
        """
        if self.info and "total_episodes" in self.info:
            return self.info["total_episodes"]
        else:
            return len(self.episodes)
    
    def get_episode_metadata(self, episode_index: int) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific episode.
        
        Args:
            episode_index: Index of the episode
            
        Returns:
            Episode metadata dictionary or None if not found
        """
        for episode in self.episodes:
            if episode.get("episode_index") == episode_index:
                return episode
        return None
    
    def add_or_get_task(self, instruction: str) -> int:
        """
        Add a new task or get existing task index.
        
        Args:
            instruction: Task instruction text
            
        Returns:
            Task index
        """
        # Check if task already exists
        for task in self.tasks:
            if task.get("task") == instruction:
                return task.get("task_index", 0)
        
        # Add new task
        new_task_index = len(self.tasks)
        new_task = {"task_index": new_task_index, "task": instruction}
        self.tasks.append(new_task)
        return new_task_index
    
    def remove_episode(self, episode_index: int) -> None:
        """
        Remove an episode from metadata.
        
        Args:
            episode_index: Index of episode to remove
        """
        self.episodes = [ep for ep in self.episodes if ep.get("episode_index") != episode_index]
        
        # Renumber remaining episodes
        for episode in self.episodes:
            if episode.get("episode_index", 0) > episode_index:
                episode["episode_index"] -= 1
        
        # Update info
        if self.info:
            self.info["total_episodes"] = len(self.episodes)
            if "total_frames" in self.info:
                # Recalculate total frames (approximation)
                self.info["total_frames"] = sum(ep.get("length", 0) for ep in self.episodes)
    
    def add_episode(self, episode_index: int, length: Any, tasks: List[str]) -> None:
        """
        Add a new episode to metadata.
        
        Args:
            episode_index: Index of the new episode
            length: Length of the episode
            tasks: List of task descriptions
        """
        # For consistency with existing format, use the first task as the main task
        task = tasks[0] if tasks else "Unknown task"
        
        # Get or create task index
        task_index = self.add_or_get_task(task)
        
        new_episode = {
            "episode_index": episode_index,
            "task": task,
            "task_index": task_index,
            "length": length,
            "timestamp": f"2024-01-01T10:00:00"  # Default timestamp
        }
        
        self.episodes.append(new_episode)
        
        # Update info
        if self.info:
            self.info["total_episodes"] = len(self.episodes)
            if "total_frames" in self.info and isinstance(length, int):
                self.info["total_frames"] = self.info.get("total_frames", 0) + length
            if "total_tasks" in self.info:
                self.info["total_tasks"] = len(self.tasks)
    
    def get_video_features(self) -> Dict[str, Dict[str, Any]]:
        """
        Get video features from dataset info.
        
        Returns:
            Dictionary of video features
        """
        video_features = {}
        if self.info and "features" in self.info:
            for feature_name, feature_info in self.info["features"].items():
                if feature_info.get("dtype") == "video":
                    video_features[feature_name] = feature_info
        return video_features
    
    def get_dataset_summary(self) -> Dict[str, Any]:
        """
        Get a summary of dataset information.
        
        Returns:
            Dictionary containing dataset summary
        """
        summary = {
            "total_episodes": self.get_episode_count(),
            "total_tasks": len(self.tasks)
        }
        
        if self.info:
            summary.update({
                "total_frames": self.info.get("total_frames", "Unknown"),
                "robot_type": self.info.get("robot_type", "Unknown"),
                "fps": self.info.get("fps", "Unknown"),
                "codebase_version": self.info.get("codebase_version", "Unknown")
            })
        
        return summary