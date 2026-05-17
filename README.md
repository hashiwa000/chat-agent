# chat-agent

OpenAI API を使う簡易チャットエージェントです。  
`main.py` からツール（温度ツール、Minecraft 情報検索ツール）を呼び出せます。

## 前提

- Python 3.11 以上
- `uv` がインストール済み
- OpenAI API Key

## セットアップ

1. 依存関係をインストール

```sh
uv sync
```

2. `.env` を作成

```sh
cp .env.example .env
```

`.env.example` がない場合は、以下内容で `.env` を新規作成してください。

```dotenv
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

3. 環境変数を読み込み（`run.sh` を使う場合は不要）

```sh
set -a
source .env
set +a
```

## 実行方法

### 方法1: run.sh で実行

```sh
chmod +x run.sh
./run.sh
```

`run.sh` は `.env` を読み込んだ上で `uv run src/main.py` を実行します。

### 方法2: 直接実行

```sh
uv run src/main.py
```

## 設定

`src/config/app_config.json` で以下を変更できます。

- `model`
- `system_prompt`
- `logger.level`（例: `DEBUG`, `INFO`）
- `logger.format`

## テスト

### Minecraft ツールのテストのみ実行

```sh
python3 -m unittest -v tests/test_minecraft.py
```

### 全テスト実行

```sh
python3 -m unittest discover -s tests -p "test_*.py" -v
```
