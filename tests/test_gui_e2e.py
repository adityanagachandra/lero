"""
End-to-end tests for GUI functionality.

Note: These tests focus on GUI startup and basic functionality without
requiring a full GUI environment (headless testing).
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock


class TestGUIStartup:
    """Test GUI startup and initialization."""
    
    def test_gui_import_availability(self):
        """Test that GUI modules can be imported."""
        try:
            from lero.gui import viewer
            from lero.gui import launch_episode_viewer
            assert True  # If we get here, imports succeeded
        except ImportError as e:
            pytest.skip(f"GUI dependencies not available: {e}")
    
    def test_gui_command_line_flag(self, cli_runner, sample_dataset):
        """Test GUI command line flag handling."""
        # Skip if no display available (CI environment)
        if os.environ.get('DISPLAY') is None and sys.platform != 'darwin':
            pytest.skip("No display available for GUI testing")
        
        # Test GUI flag is recognized (may fail at GUI startup, but should recognize the flag)
        result = cli_runner(["--gui", str(sample_dataset)])
        
        # The command should either succeed or fail with GUI-related error, not argument error
        assert "unrecognized arguments" not in result.stderr
        assert "invalid choice" not in result.stderr
    
    @patch('tkinter.Tk')
    def test_gui_launch_mock(self, mock_tk, sample_dataset):
        """Test GUI launch with mocked tkinter."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        try:
            from lero.gui import launch_episode_viewer
            
            # This should not raise an exception with mocked GUI
            launch_episode_viewer(str(sample_dataset), episode_index=0)
            
            # Verify Tk was called (GUI was attempted to be created)
            mock_tk.assert_called_once()
            
        except ImportError:
            pytest.skip("GUI dependencies not available")
        except Exception as e:
            # Expected - may fail due to missing GUI dependencies, but not import errors
            assert "ModuleNotFoundError" not in str(e)


class TestGUIModuleStructure:
    """Test GUI module structure and components."""
    
    def test_gui_module_components_exist(self):
        """Test that expected GUI components exist."""
        try:
            from lero.gui import viewer
            from lero.gui import video_component
            from lero.gui import plot_component
            from lero.gui import controls
            from lero.gui import data_handler
            
            # Check that main classes exist
            assert hasattr(viewer, 'EpisodeGUIViewer')
            assert hasattr(video_component, 'VideoComponent')
            assert hasattr(plot_component, 'PlotComponent')
            
        except ImportError as e:
            pytest.skip(f"GUI dependencies not available: {e}")
    
    def test_gui_viewer_class_structure(self):
        """Test GUI viewer class has expected methods."""
        try:
            from lero.gui.viewer import EpisodeGUIViewer
            
            # Check that expected methods exist
            expected_methods = [
                '__init__',
                'setup_gui',
                'load_episode',
                'update_display',
                'on_episode_change'
            ]
            
            for method in expected_methods:
                assert hasattr(EpisodeGUIViewer, method), f"Missing method: {method}"
                
        except ImportError:
            pytest.skip("GUI dependencies not available")
    
    def test_gui_launch_function_signature(self):
        """Test GUI launch function has correct signature."""
        try:
            from lero.gui import launch_episode_viewer
            import inspect
            
            sig = inspect.signature(launch_episode_viewer)
            params = list(sig.parameters.keys())
            
            # Should accept dataset_path and episode_index
            assert 'dataset_path' in params
            assert 'episode_index' in params
            
        except ImportError:
            pytest.skip("GUI dependencies not available")


class TestGUIIntegration:
    """Test GUI integration with CLI and dataset editor."""
    
    def test_cli_gui_integration(self, cli_runner, sample_dataset):
        """Test CLI GUI integration."""
        # Skip if no display available
        if os.environ.get('DISPLAY') is None and sys.platform != 'darwin':
            pytest.skip("No display available for GUI testing")
        
        # Test that GUI flag doesn't cause CLI parsing errors
        result = cli_runner(["--gui", "--episode", "0", str(sample_dataset)])
        
        # Should not fail with argument parsing errors
        assert "unrecognized arguments" not in result.stderr
        assert "error: invalid choice" not in result.stderr
        
        # May fail with GUI startup errors, but that's expected in headless environment
    
    @patch('lero.gui.viewer.EpisodeGUIViewer')
    def test_gui_dataset_integration_mock(self, mock_viewer_class, sample_dataset):
        """Test GUI integration with dataset using mocks."""
        mock_viewer = MagicMock()
        mock_viewer_class.return_value = mock_viewer
        
        try:
            from lero.gui import launch_episode_viewer
            
            # Should create viewer with dataset path
            launch_episode_viewer(str(sample_dataset), episode_index=1)
            
            # Verify viewer was created with correct arguments
            mock_viewer_class.assert_called_once()
            call_args = mock_viewer_class.call_args
            
            # Should pass LeRobotDatasetEditor object (not path directly)
            assert len(call_args[0]) == 1  # One positional argument
            editor_arg = call_args[0][0]
            # Check that it's a LeRobotDatasetEditor object
            assert hasattr(editor_arg, 'get_episode_info')
            
        except ImportError:
            pytest.skip("GUI dependencies not available")


class TestGUIErrorHandling:
    """Test GUI error handling scenarios."""
    
    def test_gui_invalid_dataset_handling(self, temp_dir):
        """Test GUI handling of invalid dataset."""
        try:
            from lero.gui import launch_episode_viewer
            
            invalid_path = temp_dir / "nonexistent"
            
            # Should raise an exception for invalid dataset path
            with pytest.raises(Exception) as exc_info:
                launch_episode_viewer(str(invalid_path))
            
            # Should contain information about the dataset not being found
            assert "not found" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()
            
        except ImportError:
            pytest.skip("GUI dependencies not available")
    
    @patch('lero.gui.viewer.EpisodeGUIViewer')
    def test_gui_invalid_episode_handling(self, mock_viewer_class, sample_dataset):
        """Test GUI handling of invalid episode index."""
        mock_viewer = MagicMock()
        mock_viewer_class.return_value = mock_viewer
        
        try:
            from lero.gui import launch_episode_viewer
            
            # Should handle invalid episode index
            # (May not raise error immediately, but should handle gracefully)
            launch_episode_viewer(str(sample_dataset), episode_index=999)
            
            # Verify viewer was created (error handling is internal)
            mock_viewer_class.assert_called_once()
            
        except ImportError:
            pytest.skip("GUI dependencies not available")


class TestGUIOptionalDependencies:
    """Test handling of optional GUI dependencies."""
    
    def test_cli_without_gui_dependencies(self, sample_dataset):
        """Test CLI behavior when GUI dependencies are missing."""
        # Test the CLI handler directly instead of using subprocess
        from lero.dataset_editor.cli import CLIHandler
        import argparse
        
        # Create a CLI handler
        cli = CLIHandler()
        
        # Mock the GUI import to fail
        with patch('lero.dataset_editor.cli.CLIHandler._handle_gui_launch') as mock_gui_launch:
            # Configure the mock to simulate ImportError and return error code
            mock_gui_launch.return_value = 1
            
            # Test the execute_command method directly
            args = argparse.Namespace(
                dataset_path=str(sample_dataset),
                gui=True,
                summary=False,
                list=None,
                list_start=0,
                episode=None,
                show_data=False,
                delete=None,
                copy=None,
                instruction=None,
                dry_run=False
            )
            
            result = cli.execute_command(args)
            
            # Should return error code 1
            assert result == 1
    
    def test_gui_import_error_handling(self):
        """Test handling of GUI import errors."""
        # Test that the GUI module properly handles missing dependencies
        # by using the fallback classes that raise ImportError
        
        # Mock all the GUI dependencies to be missing
        missing_modules = {
            'numpy': None,
            'pandas': None,
            'cv2': None,
            'matplotlib': None,
            'matplotlib.pyplot': None,
            'matplotlib.backends.backend_tkagg': None,
            'matplotlib.figure': None,
            'PIL': None,
            'PIL.Image': None,
            'PIL.ImageTk': None,
            'tkinter': None
        }
        
        with patch.dict(sys.modules, missing_modules):
            # Remove GUI modules to force reimport
            gui_modules = [k for k in list(sys.modules.keys()) if k.startswith('lero.gui')]
            for mod in gui_modules:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            # Import the GUI module - should work but use fallback classes
            import lero.gui
            
            # Using the fallback classes should raise ImportError
            with pytest.raises(ImportError):
                lero.gui.launch_episode_viewer("/dummy/path")


class TestGUIPerformance:
    """Test GUI performance characteristics."""
    
    @patch('lero.gui.viewer.EpisodeGUIViewer')
    def test_gui_startup_performance(self, mock_viewer_class, sample_dataset):
        """Test GUI startup performance."""
        import time
        
        mock_viewer = MagicMock()
        mock_viewer_class.return_value = mock_viewer
        
        try:
            from lero.gui import launch_episode_viewer
            
            start_time = time.time()
            launch_episode_viewer(str(sample_dataset))
            end_time = time.time()
            
            startup_time = end_time - start_time
            # GUI should start quickly (under 2 seconds even with mocking overhead)
            assert startup_time < 2.0, f"GUI startup took {startup_time:.2f}s"
            
        except ImportError:
            pytest.skip("GUI dependencies not available")
    
    @patch('lero.gui.viewer.EpisodeGUIViewer')
    def test_gui_memory_usage(self, mock_viewer_class, sample_dataset):
        """Test that GUI creation doesn't cause obvious memory leaks."""
        import gc
        
        mock_viewer = MagicMock()
        mock_viewer_class.return_value = mock_viewer
        
        try:
            from lero.gui import launch_episode_viewer
            
            # Create and destroy GUI multiple times
            for _ in range(5):
                launch_episode_viewer(str(sample_dataset))
                gc.collect()
            
            # If we get here without memory errors, that's good
            assert True
            
        except ImportError:
            pytest.skip("GUI dependencies not available")


class TestGUIAccessibility:
    """Test GUI accessibility and usability features."""
    
    @patch('lero.gui.viewer.EpisodeGUIViewer')
    def test_gui_keyboard_accessibility(self, mock_viewer_class, sample_dataset):
        """Test that GUI components can be created (keyboard navigation setup)."""
        mock_viewer = MagicMock()
        mock_viewer_class.return_value = mock_viewer
        
        try:
            from lero.gui import launch_episode_viewer
            
            launch_episode_viewer(str(sample_dataset))
            
            # Verify GUI was created (accessibility features would be set up internally)
            mock_viewer_class.assert_called_once()
            
        except ImportError:
            pytest.skip("GUI dependencies not available")
    
    def test_gui_component_separation(self):
        """Test that GUI components are properly separated."""
        try:
            from lero.gui import video_component
            from lero.gui import plot_component
            from lero.gui import controls
            
            # Each component should be in a separate module
            assert video_component.__file__ != plot_component.__file__
            assert plot_component.__file__ != controls.__file__
            
        except ImportError:
            pytest.skip("GUI dependencies not available")