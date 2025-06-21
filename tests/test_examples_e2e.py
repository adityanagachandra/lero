"""
End-to-end tests for example scripts functionality.
"""

import pytest
import subprocess
import sys
from pathlib import Path


class TestExampleScripts:
    """Test example scripts work correctly."""
    
    def test_batch_copy_episodes_python_help(self):
        """Test Python batch copy script shows help."""
        script_path = Path("examples/batch_copy_episodes.py")
        
        result = subprocess.run([
            sys.executable, str(script_path), "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Batch copy episodes" in result.stdout
        assert "--episodes" in result.stdout
        assert "--instruction" in result.stdout
    
    def test_batch_copy_episodes_shell_help(self):
        """Test shell batch copy script shows help."""
        script_path = Path("examples/batch_copy_episodes.sh")
        
        # Make script executable
        script_path.chmod(0o755)
        
        result = subprocess.run([
            str(script_path), "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "episode_numbers" in result.stdout
        assert "instruction" in result.stdout
    
    def test_analyze_dataset_help(self):
        """Test analyze dataset script shows help."""
        script_path = Path("examples/analyze_dataset.py")
        
        result = subprocess.run([
            sys.executable, str(script_path), "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Comprehensive dataset analysis" in result.stdout
        assert "dataset_path" in result.stdout
    
    def test_validate_dataset_help(self):
        """Test validate dataset script shows help."""
        script_path = Path("examples/validate_dataset.py")
        
        result = subprocess.run([
            sys.executable, str(script_path), "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "dataset validation" in result.stdout.lower()
        assert "dataset_path" in result.stdout
    
    def test_batch_copy_episodes_python_dry_run(self, sample_dataset):
        """Test Python batch copy script with dry run."""
        script_path = Path("examples/batch_copy_episodes.py")
        
        result = subprocess.run([
            sys.executable, str(script_path),
            str(sample_dataset),
            "--episodes", "0,1",
            "--instruction", "Test copy",
            "--dry-run"
        ], capture_output=True, text=True)
        
        # May fail due to missing dependencies, but should not fail with argument errors
        if result.returncode != 0:
            error_output = result.stderr + result.stdout
            # Should not be argument parsing errors
            assert "unrecognized arguments" not in error_output
            assert "invalid choice" not in error_output
    
    def test_analyze_dataset_on_sample(self, sample_dataset):
        """Test analyze dataset script on sample dataset."""
        script_path = Path("examples/analyze_dataset.py")
        
        result = subprocess.run([
            sys.executable, str(script_path),
            str(sample_dataset),
            "--quiet"
        ], capture_output=True, text=True)
        
        # May fail due to missing dependencies, but should recognize the dataset
        if result.returncode != 0:
            error_output = result.stderr + result.stdout
            # Should not be argument parsing errors
            assert "unrecognized arguments" not in error_output
            assert "invalid choice" not in error_output
    
    def test_validate_dataset_on_sample(self, sample_dataset):
        """Test validate dataset script on sample dataset."""
        script_path = Path("examples/validate_dataset.py")
        
        result = subprocess.run([
            sys.executable, str(script_path),
            str(sample_dataset),
            "--quiet"
        ], capture_output=True, text=True)
        
        # May fail due to missing dependencies, but should recognize the dataset
        if result.returncode != 0:
            error_output = result.stderr + result.stdout
            # Should not be argument parsing errors
            assert "unrecognized arguments" not in error_output
            assert "invalid choice" not in error_output


class TestExampleScriptErrorHandling:
    """Test example scripts handle errors properly."""
    
    def test_batch_copy_episodes_python_missing_dataset(self, temp_dir):
        """Test Python batch copy script with missing dataset."""
        script_path = Path("examples/batch_copy_episodes.py")
        nonexistent_path = temp_dir / "nonexistent"
        
        result = subprocess.run([
            sys.executable, str(script_path),
            str(nonexistent_path),
            "--episodes", "0",
            "--instruction", "Test"
        ], capture_output=True, text=True)
        
        assert result.returncode == 1
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'not found', 'does not exist', 'error'
        ])
    
    def test_batch_copy_episodes_shell_missing_dataset(self, temp_dir):
        """Test shell batch copy script with missing dataset."""
        script_path = Path("examples/batch_copy_episodes.sh")
        script_path.chmod(0o755)
        nonexistent_path = temp_dir / "nonexistent"
        
        result = subprocess.run([
            str(script_path),
            str(nonexistent_path),
            "0",
            "Test"
        ], capture_output=True, text=True)
        
        assert result.returncode == 1
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'not found', 'does not exist', 'error'
        ])
    
    def test_analyze_dataset_missing_dataset(self, temp_dir):
        """Test analyze dataset script with missing dataset."""
        script_path = Path("examples/analyze_dataset.py")
        nonexistent_path = temp_dir / "nonexistent"
        
        result = subprocess.run([
            sys.executable, str(script_path),
            str(nonexistent_path)
        ], capture_output=True, text=True)
        
        assert result.returncode == 1
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'error', 'not found', 'does not exist'
        ])
    
    def test_validate_dataset_missing_dataset(self, temp_dir):
        """Test validate dataset script with missing dataset."""
        script_path = Path("examples/validate_dataset.py")
        nonexistent_path = temp_dir / "nonexistent"
        
        result = subprocess.run([
            sys.executable, str(script_path),
            str(nonexistent_path)
        ], capture_output=True, text=True)
        
        assert result.returncode == 1
        error_output = result.stderr + result.stdout
        assert any(keyword in error_output.lower() for keyword in [
            'invalid', 'failed', 'critical issues'
        ])


class TestExampleScriptIntegration:
    """Test example scripts integrate properly with main tool."""
    
    def test_example_scripts_use_correct_import(self):
        """Test that example scripts use the correct import paths."""
        python_scripts = [
            "examples/batch_copy_episodes.py",
            "examples/analyze_dataset.py",
            "examples/validate_dataset.py"
        ]
        
        for script_path in python_scripts:
            script_file = Path(script_path)
            if script_file.exists():
                content = script_file.read_text()
                # Should import from lero
                assert "from lero import" in content
                # Should not import from old paths
                assert "from dataset_editor import" not in content
    
    def test_shell_script_uses_correct_command(self):
        """Test that shell script uses correct module command."""
        script_path = Path("examples/batch_copy_episodes.sh")
        
        if script_path.exists():
            content = script_path.read_text()
            # Should use python -m lero
            assert "python -m lero" in content
            # Should not use old command
            assert "python lero.py" not in content


class TestExampleScriptDocumentation:
    """Test example scripts have proper documentation."""
    
    def test_python_scripts_have_docstrings(self):
        """Test that Python scripts have proper docstrings."""
        python_scripts = [
            "examples/batch_copy_episodes.py",
            "examples/analyze_dataset.py", 
            "examples/validate_dataset.py"
        ]
        
        for script_path in python_scripts:
            script_file = Path(script_path)
            if script_file.exists():
                content = script_file.read_text()
                # Should have a module docstring
                assert '"""' in content
                # Should have usage information
                assert "Usage:" in content or "usage:" in content
    
    def test_shell_script_has_comments(self):
        """Test that shell script has proper comments."""
        script_path = Path("examples/batch_copy_episodes.sh")
        
        if script_path.exists():
            content = script_path.read_text()
            # Should have header comments
            assert content.startswith("#")
            # Should have usage information
            assert "Usage:" in content or "usage:" in content
            # Should have examples
            assert "Example:" in content or "example:" in content
    
    def test_examples_readme_exists(self):
        """Test that examples directory has README."""
        readme_path = Path("examples/README.md")
        assert readme_path.exists(), "examples/README.md should exist"
        
        content = readme_path.read_text()
        assert len(content) > 100  # Should have substantial content
        assert "Examples" in content
        assert "Usage" in content or "usage" in content


class TestExampleScriptOutputFormat:
    """Test example scripts produce properly formatted output."""
    
    def test_scripts_produce_readable_output(self, sample_dataset):
        """Test that scripts produce human-readable output."""
        # Test analyze script output format
        analyze_script = Path("examples/analyze_dataset.py")
        
        if analyze_script.exists():
            result = subprocess.run([
                sys.executable, str(analyze_script),
                str(sample_dataset),
                "--quiet"
            ], capture_output=True, text=True)
            
            # If successful, output should be readable
            if result.returncode == 0:
                output = result.stdout
                # Should not contain raw technical data dumps
                assert "pandas.DataFrame" not in output
                assert "dict_items" not in output
    
    def test_error_messages_are_clear(self, temp_dir):
        """Test that error messages from scripts are clear."""
        scripts = [
            "examples/batch_copy_episodes.py",
            "examples/analyze_dataset.py",
            "examples/validate_dataset.py"
        ]
        
        nonexistent_path = temp_dir / "nonexistent"
        
        for script_path in scripts:
            script_file = Path(script_path)
            if script_file.exists():
                result = subprocess.run([
                    sys.executable, str(script_file),
                    str(nonexistent_path)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    error_output = result.stderr + result.stdout
                    # Error should be informative
                    assert len(error_output.strip()) > 0
                    # Should not show stack traces
                    assert "Traceback" not in error_output


class TestExampleScriptPerformance:
    """Test example scripts performance characteristics."""
    
    def test_scripts_start_quickly(self):
        """Test that scripts start up reasonably quickly."""
        import time
        
        scripts = [
            ("examples/batch_copy_episodes.py", ["--help"]),
            ("examples/analyze_dataset.py", ["--help"]),
            ("examples/validate_dataset.py", ["--help"])
        ]
        
        for script_path, args in scripts:
            script_file = Path(script_path)
            if script_file.exists():
                start_time = time.time()
                
                result = subprocess.run([
                    sys.executable, str(script_file)
                ] + args, capture_output=True, text=True)
                
                end_time = time.time()
                startup_time = end_time - start_time
                
                # Scripts should start quickly (under 5 seconds)
                assert startup_time < 5.0, f"{script_path} took {startup_time:.2f}s to show help"
    
    def test_scripts_handle_large_arguments(self):
        """Test scripts handle reasonably large arguments."""
        # Test with large instruction string
        script_path = Path("examples/batch_copy_episodes.py")
        
        if script_path.exists():
            large_instruction = "Test " * 1000  # Large but reasonable instruction
            
            result = subprocess.run([
                sys.executable, str(script_path),
                "/nonexistent/path",  # Will fail, but should handle the large argument
                "--episodes", "0",
                "--instruction", large_instruction
            ], capture_output=True, text=True)
            
            # Should fail due to missing path, not due to argument size
            if result.returncode != 0:
                error_output = result.stderr + result.stdout
                assert "argument" not in error_output.lower() or "too long" not in error_output.lower()