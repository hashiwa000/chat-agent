import random

def get_room_temp():
    return str(random.randint(60, 80))

def set_room_temp(temp):
    return "DONE"

tools_spec = [
    {
        "type": "function",
        "function": {
            "name": "get_room_temp",
            "description": "華氏で部屋の温度を取得",
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_room_temp",
            "description": "華氏で部屋の温度を設定",
            "parameters": {
                "type": "object",
                "properties": {
                    "temp": {
                        "type": "integer",
                        "description": "華氏での望ましい部屋の温度",
                    },
                },
                "required": ["temp"],
            },
        },
    }
]

