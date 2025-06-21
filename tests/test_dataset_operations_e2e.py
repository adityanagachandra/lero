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