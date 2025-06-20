"""
Control panel components for the GUI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from .constants import (
    MIN_PLAYBACK_SPEED, 
    MAX_PLAYBACK_SPEED, 
    DEFAULT_PLAYBACK_SPEED,
    LABEL_FONT
)


class ControlPanel:
    """Main control panel containing episode selection and playback controls."""
    
    def __init__(self, parent_frame: ttk.Frame, total_episodes: int):
        """
        Initialize the control panel.
        
        Args:
            parent_frame: Parent frame to contain controls
            total_episodes: Total number of episodes in dataset
        """
        self.parent_frame = parent_frame
        self.total_episodes = total_episodes
        
        # Control variables
        self.episode_var = tk.StringVar()
        self.episode_info_var = tk.StringVar()
        self.frame_var = tk.StringVar()
        self.speed_var = tk.DoubleVar(value=DEFAULT_PLAYBACK_SPEED)
        
        # Control widgets
        self.play_button: Optional[ttk.Button] = None
        self.speed_label: Optional[ttk.Label] = None
        
        # Callbacks (to be set by parent)
        self.on_load_episode: Optional[Callable] = None
        self.on_toggle_playback: Optional[Callable] = None
        self.on_stop_playback: Optional[Callable] = None
        self.on_step_forward: Optional[Callable] = None
        self.on_step_backward: Optional[Callable] = None
        self.on_speed_change: Optional[Callable] = None
        
        self._setup_controls()
    
    def _setup_controls(self) -> None:
        """Setup all control widgets."""
        control_frame = ttk.LabelFrame(self.parent_frame, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self._setup_episode_controls(control_frame)
        self._setup_playback_controls(control_frame)
    
    def _setup_episode_controls(self, parent: ttk.Frame) -> None:
        """Setup episode selection controls."""
        episode_frame = ttk.Frame(parent)
        episode_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Episode selection
        ttk.Label(episode_frame, text="Episode:").pack(side=tk.LEFT)
        
        episode_spinbox = ttk.Spinbox(
            episode_frame,
            from_=0,
            to=max(0, self.total_episodes - 1),
            textvariable=self.episode_var,
            width=10,
            command=self._on_episode_spinbox_change
        )
        episode_spinbox.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(
            episode_frame,
            text="Load Episode",
            command=self._on_load_episode_button
        ).pack(side=tk.LEFT)
        
        # Episode info display
        episode_info_label = ttk.Label(
            episode_frame, 
            textvariable=self.episode_info_var, 
            font=LABEL_FONT
        )
        episode_info_label.pack(side=tk.LEFT, padx=(20, 0))
    
    def _setup_playback_controls(self, parent: ttk.Frame) -> None:
        """Setup playback control widgets."""
        playback_frame = ttk.Frame(parent)
        playback_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Playback buttons
        self.play_button = ttk.Button(
            playback_frame,
            text="Play",
            command=self._on_toggle_playback_button
        )
        self.play_button.pack(side=tk.LEFT)
        
        ttk.Button(
            playback_frame,
            text="Stop",
            command=self._on_stop_playback_button
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(
            playback_frame,
            text="Step Back",
            command=self._on_step_backward_button
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(
            playback_frame,
            text="Step Forward",
            command=self._on_step_forward_button
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Speed control
        self._setup_speed_control(playback_frame)
        
        # Frame info display
        frame_info_label = ttk.Label(
            playback_frame, 
            textvariable=self.frame_var, 
            font=LABEL_FONT
        )
        frame_info_label.pack(side=tk.RIGHT)
    
    def _setup_speed_control(self, parent: ttk.Frame) -> None:
        """Setup speed control widgets."""
        ttk.Label(parent, text="Speed:").pack(side=tk.LEFT, padx=(20, 5))
        
        speed_scale = ttk.Scale(
            parent,
            from_=MIN_PLAYBACK_SPEED,
            to=MAX_PLAYBACK_SPEED,
            variable=self.speed_var,
            orient=tk.HORIZONTAL,
            length=120,
            command=self._on_speed_scale_change
        )
        speed_scale.pack(side=tk.LEFT)
        
        self.speed_label = ttk.Label(parent, text="1.0x")
        self.speed_label.pack(side=tk.LEFT, padx=(5, 0))
    
    # Callback wrappers
    def _on_episode_spinbox_change(self):
        """Handle episode spinbox change."""
        pass  # Called by spinbox, but we use the button instead
    
    def _on_load_episode_button(self):
        """Handle load episode button click."""
        if self.on_load_episode:
            self.on_load_episode()
    
    def _on_toggle_playback_button(self):
        """Handle play/pause button click."""
        if self.on_toggle_playback:
            self.on_toggle_playback()
    
    def _on_stop_playback_button(self):
        """Handle stop button click."""
        if self.on_stop_playback:
            self.on_stop_playback()
    
    def _on_step_forward_button(self):
        """Handle step forward button click."""
        if self.on_step_forward:
            self.on_step_forward()
    
    def _on_step_backward_button(self):
        """Handle step backward button click."""
        if self.on_step_backward:
            self.on_step_backward()
    
    def _on_speed_scale_change(self, value):
        """Handle speed scale change."""
        if self.on_speed_change:
            self.on_speed_change(value)
    
    # Public methods for updating display
    def update_play_button_text(self, text: str) -> None:
        """Update the play button text."""
        if self.play_button:
            self.play_button.configure(text=text)
    
    def update_speed_display(self, speed_text: str) -> None:
        """Update the speed display label."""
        if self.speed_label:
            self.speed_label.configure(text=speed_text)
    
    def update_episode_info(self, info_text: str) -> None:
        """Update the episode information display."""
        self.episode_info_var.set(info_text)
    
    def update_frame_info(self, frame_text: str) -> None:
        """Update the frame information display."""
        self.frame_var.set(frame_text)
    
    def get_episode_index(self) -> int:
        """Get the currently selected episode index."""
        try:
            return int(self.episode_var.get())
        except ValueError:
            return 0
    
    def get_playback_speed(self) -> float:
        """Get the current playback speed."""
        return self.speed_var.get()


class TimelineComponent:
    """Timeline scrubber component for frame navigation."""
    
    def __init__(self, parent_frame: ttk.Frame):
        """
        Initialize the timeline component.
        
        Args:
            parent_frame: Parent frame to contain the timeline
        """
        self.parent_frame = parent_frame
        self.timeline_scale: Optional[ttk.Scale] = None
        self.on_timeline_change: Optional[Callable] = None
        
        self._setup_timeline()
    
    def _setup_timeline(self) -> None:
        """Setup the timeline scrubber."""
        timeline_frame = ttk.LabelFrame(self.parent_frame, text="Timeline", padding=10)
        timeline_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.timeline_scale = ttk.Scale(
            timeline_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self._on_timeline_scale_change
        )
        self.timeline_scale.pack(fill=tk.X)
    
    def _on_timeline_scale_change(self, value):
        """Handle timeline scale change."""
        if self.on_timeline_change:
            self.on_timeline_change(value)
    
    def set_range(self, max_frame: int) -> None:
        """Set the maximum range of the timeline."""
        if self.timeline_scale:
            self.timeline_scale.configure(to=max_frame)
    
    def set_position(self, frame: int) -> None:
        """Set the current position of the timeline."""
        if self.timeline_scale:
            self.timeline_scale.set(frame)
    
    def get_position(self) -> float:
        """Get the current position of the timeline."""
        if self.timeline_scale:
            return self.timeline_scale.get()
        return 0.0