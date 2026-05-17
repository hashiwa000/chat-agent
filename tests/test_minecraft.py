import unittest
from unittest.mock import patch

from src.tools import minecraft


class TestMinecraftTool(unittest.TestCase):
    def test_empty_query_returns_message(self):
        result = minecraft.search_minecraft_info("")
        self.assertEqual(result, "検索キーワードが空です。")

    @patch("src.tools.minecraft._search_mediawiki")
    def test_default_sources_search_all(self, mock_search):
        mock_search.side_effect = [
            [{"title": "村", "snippet": "<span class=\"searchmatch\">構造物</span>"}],
            [{"title": "Village", "snippet": "A naturally generated structure"}],
            [{"title": "Village (Fandom)", "snippet": "Village page"}],
        ]

        result = minecraft.search_minecraft_info("village", limit=1)

        self.assertIn("[Wikipedia]", result)
        self.assertIn("[Minecraft Wiki]", result)
        self.assertIn("[Fandom]", result)
        self.assertIn("要約: 構造物", result)
        self.assertEqual(mock_search.call_count, 3)

    @patch("src.tools.minecraft._search_mediawiki")
    def test_sources_filter_works(self, mock_search):
        mock_search.return_value = [{"title": "Village", "snippet": "Village page"}]

        result = minecraft.search_minecraft_info("village", sources=["minecraft_wiki"], limit=2)

        self.assertIn("[Minecraft Wiki]", result)
        self.assertNotIn("[Wikipedia]", result)
        self.assertNotIn("[Fandom]", result)
        self.assertEqual(mock_search.call_count, 1)

    @patch("src.tools.minecraft._search_mediawiki")
    def test_limit_is_clamped_to_range(self, mock_search):
        mock_search.return_value = []

        minecraft.search_minecraft_info("village", limit=99, sources=["wikipedia"])

        _, kwargs = mock_search.call_args
        self.assertEqual(kwargs, {"prefix": "Minecraft "})
        args = mock_search.call_args.args
        self.assertEqual(args[2], 5)

    @patch("src.tools.minecraft._search_mediawiki", side_effect=RuntimeError("network error"))
    def test_error_is_returned_as_message(self, _mock_search):
        result = minecraft.search_minecraft_info("village")
        self.assertIn("情報取得に失敗しました", result)


if __name__ == "__main__":
    unittest.main()
