#!/bin/bash

# batch_matrix_copy.sh
#
# 複数のエピソードと複数のインストラクションを組み合わせてバッチコピーを行うシェルスクリプト
# Python版のbatch_matrix_copy.pyを呼び出して処理を実行します
#
# 使用例:
#   ./batch_matrix_copy.sh /path/to/dataset "1,2,10,15" "put the block,catch the block"
#
# Licensed under the Apache License 2.0

set -euo pipefail  # エラー時に即座に終了

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# カラー出力の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# ヘルプメッセージ
show_help() {
    cat << EOF
batch_matrix_copy.sh - 複数エピソード × 複数インストラクション バッチコピー

使用法:
    $0 <dataset_path> <episodes> <instructions> [options]

引数:
    dataset_path    LeRobotデータセットのパス
    episodes        エピソード番号（カンマ区切り、範囲指定可能）
                   例: "1,2,10,15" または "1-5,10"
    instructions    インストラクション（カンマ区切り）
                   例: "put the block,catch the block"

オプション:
    --dry-run       実際の変更を行わずにプレビュー
    --stop-on-error エラー時に処理を停止
    --log-level     ログレベル（DEBUG|INFO|WARNING|ERROR）
    --help, -h      このヘルプメッセージを表示

使用例:
    # 基本的な使用例
    $0 /path/to/dataset "1,2,10,15" "put the block,catch the block"
    
    # ドライランで確認
    $0 /path/to/dataset "1,2,3" "task A,task B" --dry-run
    
    # 範囲指定とデバッグログ
    $0 /path/to/dataset "1-5,10" "instruction 1,instruction 2" --log-level DEBUG

処理の流れ:
    1. インストラクション1で全エピソードをコピー
    2. インストラクション2で全エピソードをコピー
    3. ...（以下同様）

EOF
}

# Python環境の確認
check_python_env() {
    log_info "Checking Python environment..."
    
    # Pythonの存在確認
    if ! command -v python &> /dev/null; then
        log_error "Python not found. Please install Python 3.8 or later."
        return 1
    fi
    
    # Pythonバージョン確認
    python_version=$(python --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
    log_info "Python version: $python_version"
    
    # leroモジュールの確認
    if ! python -c "import lero" &> /dev/null; then
        log_warn "lero module not found. Attempting to install..."
        
        # プロジェクトルートから開発モードでインストール
        if [ -f "$PROJECT_ROOT/setup.py" ] || [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
            (cd "$PROJECT_ROOT" && pip install -e .)
        else
            log_error "Could not find setup.py or pyproject.toml in project root"
            return 1
        fi
    fi
    
    log_success "Python environment OK"
}

# 引数の妥当性チェック
validate_args() {
    local dataset_path="$1"
    local episodes="$2"
    local instructions="$3"
    
    log_info "Validating arguments..."
    
    # データセットパスの確認
    if [ ! -d "$dataset_path" ]; then
        log_error "Dataset directory does not exist: $dataset_path"
        return 1
    fi
    
    if [ ! -d "$dataset_path/meta" ]; then
        log_error "Invalid dataset: meta directory not found in $dataset_path"
        return 1
    fi
    
    if [ ! -f "$dataset_path/meta/info.json" ]; then
        log_error "Invalid dataset: info.json not found in $dataset_path/meta/"
        return 1
    fi
    
    # エピソード文字列の基本チェック
    if [[ ! "$episodes" =~ ^[0-9,\-\ ]+$ ]]; then
        log_error "Invalid episodes format: $episodes"
        log_error "Expected format: '1,2,3' or '1-5,10'"
        return 1
    fi
    
    # インストラクション文字列の基本チェック
    if [ -z "$instructions" ]; then
        log_error "Instructions cannot be empty"
        return 1
    fi
    
    log_success "Arguments validated"
}

# Pythonスクリプトの実行
run_matrix_copy() {
    local dataset_path="$1"
    local episodes="$2"
    local instructions="$3"
    shift 3
    local additional_args=("$@")
    
    local python_script="$SCRIPT_DIR/batch_matrix_copy.py"
    
    if [ ! -f "$python_script" ]; then
        log_error "Python script not found: $python_script"
        return 1
    fi
    
    log_info "Starting matrix batch copy operation..."
    log_info "Dataset: $dataset_path"
    log_info "Episodes: $episodes"
    log_info "Instructions: $instructions"
    
    # Pythonスクリプトを実行
    python "$python_script" \
        "$dataset_path" \
        --episodes "$episodes" \
        --instructions "$instructions" \
        "${additional_args[@]}"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "Matrix batch copy completed successfully"
    else
        log_error "Matrix batch copy failed with exit code $exit_code"
    fi
    
    return $exit_code
}

# 統計情報の表示
show_dataset_stats() {
    local dataset_path="$1"
    
    log_info "Dataset statistics:"
    
    # エピソード数を取得
    if command -v python &> /dev/null; then
        local episode_count
        episode_count=$(python -c "
import sys
sys.path.append('$PROJECT_ROOT')
from lero import LeRobotDatasetEditor
try:
    editor = LeRobotDatasetEditor('$dataset_path')
    print(f'Total episodes: {editor.count_episodes()}')
except Exception as e:
    print(f'Error: {e}')
")
        echo "  $episode_count"
    fi
}

# メイン処理
main() {
    # ヘルプの確認
    for arg in "$@"; do
        case $arg in
            -h|--help)
                show_help
                exit 0
                ;;
        esac
    done
    
    # 引数の数をチェック
    if [ $# -lt 3 ]; then
        log_error "Insufficient arguments"
        echo
        show_help
        exit 1
    fi
    
    local dataset_path="$1"
    local episodes="$2"
    local instructions="$3"
    shift 3
    
    # 残りの引数を配列として保存
    local additional_args=("$@")
    
    log_info "=== Matrix Batch Copy Script ==="
    
    # Python環境の確認
    if ! check_python_env; then
        exit 1
    fi
    
    # 引数の妥当性チェック
    if ! validate_args "$dataset_path" "$episodes" "$instructions"; then
        exit 1
    fi
    
    # 開始前の統計表示
    show_dataset_stats "$dataset_path"
    
    # 確認プロンプト（ドライランでない場合）
    if [[ ! " ${additional_args[*]} " =~ " --dry-run " ]]; then
        echo
        log_warn "This operation will modify the dataset."
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Operation cancelled by user"
            exit 0
        fi
    fi
    
    # マトリックスコピーの実行
    if run_matrix_copy "$dataset_path" "$episodes" "$instructions" "${additional_args[@]}"; then
        echo
        log_success "=== Operation completed successfully ==="
        
        # 終了後の統計表示
        show_dataset_stats "$dataset_path"
        exit 0
    else
        echo
        log_error "=== Operation failed ==="
        exit 1
    fi
}

# スクリプトが直接実行された場合
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi