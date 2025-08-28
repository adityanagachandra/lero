#!/usr/bin/env python3
"""
Refactored GUI Viewer for LeRobot Dataset Episodes

This module provides a clean, modular graphical interface for viewing episodes with:
- Video playback from multiple cameras
- Real-time joint angle visualization
- Synchronized timeline control
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    import numpy as np
    import pandas as pd
    import cv2
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from PIL import Image, ImageTk
except ImportError as e:
    # Re-raise ImportError to be handled by the GUI __init__.py
    raise ImportError(f"GUI dependencies not available: {e}") from e

from lero import LeRobotDatasetEditor
from .constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, BASE_FPS, MIN_DELAY_MS, 
    VIDEO_UPDATE_SPEED_THRESHOLD
)
from .data_handler import DatasetInfoFormatter
from .video_component import VideoDisplayComponent
from .plot_component import JointPlotComponent
from .controls import ControlPanel, TimelineComponent


class EpisodeGUIViewer:
    """Main GUI viewer class for LeRobot dataset episodes."""
    
    def __init__(self, dataset_editor: LeRobotDatasetEditor):
        """
        Initialize the GUI viewer.
        
        Args:
            dataset_editor: LeRobotDatasetEditor instance
        """
        self.editor = dataset_editor
        self.current_episode = 0
        self.current_frame = 0
        self.total_frames = 0
        self.episode_data: Optional[pd.DataFrame] = None
        self.is_playing = False
        self._updating_timeline = False  # Flag to prevent recursive updates
        
        # GUI components
        self.root: Optional[tk.Tk] = None
        self.video_component: Optional[VideoDisplayComponent] = None
        self.plot_component: Optional[JointPlotComponent] = None
        self.control_panel: Optional[ControlPanel] = None
        self.timeline: Optional[TimelineComponent] = None
        
        self._setup_gui()
        self._load_episode(0)
    
    def _setup_gui(self) -> None:
        """Setup the main GUI window and components."""
        self.root = tk.Tk()
        self.root.title("LeRobot Dataset Episode Viewer")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Setup components
        self._setup_control_panel(main_frame)
        self._setup_content_area(main_frame)
        self._setup_timeline(main_frame)
        
        # Connect callbacks
        self._connect_callbacks()
    
    def _setup_control_panel(self, parent: ttk.Frame) -> None:
        """Setup the control panel."""
        self.control_panel = ControlPanel(parent, self.editor.count_episodes())
    
    def _setup_content_area(self, parent: ttk.Frame) -> None:
        """Setup the content area with video and plot components."""
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Video panel
        video_frame = ttk.LabelFrame(content_frame, text="Camera Views", padding=10)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.video_component = VideoDisplayComponent(video_frame)
        
        # Joint angle panel
        joint_frame = ttk.LabelFrame(content_frame, text="Joint Angles", padding=10)
        joint_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.plot_component = JointPlotComponent(joint_frame)
    
    def _setup_timeline(self, parent: ttk.Frame) -> None:
        """Setup the timeline component."""
        self.timeline = TimelineComponent(parent)
    
    def _connect_callbacks(self) -> None:
        """Connect all callback functions."""
        if self.control_panel:
            self.control_panel.on_load_episode = self._handle_load_episode
            self.control_panel.on_toggle_playback = self._handle_toggle_playback
            self.control_panel.on_stop_playback = self._handle_stop_playback
            self.control_panel.on_step_forward = self._handle_step_forward
            self.control_panel.on_step_backward = self._handle_step_backward
            self.control_panel.on_speed_change = self._handle_speed_change
            self.control_panel.on_jump_to_frame = self._handle_jump_to_frame
        
        if self.timeline:
            self.timeline.on_timeline_change = self._handle_timeline_change
    
    def _load_episode(self, episode_index: int) -> None:
        """
        Load an episode for viewing.
        
        Args:
            episode_index: Index of the episode to load
        """
        try:
            # Get episode info
            episode_info = self.editor.get_episode_info(episode_index)
            self.current_episode = episode_index
            
            # Update episode info display
            info_text = DatasetInfoFormatter.format_episode_info(episode_info)
            if self.control_panel:
                self.control_panel.update_episode_info(info_text)
            
            # Load episode data
            if episode_info['data_exists']:
                self.episode_data = pd.read_parquet(episode_info['data_file'])
                self.total_frames = len(self.episode_data)
            else:
                self.episode_data = None
                length = episode_info['length']
                self.total_frames = int(length) if isinstance(length, (int, str)) and str(length).isdigit() else 0
            
            # Setup video component
            if self.video_component:
                self.video_component.setup_video_captures(episode_info)
                self.video_component.setup_video_display_layout()
            
            # Setup joint angle plots
            if self.plot_component:
                self.plot_component.setup_joint_plots(self.episode_data)
            
            # Update timeline
            if self.timeline and self.total_frames > 0:
                self.timeline.set_range(self.total_frames - 1)
                self.current_frame = 0
                self._update_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load episode {episode_index}: {e}")
    
    def _update_display(self, update_timeline: bool = True, update_video: bool = True) -> None:
        """
        Update video frames and joint angle display for current frame.
        
        Args:
            update_timeline: Whether to update the timeline position
            update_video: Whether to update video frames (for performance)
        """
        # Update video frames
        if update_video and self.video_component:
            self.video_component.update_video_frames(self.current_frame)
        
        # Update joint angle display
        if self.plot_component:
            self.plot_component.update_current_frame_marker(self.current_frame)
        
        # Update frame counter
        if self.control_panel:
            frame_text = DatasetInfoFormatter.format_frame_info(self.current_frame, self.total_frames)
            self.control_panel.update_frame_info(frame_text)
        
        # Update timeline (only if not called from timeline change)
        if update_timeline and not self._updating_timeline and self.timeline:
            self._updating_timeline = True
            try:
                self.timeline.set_position(self.current_frame)
            except Exception as e:
                print(f"Timeline update error: {e}")
            finally:
                self._updating_timeline = False
    
    # Event handlers
    def _handle_load_episode(self) -> None:
        """Handle load episode request."""
        if not self.control_panel:
            return
        
        try:
            episode_index = self.control_panel.get_episode_index()
            if 0 <= episode_index < self.editor.count_episodes():
                self._load_episode(episode_index)
            else:
                messagebox.showerror("Error", f"Episode {episode_index} is out of range")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid episode number")
    
    def _handle_toggle_playback(self) -> None:
        """Handle play/pause toggle."""
        self.is_playing = not self.is_playing
        
        if self.control_panel:
            button_text = "Pause" if self.is_playing else "Play"
            self.control_panel.update_play_button_text(button_text)
        
        if self.is_playing:
            self._play_next_frame()
    
    def _handle_stop_playback(self) -> None:
        """Handle stop playback."""
        self.is_playing = False
        if self.control_panel:
            self.control_panel.update_play_button_text("Play")
        self.current_frame = 0
        self._update_display()
    
    def _handle_step_forward(self) -> None:
        """Handle step forward."""
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self._update_display()
    
    def _handle_step_backward(self) -> None:
        """Handle step backward."""
        if self.current_frame > 0:
            self.current_frame -= 1
            self._update_display()
    
    def _handle_speed_change(self, value: str) -> None:
        """Handle playback speed change."""
        try:
            speed = float(value)
            if self.control_panel:
                speed_text = DatasetInfoFormatter.format_speed_info(speed)
                self.control_panel.update_speed_display(speed_text)
        except ValueError:
            pass
    
    def _handle_timeline_change(self, value: str) -> None:
        """Handle timeline scrubber change."""
        if self._updating_timeline:
            return  # Prevent recursive calls
        
        try:
            frame = int(float(value))
            if 0 <= frame < self.total_frames and frame != self.current_frame:
                self.current_frame = frame
                self._update_display(update_timeline=False)  # Don't update timeline again
        except (ValueError, TypeError):
            pass
    
    def _handle_jump_to_frame(self) -> None:
        """Handle jump to frame request."""
        if not self.control_panel:
            return
        
        try:
            # Get frame number from input (1-indexed from user)
            frame_input = self.control_panel.get_frame_input()
            
            if frame_input < 1:
                messagebox.showerror("Error", "Please enter a valid frame number (1 or greater)")
                return
            
            # Convert to 0-indexed for internal use
            target_frame = frame_input - 1
            
            if target_frame >= self.total_frames:
                messagebox.showerror("Error", f"Frame {frame_input} is out of range. Maximum frame is {self.total_frames}")
                return
            
            # Jump to the specified frame
            self.current_frame = target_frame
            self._update_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to jump to frame: {e}")
    
    def _play_next_frame(self) -> None:
        """Play next frame automatically."""
        if self.is_playing and self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            
            # Skip video updates during fast playback for better performance
            speed = self.control_panel.get_playback_speed() if self.control_panel else 1.0
            update_video = speed <= VIDEO_UPDATE_SPEED_THRESHOLD
            self._update_display(update_video=update_video)
            
            # Schedule next frame based on speed
            delay = max(MIN_DELAY_MS, int((1000 / BASE_FPS) / speed))
            if self.root:
                self.root.after(delay, self._play_next_frame)
        else:
            self.is_playing = False
            if self.control_panel:
                self.control_panel.update_play_button_text("Play")
    
    # Public API methods for testing and external use
    def setup_gui(self) -> None:
        """Public wrapper for GUI setup."""
        self._setup_gui()
    
    def load_episode(self, episode_index: int) -> None:
        """Public wrapper for loading an episode."""
        self._load_episode(episode_index)
    
    def update_display(self, update_timeline: bool = True, update_video: bool = True) -> None:
        """Public wrapper for updating the display."""
        self._update_display(update_timeline, update_video)
    
    def on_episode_change(self, episode_index: int) -> None:
        """Handle episode change events."""
        self.load_episode(episode_index)
    
    def run(self) -> None:
        """Start the GUI main loop."""
        if self.root:
            try:
                self.root.mainloop()
            finally:
                self._cleanup()
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.video_component:
            self.video_component.close_all_captures()


def launch_episode_viewer(dataset_path: str, episode_index: Optional[int] = None) -> None:
    """
    Launch the episode viewer GUI.
    
    Args:
        dataset_path: Path to the dataset
        episode_index: Optional specific episode to load
    """
    try:
        editor = LeRobotDatasetEditor(dataset_path)
        viewer = EpisodeGUIViewer(editor)
        
        if episode_index is not None:
            viewer._load_episode(episode_index)
        
        viewer.run()
        
    except Exception as e:
        # Re-raise the exception for proper error handling in tests and CLI
        raise e


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LeRobot Dataset Episode Viewer")
    parser.add_argument("dataset_path", help="Path to the dataset")
    parser.add_argument("--episode", type=int, help="Episode to load initially")
    
    args = parser.parse_args()
    launch_episode_viewer(args.dataset_path, args.episode)