#!/usr/bin/env python3
"""
validate_dataset.py

Dataset validation script that performs comprehensive integrity checking
of LeRobot datasets.

This script validates:
- Dataset structure and metadata files
- Episode data and video file consistency
- File integrity and accessibility
- Metadata consistency

Usage:
    python validate_dataset.py <dataset_path> [options]

Licensed under the Apache License 2.0
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from lero import LeRobotDatasetEditor
except ImportError as e:
    print(f"Error: Could not import LeRobot Dataset Editor: {e}")
    sys.exit(1)


class DatasetValidator:
    """Comprehensive dataset validation tool."""
    
    def __init__(self, dataset_path: str, verbose: bool = False):
        """Initialize the validator."""
        self.dataset_path = Path(dataset_path)
        self.verbose = verbose
        self.validation_results = {
            "structure_check": {},
            "metadata_check": {},
            "episode_check": {},
            "file_integrity_check": {},
            "summary": {}
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 Starting comprehensive dataset validation...")
        print("=" * 60)
        
        # Run all validation checks
        self._validate_structure()
        self._validate_metadata()
        self._validate_episodes()
        self._validate_file_integrity()
        self._generate_summary()
        
        return self.validation_results
    
    def _validate_structure(self) -> None:
        """Validate basic dataset structure."""
        print("📁 Validating dataset structure...")
        
        structure_check = {
            "dataset_exists": False,
            "meta_dir_exists": False,
            "data_dir_exists": False,
            "videos_dir_exists": False,
            "required_files": {},
            "issues": []
        }
        
        # Check dataset directory
        if self.dataset_path.exists():
            structure_check["dataset_exists"] = True
        else:
            structure_check["issues"].append("Dataset directory does not exist")
        
        # Check required directories
        meta_dir = self.dataset_path / "meta"
        data_dir = self.dataset_path / "data"
        videos_dir = self.dataset_path / "videos"
        
        structure_check["meta_dir_exists"] = meta_dir.exists()
        structure_check["data_dir_exists"] = data_dir.exists()
        structure_check["videos_dir_exists"] = videos_dir.exists()
        
        if not meta_dir.exists():
            structure_check["issues"].append("Meta directory missing")
        if not data_dir.exists():
            structure_check["issues"].append("Data directory missing")
        if not videos_dir.exists():
            structure_check["issues"].append("Videos directory missing")
        
        # Check required files
        required_files = {
            "info.json": meta_dir / "info.json",
            "episodes.jsonl": meta_dir / "episodes.jsonl",
            "tasks.jsonl": meta_dir / "tasks.jsonl"
        }
        
        for file_name, file_path in required_files.items():
            exists = file_path.exists()
            structure_check["required_files"][file_name] = exists
            if not exists:
                structure_check["issues"].append(f"Required file missing: {file_name}")
        
        structure_check["is_valid"] = len(structure_check["issues"]) == 0
        self.validation_results["structure_check"] = structure_check
        
        if self.verbose:
            self._print_structure_results(structure_check)
    
    def _validate_metadata(self) -> None:
        """Validate metadata consistency."""
        print("📋 Validating metadata...")
        
        metadata_check = {
            "info_valid": False,
            "episodes_valid": False,
            "tasks_valid": False,
            "consistency_issues": [],
            "is_valid": False
        }
        
        try:
            # Try to load the dataset
            editor = LeRobotDatasetEditor(str(self.dataset_path))
            
            # Check if metadata loads correctly
            episode_count = editor.count_episodes()
            metadata_check["info_valid"] = True
            metadata_check["episodes_valid"] = True
            metadata_check["tasks_valid"] = True
            
            # Check consistency between metadata and actual episodes
            metadata = editor.operations.metadata
            
            # Check episode count consistency
            info_episode_count = metadata.info.get("total_episodes", 0) if metadata.info else 0
            actual_episode_count = len(metadata.episodes)
            
            if info_episode_count != actual_episode_count:
                metadata_check["consistency_issues"].append(
                    f"Episode count mismatch: info.json says {info_episode_count}, "
                    f"but found {actual_episode_count} in episodes.jsonl"
                )
            
            # Check task consistency
            info_task_count = metadata.info.get("total_tasks", 0) if metadata.info else 0
            actual_task_count = len(metadata.tasks)
            
            if info_task_count != actual_task_count:
                metadata_check["consistency_issues"].append(
                    f"Task count mismatch: info.json says {info_task_count}, "
                    f"but found {actual_task_count} in tasks.jsonl"
                )
            
            # Check episode index consistency
            for episode in metadata.episodes:
                episode_index = episode.get("episode_index")
                if episode_index is None:
                    metadata_check["consistency_issues"].append(
                        "Episode found without episode_index"
                    )
                elif episode_index >= episode_count:
                    metadata_check["consistency_issues"].append(
                        f"Episode index {episode_index} exceeds total episode count"
                    )
            
            metadata_check["is_valid"] = len(metadata_check["consistency_issues"]) == 0
            
        except Exception as e:
            metadata_check["consistency_issues"].append(f"Failed to load metadata: {e}")
            metadata_check["is_valid"] = False
        
        self.validation_results["metadata_check"] = metadata_check
        
        if self.verbose:
            self._print_metadata_results(metadata_check)
    
    def _validate_episodes(self) -> None:
        """Validate individual episodes."""
        print("📹 Validating episodes...")
        
        episode_check = {
            "total_episodes": 0,
            "valid_episodes": 0,
            "episodes_with_data": 0,
            "episodes_with_videos": 0,
            "problematic_episodes": [],
            "is_valid": False
        }
        
        try:
            editor = LeRobotDatasetEditor(str(self.dataset_path))
            total_episodes = editor.count_episodes()
            episode_check["total_episodes"] = total_episodes
            
            for i in range(total_episodes):
                try:
                    episode_info = editor.get_episode_info(i)
                    episode_issues = []
                    
                    # Check data file
                    if episode_info["data_exists"]:
                        episode_check["episodes_with_data"] += 1
                    else:
                        episode_issues.append("Missing data file")
                    
                    # Check video files
                    video_exists = any(episode_info["videos_exist"].values())
                    if video_exists:
                        episode_check["episodes_with_videos"] += 1
                    else:
                        episode_issues.append("Missing all video files")
                    
                    # Check for missing individual videos
                    missing_videos = [
                        key for key, exists in episode_info["videos_exist"].items()
                        if not exists
                    ]
                    if missing_videos:
                        episode_issues.append(f"Missing video files: {missing_videos}")
                    
                    # Check episode length
                    length = episode_info["length"]
                    if length == "Unknown" or (isinstance(length, int) and length <= 0):
                        episode_issues.append("Invalid episode length")
                    
                    if episode_issues:
                        episode_check["problematic_episodes"].append({
                            "episode_index": i,
                            "issues": episode_issues
                        })
                    else:
                        episode_check["valid_episodes"] += 1
                
                except Exception as e:
                    episode_check["problematic_episodes"].append({
                        "episode_index": i,
                        "issues": [f"Error accessing episode: {e}"]
                    })
            
            # Determine if validation passed
            problem_count = len(episode_check["problematic_episodes"])
            episode_check["is_valid"] = problem_count == 0
            
        except Exception as e:
            episode_check["problematic_episodes"].append({
                "episode_index": "global",
                "issues": [f"Failed to validate episodes: {e}"]
            })
            episode_check["is_valid"] = False
        
        self.validation_results["episode_check"] = episode_check
        
        if self.verbose:
            self._print_episode_results(episode_check)
    
    def _validate_file_integrity(self) -> None:
        """Validate file integrity and accessibility."""
        print("🔧 Validating file integrity...")
        
        integrity_check = {
            "data_files_readable": 0,
            "data_files_unreadable": 0,
            "video_files_readable": 0,
            "video_files_unreadable": 0,
            "corrupted_files": [],
            "is_valid": False
        }
        
        try:
            editor = LeRobotDatasetEditor(str(self.dataset_path))
            total_episodes = editor.count_episodes()
            
            for i in range(min(total_episodes, 10)):  # Sample first 10 episodes
                try:
                    episode_info = editor.get_episode_info(i)
                    
                    # Test data file readability
                    if episode_info["data_exists"]:
                        try:
                            import pandas as pd
                            df = pd.read_parquet(episode_info["data_file"])
                            if len(df) > 0:
                                integrity_check["data_files_readable"] += 1
                            else:
                                integrity_check["corrupted_files"].append(
                                    f"Episode {i}: Empty data file"
                                )
                                integrity_check["data_files_unreadable"] += 1
                        except Exception as e:
                            integrity_check["corrupted_files"].append(
                                f"Episode {i}: Corrupted data file - {e}"
                            )
                            integrity_check["data_files_unreadable"] += 1
                    
                    # Test video file accessibility (basic check)
                    for video_key, video_path in episode_info["video_files"].items():
                        if episode_info["videos_exist"][video_key]:
                            try:
                                # Basic file size check
                                size = video_path.stat().st_size
                                if size > 0:
                                    integrity_check["video_files_readable"] += 1
                                else:
                                    integrity_check["corrupted_files"].append(
                                        f"Episode {i}: Empty video file {video_key}"
                                    )
                                    integrity_check["video_files_unreadable"] += 1
                            except Exception as e:
                                integrity_check["corrupted_files"].append(
                                    f"Episode {i}: Inaccessible video file {video_key} - {e}"
                                )
                                integrity_check["video_files_unreadable"] += 1
                
                except Exception as e:
                    integrity_check["corrupted_files"].append(
                        f"Episode {i}: Error during integrity check - {e}"
                    )
            
            integrity_check["is_valid"] = len(integrity_check["corrupted_files"]) == 0
            
        except Exception as e:
            integrity_check["corrupted_files"].append(f"Global integrity check failed: {e}")
            integrity_check["is_valid"] = False
        
        self.validation_results["file_integrity_check"] = integrity_check
        
        if self.verbose:
            self._print_integrity_results(integrity_check)
    
    def _generate_summary(self) -> None:
        """Generate validation summary."""
        summary = {
            "overall_valid": True,
            "checks_passed": 0,
            "checks_failed": 0,
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check each validation result
        checks = [
            ("structure_check", "Dataset Structure"),
            ("metadata_check", "Metadata Consistency"),
            ("episode_check", "Episode Validation"),
            ("file_integrity_check", "File Integrity")
        ]
        
        for check_key, check_name in checks:
            check_result = self.validation_results.get(check_key, {})
            is_valid = check_result.get("is_valid", False)
            
            if is_valid:
                summary["checks_passed"] += 1
            else:
                summary["checks_failed"] += 1
                summary["overall_valid"] = False
                summary["critical_issues"].append(f"{check_name} failed")
        
        # Generate recommendations
        if not summary["overall_valid"]:
            summary["recommendations"].append("Fix critical issues before using the dataset")
        
        episode_check = self.validation_results.get("episode_check", {})
        if episode_check.get("problematic_episodes"):
            count = len(episode_check["problematic_episodes"])
            summary["warnings"].append(f"{count} episodes have issues")
        
        self.validation_results["summary"] = summary
    
    def print_validation_report(self) -> None:
        """Print a comprehensive validation report."""
        print("\n" + "=" * 80)
        print("📋 DATASET VALIDATION REPORT")
        print("=" * 80)
        
        summary = self.validation_results["summary"]
        
        # Overall status
        status = "✅ VALID" if summary["overall_valid"] else "❌ INVALID"
        print(f"\n🎯 OVERALL STATUS: {status}")
        print(f"   Checks Passed: {summary['checks_passed']}")
        print(f"   Checks Failed: {summary['checks_failed']}")
        
        # Critical issues
        if summary["critical_issues"]:
            print(f"\n❌ CRITICAL ISSUES:")
            for issue in summary["critical_issues"]:
                print(f"   - {issue}")
        
        # Warnings
        if summary["warnings"]:
            print(f"\n⚠️  WARNINGS:")
            for warning in summary["warnings"]:
                print(f"   - {warning}")
        
        # Recommendations
        if summary["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in summary["recommendations"]:
                print(f"   - {rec}")
        
        # Detailed results
        if self.verbose:
            self._print_detailed_results()
        
        print("\n" + "=" * 80)
    
    def _print_detailed_results(self) -> None:
        """Print detailed validation results."""
        print(f"\n📁 STRUCTURE CHECK:")
        structure = self.validation_results["structure_check"]
        print(f"   Dataset exists: {'✅' if structure['dataset_exists'] else '❌'}")
        print(f"   Meta directory: {'✅' if structure['meta_dir_exists'] else '❌'}")
        print(f"   Data directory: {'✅' if structure['data_dir_exists'] else '❌'}")
        print(f"   Videos directory: {'✅' if structure['videos_dir_exists'] else '❌'}")
        
        print(f"\n📋 METADATA CHECK:")
        metadata = self.validation_results["metadata_check"]
        print(f"   Info valid: {'✅' if metadata['info_valid'] else '❌'}")
        print(f"   Episodes valid: {'✅' if metadata['episodes_valid'] else '❌'}")
        print(f"   Tasks valid: {'✅' if metadata['tasks_valid'] else '❌'}")
        
        print(f"\n📹 EPISODE CHECK:")
        episodes = self.validation_results["episode_check"]
        print(f"   Total episodes: {episodes['total_episodes']}")
        print(f"   Valid episodes: {episodes['valid_episodes']}")
        print(f"   Episodes with data: {episodes['episodes_with_data']}")
        print(f"   Episodes with videos: {episodes['episodes_with_videos']}")
        print(f"   Problematic episodes: {len(episodes['problematic_episodes'])}")
        
        print(f"\n🔧 FILE INTEGRITY:")
        integrity = self.validation_results["file_integrity_check"]
        print(f"   Readable data files: {integrity['data_files_readable']}")
        print(f"   Unreadable data files: {integrity['data_files_unreadable']}")
        print(f"   Readable video files: {integrity['video_files_readable']}")
        print(f"   Unreadable video files: {integrity['video_files_unreadable']}")
    
    def _print_structure_results(self, results: Dict) -> None:
        """Print structure validation results."""
        pass  # Detailed printing handled in _print_detailed_results
    
    def _print_metadata_results(self, results: Dict) -> None:
        """Print metadata validation results."""
        pass  # Detailed printing handled in _print_detailed_results
    
    def _print_episode_results(self, results: Dict) -> None:
        """Print episode validation results."""
        pass  # Detailed printing handled in _print_detailed_results
    
    def _print_integrity_results(self, results: Dict) -> None:
        """Print integrity validation results."""
        pass  # Detailed printing handled in _print_detailed_results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive dataset validation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "dataset_path",
        help="Path to the LeRobot dataset directory"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed validation results"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only show final validation status"
    )
    
    args = parser.parse_args()
    
    try:
        # Create validator
        validator = DatasetValidator(args.dataset_path, verbose=args.verbose)
        
        # Run validation
        results = validator.validate_all()
        
        # Print report
        if not args.quiet:
            validator.print_validation_report()
        else:
            # Just print the overall status
            is_valid = results["summary"]["overall_valid"]
            status = "VALID" if is_valid else "INVALID"
            print(f"Dataset validation: {status}")
        
        # Return exit code based on validation result
        return 0 if results["summary"]["overall_valid"] else 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())