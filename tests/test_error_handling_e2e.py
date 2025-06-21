"""
End-to-end tests for error handling scenarios.
"""

import json
import pytest
import shutil
from pathlib import Path


class TestInvalidDatasetHandling:
    """Test handling of invalid or corrupted datasets."""
    
    def test_missing_dataset_directory(self, cli_runner, temp_dir):
        """Test handling of completely missing dataset directory."""
        nonexistent_path = temp_dir / "does_not_exist"
        
        result = cli_runner([str(nonexistent_path)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'not found', 'does not exist', 'invalid', 'error'
        ])
    
    def test_missing_meta_directory(self, cli_runner, temp_dir):
        """Test handling of dataset missing meta directory."""
        incomplete_dataset = temp_dir / "incomplete_dataset"
        incomplete_dataset.mkdir()
        (incomplete_dataset / "data").mkdir()
        (incomplete_dataset / "videos").mkdir()
        # Missing meta directory
        
        result = cli_runner([str(incomplete_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'meta', 'invalid', 'missing', 'error'
        ])
    
    def test_missing_info_json(self, cli_runner, temp_dir):
        """Test handling of missing info.json file."""
        incomplete_dataset = temp_dir / "incomplete_dataset"
        (incomplete_dataset / "meta").mkdir(parents=True)
        (incomplete_dataset / "data").mkdir(parents=True)
        (incomplete_dataset / "videos").mkdir(parents=True)
        
        # Create empty episodes.jsonl and tasks.jsonl but no info.json
        (incomplete_dataset / "meta" / "episodes.jsonl").touch()
        (incomplete_dataset / "meta" / "tasks.jsonl").touch()
        
        result = cli_runner([str(incomplete_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'info.json', 'missing', 'invalid', 'error'
        ])
    
    def test_corrupted_info_json(self, cli_runner, temp_dir):
        """Test handling of corrupted info.json file."""
        corrupted_dataset = temp_dir / "corrupted_dataset"
        (corrupted_dataset / "meta").mkdir(parents=True)
        (corrupted_dataset / "data").mkdir(parents=True)
        (corrupted_dataset / "videos").mkdir(parents=True)
        
        # Create corrupted info.json
        with open(corrupted_dataset / "meta" / "info.json", "w") as f:
            f.write("{ invalid json content }")
        
        # Create empty other files
        (corrupted_dataset / "meta" / "episodes.jsonl").touch()
        (corrupted_dataset / "meta" / "tasks.jsonl").touch()
        
        result = cli_runner([str(corrupted_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'json', 'parse', 'invalid', 'error', 'corrupted'
        ])
    
    def test_missing_required_fields_in_info_json(self, cli_runner, temp_dir):
        """Test handling of info.json missing required fields."""
        incomplete_dataset = temp_dir / "incomplete_dataset"
        (incomplete_dataset / "meta").mkdir(parents=True)
        (incomplete_dataset / "data").mkdir(parents=True)
        (incomplete_dataset / "videos").mkdir(parents=True)
        
        # Create info.json missing required fields
        incomplete_info = {
            "fps": 30
            # Missing total_episodes, robot_type, etc.
        }
        
        with open(incomplete_dataset / "meta" / "info.json", "w") as f:
            json.dump(incomplete_info, f)
        
        (incomplete_dataset / "meta" / "episodes.jsonl").touch()
        (incomplete_dataset / "meta" / "tasks.jsonl").touch()
        
        result = cli_runner([str(incomplete_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'missing', 'required', 'field', 'invalid', 'error'
        ])


class TestFileSystemErrorHandling:
    """Test handling of file system related errors."""
    
    def test_permission_denied_dataset(self, cli_runner, sample_dataset):
        """Test handling of permission denied errors."""
        # Make dataset directory read-only
        try:
            sample_dataset.chmod(0o444)
            
            # Try to delete an episode (should fail due to permissions)
            result = cli_runner(["--delete", "0", str(sample_dataset)])
            assert result.returncode == 1
            
            error_output = result.stderr + result.stdout
            assert any(keyword in error_output.lower() for keyword in [
                'permission', 'denied', 'error', 'cannot'
            ])
        
        finally:
            # Restore permissions for cleanup
            sample_dataset.chmod(0o755)
    
    def test_disk_space_simulation(self, cli_runner, sample_dataset):
        """Test handling of disk space issues (simulated)."""
        # Create a scenario where copy would fail due to insufficient space
        # by making the target directory read-only to simulate permission errors
        import os
        
        # Make the data directory read-only to simulate disk space/permission issues
        data_dir = sample_dataset / "data"
        original_mode = data_dir.stat().st_mode
        
        try:
            # Remove write permissions to simulate disk space issues
            data_dir.chmod(0o444)
            
            result = cli_runner(["--copy", "0", "--instruction", "Test", str(sample_dataset)])
            assert result.returncode == 1
            
            error_output = result.stderr + result.stdout
            assert any(keyword in error_output.lower() for keyword in [
                'permission', 'error', 'cannot', 'failed'
            ])
            
        finally:
            # Restore original permissions
            data_dir.chmod(original_mode)
    
    def test_corrupted_parquet_file(self, cli_runner, sample_dataset):
        """Test handling of corrupted parquet files."""
        # Corrupt a parquet file
        parquet_file = sample_dataset / "data" / "chunk-000" / "episode_000000.parquet"
        
        with open(parquet_file, "w") as f:
            f.write("corrupted parquet content")
        
        result = cli_runner(["--episode", "0", "--show-data", str(sample_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'parquet', 'corrupted', 'error', 'cannot', 'read'
        ])


class TestOperationErrorHandling:
    """Test error handling in dataset operations."""
    
    def test_delete_out_of_range_episode(self, cli_runner, sample_dataset):
        """Test deleting episode with index out of range."""
        result = cli_runner(["--delete", "999", str(sample_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'out of range', 'invalid', 'episode', 'error'
        ])
    
    def test_copy_out_of_range_episode(self, cli_runner, sample_dataset):
        """Test copying episode with index out of range."""
        result = cli_runner(["--copy", "999", "--instruction", "Test", str(sample_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'out of range', 'invalid', 'episode', 'error'
        ])
    
    def test_negative_episode_index(self, cli_runner, sample_dataset):
        """Test negative episode indices."""
        result = cli_runner(["--episode", "-1", str(sample_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'negative', 'non-negative', 'invalid', 'error'
        ])
    
    def test_copy_without_instruction_parameter(self, cli_runner, sample_dataset):
        """Test copy operation without required instruction."""
        result = cli_runner(["--copy", "0", str(sample_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'instruction', 'required', 'missing', 'error'
        ])
    
    def test_empty_instruction_string(self, cli_runner, sample_dataset):
        """Test copy operation with empty instruction."""
        result = cli_runner(["--copy", "0", "--instruction", "", str(sample_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'instruction', 'empty', 'invalid', 'error'
        ])


class TestConcurrencyErrorHandling:
    """Test handling of concurrent access scenarios."""
    
    def test_dataset_modified_during_operation(self, cli_runner, sample_dataset):
        """Test handling of dataset modified during operation."""
        # Start an operation, then modify the dataset structure
        # This simulates concurrent access
        
        # First, verify the dataset works normally
        result = cli_runner([str(sample_dataset), "--summary"])
        assert result.returncode == 0
        
        # Remove an episode file while trying to access it
        episode_file = sample_dataset / "data" / "chunk-000" / "episode_000001.parquet"
        episode_file.unlink()
        
        # Now try to access the missing episode
        result = cli_runner([str(sample_dataset), "--episode", "1"])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'not found', 'missing', 'error', 'file'
        ])
    
    def test_metadata_inconsistency(self, cli_runner, sample_dataset):
        """Test handling of metadata inconsistency."""
        # Create inconsistent metadata (info.json says 3 episodes, but only 2 exist)
        info_path = sample_dataset / "meta" / "info.json"
        with open(info_path, "r") as f:
            info = json.load(f)
        
        # Remove one episode file but don't update metadata
        episode_file = sample_dataset / "data" / "chunk-000" / "episode_000002.parquet"
        episode_file.unlink()
        
        # Try to access the missing episode
        result = cli_runner([str(sample_dataset), "--episode", "2"])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'not found', 'missing', 'inconsistent', 'error'
        ])


class TestResourceLimitHandling:
    """Test handling of resource limitations."""
    
    def test_very_large_episode_index(self, cli_runner, sample_dataset):
        """Test handling of extremely large episode indices."""
        result = cli_runner(["--episode", "999999999", str(sample_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'out of range', 'invalid', 'large', 'error'
        ])
    
    def test_very_large_list_count(self, cli_runner, sample_dataset):
        """Test handling of extremely large list counts."""
        result = cli_runner(["--list", "999999999", str(sample_dataset)])
        
        # Should either succeed (listing all available) or fail gracefully
        if result.returncode != 0:
            error_output = result.stderr + result.stdout
            assert any(keyword in error_output.lower() for keyword in [
                'large', 'limit', 'invalid', 'error'
            ])
    
    def test_very_long_instruction_string(self, cli_runner, sample_dataset):
        """Test handling of extremely long instruction strings."""
        very_long_instruction = "A" * 10000  # 10KB string
        
        result = cli_runner([
            "--copy", "0", 
            "--instruction", very_long_instruction,
            "--dry-run",  # Use dry run to avoid actually creating large files
            str(sample_dataset)
        ])
        
        # Should either succeed or fail gracefully
        if result.returncode != 0:
            error_output = result.stderr + result.stdout
            assert any(keyword in error_output.lower() for keyword in [
                'long', 'large', 'limit', 'error'
            ])


class TestNetworkAndIOErrorHandling:
    """Test handling of network and I/O related errors."""
    
    def test_read_only_filesystem(self, cli_runner, sample_dataset):
        """Test operations on read-only filesystem."""
        # Make the entire dataset read-only
        import os
        for root, dirs, files in os.walk(sample_dataset):
            root_path = Path(root)
            # Make directories read-only
            root_path.chmod(0o555)
            # Make files read-only
            for file in files:
                file_path = root_path / file
                file_path.chmod(0o444)
        
        try:
            # Try to modify the dataset (should fail)
            result = cli_runner(["--delete", "0", str(sample_dataset)])
            assert result.returncode == 1
            
            error_output = result.stderr + result.stdout
            assert any(keyword in error_output.lower() for keyword in [
                'read-only', 'permission', 'cannot', 'error'
            ])
        
        finally:
            # Restore write permissions for cleanup
            for root, dirs, files in os.walk(sample_dataset):
                root_path = Path(root)
                # Restore directory permissions
                root_path.chmod(0o755)
                # Restore file permissions
                for file in files:
                    file_path = root_path / file
                    file_path.chmod(0o644)
    
    def test_interrupted_operation_recovery(self, cli_runner, sample_dataset):
        """Test recovery from interrupted operations."""
        # Simulate an interrupted operation by creating partial state
        
        # Start by creating a backup copy of the dataset
        backup_episodes = []
        with open(sample_dataset / "meta" / "episodes.jsonl", "r") as f:
            for line in f:
                backup_episodes.append(line.strip())
        
        # Corrupt the episodes.jsonl file (simulate interrupted write)
        with open(sample_dataset / "meta" / "episodes.jsonl", "w") as f:
            f.write("{ incomplete json")
        
        # Try to use the dataset
        result = cli_runner(["--summary", str(sample_dataset)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'json', 'parse', 'corrupted', 'error'
        ])
        
        # Restore the backup for cleanup
        with open(sample_dataset / "meta" / "episodes.jsonl", "w") as f:
            for line in backup_episodes:
                f.write(line + "\n")


class TestGracefulErrorReporting:
    """Test that errors are reported gracefully to users."""
    
    def test_error_messages_are_user_friendly(self, cli_runner, temp_dir):
        """Test that error messages are user-friendly."""
        nonexistent_path = temp_dir / "does_not_exist"
        
        result = cli_runner([str(nonexistent_path)])
        assert result.returncode == 1
        
        error_output = result.stderr + result.stdout
        
        # Error message should be informative but not too technical
        assert len(error_output) > 10  # Should have meaningful content
        assert "Traceback" not in error_output  # Should not show stack traces to users
        
        # Should contain helpful information
        assert any(keyword in error_output.lower() for keyword in [
            'path', 'directory', 'not found', 'does not exist'
        ])
    
    def test_help_available_on_error(self, cli_runner):
        """Test that help is accessible when errors occur."""
        # Run with invalid arguments
        result = cli_runner(["--invalid-argument"])
        assert result.returncode != 0
        
        # Should suggest help or show usage
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'help', 'usage', '--help', 'argument'
        ])
    
    def test_error_exit_codes_are_consistent(self, cli_runner, sample_dataset):
        """Test that error exit codes are consistent."""
        # Different types of errors should have consistent exit code (1)
        
        test_cases = [
            ["--episode", "999", str(sample_dataset)],  # Out of range
            ["--copy", "0", str(sample_dataset)],        # Missing instruction
            ["--delete", "-1", str(sample_dataset)],     # Invalid negative
            ["/nonexistent/path"]                        # Invalid path
        ]
        
        for args in test_cases:
            result = cli_runner(args)
            assert result.returncode == 1, f"Failed for args: {args}"