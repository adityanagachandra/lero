"""
Video display component for the GUI.
"""

import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from typing import Dict, Optional
from .constants import MAX_VIDEO_SIZE


class VideoDisplayComponent:
    """Handles video display functionality for multiple camera views."""
    
    def __init__(self, parent_frame: ttk.Frame):
        """
        Initialize the video display component.
        
        Args:
            parent_frame: Parent frame to contain video displays
        """
        self.parent_frame = parent_frame
        self.video_captures: Dict[str, Optional[cv2.VideoCapture]] = {}
        self.video_labels: Dict[str, ttk.Label] = {}
        
        # Create container for video frames
        self.container = ttk.Frame(parent_frame)
        self.container.pack(fill=tk.BOTH, expand=True)
    
    def setup_video_captures(self, episode_info: dict) -> None:
        """
        Setup video capture objects for all camera views.
        
        Args:
            episode_info: Dictionary containing episode information including video files
        """
        # Close existing captures
        self.close_all_captures()
        
        # Open new captures
        for video_key, video_path in episode_info['video_files'].items():
            if episode_info['videos_exist'][video_key]:
                cap = cv2.VideoCapture(str(video_path))
                if cap.isOpened():
                    self.video_captures[video_key] = cap
                else:
                    self.video_captures[video_key] = None
                    print(f"Failed to open video: {video_path}")
            else:
                self.video_captures[video_key] = None
    
    def setup_video_display_layout(self) -> None:
        """Setup video display widgets based on available cameras."""
        # Clear existing video widgets
        for widget in self.container.winfo_children():
            widget.destroy()
        self.video_labels.clear()
        
        # Create video display for each camera
        num_cameras = len(self.video_captures)
        if num_cameras == 0:
            ttk.Label(self.container, text="No video files available").pack()
            return
        
        # Arrange cameras in grid (2 columns max)
        cols = 2 if num_cameras > 1 else 1
        rows = (num_cameras + cols - 1) // cols
        
        for i, (video_key, cap) in enumerate(self.video_captures.items()):
            row = i // cols
            col = i % cols
            
            camera_frame = ttk.LabelFrame(self.container, text=video_key, padding=5)
            camera_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            if cap is not None:
                video_label = ttk.Label(camera_frame)
                video_label.pack()
                self.video_labels[video_key] = video_label
            else:
                ttk.Label(camera_frame, text="Video not available").pack()
        
        # Configure grid weights for proper resizing
        for i in range(cols):
            self.container.columnconfigure(i, weight=1)
        for i in range(rows):
            self.container.rowconfigure(i, weight=1)
    
    def update_video_frames(self, current_frame: int) -> None:
        """
        Update video frames for the current frame.
        
        Args:
            current_frame: Frame number to display
        """
        for video_key, cap in self.video_captures.items():
            if cap is not None and video_key in self.video_labels:
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                ret, frame = cap.read()
                if ret:
                    processed_frame = self._process_frame_for_display(frame)
                    self.video_labels[video_key].configure(image=processed_frame)
                    self.video_labels[video_key].image = processed_frame  # Keep reference
    
    def _process_frame_for_display(self, frame) -> ImageTk.PhotoImage:
        """
        Process a video frame for display in the GUI.
        
        Args:
            frame: OpenCV frame (BGR format)
            
        Returns:
            PhotoImage ready for display in tkinter
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize frame for display
        height, width = frame_rgb.shape[:2]
        if width > height:
            new_width = MAX_VIDEO_SIZE
            new_height = int(height * MAX_VIDEO_SIZE / width)
        else:
            new_height = MAX_VIDEO_SIZE
            new_width = int(width * MAX_VIDEO_SIZE / height)
        
        frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
        
        # Convert to PhotoImage
        image = Image.fromarray(frame_resized)
        return ImageTk.PhotoImage(image)
    
    def close_all_captures(self) -> None:
        """Close all video capture objects."""
        for cap in self.video_captures.values():
            if cap is not None:
                cap.release()
        self.video_captures.clear()
    
    def __del__(self):
        """Destructor to ensure video captures are closed."""
        self.close_all_captures()