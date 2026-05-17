import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen


WIKIPEDIA_API = "https://ja.wikipedia.org/w/api.php"
MINECRAFT_WIKI_API = "https://minecraft.wiki/api.php"
FANDOM_API = "https://minecraft.fandom.com/api.php"
USER_AGENT = "chat-agent/1.0"


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _search_mediawiki(api_url: str, query: str, limit: int, prefix: str = ""):
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"{prefix}{query}",
        "format": "json",
        "utf8": 1,
        "srlimit": limit,
    }
    url = f"{api_url}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=10) as res:
        payload = json.loads(res.read().decode("utf-8"))
    return payload.get("query", {}).get("search", [])


def search_minecraft_info(
    query: str,
    limit: int = 3,
    lang: str = "ja",
    sources: list[str] | None = None,
) -> str:
    """Wikipedia / Minecraft Wiki / Fandom の公開情報を検索して要約を返す。"""
    query = (query or "").strip()
    if not query:
        return "検索キーワードが空です。"

    if limit < 1:
        limit = 1
    if limit > 5:
        limit = 5

    wikipedia_api_url = WIKIPEDIA_API
    if lang == "en":
        wikipedia_api_url = "https://en.wikipedia.org/w/api.php"

    try:
        selected_sources = sources or ["wikipedia", "minecraft_wiki", "fandom"]
        selected_sources = [s for s in selected_sources if s in ("wikipedia", "minecraft_wiki", "fandom")]
        if not selected_sources:
            selected_sources = ["wikipedia", "minecraft_wiki", "fandom"]

        provider_results = []

        if "wikipedia" in selected_sources:
            items = _search_mediawiki(wikipedia_api_url, query, limit, prefix="Minecraft ")
            provider_results.append(("Wikipedia", f"https://{lang}.wikipedia.org/wiki/", items))

        if "minecraft_wiki" in selected_sources:
            items = _search_mediawiki(MINECRAFT_WIKI_API, query, limit)
            provider_results.append(("Minecraft Wiki", "https://minecraft.wiki/w/", items))

        if "fandom" in selected_sources:
            items = _search_mediawiki(FANDOM_API, query, limit)
            provider_results.append(("Fandom", "https://minecraft.fandom.com/wiki/", items))
    except Exception as e:
        return f"情報取得に失敗しました: {e}"

    lines = []
    for source_name, base_url, items in provider_results:
        if not items:
            lines.append(f"[{source_name}] 結果なし")
            continue
        lines.append(f"[{source_name}]")
        for i, item in enumerate(items, start=1):
            title = item.get("title", "(タイトル不明)")
            snippet = _strip_html(item.get("snippet", ""))
            page_url = f"{base_url}{title.replace(' ', '_')}"
            lines.append(f"{i}. {title}\\n要約: {snippet}\\nURL: {page_url}")

    if not lines:
        return f"'{query}' に関する結果は見つかりませんでした。"
    return "\\n\\n".join(lines)


tools_spec = [
    {
        "type": "function",
        "function": {
            "name": "search_minecraft_info",
            "description": "インターネット上の公開情報からMinecraft関連情報を検索する",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索キーワード。例: 1.21 update, village, enchantment",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得件数(1-5)",
                        "default": 3,
                    },
                    "lang": {
                        "type": "string",
                        "description": "検索言語。ja または en",
                        "enum": ["ja", "en"],
                        "default": "ja",
                    },
                    "sources": {
                        "type": "array",
                        "description": "検索対象ソース。未指定ならすべて検索",
                        "items": {
                            "type": "string",
                            "enum": ["wikipedia", "minecraft_wiki", "fandom"],
                        },
                    },
                },
                "required": ["query"],
            },
        },
    }
]
