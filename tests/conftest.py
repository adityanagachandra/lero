"""
Pytest configuration and fixtures for E2E testing.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator
import pytest
import pandas as pd


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_dataset(temp_dir: Path) -> Path:
    """Create a minimal sample dataset for testing."""
    dataset_path = temp_dir / "test_dataset"
    
    # Create directory structure
    (dataset_path / "meta").mkdir(parents=True)
    (dataset_path / "data" / "chunk-000").mkdir(parents=True)
    (dataset_path / "videos" / "chunk-000" / "observation.images.left").mkdir(parents=True)
    (dataset_path / "videos" / "chunk-000" / "observation.images.wrist.right").mkdir(parents=True)
    
    # Create info.json
    info_data = {
        "codebase_version": "v2.1",
        "data_path": "data",
        "dataset_type": "LeRobotDataset",
        "fps": 30,
        "robot_type": "so100",
        "total_episodes": 3,
        "total_frames": 300,
        "total_tasks": 2,
        "total_videos": 6,
        "video_path": "videos"
    }
    
    with open(dataset_path / "meta" / "info.json", "w") as f:
        json.dump(info_data, f, indent=2)
    
    # Create tasks.jsonl
    tasks = [
        {"task_index": 0, "task": "Pick up the red block"},
        {"task_index": 1, "task": "Place the block in container"}
    ]
    
    with open(dataset_path / "meta" / "tasks.jsonl", "w") as f:
        for task in tasks:
            f.write(json.dumps(task) + "\n")
    
    # Create episodes.jsonl
    episodes = []
    for i in range(3):
        episode = {
            "episode_index": i,
            "task": tasks[i % 2]["task"],
            "task_index": i % 2,
            "length": 100,
            "timestamp": f"2024-01-{i+1:02d}T10:00:00"
        }
        episodes.append(episode)
    
    with open(dataset_path / "meta" / "episodes.jsonl", "w") as f:
        for episode in episodes:
            f.write(json.dumps(episode) + "\n")
    
    # Create sample parquet files
    for i in range(3):
        # Create sample data with proper structure
        data = {
            "episode_index": [i] * 100,
            "frame_index": list(range(100)),
            "timestamp": [f"2024-01-{i+1:02d}T10:00:{j:02d}" for j in range(100)],
            "observation.state": [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6] for _ in range(100)],
            "action": [[0.01, 0.02, 0.03, 0.04, 0.05, 0.06] for _ in range(100)]
        }
        
        df = pd.DataFrame(data)
        parquet_path = dataset_path / "data" / "chunk-000" / f"episode_{i:06d}.parquet"
        df.to_parquet(parquet_path, index=False)
    
    # Create dummy video files (empty files for testing)
    for i in range(3):
        for camera in ["observation.images.left", "observation.images.wrist.right"]:
            video_path = dataset_path / "videos" / "chunk-000" / camera / f"episode_{i:06d}.mp4"
            video_path.touch()
    
    return dataset_path


@pytest.fixture
def cli_runner():
    """Fixture to run CLI commands."""
    import subprocess
    import sys
    from pathlib import Path
    
    def run_command(args: list, cwd: Path = None) -> subprocess.CompletedProcess:
        """Run a CLI command and return the result."""
        cmd = [sys.executable, "-m", "lerobot_dataset_editor"] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd or Path.cwd()
        )
        return result
    
    return run_command


@pytest.fixture
def dataset_validator():
    """Fixture to validate dataset structure and content."""
    def validate_dataset_structure(dataset_path: Path) -> Dict[str, Any]:
        """Validate that a dataset has the expected structure."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required directories
        required_dirs = [
            "meta",
            "data",
            "videos"
        ]
        
        for dir_name in required_dirs:
            if not (dataset_path / dir_name).exists():
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing directory: {dir_name}")
        
        # Check required metadata files
        required_files = [
            "meta/info.json",
            "meta/episodes.jsonl",
            "meta/tasks.jsonl"
        ]
        
        for file_path in required_files:
            if not (dataset_path / file_path).exists():
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing file: {file_path}")
        
        # Validate info.json structure
        try:
            with open(dataset_path / "meta" / "info.json", "r") as f:
                info = json.load(f)
                required_keys = ["total_episodes", "total_tasks", "fps", "robot_type"]
                for key in required_keys:
                    if key not in info:
                        validation_result["errors"].append(f"Missing key in info.json: {key}")
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Error reading info.json: {e}")
        
        return validation_result
    
    return validate_dataset_structure


@pytest.fixture
def episode_counter():
    """Fixture to count episodes in a dataset."""
    def count_episodes(dataset_path: Path) -> int:
        """Count the number of episodes in a dataset."""
        try:
            with open(dataset_path / "meta" / "info.json", "r") as f:
                info = json.load(f)
                return info.get("total_episodes", 0)
        except Exception:
            return 0
    
    return count_episodes


@pytest.fixture
def episode_data_reader():
    """Fixture to read episode data."""
    def read_episode_data(dataset_path: Path, episode_index: int) -> Dict[str, Any]:
        """Read episode data and return information."""
        result = {
            "exists": False,
            "data_file_exists": False,
            "video_files_exist": {},
            "data_length": 0
        }
        
        # Check data file
        data_file = dataset_path / "data" / "chunk-000" / f"episode_{episode_index:06d}.parquet"
        if data_file.exists():
            result["data_file_exists"] = True
            try:
                df = pd.read_parquet(data_file)
                result["data_length"] = len(df)
                result["exists"] = True
            except Exception:
                pass
        
        # Check video files
        cameras = ["observation.images.left", "observation.images.wrist.right"]
        for camera in cameras:
            video_file = dataset_path / "videos" / "chunk-000" / camera / f"episode_{episode_index:06d}.mp4"
            result["video_files_exist"][camera] = video_file.exists()
        
        return result
    
    return read_episode_data