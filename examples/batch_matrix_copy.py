#!/usr/bin/env python3
"""
batch_matrix_copy.py

複数のエピソードと複数のインストラクションを組み合わせてバッチコピーを行うスクリプト。
各エピソードに対して各インストラクションでコピーを作成します。

使用例:
    python batch_matrix_copy.py <dataset_path> --episodes 1,2,10,15 --instructions "put the block,catch the block"

詳細な例:
    # エピソード1,2,10,15を「put the block」と「catch the block」の両方のインストラクションでコピー
    python batch_matrix_copy.py /path/to/dataset \\
        --episodes "1,2,10,15" \\
        --instructions "put the block,catch the block"
    
    # 範囲指定とドライラン
    python batch_matrix_copy.py /path/to/dataset \\
        --episodes "1-5,10" \\
        --instructions "task A,task B,task C" \\
        --dry-run

Licensed under the Apache License 2.0
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from lero import LeRobotDatasetEditor
except ImportError as e:
    print(f"Error: Could not import LeRobot Dataset Editor: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)


class MatrixBatchCopier:
    """
    複数のエピソードと複数のインストラクションの組み合わせでバッチコピーを実行するクラス。
    """
    
    def __init__(self, dataset_path: str, log_level: str = "INFO"):
        """
        初期化
        
        Args:
            dataset_path: データセットのパス
            log_level: ログレベル (DEBUG, INFO, WARNING, ERROR)
        """
        self.dataset_path = Path(dataset_path)
        self.editor: Optional[LeRobotDatasetEditor] = None
        
        # ログ設定
        self._setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        
        # 統計情報
        self.stats = {
            "total_combinations": 0,
            "successful_copies": 0,
            "failed_copies": 0,
            "skipped_episodes": 0,
            "original_episode_count": 0,
            "final_episode_count": 0,
            "start_time": None,
            "end_time": None,
            "copy_matrix": {}  # {episode: {instruction: result}}
        }
    
    def _setup_logging(self, log_level: str) -> None:
        """ログ設定を初期化"""
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        
        # フォーマッター作成
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # ファイルハンドラー
        log_file = Path(__file__).parent / "batch_matrix_copy.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        # ログガー設定
        logger = logging.getLogger()
        logger.setLevel(numeric_level)
        # 既存ハンドラーをクリア
        logger.handlers.clear()
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    def validate_dataset(self) -> bool:
        """
        データセットの妥当性を検証しエディターを初期化
        
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
            
            # エディター初期化
            self.editor = LeRobotDatasetEditor(str(self.dataset_path))
            
            # データセット情報取得
            episode_count = self.editor.count_episodes()
            self.stats["original_episode_count"] = episode_count
            self.logger.info(f"Dataset validated successfully - {episode_count} episodes found")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating dataset: {e}")
            return False
    
    def validate_episodes(self, episode_numbers: List[int]) -> Tuple[List[int], List[int]]:
        """
        エピソード番号の妥当性を検証
        
        Args:
            episode_numbers: 検証するエピソード番号のリスト
            
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
        エラーハンドリング付きでエピソードを安全にコピー
        
        Args:
            episode_num: コピーするエピソード番号
            instruction: 新しいインストラクション
            dry_run: ドライランかどうか
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.debug(f"{'[DRY RUN] ' if dry_run else ''}Copying episode {episode_num} with instruction '{instruction}'")
            
            # エピソード情報を取得（ログ用）
            episode_info = self.editor.get_episode_info(episode_num)
            self.logger.debug(f"Episode {episode_num} info: {episode_info['length']} frames")
            
            # コピー実行
            success = self.editor.copy_episode_with_new_instruction(
                episode_num, instruction, dry_run=dry_run
            )
            
            if success:
                action = "would be copied" if dry_run else "copied successfully"
                self.logger.debug(f"Episode {episode_num} {action} with instruction '{instruction}'")
                return True
            else:
                self.logger.error(f"Failed to copy episode {episode_num} with instruction '{instruction}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Error copying episode {episode_num} with instruction '{instruction}': {e}")
            return False
    
    def matrix_copy(self, episode_numbers: List[int], instructions: List[str], 
                   dry_run: bool = False, continue_on_error: bool = True) -> bool:
        """
        マトリックス形式でバッチコピーを実行
        
        Args:
            episode_numbers: コピーするエピソード番号のリスト
            instructions: 適用するインストラクションのリスト
            dry_run: ドライランかどうか
            continue_on_error: エラー時に継続するかどうか
            
        Returns:
            True if all operations successful, False otherwise
        """
        if not self.editor:
            raise RuntimeError("Editor not initialized")
        
        self.stats["start_time"] = time.time()
        
        # エピソードの妥当性検証
        valid_episodes, invalid_episodes = self.validate_episodes(episode_numbers)
        
        if invalid_episodes:
            self.stats["skipped_episodes"] = len(invalid_episodes)
            self.logger.warning(f"Skipping {len(invalid_episodes)} invalid episodes: {invalid_episodes}")
        
        if not valid_episodes:
            self.logger.error("No valid episodes to process")
            return False
        
        # 総操作数を計算
        self.stats["total_combinations"] = len(valid_episodes) * len(instructions)
        
        self.logger.info("="*80)
        self.logger.info("Starting matrix batch copy operation")
        self.logger.info(f"Episodes to copy: {valid_episodes}")
        self.logger.info(f"Instructions: {instructions}")
        self.logger.info(f"Total combinations: {self.stats['total_combinations']}")
        self.logger.info(f"Dry run mode: {dry_run}")
        self.logger.info(f"Continue on error: {continue_on_error}")
        self.logger.info("="*80)
        
        # マトリックス処理の実行
        all_successful = True
        operation_count = 0
        
        # インストラクション毎にループ（要件に従い、各インストラクションで全エピソードを処理）
        for instruction_idx, instruction in enumerate(instructions, 1):
            self.logger.info(f"\n[INSTRUCTION {instruction_idx}/{len(instructions)}] Processing instruction: '{instruction}'")
            self.logger.info("-" * 60)
            
            # 各インストラクションで統計を初期化
            if instruction not in self.stats["copy_matrix"]:
                self.stats["copy_matrix"][instruction] = {}
            
            # エピソード毎にコピー実行
            for episode_idx, episode_num in enumerate(valid_episodes, 1):
                operation_count += 1
                
                self.logger.info(
                    f"[{operation_count}/{self.stats['total_combinations']}] "
                    f"Episode {episode_num} with instruction '{instruction}' "
                    f"(Episode {episode_idx}/{len(valid_episodes)})"
                )
                
                success = self.copy_episode_safe(episode_num, instruction, dry_run)
                
                # 結果を記録
                self.stats["copy_matrix"][instruction][episode_num] = success
                
                if success:
                    self.stats["successful_copies"] += 1
                    self.logger.info(f"✓ Success: Episode {episode_num} → '{instruction}'")
                else:
                    self.stats["failed_copies"] += 1
                    all_successful = False
                    self.logger.error(f"✗ Failed: Episode {episode_num} → '{instruction}'")
                    
                    if not continue_on_error:
                        self.logger.error("Stopping due to error (continue_on_error=False)")
                        self.stats["end_time"] = time.time()
                        self._print_summary()
                        return False
                
                # システム負荷軽減のための小さな遅延
                time.sleep(0.1)
        
        # 最終エピソード数を記録
        self.stats["final_episode_count"] = self.editor.count_episodes()
        self.stats["end_time"] = time.time()
        self._print_summary()
        
        return all_successful
    
    def _print_summary(self) -> None:
        """操作サマリーを表示"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        self.logger.info("\n" + "="*80)
        self.logger.info("MATRIX BATCH COPY OPERATION SUMMARY")
        self.logger.info("="*80)
        
        # 基本統計
        self.logger.info(f"Total combinations processed: {self.stats['total_combinations']}")
        self.logger.info(f"Successful copies: {self.stats['successful_copies']}")
        self.logger.info(f"Failed copies: {self.stats['failed_copies']}")
        self.logger.info(f"Skipped episodes: {self.stats['skipped_episodes']}")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        
        # エピソード数の変化
        added_episodes = self.stats["final_episode_count"] - self.stats["original_episode_count"]
        self.logger.info(f"Original episodes: {self.stats['original_episode_count']}")
        self.logger.info(f"Final episodes: {self.stats['final_episode_count']}")
        self.logger.info(f"Episodes added: {added_episodes}")
        
        # 詳細マトリックス結果
        if self.stats["copy_matrix"]:
            self.logger.info("\nDetailed Results by Instruction:")
            self.logger.info("-" * 50)
            
            for instruction, episodes in self.stats["copy_matrix"].items():
                successful = sum(1 for result in episodes.values() if result)
                total = len(episodes)
                self.logger.info(f"'{instruction}': {successful}/{total} successful")
                
                # 失敗したエピソードを表示
                failed_episodes = [ep for ep, result in episodes.items() if not result]
                if failed_episodes:
                    self.logger.warning(f"  Failed episodes: {failed_episodes}")
        
        # 最終ステータス
        if self.stats["failed_copies"] > 0:
            self.logger.warning(f"\n⚠️  {self.stats['failed_copies']} operations failed")
        else:
            self.logger.info(f"\n✅ All operations completed successfully")
        
        self.logger.info("="*80)


def parse_episode_list(episode_str: str) -> List[int]:
    """
    カンマ区切りのエピソード番号をパース
    
    Args:
        episode_str: カンマ区切りのエピソード番号 (例: "1,3,5,7" または "1-5,10")
        
    Returns:
        エピソード番号のリスト
        
    Raises:
        ValueError: パースに失敗した場合
    """
    try:
        episodes = []
        for part in episode_str.split(','):
            part = part.strip()
            if '-' in part:
                # 範囲指定の処理 (例: "1-5")
                start, end = part.split('-', 1)
                episodes.extend(range(int(start), int(end) + 1))
            else:
                episodes.append(int(part))
        
        # 重複を除去してソート
        return sorted(list(set(episodes)))
        
    except ValueError as e:
        raise ValueError(f"Invalid episode format '{episode_str}': {e}")


def parse_instruction_list(instruction_str: str) -> List[str]:
    """
    カンマ区切りのインストラクションをパース
    
    Args:
        instruction_str: カンマ区切りのインストラクション (例: "put the block,catch the block")
        
    Returns:
        インストラクションのリスト
    """
    instructions = []
    for instruction in instruction_str.split(','):
        instruction = instruction.strip()
        if instruction:  # 空文字列を除外
            instructions.append(instruction)
    
    if not instructions:
        raise ValueError("No valid instructions provided")
    
    return instructions


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="複数のエピソードと複数のインストラクションの組み合わせでバッチコピーを実行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # エピソード1,2,10,15を「put the block」と「catch the block」でコピー
  python batch_matrix_copy.py /path/to/dataset \\
      --episodes "1,2,10,15" \\
      --instructions "put the block,catch the block"
  
  # 範囲指定とより多くのインストラクション
  python batch_matrix_copy.py /path/to/dataset \\
      --episodes "1-5,10" \\
      --instructions "task A,task B,task C"
  
  # ドライラン（実際の変更なし）
  python batch_matrix_copy.py /path/to/dataset \\
      --episodes "1,2,3" \\
      --instructions "test instruction 1,test instruction 2" \\
      --dry-run
  
  # デバッグログ付き
  python batch_matrix_copy.py /path/to/dataset \\
      --episodes "1,2" \\
      --instructions "instruction 1,instruction 2" \\
      --log-level DEBUG

処理の順序:
  1. インストラクション1で全エピソードをコピー
  2. インストラクション2で全エピソードをコピー
  3. ...（以下同様）
  
例: episodes=[1,2,10,15], instructions=["put the block","catch the block"]
  → Episode 1 with "put the block"
  → Episode 2 with "put the block" 
  → Episode 10 with "put the block"
  → Episode 15 with "put the block"
  → Episode 1 with "catch the block"
  → Episode 2 with "catch the block"
  → Episode 10 with "catch the block"
  → Episode 15 with "catch the block"
        """
    )
    
    parser.add_argument(
        "dataset_path",
        help="LeRobotデータセットディレクトリのパス"
    )
    
    parser.add_argument(
        "--episodes", "-e",
        required=True,
        help="コピーするエピソード番号（カンマ区切り、範囲指定可能）例: '1,2,10,15' または '1-5,10'"
    )
    
    parser.add_argument(
        "--instructions", "-i",
        required=True,
        help="適用するインストラクション（カンマ区切り）例: 'put the block,catch the block'"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際の変更を行わずに操作をプレビュー"
    )
    
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="任意のエピソードが失敗した場合に処理を停止（デフォルト: 継続）"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="ログレベル（デフォルト: INFO）"
    )
    
    args = parser.parse_args()
    
    try:
        # エピソード番号をパース
        episode_numbers = parse_episode_list(args.episodes)
        
        # インストラクションをパース
        instructions = parse_instruction_list(args.instructions)
        
        print(f"Parsed episodes: {episode_numbers}")
        print(f"Parsed instructions: {instructions}")
        print(f"Total combinations: {len(episode_numbers)} × {len(instructions)} = {len(episode_numbers) * len(instructions)}")
        
        # コピアーを作成
        copier = MatrixBatchCopier(args.dataset_path, args.log_level)
        
        # データセット検証
        if not copier.validate_dataset():
            return 1
        
        # マトリックスバッチコピー実行
        success = copier.matrix_copy(
            episode_numbers=episode_numbers,
            instructions=instructions,
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