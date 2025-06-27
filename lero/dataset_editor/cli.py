"""
Command line interface for the dataset editor.
"""

import argparse
import sys
from pathlib import Path
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
  
  # List all tasks in dataset  
  %(prog)s /path/to/dataset --tasks
  
  # List episodes
  %(prog)s /path/to/dataset --list 20 --list-start 10
  
  # Show specific episode with data sample
  %(prog)s /path/to/dataset --episode 5 --show-data
  
  # Delete episode (with dry run first)
  %(prog)s /path/to/dataset --delete 5 --dry-run
  %(prog)s /path/to/dataset --delete 5
  
  # Copy episode with new instruction
  %(prog)s /path/to/dataset --copy 3 --instruction "New task description"
  
  # Merge datasets (with dry run first)
  %(prog)s /path/to/dataset --merge /path/to/dataset1 /path/to/dataset2 --output /path/to/merged --dry-run
  %(prog)s /path/to/dataset --merge /path/to/dataset1 /path/to/dataset2 --output /path/to/merged
  
  # Merge with task mapping
  %(prog)s /path/to/dataset --merge /path/to/dataset1 /path/to/dataset2 --output /path/to/merged --task-mapping mapping.json
  
  # Filter dataset excluding specific features (with dry run first)
  %(prog)s /path/to/dataset --filter-exclude observation.images.left,observation.depth --output /path/to/filtered --dry-run
  %(prog)s /path/to/dataset --filter-exclude observation.images.left,observation.depth --output /path/to/filtered
  
  # Filter dataset including only specific features
  %(prog)s /path/to/dataset --filter-include action,observation.state --output /path/to/filtered
  
  # Filter dataset with frame range
  %(prog)s /path/to/dataset --filter-frames 10:90 --output /path/to/filtered
  
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
        display_group.add_argument(
            "--tasks", 
            action="store_true", 
            help="Show list of all tasks in the dataset"
        )
        display_group.add_argument(
            "--no-color", 
            action="store_true", 
            help="Disable colored output"
        )
        display_group.add_argument(
            "--color", 
            action="store_true", 
            help="Force colored output even when not detected"
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
            "--merge", 
            nargs="+", 
            help="Merge multiple datasets into one (provide source dataset paths)"
        )
        edit_group.add_argument(
            "--output", 
            type=str, 
            help="Output path for merged dataset (required with --merge)"
        )
        edit_group.add_argument(
            "--task-mapping", 
            type=str, 
            help="JSON file containing task name mappings for merge operation"
        )
        edit_group.add_argument(
            "--filter-exclude", 
            type=str, 
            help="Comma-separated list of features to exclude from filtered dataset"
        )
        edit_group.add_argument(
            "--filter-include", 
            type=str, 
            help="Comma-separated list of features to include in filtered dataset"
        )
        edit_group.add_argument(
            "--filter-frames", 
            type=str, 
            help="Frame range to filter (format: start:end, e.g., 10:90)"
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
        
        # Validate merge operation requires output path
        if args.merge is not None and not args.output:
            print("Error: --merge requires --output to specify the merged dataset path")
            return False
        
        # Validate merge source datasets exist
        if args.merge is not None:
            for merge_path in args.merge:
                if not Path(merge_path).exists():
                    print(f"Error: Merge source dataset does not exist: {merge_path}")
                    return False
        
        # Validate task mapping file exists if provided
        if args.task_mapping and not Path(args.task_mapping).exists():
            print(f"Error: Task mapping file does not exist: {args.task_mapping}")
            return False
        
        # Validate filter operations require output path
        filter_operations = [args.filter_exclude, args.filter_include, args.filter_frames]
        if any(filter_operations) and not args.output:
            print("Error: Filter operations require --output to specify the filtered dataset path")
            return False
        
        # Validate filter exclude and include are mutually exclusive
        if args.filter_exclude and args.filter_include:
            print("Error: --filter-exclude and --filter-include are mutually exclusive")
            return False
        
        # Validate frame range format
        if args.filter_frames:
            try:
                if ':' not in args.filter_frames:
                    raise ValueError("Invalid format")
                start, end = args.filter_frames.split(':')
                start_frame, end_frame = int(start), int(end)
                if start_frame < 0 or end_frame < 0 or start_frame > end_frame:
                    raise ValueError("Invalid range")
            except ValueError:
                print("Error: --filter-frames must be in format 'start:end' with valid positive integers")
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
            # Set color environment variables based on arguments
            import os
            if args.no_color:
                os.environ['NO_COLOR'] = '1'
            elif args.color:
                os.environ['FORCE_COLOR'] = '1'
            
            editor = LeRobotDatasetEditor(args.dataset_path)
            
            # Handle GUI launch first (exclusive operation)
            if args.gui:
                return self._handle_gui_launch(args, editor)
            
            # Handle other operations
            executed_operation = False
            
            if args.summary:
                editor.dataset_summary()
                executed_operation = True
            
            if args.tasks:
                editor.list_tasks()
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
            
            if args.merge is not None:
                success = self._handle_merge_operation(args, editor)
                if not success:
                    return 1
                executed_operation = True
            
            # Handle filter operations
            filter_operations = [args.filter_exclude, args.filter_include, args.filter_frames]
            if any(filter_operations):
                success = self._handle_filter_operation(args, editor)
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
    
    def _handle_merge_operation(self, args: argparse.Namespace, editor: LeRobotDatasetEditor) -> bool:
        """
        Handle dataset merge operation.
        
        Args:
            args: Parsed arguments
            editor: Dataset editor instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load task mapping if provided
            task_mapping = None
            if args.task_mapping:
                import json
                with open(args.task_mapping, 'r') as f:
                    task_mapping = json.load(f)
            
            # Convert merge paths to Path objects
            source_datasets = [Path(path) for path in args.merge]
            output_path = Path(args.output)
            
            # Execute merge operation
            return editor.operations.merge_datasets(
                source_datasets=source_datasets,
                output_path=output_path,
                task_mapping=task_mapping,
                dry_run=args.dry_run
            )
            
        except Exception as e:
            print(f"Error during merge operation: {e}")
            return False
    
    def _handle_filter_operation(self, args: argparse.Namespace, editor: LeRobotDatasetEditor) -> bool:
        """
        Handle dataset filter operation.
        
        Args:
            args: Parsed arguments
            editor: Dataset editor instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse filter arguments
            exclude_features = None
            include_features = None
            frame_range = None
            
            if args.filter_exclude:
                exclude_features = [f.strip() for f in args.filter_exclude.split(',')]
            
            if args.filter_include:
                include_features = [f.strip() for f in args.filter_include.split(',')]
            
            if args.filter_frames:
                start, end = args.filter_frames.split(':')
                frame_range = (int(start), int(end))
            
            # Execute filter operation
            output_path = Path(args.output)
            return editor.operations.filter_dataset(
                output_path=output_path,
                exclude_features=exclude_features,
                include_features=include_features,
                frame_range=frame_range,
                dry_run=args.dry_run
            )
            
        except Exception as e:
            print(f"Error during filter operation: {e}")
            return False
    
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