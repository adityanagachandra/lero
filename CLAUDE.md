# CLAUDE.md - Development Guidelines

このファイルは、LERO (LeRobot dataset Operations toolkit) プロジェクトの開発において、Claude Code や他のAI開発ツールが効率的に作業するためのガイドラインとプロジェクト情報をまとめたものです。

## プロジェクト概要

**LERO** は LeRobot データセット操作のための包括的なツールキットです。ロボット模倣学習用のLeRobotデータセットの編集・管理機能を提供します。

### 主な機能
- LeRobotデータセットの読み込み・編集
- エピソード管理（削除、コピー、修正）
- GUI インターフェースによる視覚的なデータセット閲覧
- バッチ操作と自動化
- コマンドライン インターフェース

### プロジェクト構造
```
lero/
├── __init__.py              # メインエントリーポイント
├── __main__.py              # CLI メインエントリー
├── dataset_editor/          # コアデータセット編集機能
│   ├── cli.py              # コマンドライン インターフェース
│   ├── core.py             # メインデータセットエディタークラス
│   ├── operations.py       # データセット操作（削除、コピーなど）
│   ├── metadata.py         # メタデータ管理
│   ├── file_utils.py       # ファイルシステム操作
│   ├── display.py          # データ表示機能
│   └── constants.py        # 定数とエラーメッセージ
├── gui/                    # GUI コンポーネント（オプション）
│   ├── __init__.py         # GUI モジュール（フォールバック対応）
│   ├── viewer.py           # メインGUIビューワー
│   ├── video_component.py  # ビデオ表示コンポーネント
│   ├── plot_component.py   # プロット表示コンポーネント
│   ├── controls.py         # コントロールパネル
│   ├── data_handler.py     # データフォーマッター
│   └── constants.py        # GUI定数
tests/                      # E2Eテストスイート
examples/                   # 使用例スクリプト
```

## 開発環境とツール

### 仮想環境
```bash
# 仮想環境の有効化（開発時は必ず使用）
source venv/bin/activate

# 依存関係のインストール
pip install -e .

# GUI依存関係（オプション）
uv sync --group gui
```

### テスト実行
```bash
# 全テスト実行（venv環境で実行）
source venv/bin/activate && python -m pytest tests/ -v --tb=short -o addopts=""

# 特定のテストカテゴリ
python -m pytest tests/test_cli_e2e.py -v        # CLI テスト
python -m pytest tests/test_gui_e2e.py -v        # GUI テスト
python -m pytest tests/test_dataset_operations_e2e.py -v  # データセット操作テスト
python -m pytest tests/test_error_handling_e2e.py -v     # エラーハンドリングテスト
```

### リント・フォーマット
```bash
# コードフォーマット確認
npm run lint      # プロジェクトにlintコマンドがある場合
npm run typecheck # プロジェクトにtypecheckコマンドがある場合
```

## 重要な開発ガイドライン

### 1. エラーハンドリング
- **CLI**: エラー時は適切な終了コード（1）を返す
- **GUI**: ImportError を適切にハンドリングし、フォールバック機能を提供
- **例外**: 具体的なエラーメッセージを含むカスタム例外を使用

### 2. テスト要件
- **全テストは venv 環境で実行する**
- E2E テストが優先（99個のテスト全てが通る必要がある）
- GUI テストはヘッドレス環境での実行をサポート
- モック使用時は subprocess との互換性に注意

### 3. GUI 依存関係
- GUI機能は **オプション** である
- 依存関係が欠けている場合の適切なフォールバック
- ImportError 時の明確なエラーメッセージ

### 4. データセット構造
```
dataset/
├── meta/
│   ├── info.json           # データセット情報
│   ├── episodes.jsonl      # エピソードメタデータ
│   └── tasks.jsonl         # タスク定義
├── data/
│   └── chunk-000/
│       └── episode_XXXXXX.parquet  # エピソードデータ
└── videos/
    └── chunk-000/
        ├── observation.images.left/
        └── observation.images.wrist.right/
```

## よくある問題と解決方法

### 1. テスト失敗
**症状**: GUI テストが失敗する
**解決**: 
- venv環境で実行しているか確認
- GUI依存関係がインストールされているか確認
- ヘッドレス環境の場合、適切なモックが設定されているか確認

### 2. ImportError
**症状**: GUI関連のImportError
**解決**:
- `uv sync --group gui` で GUI依存関係をインストール
- フォールバック機能が正しく動作するか確認

### 3. データセット構造エラー
**症状**: 無効なデータセットエラー
**解決**:
- 必須ディレクトリ（meta, data）が存在するか確認
- info.json に required_fields が含まれているか確認

## 最近の主要な修正履歴

### 2024年版 E2E テスト修正
1. **CLI 出力フォーマット修正**: テスト期待値をアプリケーションの実際の出力に合わせて更新
2. **エラーハンドリング強化**: 適切な終了コードとエラーメッセージの実装
3. **GUI テスト修正**: インポートパス更新とフォールバック機能の改善
4. **データセット操作修正**: ファイル削除・リネーミングロジックの修正
5. **メタデータ一貫性**: エピソード追加時のデータ構造統一

### パッケージ名変更対応
- `lerobot_dataset_editor` から `lero` へのリブランディング対応
- 全インポートパスとテストの更新完了

## コード品質基準

### コミット前チェックリスト
- [ ] 全テスト通過（99/99）
- [ ] venv環境でのテスト実行確認
- [ ] 新機能にはテストを追加
- [ ] エラーハンドリングが適切
- [ ] GUI依存関係のフォールバック動作確認

### コーディング規約
- PEP 8 準拠
- 型ヒント使用推奨
- docstring でクラス・関数の説明を記載
- エラーメッセージは constants.py で管理

## 追加情報

### CLI 使用例
```bash
# データセット概要表示
lero /path/to/dataset --summary

# エピソード一覧
lero /path/to/dataset --list 10

# 特定エピソード表示
lero /path/to/dataset --episode 5 --show-data

# エピソード削除（ドライラン）
lero /path/to/dataset --delete 5 --dry-run

# エピソードコピー
lero /path/to/dataset --copy 3 --instruction "新しいタスク説明"

# GUI起動
lero /path/to/dataset --gui --episode 5
```

### 重要なファイル
- `lero/dataset_editor/constants.py`: エラーメッセージと定数
- `lero/gui/__init__.py`: GUI フォールバック処理
- `tests/conftest.py`: テスト用フィクスチャ
- `tests/pytest.ini`: テスト設定

このガイドラインに従うことで、一貫性のある高品質な開発を継続できます。