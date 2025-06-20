#!/usr/bin/env python3
"""
analyze_dataset.py

Comprehensive dataset analysis script that demonstrates advanced usage
of the LeRobot Dataset Editor API.

This script provides detailed analysis including:
- Dataset statistics and overview
- Episode-by-episode analysis
- Task distribution analysis
- File size analysis
- Data integrity checking

Usage:
    python analyze_dataset.py <dataset_path> [options]

Licensed under the Apache License 2.0
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from lero import LeRobotDatasetEditor
except ImportError as e:
    print(f"Error: Could not import LeRobot Dataset Editor: {e}")
    sys.exit(1)


class DatasetAnalyzer:
    """Comprehensive dataset analysis tool."""
    
    def __init__(self, dataset_path: str):
        """Initialize the analyzer."""
        self.dataset_path = Path(dataset_path)
        self.editor = LeRobotDatasetEditor(str(dataset_path))
        self.analysis_results = {}
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete dataset analysis."""
        print("🔍 Starting comprehensive dataset analysis...")
        print("=" * 60)
        
        self.analysis_results = {
            "basic_stats": self._analyze_basic_statistics(),
            "episode_analysis": self._analyze_episodes(),
            "task_analysis": self._analyze_tasks(),
            "file_analysis": self._analyze_files(),
            "integrity_check": self._check_integrity()
        }
        
        return self.analysis_results
    
    def _analyze_basic_statistics(self) -> Dict[str, Any]:
        """Analyze basic dataset statistics."""
        print("📊 Analyzing basic statistics...")
        
        stats = self.editor.get_statistics()
        summary = self.editor.operations.get_dataset_summary()
        
        basic_stats = {
            "dataset_path": str(self.dataset_path),
            "total_episodes": stats["total_episodes"],
            "total_tasks": stats["total_tasks"],
            "episodes_with_data": stats["episodes_with_data"],
            "episodes_with_videos": stats["episodes_with_videos"],
            "total_frames": stats["total_frames"],
            "robot_type": summary.get("robot_type", "Unknown"),
            "fps": summary.get("fps", "Unknown"),
            "codebase_version": summary.get("codebase_version", "Unknown")
        }
        
        # Calculate percentages
        if basic_stats["total_episodes"] > 0:
            basic_stats["data_coverage_percent"] = (
                stats["episodes_with_data"] / stats["total_episodes"] * 100
            )
            basic_stats["video_coverage_percent"] = (
                stats["episodes_with_videos"] / stats["total_episodes"] * 100
            )
        
        return basic_stats
    
    def _analyze_episodes(self) -> Dict[str, Any]:
        """Analyze episode-level information."""
        print("📹 Analyzing episodes...")
        
        episode_analysis = {
            "episode_lengths": [],
            "missing_data_episodes": [],
            "missing_video_episodes": [],
            "tasks_per_episode": [],
            "length_statistics": {}
        }
        
        total_episodes = self.editor.count_episodes()
        
        for i in range(total_episodes):
            try:
                episode_info = self.editor.get_episode_info(i)
                
                # Episode length
                length = episode_info['length']
                if isinstance(length, int):
                    episode_analysis["episode_lengths"].append(length)
                
                # Missing files
                if not episode_info['data_exists']:
                    episode_analysis["missing_data_episodes"].append(i)
                
                missing_videos = [
                    video_key for video_key, exists in episode_info['videos_exist'].items()
                    if not exists
                ]
                if missing_videos:
                    episode_analysis["missing_video_episodes"].append({
                        "episode": i,
                        "missing_videos": missing_videos
                    })
                
                # Tasks per episode
                episode_analysis["tasks_per_episode"].append(len(episode_info['tasks']))
                
            except Exception as e:
                print(f"Warning: Could not analyze episode {i}: {e}")
        
        # Calculate length statistics
        if episode_analysis["episode_lengths"]:
            lengths = episode_analysis["episode_lengths"]
            episode_analysis["length_statistics"] = {
                "min_length": min(lengths),
                "max_length": max(lengths),
                "mean_length": sum(lengths) / len(lengths),
                "median_length": sorted(lengths)[len(lengths) // 2]
            }
        
        return episode_analysis
    
    def _analyze_tasks(self) -> Dict[str, Any]:
        """Analyze task distribution."""
        print("🎯 Analyzing tasks...")
        
        tasks = self.editor.operations.metadata.tasks
        
        task_analysis = {
            "total_unique_tasks": len(tasks),
            "task_list": [],
            "task_usage": {},
            "episodes_per_task": {}
        }
        
        # Build task list
        for task in tasks:
            task_info = {
                "task_index": task.get("task_index"),
                "task_description": task.get("task"),
                "usage_count": 0
            }
            task_analysis["task_list"].append(task_info)
            task_analysis["task_usage"][task.get("task", "")] = 0
        
        # Count task usage
        total_episodes = self.editor.count_episodes()
        for i in range(total_episodes):
            try:
                episode_info = self.editor.get_episode_info(i)
                for task_desc in episode_info['tasks']:
                    if task_desc in task_analysis["task_usage"]:
                        task_analysis["task_usage"][task_desc] += 1
            except Exception as e:
                print(f"Warning: Could not analyze tasks for episode {i}: {e}")
        
        # Update usage counts in task list
        for task_info in task_analysis["task_list"]:
            task_desc = task_info["task_description"]
            task_info["usage_count"] = task_analysis["task_usage"].get(task_desc, 0)
        
        return task_analysis
    
    def _analyze_files(self) -> Dict[str, Any]:
        """Analyze file sizes and storage usage."""
        print("💾 Analyzing file sizes...")
        
        file_analysis = {
            "total_size_bytes": 0,
            "data_size_bytes": 0,
            "video_size_bytes": 0,
            "episode_sizes": [],
            "storage_statistics": {}
        }
        
        # Get statistics from editor
        stats = self.editor.get_statistics()
        file_sizes = stats.get("file_sizes", {})
        
        file_analysis["total_size_bytes"] = file_sizes.get("total_size", 0)
        file_analysis["data_size_bytes"] = file_sizes.get("total_data_size", 0)
        file_analysis["video_size_bytes"] = file_sizes.get("total_video_size", 0)
        
        # Calculate human-readable sizes
        file_analysis["total_size_human"] = self._format_bytes(file_analysis["total_size_bytes"])
        file_analysis["data_size_human"] = self._format_bytes(file_analysis["data_size_bytes"])
        file_analysis["video_size_human"] = self._format_bytes(file_analysis["video_size_bytes"])
        
        # Calculate percentages
        if file_analysis["total_size_bytes"] > 0:
            file_analysis["data_percentage"] = (
                file_analysis["data_size_bytes"] / file_analysis["total_size_bytes"] * 100
            )
            file_analysis["video_percentage"] = (
                file_analysis["video_size_bytes"] / file_analysis["total_size_bytes"] * 100
            )
        
        return file_analysis
    
    def _check_integrity(self) -> Dict[str, Any]:
        """Check dataset integrity."""
        print("🔍 Checking dataset integrity...")
        
        validation_results = self.editor.validate_dataset()
        
        integrity_check = {
            "is_valid": validation_results["valid"],
            "error_count": len(validation_results["errors"]),
            "warning_count": len(validation_results["warnings"]),
            "errors": validation_results["errors"],
            "warnings": validation_results["warnings"],
            "missing_files_count": len(validation_results["missing_files"]),
            "missing_files": validation_results["missing_files"][:10]  # Limit to first 10
        }
        
        return integrity_check
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def print_analysis_report(self) -> None:
        """Print a formatted analysis report."""
        if not self.analysis_results:
            print("No analysis results available. Run run_full_analysis() first.")
            return
        
        print("\n" + "=" * 80)
        print("📋 DATASET ANALYSIS REPORT")
        print("=" * 80)
        
        # Basic Statistics
        basic = self.analysis_results["basic_stats"]
        print(f"\n📊 BASIC STATISTICS")
        print(f"   Dataset Path: {basic['dataset_path']}")
        print(f"   Total Episodes: {basic['total_episodes']}")
        print(f"   Total Tasks: {basic['total_tasks']}")
        print(f"   Total Frames: {basic['total_frames']}")
        print(f"   Robot Type: {basic['robot_type']}")
        print(f"   FPS: {basic['fps']}")
        print(f"   Data Coverage: {basic.get('data_coverage_percent', 0):.1f}%")
        print(f"   Video Coverage: {basic.get('video_coverage_percent', 0):.1f}%")
        
        # Episode Analysis
        episodes = self.analysis_results["episode_analysis"]
        print(f"\n📹 EPISODE ANALYSIS")
        if episodes["length_statistics"]:
            stats = episodes["length_statistics"]
            print(f"   Episode Length Stats:")
            print(f"     Min: {stats['min_length']} frames")
            print(f"     Max: {stats['max_length']} frames")
            print(f"     Mean: {stats['mean_length']:.1f} frames")
            print(f"     Median: {stats['median_length']} frames")
        
        print(f"   Missing Data Episodes: {len(episodes['missing_data_episodes'])}")
        print(f"   Missing Video Episodes: {len(episodes['missing_video_episodes'])}")
        
        # Task Analysis
        tasks = self.analysis_results["task_analysis"]
        print(f"\n🎯 TASK ANALYSIS")
        print(f"   Total Unique Tasks: {tasks['total_unique_tasks']}")
        print(f"   Most Common Tasks:")
        
        # Sort tasks by usage
        sorted_tasks = sorted(
            tasks["task_usage"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for i, (task_desc, count) in enumerate(sorted_tasks[:5]):
            print(f"     {i+1}. '{task_desc}': {count} episodes")
        
        # File Analysis
        files = self.analysis_results["file_analysis"]
        print(f"\n💾 STORAGE ANALYSIS")
        print(f"   Total Size: {files['total_size_human']}")
        print(f"   Data Files: {files['data_size_human']} ({files.get('data_percentage', 0):.1f}%)")
        print(f"   Video Files: {files['video_size_human']} ({files.get('video_percentage', 0):.1f}%)")
        
        # Integrity Check
        integrity = self.analysis_results["integrity_check"]
        print(f"\n🔍 INTEGRITY CHECK")
        print(f"   Dataset Valid: {'✅ Yes' if integrity['is_valid'] else '❌ No'}")
        print(f"   Errors: {integrity['error_count']}")
        print(f"   Warnings: {integrity['warning_count']}")
        print(f"   Missing Files: {integrity['missing_files_count']}")
        
        if integrity["errors"]:
            print(f"\n   Errors:")
            for error in integrity["errors"][:5]:
                print(f"     - {error}")
        
        if integrity["warnings"]:
            print(f"\n   Warnings:")
            for warning in integrity["warnings"][:5]:
                print(f"     - {warning}")
        
        print("\n" + "=" * 80)
    
    def export_analysis(self, output_path: str, format: str = "json") -> None:
        """Export analysis results to file."""
        output_file = Path(output_path)
        
        if format.lower() == "json":
            with open(output_file, 'w') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
            print(f"📄 Analysis exported to {output_file}")
        
        elif format.lower() == "csv":
            # Export basic episode info as CSV
            episodes_data = []
            total_episodes = self.editor.count_episodes()
            
            for i in range(total_episodes):
                try:
                    episode_info = self.editor.get_episode_info(i)
                    episodes_data.append({
                        "episode_index": i,
                        "length": episode_info["length"],
                        "data_exists": episode_info["data_exists"],
                        "num_tasks": len(episode_info["tasks"]),
                        "tasks": "; ".join(episode_info["tasks"])
                    })
                except Exception:
                    continue
            
            df = pd.DataFrame(episodes_data)
            df.to_csv(output_file, index=False)
            print(f"📄 Episode data exported to {output_file}")
        
        else:
            raise ValueError(f"Unsupported format: {format}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive dataset analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "dataset_path",
        help="Path to the LeRobot dataset directory"
    )
    
    parser.add_argument(
        "--export",
        help="Export analysis results to file"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Export format (default: json)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress detailed output"
    )
    
    args = parser.parse_args()
    
    try:
        # Create analyzer
        analyzer = DatasetAnalyzer(args.dataset_path)
        
        # Run analysis
        results = analyzer.run_full_analysis()
        
        # Print report
        if not args.quiet:
            analyzer.print_analysis_report()
        
        # Export results
        if args.export:
            analyzer.export_analysis(args.export, args.format)
        
        # Return success/failure based on integrity check
        is_valid = results["integrity_check"]["is_valid"]
        return 0 if is_valid else 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())