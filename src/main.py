import json
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
import logging

from tools.temp import get_room_temp, set_room_temp, tools_spec

logger = logging.getLogger(__name__)

# debug
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

available_functions = {
    "get_room_temp": get_room_temp,
    "set_room_temp": set_room_temp,
}

def process_messages(client, messages):
    logger.debug(f'messages = {messages}')
    logger.debug(f'tools_spec = {tools_spec}')

    # ステップ 1：モデルに、ツール定義とともにメッセージを送信
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools_spec,
    )
    response_message = response.choices[0].message
    logger.debug(f'response_message = {response_message}')

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

#messages = [
#    {
#        "role": "system",
#        "content": "あなたはホームボーイ、陽気で役に立つホームアシスタントです。"
#    },
#    {
#        "role": "user",
#        "content": "部屋を数度暖かくしてもらえますか。"
#    }
#]

client = OpenAI()
#process_messages(client, messages)

def run_conversation(client):
    # メッセージを初期化し、エージェントの機能を説明する序文を作成
    messages = [
        {
            "role": "system",
            "content": " あなたは、役に立つサーモスタットアシスタントです ",
        }
    ] # tools がグローバル名前空間で定義されていることに注意
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
