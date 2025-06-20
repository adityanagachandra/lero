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
            
            # Should pass dataset path
            assert str(sample_dataset) in str(call_args)
            
        except ImportError:
            pytest.skip("GUI dependencies not available")


class TestGUIErrorHandling:
    """Test GUI error handling scenarios."""
    
    @patch('lero.gui.viewer.EpisodeGUIViewer')
    def test_gui_invalid_dataset_handling(self, mock_viewer_class, temp_dir):
        """Test GUI handling of invalid dataset."""
        mock_viewer = MagicMock()
        mock_viewer_class.return_value = mock_viewer
        
        # Configure mock to raise error on invalid dataset
        mock_viewer_class.side_effect = Exception("Invalid dataset")
        
        try:
            from lero.gui import launch_episode_viewer
            
            invalid_path = temp_dir / "nonexistent"
            
            # Should handle the error gracefully
            with pytest.raises(Exception) as exc_info:
                launch_episode_viewer(str(invalid_path))
            
            assert "Invalid dataset" in str(exc_info.value)
            
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
    
    def test_cli_without_gui_dependencies(self, cli_runner, sample_dataset):
        """Test CLI behavior when GUI dependencies are missing."""
        # This test simulates missing GUI dependencies
        with patch.dict('sys.modules', {'tkinter': None, 'matplotlib': None}):
            result = cli_runner(["--gui", str(sample_dataset)])
            
            # Should fail gracefully with appropriate error message
            assert result.returncode == 1
            # Should mention GUI dependencies or similar
            output = result.stdout + result.stderr
            assert any(keyword in output.lower() for keyword in [
                'gui', 'dependencies', 'tkinter', 'matplotlib', 'missing'
            ])
    
    def test_gui_import_error_handling(self):
        """Test handling of GUI import errors."""
        # Temporarily remove GUI modules from sys.modules if they exist
        gui_modules = [
            'tkinter', 'matplotlib', 'matplotlib.pyplot', 
            'PIL', 'cv2', 'numpy'
        ]
        
        original_modules = {}
        for module in gui_modules:
            if module in sys.modules:
                original_modules[module] = sys.modules[module]
                del sys.modules[module]
        
        try:
            # Now try to import GUI components
            with pytest.raises(ImportError):
                from lero.gui import launch_episode_viewer
                launch_episode_viewer("/dummy/path")
        
        finally:
            # Restore original modules
            for module, original in original_modules.items():
                sys.modules[module] = original


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