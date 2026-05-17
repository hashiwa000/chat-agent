import json
from pathlib import Path
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
import logging

from tools.minecraft import search_minecraft_info, tools_spec as minecraft_tools_spec

logger = logging.getLogger(__name__)

APP_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "app_config.json"

available_functions = {
    "search_minecraft_info": search_minecraft_info,
}
all_tools_spec = minecraft_tools_spec


def load_app_config():
    with open(APP_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


app_config = load_app_config()


def configure_logger():
    logger_config = app_config.get("logger", {})
    level_name = str(logger_config.get("level", "INFO")).upper()
    log_level = getattr(logging, level_name, logging.INFO)
    log_format = logger_config.get(
        "format",
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    logger.setLevel(log_level)
    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(handler)

configure_logger()

def process_messages(client, messages):
    logger.debug(f'message(frontend => llm) = {messages}')
    logger.debug(f'tools_spec = {all_tools_spec}')

    # ステップ 1：モデルに、ツール定義とともにメッセージを送信
    response = client.chat.completions.create(
        model=app_config.get("model", "gpt-4o"),
        messages=messages,
        tools=all_tools_spec,
    )
    response_message = response.choices[0].message
    logger.debug(f'message(llm -> frontend) = {response_message}')
    if response.usage is not None:
        logger.debug(
            "context window usage: prompt_tokens=%s, completion_tokens=%s, total_tokens=%s",
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
            response.usage.total_tokens,
        )
    else:
        logger.debug("context window usage: unavailable")

    # ステップ 2：会話にモデルのレスポンスを追加
    #（関数呼び出し、または通常のメッセージの可能性がある）
    messages.append(response_message)
    # ステップ 3：モデルがツールを使いたいかどうかを確認
    if response_message.tool_calls:
        # ステップ 4：ツール呼び出しを抽出し、評価を行う
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            logger.debug(f'function call: {function_name}({function_args})')

            function_response = function_to_call(
                # 注：Python では `**` 演算子は辞書を
                # キーワード引数にアンパックする
                **function_args
            )
            logger.debug(f'function result: {function_name}({function_args}) => {function_response}')
            # ステップ 5：モデルが今後のターンで関数のレスポンスを
            # 確認できるように、関数のレスポンスで会話を拡張
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )

client = OpenAI()

def run_conversation(client):
    # メッセージを初期化し、エージェントの機能を説明する序文を作成
    messages = [
        {
            "role": "system",
            "content": app_config.get("system_prompt", "あなたは役に立つアシスタントです。"),
        }
    ] # tools がグローバル名前空間で定義されていることに注意

    print("チャットエージェントに聞きたいことを書いてください！")

    while True:
        # ユーザー入力を要求し、メッセージに追加
        user_input = input(">> ")
        if user_input == "":
            break
        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )
        while True:
            new_messages = process_messages(client, messages)
            last_message = messages[-1]
            if not isinstance(last_message, ChatCompletionMessage):
                continue # これは、単なるツールレスポンスメッセージ
            # 最後のメッセージがアシスタントのレスポンスの場合、そのコンテンツを出力
            if last_message.content is not None:
                print(last_message.content)
                # ツール呼び出しでない場合、次のメッセージを待機
                # ブレークし、入力を待機
                if last_message.tool_calls is None:
                    break
    return messages

run_conversation(client)
