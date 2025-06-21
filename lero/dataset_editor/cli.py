"""
Command line interface for the dataset editor.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
from .core import LeRobotDatasetEditor
from .constants import ErrorMessages


class CLIHandler:
    """Handles command line interface operations."""
    
    def __init__(self):
        """Initialize CLI handler."""
        self.parser = self._setup_argument_parser()
    
    def _setup_argument_parser(self) -> argparse.ArgumentParser:
        """Setup command line argument parser."""
        parser = argparse.ArgumentParser(
            description="LERO - LeRobot dataset Operations toolkit",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Show dataset summary
  %(prog)s /path/to/dataset --summary
  
  # List episodes
  %(prog)s /path/to/dataset --list 20 --list-start 10
  
  # Show specific episode with data sample
  %(prog)s /path/to/dataset --episode 5 --show-data
  
  # Delete episode (with dry run first)
  %(prog)s /path/to/dataset --delete 5 --dry-run
  %(prog)s /path/to/dataset --delete 5
  
  # Copy episode with new instruction
  %(prog)s /path/to/dataset --copy 3 --instruction "New task description"
  
  # Launch GUI viewer
  %(prog)s /path/to/dataset --gui --episode 5
            """
        )
        
        # Positional arguments
        parser.add_argument(
            "dataset_path", 
            help="Path to the LeRobot dataset directory"
        )
        
        # Display options
        display_group = parser.add_argument_group("display options")
        display_group.add_argument(
            "--summary", 
            action="store_true", 
            help="Show detailed dataset summary"
        )
        display_group.add_argument(
            "--list", 
            type=int, 
            nargs="?", 
            const=10, 
            help="List episodes (default: 10)"
        )
        display_group.add_argument(
            "--list-start", 
            type=int, 
            default=0, 
            help="Starting episode for listing"
        )
        display_group.add_argument(
            "--episode", 
            type=int, 
            help="Show specific episode details"
        )
        display_group.add_argument(
            "--show-data", 
            action="store_true", 
            help="Include data sample when displaying episode"
        )
        
        # Edit operations
        edit_group = parser.add_argument_group("edit operations")
        edit_group.add_argument(
            "--delete", 
            type=int, 
            help="Delete specific episode and renumber remaining episodes"
        )
        edit_group.add_argument(
            "--copy", 
            type=int, 
            help="Copy specific episode with new instruction"
        )
        edit_group.add_argument(
            "--instruction", 
            type=str, 
            help="New instruction for copied episode (required with --copy)"
        )
        edit_group.add_argument(
            "--dry-run", 
            action="store_true", 
            help="Preview operations without making changes"
        )
        
        # GUI options
        gui_group = parser.add_argument_group("GUI options")
        gui_group.add_argument(
            "--gui", 
            action="store_true", 
            help="Launch GUI viewer for episodes"
        )
        
        return parser
    
    def parse_args(self, args=None) -> argparse.Namespace:
        """Parse command line arguments."""
        return self.parser.parse_args(args)
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """
        Validate command line arguments.
        
        Args:
            args: Parsed arguments
            
        Returns:
            True if valid, False otherwise
        """
        # Validate dataset path
        dataset_path = Path(args.dataset_path)
        if not dataset_path.exists():
            print(ErrorMessages.INVALID_DATASET_PATH.format(path=dataset_path))
            return False
        
        # Validate dataset structure
        if not self._validate_dataset_structure(dataset_path):
            return False
        
        # Validate copy operation requires instruction
        if args.copy is not None and not args.instruction:
            print(ErrorMessages.INSTRUCTION_REQUIRED)
            return False
        
        # Validate episode indices are non-negative
        for arg_name in ['episode', 'delete', 'copy']:
            value = getattr(args, arg_name)
            if value is not None and value < 0:
                print(f"Error: --{arg_name} must be non-negative")
                return False
        
        # Validate list parameters
        if args.list is not None and args.list <= 0:
            print("Error: --list count must be positive")
            return False
        
        if args.list_start < 0:
            print("Error: --list-start must be non-negative")
            return False
        
        return True
    
    def _validate_dataset_structure(self, dataset_path: Path) -> bool:
        """
        Validate dataset structure and required files.
        
        Args:
            dataset_path: Path to the dataset
            
        Returns:
            True if valid, False otherwise
        """
        # Check required directories
        required_dirs = ["meta", "data"]
        for dir_name in required_dirs:
            if not (dataset_path / dir_name).exists():
                print(f"Error: Missing required directory: {dir_name}")
                return False
        
        # Check required metadata files
        required_files = ["meta/info.json", "meta/episodes.jsonl", "meta/tasks.jsonl"]
        for file_path in required_files:
            if not (dataset_path / file_path).exists():
                print(f"Error: Missing required file: {file_path}")
                return False
        
        # Validate info.json structure
        try:
            import json
            with open(dataset_path / "meta" / "info.json", "r") as f:
                info = json.load(f)
                
            # Check required fields
            required_fields = ["total_episodes", "robot_type"]
            for field in required_fields:
                if field not in info:
                    print(f"Error: Missing required field in info.json: {field}")
                    return False
                    
        except Exception as e:
            print(f"Error: Invalid info.json: {e}")
            return False
        
        return True
    
    def execute_command(self, args: argparse.Namespace) -> int:
        """
        Execute the command based on parsed arguments.
        
        Args:
            args: Parsed and validated arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            editor = LeRobotDatasetEditor(args.dataset_path)
            
            # Handle GUI launch first (exclusive operation)
            if args.gui:
                return self._handle_gui_launch(args, editor)
            
            # Handle other operations
            executed_operation = False
            
            if args.summary:
                editor.dataset_summary()
                executed_operation = True
            
            if args.list is not None:
                editor.list_episodes(start=args.list_start, count=args.list)
                executed_operation = True
            
            if args.episode is not None:
                try:
                    editor.display_episode(args.episode, show_data_sample=args.show_data)
                except ValueError as e:
                    print(f"Error: {e}")
                    return 1
                executed_operation = True
            
            if args.delete is not None:
                success = editor.delete_episode(args.delete, dry_run=args.dry_run)
                if not success:
                    return 1
                executed_operation = True
            
            if args.copy is not None:
                success = editor.copy_episode_with_new_instruction(
                    args.copy, args.instruction, dry_run=args.dry_run
                )
                if not success:
                    return 1
                executed_operation = True
            
            # If no specific action is requested, show summary
            if not executed_operation:
                editor.dataset_summary()
            
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _handle_gui_launch(self, args: argparse.Namespace, editor: LeRobotDatasetEditor) -> int:
        """
        Handle GUI launch.
        
        Args:
            args: Parsed arguments
            editor: Dataset editor instance
            
        Returns:
            Exit code
        """
        try:
            from ..gui import launch_episode_viewer
            launch_episode_viewer(args.dataset_path, args.episode)
            return 0
        except ImportError:
            print(ErrorMessages.GUI_DEPENDENCIES_MISSING)
            return 1
        except Exception as e:
            print(f"Error: Failed to launch GUI: {e}")
            return 1
    
    def run(self, args=None) -> int:
        """
        Run the CLI application.
        
        Args:
            args: Command line arguments (None to use sys.argv)
            
        Returns:
            Exit code
        """
        try:
            parsed_args = self.parse_args(args)
            
            if not self.validate_args(parsed_args):
                return 1
            
            return self.execute_command(parsed_args)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1


def main() -> int:
    """Main entry point for the CLI application."""
    cli = CLIHandler()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())