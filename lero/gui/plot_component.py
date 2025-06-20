"""
Joint angle plotting component for the GUI.
"""

import numpy as np
import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Tuple
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.lines as mlines

from .constants import (
    JOINT_COLORS, 
    PLOT_TITLE_FONT_SIZE, 
    PLOT_LABEL_FONT_SIZE, 
    PLOT_TICK_FONT_SIZE,
    LEGEND_FONT_SIZE
)
from .data_handler import JointDataExtractor


class JointPlotComponent:
    """Handles joint angle plotting functionality."""
    
    def __init__(self, parent_frame: ttk.Frame):
        """
        Initialize the joint plot component.
        
        Args:
            parent_frame: Parent frame to contain the plot
        """
        self.parent_frame = parent_frame
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.current_frame_line: Optional[mlines.Line2D] = None
        self.joint_data: Optional[np.ndarray] = None
        
        self._setup_plot_area()
    
    def _setup_plot_area(self) -> None:
        """Setup the matplotlib figure and canvas."""
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, self.parent_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def setup_joint_plots(self, episode_data) -> bool:
        """
        Setup joint angle plots based on episode data.
        
        Args:
            episode_data: Pandas DataFrame containing episode data
            
        Returns:
            True if plots were successfully created, False otherwise
        """
        self.figure.clear()
        
        if episode_data is None:
            self._show_no_data_message('No joint data available')
            return False
        
        # Extract joint data
        joint_data, joint_names = JointDataExtractor.extract_joint_data(episode_data)
        
        if joint_data is None or len(joint_data) == 0:
            available_cols = '\\n'.join(episode_data.columns[:10])
            self._show_no_data_message(
                f'No joint angle data found\\nAvailable columns:\\n{available_cols}'
            )
            return False
        
        # Store joint data for updates
        self.joint_data = joint_data
        
        # Create the unified plot
        self._create_unified_joint_plot(joint_data, joint_names)
        
        self.figure.tight_layout()
        self.canvas.draw()
        return True
    
    def _create_unified_joint_plot(self, joint_data: np.ndarray, joint_names: List[str]) -> None:
        """
        Create a unified plot showing all joint angles.
        
        Args:
            joint_data: Array of shape (timesteps, num_joints)
            joint_names: List of joint names
        """
        ax = self.figure.add_subplot(111)
        
        num_joints = min(joint_data.shape[1], len(JOINT_COLORS))
        
        # Plot all joint trajectories
        for i in range(num_joints):
            joint_trajectory = joint_data[:, i]
            joint_name = joint_names[i] if i < len(joint_names) else f'Joint {i}'
            color = JOINT_COLORS[i % len(JOINT_COLORS)]
            
            ax.plot(joint_trajectory, color=color, alpha=0.8, linewidth=2, label=joint_name)
        
        # Add current frame marker (will be updated during playback)
        self.current_frame_line = ax.axvline(x=0, color='red', linewidth=3, alpha=0.8)
        
        # Configure plot appearance
        self._configure_plot_appearance(ax, joint_data)
    
    def _configure_plot_appearance(self, ax, joint_data: np.ndarray) -> None:
        """
        Configure the appearance of the joint plot.
        
        Args:
            ax: Matplotlib axis object
            joint_data: Joint data array for calculating limits
        """
        # Set labels and title
        ax.set_title('Robot Joint Angles', fontsize=PLOT_TITLE_FONT_SIZE, fontweight='bold')
        ax.set_xlabel('Frame', fontsize=PLOT_LABEL_FONT_SIZE)
        ax.set_ylabel('Angle (degrees)', fontsize=PLOT_LABEL_FONT_SIZE)
        ax.tick_params(labelsize=PLOT_TICK_FONT_SIZE)
        ax.grid(True, alpha=0.3)
        
        # Add legend
        ax.legend(loc='upper right', fontsize=LEGEND_FONT_SIZE, framealpha=0.9)
        
        # Set y-axis limits with padding
        y_min, y_max = JointDataExtractor.get_joint_value_range(joint_data)
        ax.set_ylim(y_min, y_max)
    
    def _show_no_data_message(self, message: str) -> None:
        """
        Show a message when no joint data is available.
        
        Args:
            message: Message to display
        """
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, message, 
               horizontalalignment='center', 
               verticalalignment='center',
               transform=ax.transAxes, 
               fontsize=8)
        self.canvas.draw()
    
    def update_current_frame_marker(self, current_frame: int) -> None:
        """
        Update the current frame marker on the plot.
        
        Args:
            current_frame: Current frame number
        """
        if self.current_frame_line is not None:
            self.current_frame_line.set_xdata([current_frame, current_frame])
            if self.canvas:
                self.canvas.draw_idle()
    
    def clear_plot(self) -> None:
        """Clear the plot and reset data."""
        if self.figure:
            self.figure.clear()
        if self.canvas:
            self.canvas.draw()
        self.current_frame_line = None
        self.joint_data = None