"""
End-to-end tests for CLI functionality.
"""

import json
import pytest
from pathlib import Path


class TestCLIBasicCommands:
    """Test basic CLI commands and functionality."""
    
    def test_help_command(self, cli_runner):
        """Test that help command works."""
        result = cli_runner(["--help"])
        assert result.returncode == 0
        assert "LeRobot Dataset Editor Tool" in result.stdout
        assert "--summary" in result.stdout
        assert "--list" in result.stdout
        assert "--gui" in result.stdout
    
    def test_dataset_summary(self, cli_runner, sample_dataset):
        """Test dataset summary command."""
        result = cli_runner(["--summary", str(sample_dataset)])
        assert result.returncode == 0
        assert "Dataset Summary" in result.stdout
        assert "Total episodes: 3" in result.stdout
        assert "Total tasks: 2" in result.stdout
        assert "Robot type: so100" in result.stdout
    
    def test_dataset_overview_default(self, cli_runner, sample_dataset):
        """Test default dataset overview (no flags)."""
        result = cli_runner([str(sample_dataset)])
        assert result.returncode == 0
        # Should show summary by default when no other action is specified
        assert "Dataset Summary" in result.stdout
    
    def test_list_episodes_default(self, cli_runner, sample_dataset):
        """Test listing episodes with default count."""
        result = cli_runner(["--list", str(sample_dataset)])
        assert result.returncode == 0
        assert "Episode List" in result.stdout
        assert "Episode 0" in result.stdout
        assert "Episode 1" in result.stdout
        assert "Episode 2" in result.stdout
    
    def test_list_episodes_with_count(self, cli_runner, sample_dataset):
        """Test listing episodes with specific count."""
        result = cli_runner(["--list", "2", str(sample_dataset)])
        assert result.returncode == 0
        assert "Episode 0" in result.stdout
        assert "Episode 1" in result.stdout
    
    def test_list_episodes_with_start(self, cli_runner, sample_dataset):
        """Test listing episodes with start index."""
        result = cli_runner(["--list", "2", "--list-start", "1", str(sample_dataset)])
        assert result.returncode == 0
        assert "Episode 1" in result.stdout
        assert "Episode 2" in result.stdout
    
    def test_show_specific_episode(self, cli_runner, sample_dataset):
        """Test showing specific episode details."""
        result = cli_runner(["--episode", "1", str(sample_dataset)])
        assert result.returncode == 0
        assert "Episode 1 Details" in result.stdout
        assert "Length: 100" in result.stdout
    
    def test_show_episode_with_data(self, cli_runner, sample_dataset):
        """Test showing episode with data sample."""
        result = cli_runner(["--episode", "0", "--show-data", str(sample_dataset)])
        assert result.returncode == 0
        assert "Episode 0 Details" in result.stdout
        assert "Data Sample" in result.stdout


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""
    
    def test_invalid_dataset_path(self, cli_runner, temp_dir):
        """Test handling of invalid dataset path."""
        invalid_path = temp_dir / "nonexistent_dataset"
        result = cli_runner([str(invalid_path)])
        assert result.returncode == 1
        assert "Error" in result.stderr or "Error" in result.stdout
    
    def test_invalid_episode_index(self, cli_runner, sample_dataset):
        """Test handling of invalid episode index."""
        result = cli_runner(["--episode", "999", str(sample_dataset)])
        assert result.returncode == 1
        assert "Error" in result.stderr or "out of range" in result.stdout
    
    def test_negative_episode_index(self, cli_runner, sample_dataset):
        """Test handling of negative episode index."""
        result = cli_runner(["--episode", "-1", str(sample_dataset)])
        assert result.returncode == 1
        assert "Error" in result.stderr or "non-negative" in result.stdout
    
    def test_copy_without_instruction(self, cli_runner, sample_dataset):
        """Test copy command without instruction (should fail)."""
        result = cli_runner(["--copy", "0", str(sample_dataset)])
        assert result.returncode == 1
        assert "instruction" in result.stderr.lower() or "instruction" in result.stdout.lower()
    
    def test_invalid_list_count(self, cli_runner, sample_dataset):
        """Test invalid list count."""
        result = cli_runner(["--list", "0", str(sample_dataset)])
        assert result.returncode == 1
        assert "positive" in result.stderr or "positive" in result.stdout
    
    def test_invalid_list_start(self, cli_runner, sample_dataset):
        """Test invalid list start index."""
        result = cli_runner(["--list", "1", "--list-start", "-1", str(sample_dataset)])
        assert result.returncode == 1
        assert "non-negative" in result.stderr or "non-negative" in result.stdout


class TestCLIValidation:
    """Test CLI argument validation."""
    
    def test_missing_dataset_path(self, cli_runner):
        """Test that missing dataset path is handled."""
        result = cli_runner([])
        assert result.returncode != 0
        assert "required" in result.stderr or "required" in result.stdout
    
    def test_multiple_actions_allowed(self, cli_runner, sample_dataset):
        """Test that multiple compatible actions can be run together."""
        result = cli_runner(["--summary", "--list", "2", str(sample_dataset)])
        assert result.returncode == 0
        assert "Dataset Summary" in result.stdout
        assert "Episode List" in result.stdout
    
    def test_dry_run_with_operations(self, cli_runner, sample_dataset):
        """Test dry run mode with operations."""
        result = cli_runner(["--copy", "0", "--instruction", "Test task", "--dry-run", str(sample_dataset)])
        assert result.returncode == 0
        assert "dry run" in result.stdout.lower() or "preview" in result.stdout.lower()


class TestCLIOutput:
    """Test CLI output formatting and content."""
    
    def test_output_contains_expected_sections(self, cli_runner, sample_dataset):
        """Test that summary output contains expected sections."""
        result = cli_runner(["--summary", str(sample_dataset)])
        assert result.returncode == 0
        
        # Check for expected sections in output
        output = result.stdout
        assert "Dataset Path:" in output or "Path:" in output
        assert "Total episodes:" in output
        assert "Total tasks:" in output
        assert "Robot type:" in output
        assert "FPS:" in output
    
    def test_episode_list_formatting(self, cli_runner, sample_dataset):
        """Test episode list formatting."""
        result = cli_runner(["--list", str(sample_dataset)])
        assert result.returncode == 0
        
        # Check for proper episode formatting
        output = result.stdout
        assert "Episode 0:" in output or "Episode 0 " in output
        assert "Episode 1:" in output or "Episode 1 " in output
        assert "Episode 2:" in output or "Episode 2 " in output
    
    def test_episode_detail_formatting(self, cli_runner, sample_dataset):
        """Test individual episode detail formatting."""
        result = cli_runner(["--episode", "0", str(sample_dataset)])
        assert result.returncode == 0
        
        output = result.stdout
        assert "Episode 0" in output
        assert "Length:" in output
        assert "Task:" in output
        assert "Data file:" in output
        assert "Video files:" in output


class TestCLIIntegration:
    """Test CLI integration with the underlying system."""
    
    def test_cli_reads_real_dataset_structure(self, cli_runner, sample_dataset, dataset_validator):
        """Test that CLI correctly reads and reports dataset structure."""
        # Validate our test dataset is properly structured
        validation = dataset_validator(sample_dataset)
        assert validation["valid"], f"Test dataset invalid: {validation['errors']}"
        
        # Test CLI can read it
        result = cli_runner(["--summary", str(sample_dataset)])
        assert result.returncode == 0
        
        # Verify CLI reports correct information
        assert "Total episodes: 3" in result.stdout
        assert "Total tasks: 2" in result.stdout
    
    def test_cli_episode_enumeration(self, cli_runner, sample_dataset):
        """Test that CLI correctly enumerates all episodes."""
        result = cli_runner(["--list", "10", str(sample_dataset)])  # Request more than available
        assert result.returncode == 0
        
        # Should show all 3 episodes
        output = result.stdout
        for i in range(3):
            assert f"Episode {i}" in output
    
    def test_cli_episode_details_accuracy(self, cli_runner, sample_dataset, episode_data_reader):
        """Test that CLI episode details match actual data."""
        # Get actual episode data
        episode_data = episode_data_reader(sample_dataset, 1)
        assert episode_data["exists"], "Test episode should exist"
        
        # Get CLI report
        result = cli_runner(["--episode", "1", str(sample_dataset)])
        assert result.returncode == 0
        
        # Verify CLI reports match actual data
        output = result.stdout
        assert "Length: 100" in output  # Should match our test data
        assert "Data file: ✓" in output or "exists" in output.lower()


class TestCLIPerformance:
    """Test CLI performance and responsiveness."""
    
    def test_cli_startup_time(self, cli_runner, sample_dataset):
        """Test that CLI starts up reasonably quickly."""
        import time
        
        start_time = time.time()
        result = cli_runner(["--help"])
        end_time = time.time()
        
        assert result.returncode == 0
        startup_time = end_time - start_time
        assert startup_time < 5.0, f"CLI startup took {startup_time:.2f}s, should be under 5s"
    
    def test_cli_summary_performance(self, cli_runner, sample_dataset):
        """Test that summary generation is reasonably fast."""
        import time
        
        start_time = time.time()
        result = cli_runner(["--summary", str(sample_dataset)])
        end_time = time.time()
        
        assert result.returncode == 0
        processing_time = end_time - start_time
        assert processing_time < 10.0, f"Summary took {processing_time:.2f}s, should be under 10s"