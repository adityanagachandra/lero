"""
GUI module for LERO - LeRobot dataset Operations toolkit

This module provides GUI components for viewing and editing LeRobot datasets.
"""

try:
    from .viewer import EpisodeGUIViewer, launch_episode_viewer
    from . import viewer
    from . import video_component
    from . import plot_component
    from . import controls
    from . import data_handler

    # Create aliases for backward compatibility and test expectations
    video_component.VideoComponent = video_component.VideoDisplayComponent
    plot_component.PlotComponent = plot_component.JointPlotComponent

    __all__ = [
        'EpisodeGUIViewer', 
        'launch_episode_viewer',
        'viewer',
        'video_component', 
        'plot_component',
        'controls',
        'data_handler'
    ]
    
except ImportError as e:
    # GUI dependencies not available
    error_message = f"GUI dependencies not available: {e}"
    
    def launch_episode_viewer(*args, **kwargs):
        raise ImportError(error_message)
    
    class EpisodeGUIViewer:
        def __init__(self, *args, **kwargs):
            raise ImportError(error_message)
    
    __all__ = ['EpisodeGUIViewer', 'launch_episode_viewer']