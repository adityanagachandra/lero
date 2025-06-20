#!/usr/bin/env python3
"""
batch_copy_episodes.py

This script demonstrates how to copy multiple episodes with new instructions
using the LeRobot Dataset Editor Python API.

Usage:
    python batch_copy_episodes.py <dataset_path> --episodes 1,3,5,7 --instruction "Pick up the red block"

Example:
    python batch_copy_episodes.py /path/to/dataset --episodes "1,3,5" --instruction "Pick up the red block"
    python batch_copy_episodes.py /path/to/dataset --episodes "10,20,30" --instruction "Place object in container" --dry-run

Licensed under the Apache License 2.0
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from lerobot_dataset_editor import LeRobotDatasetEditor
except ImportError as e:
    print(f"Error: Could not import LeRobot Dataset Editor: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)


class BatchEpisodeCopier:
    """Handles batch copying of episodes with enhanced error handling and logging."""
    
    def __init__(self, dataset_path: str, log_level: str = "INFO"):
        """
        Initialize the batch copier.
        
        Args:
            dataset_path: Path to the dataset
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.dataset_path = Path(dataset_path)
        self.editor: Optional[LeRobotDatasetEditor] = None
        
        # Setup logging
        self._setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            "total_episodes": 0,
            "successful_copies": 0,
            "failed_copies": 0,
            "skipped_episodes": 0,
            "start_time": None,
            "end_time": None
        }
    
    def _setup_logging(self, log_level: str) -> None:
        """Setup logging configuration."""
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Setup file handler
        log_file = Path(__file__).parent / "batch_copy_episodes.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        # Configure logger
        logger = logging.getLogger()
        logger.setLevel(numeric_level)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    def validate_dataset(self) -> bool:
        """
        Validate the dataset and initialize the editor.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            if not self.dataset_path.exists():
                self.logger.error(f"Dataset directory does not exist: {self.dataset_path}")
                return False
            
            if not (self.dataset_path / "meta").exists():
                self.logger.error(f"Invalid dataset: meta directory not found")
                return False
            
            if not (self.dataset_path / "meta" / "info.json").exists():
                self.logger.error(f"Invalid dataset: info.json not found")
                return False
            
            # Initialize editor
            self.editor = LeRobotDatasetEditor(str(self.dataset_path))
            
            # Get dataset info
            episode_count = self.editor.count_episodes()
            self.logger.info(f"Dataset validated successfully - {episode_count} episodes found")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating dataset: {e}")
            return False
    
    def validate_episodes(self, episode_numbers: List[int]) -> Tuple[List[int], List[int]]:
        """
        Validate episode numbers against the dataset.
        
        Args:
            episode_numbers: List of episode numbers to validate
            
        Returns:
            Tuple of (valid_episodes, invalid_episodes)
        """
        if not self.editor:
            raise RuntimeError("Editor not initialized - call validate_dataset() first")
        
        total_episodes = self.editor.count_episodes()
        valid_episodes = []
        invalid_episodes = []
        
        for episode_num in episode_numbers:
            if 0 <= episode_num < total_episodes:
                valid_episodes.append(episode_num)
            else:
                invalid_episodes.append(episode_num)
                self.logger.warning(
                    f"Episode {episode_num} is out of range "
                    f"(valid range: 0-{total_episodes-1})"
                )
        
        return valid_episodes, invalid_episodes
    
    def copy_episode_safe(self, episode_num: int, instruction: str, dry_run: bool = False) -> bool:
        """
        Safely copy a single episode with error handling.
        
        Args:
            episode_num: Episode number to copy
            instruction: New instruction for the copy
            dry_run: Whether to perform a dry run
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"{'[DRY RUN] ' if dry_run else ''}Copying episode {episode_num}...")
            
            # Get episode info for logging
            episode_info = self.editor.get_episode_info(episode_num)
            self.logger.debug(f"Episode {episode_num} info: {episode_info['length']} frames")
            
            # Perform the copy
            success = self.editor.copy_episode_with_new_instruction(
                episode_num, instruction, dry_run=dry_run
            )
            
            if success:
                action = "would be copied" if dry_run else "copied successfully"
                self.logger.info(f"Episode {episode_num} {action}")
                return True
            else:
                self.logger.error(f"Failed to copy episode {episode_num}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error copying episode {episode_num}: {e}")
            return False
    
    def batch_copy(self, episode_numbers: List[int], instruction: str, 
                   dry_run: bool = False, continue_on_error: bool = True) -> bool:
        """
        Perform batch copying of episodes.
        
        Args:
            episode_numbers: List of episode numbers to copy
            instruction: New instruction for copied episodes
            dry_run: Whether to perform dry run
            continue_on_error: Whether to continue if individual episodes fail
            
        Returns:
            True if all operations successful, False otherwise
        """
        if not self.editor:
            raise RuntimeError("Editor not initialized")
        
        self.stats["start_time"] = time.time()
        self.stats["total_episodes"] = len(episode_numbers)
        
        self.logger.info("="*60)
        self.logger.info("Starting batch copy operation")
        self.logger.info(f"Episodes to copy: {episode_numbers}")
        self.logger.info(f"New instruction: '{instruction}'")
        self.logger.info(f"Dry run mode: {dry_run}")
        self.logger.info(f"Continue on error: {continue_on_error}")
        self.logger.info("="*60)
        
        # Validate episodes
        valid_episodes, invalid_episodes = self.validate_episodes(episode_numbers)
        
        if invalid_episodes:
            self.stats["skipped_episodes"] = len(invalid_episodes)
            self.logger.warning(f"Skipping {len(invalid_episodes)} invalid episodes: {invalid_episodes}")
        
        if not valid_episodes:
            self.logger.error("No valid episodes to process")
            return False
        
        # Process each episode
        all_successful = True
        
        for i, episode_num in enumerate(valid_episodes, 1):
            self.logger.info(f"[{i}/{len(valid_episodes)}] Processing episode {episode_num}")
            
            success = self.copy_episode_safe(episode_num, instruction, dry_run)
            
            if success:
                self.stats["successful_copies"] += 1
            else:
                self.stats["failed_copies"] += 1
                all_successful = False
                
                if not continue_on_error:
                    self.logger.error("Stopping due to error (continue_on_error=False)")
                    break
            
            # Add small delay between operations to avoid overwhelming the system
            time.sleep(0.1)
        
        self.stats["end_time"] = time.time()
        self._print_summary()
        
        return all_successful
    
    def _print_summary(self) -> None:
        """Print operation summary."""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        self.logger.info("="*60)
        self.logger.info("Batch copy operation completed")
        self.logger.info(f"Total episodes processed: {self.stats['total_episodes']}")
        self.logger.info(f"Successful copies: {self.stats['successful_copies']}")
        self.logger.info(f"Failed copies: {self.stats['failed_copies']}")
        self.logger.info(f"Skipped episodes: {self.stats['skipped_episodes']}")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        
        if self.stats["failed_copies"] > 0:
            self.logger.warning(f"{self.stats['failed_copies']} operations failed")
        else:
            self.logger.info("All operations completed successfully")
        
        self.logger.info("="*60)


def parse_episode_list(episode_str: str) -> List[int]:
    """
    Parse comma-separated episode numbers.
    
    Args:
        episode_str: Comma-separated episode numbers (e.g., "1,3,5,7")
        
    Returns:
        List of episode numbers
        
    Raises:
        ValueError: If parsing fails
    """
    try:
        episodes = []
        for part in episode_str.split(','):
            part = part.strip()
            if '-' in part:
                # Handle ranges like "1-5"
                start, end = part.split('-', 1)
                episodes.extend(range(int(start), int(end) + 1))
            else:
                episodes.append(int(part))
        
        # Remove duplicates and sort
        return sorted(list(set(episodes)))
        
    except ValueError as e:
        raise ValueError(f"Invalid episode format '{episode_str}': {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Batch copy episodes with new instructions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Copy episodes 1, 3, 5 with new instruction
  python batch_copy_episodes.py /path/to/dataset --episodes "1,3,5" --instruction "Pick up the red block"
  
  # Copy a range of episodes
  python batch_copy_episodes.py /path/to/dataset --episodes "10-15" --instruction "New task"
  
  # Dry run to preview operations
  python batch_copy_episodes.py /path/to/dataset --episodes "1,3,5" --instruction "Test" --dry-run
  
  # With custom logging level
  python batch_copy_episodes.py /path/to/dataset --episodes "1,2,3" --instruction "Task" --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "dataset_path",
        help="Path to the LeRobot dataset directory"
    )
    
    parser.add_argument(
        "--episodes", "-e",
        required=True,
        help="Comma-separated episode numbers or ranges (e.g., '1,3,5' or '1-5,10,15-20')"
    )
    
    parser.add_argument(
        "--instruction", "-i",
        required=True,
        help="New instruction text for copied episodes"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview operations without making changes"
    )
    
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop processing if any episode fails (default: continue)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    try:
        # Parse episode numbers
        episode_numbers = parse_episode_list(args.episodes)
        
        # Create copier
        copier = BatchEpisodeCopier(args.dataset_path, args.log_level)
        
        # Validate dataset
        if not copier.validate_dataset():
            return 1
        
        # Perform batch copy
        success = copier.batch_copy(
            episode_numbers=episode_numbers,
            instruction=args.instruction,
            dry_run=args.dry_run,
            continue_on_error=not args.stop_on_error
        )
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())