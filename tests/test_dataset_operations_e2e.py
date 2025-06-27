"""
End-to-end tests for dataset operations (delete, copy, etc.).
"""

import json
import pytest
from pathlib import Path
import pandas as pd


class TestDatasetDeletionE2E:
    """Test episode deletion operations end-to-end."""
    
    def test_delete_episode_dry_run(self, cli_runner, sample_dataset, episode_counter):
        """Test episode deletion in dry run mode."""
        # Verify initial state
        initial_count = episode_counter(sample_dataset)
        assert initial_count == 3
        
        # Run dry run deletion
        result = cli_runner(["--delete", "1", "--dry-run", str(sample_dataset)])
        assert result.returncode == 0
        assert "dry run" in result.stdout.lower() or "preview" in result.stdout.lower()
        
        # Verify no actual changes were made
        final_count = episode_counter(sample_dataset)
        assert final_count == 3
        
        # Verify episode 1 still exists
        data_file = sample_dataset / "data" / "chunk-000" / "episode_000001.parquet"
        assert data_file.exists()
    
    def test_delete_episode_actual(self, cli_runner, sample_dataset, episode_counter, episode_data_reader):
        """Test actual episode deletion."""
        # Verify initial state
        initial_count = episode_counter(sample_dataset)
        assert initial_count == 3
        
        # Verify episode 1 exists before deletion
        episode_1_data = episode_data_reader(sample_dataset, 1)
        assert episode_1_data["exists"]
        assert episode_1_data["data_file_exists"]
        
        # Delete episode 1
        result = cli_runner(["--delete", "1", str(sample_dataset)])
        assert result.returncode == 0
        assert "deleted" in result.stdout.lower() or "removed" in result.stdout.lower()
        
        # Verify episode count decreased
        final_count = episode_counter(sample_dataset)
        assert final_count == 2
        
        # Verify episode files are renumbered correctly
        # After deleting episode 1, episode 2 should be renumbered to episode 1
        data_file = sample_dataset / "data" / "chunk-000" / "episode_000001.parquet"
        assert data_file.exists()  # Should exist (it's the renamed episode 2)
        
        # Verify episode 2 file no longer exists (was renamed to episode 1)
        old_episode_2_file = sample_dataset / "data" / "chunk-000" / "episode_000002.parquet"
        assert not old_episode_2_file.exists()
        
        # Verify episode 1 still exists in metadata (it's the old episode 2, renumbered)
        new_episode_1_data = episode_data_reader(sample_dataset, 1)
        assert new_episode_1_data["exists"]
    
    def test_delete_first_episode(self, cli_runner, sample_dataset, episode_counter):
        """Test deleting the first episode."""
        initial_count = episode_counter(sample_dataset)
        assert initial_count == 3
        
        # Delete episode 0
        result = cli_runner(["--delete", "0", str(sample_dataset)])
        assert result.returncode == 0
        
        # Verify count decreased
        final_count = episode_counter(sample_dataset)
        assert final_count == 2
        
        # Verify episodes were renumbered properly
        # Original episode 1 should now be episode 0
        episode_0_file = sample_dataset / "data" / "chunk-000" / "episode_000000.parquet"
        assert episode_0_file.exists()
        
        episode_1_file = sample_dataset / "data" / "chunk-000" / "episode_000001.parquet"
        assert episode_1_file.exists()
        
        # Episode 2 file should not exist anymore
        episode_2_file = sample_dataset / "data" / "chunk-000" / "episode_000002.parquet"
        assert not episode_2_file.exists()
    
    def test_delete_last_episode(self, cli_runner, sample_dataset, episode_counter):
        """Test deleting the last episode."""
        initial_count = episode_counter(sample_dataset)
        assert initial_count == 3
        
        # Delete episode 2 (last episode)
        result = cli_runner(["--delete", "2", str(sample_dataset)])
        assert result.returncode == 0
        
        # Verify count decreased
        final_count = episode_counter(sample_dataset)
        assert final_count == 2
        
        # Verify episode 2 file is gone
        episode_2_file = sample_dataset / "data" / "chunk-000" / "episode_000002.parquet"
        assert not episode_2_file.exists()
        
        # Verify episodes 0 and 1 still exist
        episode_0_file = sample_dataset / "data" / "chunk-000" / "episode_000000.parquet"
        assert episode_0_file.exists()
        
        episode_1_file = sample_dataset / "data" / "chunk-000" / "episode_000001.parquet"
        assert episode_1_file.exists()
    
    def test_delete_updates_metadata(self, cli_runner, sample_dataset):
        """Test that deletion properly updates metadata files."""
        # Delete episode 1
        result = cli_runner(["--delete", "1", str(sample_dataset)])
        assert result.returncode == 0
        
        # Check info.json was updated
        with open(sample_dataset / "meta" / "info.json", "r") as f:
            info = json.load(f)
            assert info["total_episodes"] == 2
        
        # Check episodes.jsonl was updated
        episodes = []
        with open(sample_dataset / "meta" / "episodes.jsonl", "r") as f:
            for line in f:
                episodes.append(json.loads(line.strip()))
        
        assert len(episodes) == 2
        # Episode indices should be 0, 1 (renumbered)
        episode_indices = [ep["episode_index"] for ep in episodes]
        assert episode_indices == [0, 1]


class TestDatasetCopyingE2E:
    """Test episode copying operations end-to-end."""
    
    def test_copy_episode_dry_run(self, cli_runner, sample_dataset, episode_counter):
        """Test episode copying in dry run mode."""
        initial_count = episode_counter(sample_dataset)
        assert initial_count == 3
        
        # Run dry run copy
        result = cli_runner([
            "--copy", "0", 
            "--instruction", "Test copied episode",
            "--dry-run", 
            str(sample_dataset)
        ])
        assert result.returncode == 0
        assert "dry run" in result.stdout.lower() or "preview" in result.stdout.lower()
        
        # Verify no actual changes were made
        final_count = episode_counter(sample_dataset)
        assert final_count == 3
    
    def test_copy_episode_actual(self, cli_runner, sample_dataset, episode_counter, episode_data_reader):
        """Test actual episode copying."""
        initial_count = episode_counter(sample_dataset)
        assert initial_count == 3
        
        # Copy episode 0
        result = cli_runner([
            "--copy", "0",
            "--instruction", "Test copied episode",
            str(sample_dataset)
        ])
        assert result.returncode == 0
        assert "copied" in result.stdout.lower() or "copy" in result.stdout.lower()
        
        # Verify episode count increased
        final_count = episode_counter(sample_dataset)
        assert final_count == 4
        
        # Verify new episode exists (should be episode 3)
        new_episode_data = episode_data_reader(sample_dataset, 3)
        assert new_episode_data["exists"]
        assert new_episode_data["data_file_exists"]
        
        # Verify original episode 0 still exists
        original_episode_data = episode_data_reader(sample_dataset, 0)
        assert original_episode_data["exists"]
    
    def test_copy_updates_metadata(self, cli_runner, sample_dataset):
        """Test that copying properly updates metadata files."""
        # Copy episode 1
        result = cli_runner([
            "--copy", "1",
            "--instruction", "New copied task",
            str(sample_dataset)
        ])
        assert result.returncode == 0
        
        # Check info.json was updated
        with open(sample_dataset / "meta" / "info.json", "r") as f:
            info = json.load(f)
            assert info["total_episodes"] == 4
        
        # Check episodes.jsonl was updated
        episodes = []
        with open(sample_dataset / "meta" / "episodes.jsonl", "r") as f:
            for line in f:
                episodes.append(json.loads(line.strip()))
        
        assert len(episodes) == 4
        
        # Check that new episode has correct task
        new_episode = episodes[3]  # Should be the last episode
        assert new_episode["episode_index"] == 3
        assert new_episode["task"] == "New copied task"
        
        # Check tasks.jsonl was updated
        tasks = []
        with open(sample_dataset / "meta" / "tasks.jsonl", "r") as f:
            for line in f:
                tasks.append(json.loads(line.strip()))
        
        # Should have original 2 tasks plus the new one
        assert len(tasks) == 3
        new_task = tasks[2]
        assert new_task["task"] == "New copied task"
        assert new_task["task_index"] == 2
    
    def test_copy_preserves_data_structure(self, cli_runner, sample_dataset):
        """Test that copied episode preserves data structure."""
        # Copy episode 0
        result = cli_runner([
            "--copy", "0",
            "--instruction", "Structure test copy",
            str(sample_dataset)
        ])
        assert result.returncode == 0
        
        # Read original and copied episode data
        original_file = sample_dataset / "data" / "chunk-000" / "episode_000000.parquet"
        copied_file = sample_dataset / "data" / "chunk-000" / "episode_000003.parquet"
        
        assert original_file.exists()
        assert copied_file.exists()
        
        original_df = pd.read_parquet(original_file)
        copied_df = pd.read_parquet(copied_file)
        
        # Should have same structure and length
        assert len(original_df) == len(copied_df)
        assert list(original_df.columns) == list(copied_df.columns)
        
        # Episode index should be updated in copied data
        assert copied_df["episode_index"].iloc[0] == 3
        assert original_df["episode_index"].iloc[0] == 0


class TestDatasetOperationErrors:
    """Test error handling in dataset operations."""
    
    def test_delete_nonexistent_episode(self, cli_runner, sample_dataset):
        """Test deleting non-existent episode."""
        result = cli_runner(["--delete", "999", str(sample_dataset)])
        assert result.returncode == 1
        assert "error" in result.stderr.lower() or "out of range" in result.stdout.lower()
    
    def test_copy_nonexistent_episode(self, cli_runner, sample_dataset):
        """Test copying non-existent episode."""
        result = cli_runner([
            "--copy", "999",
            "--instruction", "Should fail",
            str(sample_dataset)
        ])
        assert result.returncode == 1
        assert "error" in result.stderr.lower() or "out of range" in result.stdout.lower()
    
    def test_delete_from_empty_dataset(self, cli_runner, temp_dir):
        """Test deleting from empty dataset."""
        # Create minimal dataset structure without episodes
        empty_dataset = temp_dir / "empty_dataset"
        (empty_dataset / "meta").mkdir(parents=True)
        (empty_dataset / "data" / "chunk-000").mkdir(parents=True)
        
        # Create minimal info.json
        info_data = {
            "total_episodes": 0,
            "total_tasks": 0,
            "robot_type": "so100",
            "fps": 30
        }
        
        with open(empty_dataset / "meta" / "info.json", "w") as f:
            json.dump(info_data, f)
        
        # Create empty episodes.jsonl and tasks.jsonl
        (empty_dataset / "meta" / "episodes.jsonl").touch()
        (empty_dataset / "meta" / "tasks.jsonl").touch()
        
        result = cli_runner(["--delete", "0", str(empty_dataset)])
        assert result.returncode == 1
        assert "error" in result.stderr.lower() or "out of range" in result.stdout.lower()


class TestDatasetOperationIntegration:
    """Test integration of multiple dataset operations."""
    
    def test_delete_then_copy(self, cli_runner, sample_dataset, episode_counter):
        """Test deleting an episode then copying another."""
        initial_count = episode_counter(sample_dataset)
        assert initial_count == 3
        
        # Delete episode 1
        result = cli_runner(["--delete", "1", str(sample_dataset)])
        assert result.returncode == 0
        
        middle_count = episode_counter(sample_dataset)
        assert middle_count == 2
        
        # Copy episode 0
        result = cli_runner([
            "--copy", "0",
            "--instruction", "After deletion copy",
            str(sample_dataset)
        ])
        assert result.returncode == 0
        
        final_count = episode_counter(sample_dataset)
        assert final_count == 3
    
    def test_multiple_copies(self, cli_runner, sample_dataset, episode_counter):
        """Test multiple episode copies."""
        initial_count = episode_counter(sample_dataset)
        assert initial_count == 3
        
        # Copy episode 0 twice
        result1 = cli_runner([
            "--copy", "0",
            "--instruction", "First copy",
            str(sample_dataset)
        ])
        assert result1.returncode == 0
        
        result2 = cli_runner([
            "--copy", "0",
            "--instruction", "Second copy",
            str(sample_dataset)
        ])
        assert result2.returncode == 0
        
        final_count = episode_counter(sample_dataset)
        assert final_count == 5
    
    def test_operation_sequence_metadata_consistency(self, cli_runner, sample_dataset):
        """Test that metadata remains consistent after multiple operations."""
        # Perform sequence of operations
        cli_runner(["--delete", "1", str(sample_dataset)])
        cli_runner(["--copy", "0", "--instruction", "Copy 1", str(sample_dataset)])
        cli_runner(["--copy", "1", "--instruction", "Copy 2", str(sample_dataset)])
        
        # Verify metadata consistency
        with open(sample_dataset / "meta" / "info.json", "r") as f:
            info = json.load(f)
        
        # Count actual episodes
        episodes = []
        with open(sample_dataset / "meta" / "episodes.jsonl", "r") as f:
            for line in f:
                episodes.append(json.loads(line.strip()))
        
        # Count actual tasks
        tasks = []
        with open(sample_dataset / "meta" / "tasks.jsonl", "r") as f:
            for line in f:
                tasks.append(json.loads(line.strip()))
        
        # Verify consistency
        assert info["total_episodes"] == len(episodes)
        assert info["total_tasks"] == len(tasks)
        
        # Verify episode indices are sequential
        episode_indices = [ep["episode_index"] for ep in episodes]
        expected_indices = list(range(len(episodes)))
        assert episode_indices == expected_indices


class TestDatasetMergeE2E:
    """Test dataset merge operations end-to-end."""

    def test_merge_datasets_dry_run(self, cli_runner, sample_dataset, temp_dir):
        """Test dataset merge in dry run mode."""
        # Create a second sample dataset
        dataset2 = temp_dir / "dataset2"
        self._create_minimal_dataset(dataset2, episodes=2, task_prefix="task2")
        
        output_path = temp_dir / "merged_output"
        
        # Run dry run merge
        result = cli_runner([
            "--merge", str(sample_dataset), str(dataset2),
            "--output", str(output_path),
            "--dry-run",
            str(sample_dataset)
        ])
        assert result.returncode == 0
        assert "dry run" in result.stdout.lower() or "preview" in result.stdout.lower()
        
        # Verify no output was created
        assert not output_path.exists()

    def test_merge_two_datasets(self, cli_runner, sample_dataset, temp_dir, episode_counter):
        """Test merging two datasets."""
        # Create a second sample dataset
        dataset2 = temp_dir / "dataset2" 
        self._create_minimal_dataset(dataset2, episodes=2, task_prefix="second")
        
        output_path = temp_dir / "merged_output"
        
        # Merge datasets
        result = cli_runner([
            "--merge", str(sample_dataset), str(dataset2),
            "--output", str(output_path),
            str(sample_dataset)
        ])
        assert result.returncode == 0
        assert "merged" in result.stdout.lower() or "success" in result.stdout.lower()
        
        # Verify output dataset was created
        assert output_path.exists()
        assert (output_path / "meta").exists()
        assert (output_path / "data").exists()
        
        # Check merged episode count
        merged_count = episode_counter(output_path)
        assert merged_count == 5  # 3 from sample_dataset + 2 from dataset2

    def test_merge_with_task_mapping(self, cli_runner, sample_dataset, temp_dir):
        """Test merging datasets with task mapping."""
        # Create a second dataset
        dataset2 = temp_dir / "dataset2"
        self._create_minimal_dataset(dataset2, episodes=1, task_prefix="old_task")
        
        # Create task mapping file
        mapping_file = temp_dir / "mapping.json"
        mapping = {"old_task_0": "new_task_name"}
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f)
        
        output_path = temp_dir / "mapped_output"
        
        # Merge with task mapping
        result = cli_runner([
            "--merge", str(sample_dataset), str(dataset2),
            "--output", str(output_path),
            "--task-mapping", str(mapping_file),
            str(sample_dataset)
        ])
        assert result.returncode == 0
        
        # Verify task mapping was applied
        with open(output_path / "meta" / "tasks.jsonl", 'r') as f:
            tasks = [json.loads(line) for line in f]
        
        task_names = [task["task"] for task in tasks]
        assert "new_task_name" in task_names
        assert "old_task_0" not in task_names

    def test_merge_updates_metadata_correctly(self, cli_runner, sample_dataset, temp_dir):
        """Test that merge operation updates metadata correctly."""
        # Create second dataset
        dataset2 = temp_dir / "dataset2"
        self._create_minimal_dataset(dataset2, episodes=2, task_prefix="second")
        
        output_path = temp_dir / "metadata_test_output"
        
        # Merge datasets
        result = cli_runner([
            "--merge", str(sample_dataset), str(dataset2),
            "--output", str(output_path),
            str(sample_dataset)
        ])
        assert result.returncode == 0
        
        # Check info.json
        with open(output_path / "meta" / "info.json", 'r') as f:
            info = json.load(f)
        assert "total_episodes" in info
        
        # Check episodes.jsonl
        with open(output_path / "meta" / "episodes.jsonl", 'r') as f:
            episodes = [json.loads(line) for line in f]
        
        # Should have episodes 0-4 with proper indices
        episode_indices = [ep["episode_index"] for ep in episodes]
        assert episode_indices == [0, 1, 2, 3, 4]
        
        # Check tasks.jsonl
        with open(output_path / "meta" / "tasks.jsonl", 'r') as f:
            tasks = [json.loads(line) for line in f]
        
        # Should have unique task indices
        task_indices = [task["task_index"] for task in tasks]
        assert len(set(task_indices)) == len(task_indices)

    def test_merge_nonexistent_dataset(self, cli_runner, sample_dataset, temp_dir):
        """Test merging with non-existent source dataset."""
        nonexistent = temp_dir / "nonexistent"
        output_path = temp_dir / "error_output"
        
        result = cli_runner([
            "--merge", str(sample_dataset), str(nonexistent),
            "--output", str(output_path),
            str(sample_dataset)
        ])
        assert result.returncode == 1
        assert "error" in result.stderr.lower() or "not exist" in result.stdout.lower()
        
        # Output should not be created
        assert not output_path.exists()

    def test_merge_missing_output_path(self, cli_runner, sample_dataset, temp_dir):
        """Test merge operation without output path."""
        dataset2 = temp_dir / "dataset2"
        self._create_minimal_dataset(dataset2, episodes=1)
        
        result = cli_runner([
            str(sample_dataset),
            "--merge", str(sample_dataset), str(dataset2)
        ])
        assert result.returncode == 1

    def test_merge_invalid_task_mapping(self, cli_runner, sample_dataset, temp_dir):
        """Test merge with invalid task mapping file."""
        dataset2 = temp_dir / "dataset2"
        self._create_minimal_dataset(dataset2, episodes=1)
        
        nonexistent_mapping = temp_dir / "nonexistent_mapping.json"
        output_path = temp_dir / "output"
        
        result = cli_runner([
            "--merge", str(sample_dataset), str(dataset2),
            "--output", str(output_path),
            "--task-mapping", str(nonexistent_mapping),
            str(sample_dataset)
        ])
        assert result.returncode == 1
        assert "mapping" in result.stderr.lower() or "not exist" in result.stdout.lower()

    def _create_minimal_dataset(self, path: Path, episodes: int, task_prefix: str = "task"):
        """Create a minimal dataset for testing."""
        path.mkdir(parents=True, exist_ok=True)
        (path / "meta").mkdir(exist_ok=True)
        (path / "data" / "chunk-000").mkdir(parents=True, exist_ok=True)
        (path / "videos" / "chunk-000").mkdir(parents=True, exist_ok=True)
        
        # Create info.json
        info_data = {
            "total_episodes": episodes,
            "total_tasks": episodes,
            "robot_type": "test_robot",
            "fps": 30,
            "features": {}
        }
        with open(path / "meta" / "info.json", 'w') as f:
            json.dump(info_data, f, indent=2)
        
        # Create episodes.jsonl
        with open(path / "meta" / "episodes.jsonl", 'w') as f:
            for i in range(episodes):
                episode_data = {
                    "episode_index": i,
                    "length": 100,
                    "task": f"{task_prefix}_{i}",
                    "tasks": [f"{task_prefix}_{i}"]
                }
                f.write(json.dumps(episode_data) + '\n')
        
        # Create tasks.jsonl
        with open(path / "meta" / "tasks.jsonl", 'w') as f:
            for i in range(episodes):
                task_data = {
                    "task_index": i,
                    "task": f"{task_prefix}_{i}",
                    "instruction": f"{task_prefix}_{i}"
                }
                f.write(json.dumps(task_data) + '\n')
        
        # Create sample parquet files
        for i in range(episodes):
            episode_data = pd.DataFrame({
                "episode_index": [i] * 10,
                "timestamp": range(10),
                "frame_index": range(10)
            })
            episode_file = path / "data" / "chunk-000" / f"episode_{i:06d}.parquet"
            episode_data.to_parquet(episode_file, index=False)


class TestDatasetFilterE2E:
    """Test dataset filter operations end-to-end."""

    def test_filter_exclude_features_dry_run(self, cli_runner, sample_dataset, temp_dir):
        """Test dataset filtering with exclude features in dry run mode."""
        output_path = temp_dir / "filtered_output"
        
        # Run dry run filter
        result = cli_runner([
            str(sample_dataset),
            "--filter-exclude", "observation.images.left,observation.depth",
            "--output", str(output_path),
            "--dry-run"
        ])
        assert result.returncode == 0
        assert "dry run" in result.stdout.lower() or "preview" in result.stdout.lower()
        
        # Verify no output was created
        assert not output_path.exists()

    def test_filter_exclude_features(self, cli_runner, sample_dataset, temp_dir):
        """Test dataset filtering with exclude features."""
        output_path = temp_dir / "filtered_exclude"
        
        # Create sample dataset with features
        self._add_features_to_dataset(sample_dataset)
        
        # Filter excluding specific features
        result = cli_runner([
            str(sample_dataset),
            "--filter-exclude", "observation.images.left",
            "--output", str(output_path)
        ])
        assert result.returncode == 0
        assert "filtered" in result.stdout.lower() or "success" in result.stdout.lower()
        
        # Verify output dataset was created
        assert output_path.exists()
        assert (output_path / "meta").exists()
        assert (output_path / "data").exists()
        
        # Check that excluded feature is not in filtered info.json
        with open(output_path / "meta" / "info.json", 'r') as f:
            filtered_info = json.load(f)
        
        if "features" in filtered_info:
            assert "observation.images.left" not in filtered_info["features"]

    def test_filter_include_features(self, cli_runner, sample_dataset, temp_dir):
        """Test dataset filtering with include features."""
        output_path = temp_dir / "filtered_include"
        
        # Create sample dataset with features
        self._add_features_to_dataset(sample_dataset)
        
        # Filter including only specific features
        result = cli_runner([
            str(sample_dataset),
            "--filter-include", "action,observation.state",
            "--output", str(output_path)
        ])
        assert result.returncode == 0
        
        # Verify output dataset was created
        assert output_path.exists()
        
        # Check that only included features are in filtered info.json
        with open(output_path / "meta" / "info.json", 'r') as f:
            filtered_info = json.load(f)
        
        if "features" in filtered_info:
            feature_names = set(filtered_info["features"].keys())
            expected_features = {"action", "observation.state"}
            # Only expected features should remain (if they existed in original)
            assert feature_names.issubset(expected_features)

    def test_filter_frame_range(self, cli_runner, sample_dataset, temp_dir):
        """Test dataset filtering with frame range."""
        output_path = temp_dir / "filtered_frames"
        
        # Filter with frame range
        result = cli_runner([
            str(sample_dataset),
            "--filter-frames", "5:15",
            "--output", str(output_path)
        ])
        assert result.returncode == 0
        
        # Verify output dataset was created
        assert output_path.exists()
        
        # Check that filtered parquet files exist and have correct frame range
        for episode_idx in range(3):  # sample dataset has 3 episodes
            episode_file = output_path / "data" / "chunk-000" / f"episode_{episode_idx:06d}.parquet"
            if episode_file.exists():
                df = pd.read_parquet(episode_file)
                if len(df) > 0:
                    assert df['frame_index'].min() >= 5
                    assert df['frame_index'].max() <= 15

    def test_filter_combined_exclude_and_frames(self, cli_runner, sample_dataset, temp_dir):
        """Test dataset filtering with both feature exclusion and frame range."""
        output_path = temp_dir / "filtered_combined"
        
        # Add features to dataset
        self._add_features_to_dataset(sample_dataset)
        
        # Filter with both exclude features and frame range
        result = cli_runner([
            str(sample_dataset),
            "--filter-exclude", "observation.images.left",
            "--filter-frames", "10:20",
            "--output", str(output_path)
        ])
        assert result.returncode == 0
        
        # Verify output dataset was created
        assert output_path.exists()

    def test_filter_exclude_include_mutually_exclusive(self, cli_runner, sample_dataset, temp_dir):
        """Test that exclude and include options are mutually exclusive."""
        output_path = temp_dir / "invalid_filter"
        
        result = cli_runner([
            str(sample_dataset),
            "--filter-exclude", "feature1",
            "--filter-include", "feature2",
            "--output", str(output_path)
        ])
        assert result.returncode == 1
        assert "mutually exclusive" in result.stdout.lower() or "exclusive" in result.stderr.lower()

    def test_filter_missing_output_path(self, cli_runner, sample_dataset):
        """Test filter operation without output path."""
        result = cli_runner([
            str(sample_dataset),
            "--filter-exclude", "observation.images.left"
        ])
        assert result.returncode == 1
        assert "output" in result.stdout.lower() or "required" in result.stdout.lower()

    def test_filter_invalid_frame_range(self, cli_runner, sample_dataset, temp_dir):
        """Test filter with invalid frame range format."""
        output_path = temp_dir / "invalid_frames"
        
        # Test invalid format
        result = cli_runner([
            str(sample_dataset),
            "--filter-frames", "invalid",
            "--output", str(output_path)
        ])
        assert result.returncode == 1
        assert "format" in result.stdout.lower() or "format" in result.stderr.lower()
        
        # Test negative range
        result = cli_runner([
            str(sample_dataset),
            "--filter-frames", "10:5",  # end < start
            "--output", str(output_path)
        ])
        assert result.returncode == 1

    def test_filter_preserves_metadata_structure(self, cli_runner, sample_dataset, temp_dir):
        """Test that filter operation preserves metadata structure."""
        output_path = temp_dir / "metadata_test"
        
        # Add features to dataset
        self._add_features_to_dataset(sample_dataset)
        
        # Filter dataset
        result = cli_runner([
            str(sample_dataset),
            "--filter-exclude", "observation.images.left",
            "--output", str(output_path)
        ])
        assert result.returncode == 0
        
        # Check that all required metadata files exist
        assert (output_path / "meta" / "info.json").exists()
        assert (output_path / "meta" / "episodes.jsonl").exists()
        assert (output_path / "meta" / "tasks.jsonl").exists()
        
        # Check episodes metadata
        with open(output_path / "meta" / "episodes.jsonl", 'r') as f:
            episodes = [json.loads(line) for line in f]
        
        # Should have same number of episodes
        assert len(episodes) == 3
        
        # Episode indices should be sequential
        episode_indices = [ep["episode_index"] for ep in episodes]
        assert episode_indices == [0, 1, 2]

    def _add_features_to_dataset(self, dataset_path: Path):
        """Add sample features to the dataset for testing."""
        # Update info.json with sample features
        info_path = dataset_path / "meta" / "info.json"
        with open(info_path, 'r') as f:
            info_data = json.load(f)
        
        info_data["features"] = {
            "observation.images.left": {
                "dtype": "video",
                "shape": [3, 224, 224],
                "names": ["channel", "height", "width"]
            },
            "observation.images.right": {
                "dtype": "video", 
                "shape": [3, 224, 224],
                "names": ["channel", "height", "width"]
            },
            "observation.depth": {
                "dtype": "image",
                "shape": [1, 224, 224],
                "names": ["channel", "height", "width"]
            },
            "observation.state": {
                "dtype": "float32",
                "shape": [6],
                "names": ["joint_positions"]
            },
            "action": {
                "dtype": "float32",
                "shape": [6],
                "names": ["joint_actions"]
            }
        }
        
        with open(info_path, 'w') as f:
            json.dump(info_data, f, indent=2)
        
        # Update parquet files to include feature columns
        for episode_idx in range(3):
            episode_file = dataset_path / "data" / "chunk-000" / f"episode_{episode_idx:06d}.parquet"
            if episode_file.exists():
                df = pd.read_parquet(episode_file)
                
                # Add sample feature columns
                df["observation.images.left"] = f"video_path_left_{episode_idx}"
                df["observation.images.right"] = f"video_path_right_{episode_idx}"
                df["observation.depth"] = f"depth_path_{episode_idx}"
                df["observation.state"] = [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]] * len(df)
                df["action"] = [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6]] * len(df)
                
                df.to_parquet(episode_file, index=False)