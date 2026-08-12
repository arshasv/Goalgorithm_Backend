import json
import asyncio
import unittest
from datetime import date
from unittest.mock import AsyncMock, patch

import httpx

from app.services.football_api_service import FootballAPIError, FootballAPIService


class TestFootballAPI(unittest.TestCase):
    def setUp(self):
        self.patcher = patch("app.services.football_api_service.settings")
        self.mock_settings = self.patcher.start()
        self.mock_settings.football_api_key = "test_api_key"
        self.mock_settings.football_api_base_url = "https://test.api"
        self.mock_settings.football_allowed_leagues = {"1"}
        self.mock_settings.football_timezone = "Asia/Kolkata"

    def tearDown(self):
        self.patcher.stop()

    def test_fetch_fixtures_success(self):
        service = FootballAPIService()
        mock_response = httpx.Response(
            200,
            json={
                "response": [
                    {
                        "fixture": {"id": 12345, "date": "2026-06-18T20:00:00+00:00", "status": {"short": "NS"}},
                        "league": {"name": "Test League", "id": 1},
                        "teams": {
                            "home": {"name": "Home FC"},
                            "away": {"name": "Away FC"}
                        }
                    }
                ],
                "errors": []
            },
            request=httpx.Request("GET", "https://test.api/fixtures")
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = asyncio.run(service.fetch_fixtures_by_date(date(2026, 6, 18)))
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["external_api_id"], "12345")
            self.assertEqual(result[0]["home_team_name"], "Home FC")
            self.assertEqual(result[0]["away_team_name"], "Away FC")
            self.assertEqual(result[0]["competition_name"], "Test League")
            self.assertEqual(result[0]["status"], "NS")
            mock_get.assert_called_once()

    def test_fetch_fixtures_empty(self):
        service = FootballAPIService()
        mock_response = httpx.Response(
            200,
            json={
                "response": [],
                "errors": []
            },
            request=httpx.Request("GET", "https://test.api/fixtures")
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = asyncio.run(service.fetch_fixtures_by_date(date(2026, 6, 18)))
            
            self.assertEqual(len(result), 0)
            mock_get.assert_called_once()

    def test_fetch_fixtures_api_error(self):
        service = FootballAPIService()
        mock_response = httpx.Response(
            200,
            json={
                "response": [],
                "errors": {"rateLimit": "Rate limit exceeded"}
            },
            request=httpx.Request("GET", "https://test.api/fixtures")
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            with self.assertRaisesRegex(FootballAPIError, "Football API Error: Rate limit exceeded"):
                asyncio.run(service.fetch_fixtures_by_date(date(2024, 6, 1)))

    def test_fetch_fixtures_http_error(self):
        service = FootballAPIService()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = httpx.Response(
                500,
                request=httpx.Request("GET", "https://test.api/fixtures")
            )
            mock_get.return_value = mock_response
            
            with self.assertRaisesRegex(FootballAPIError, "Football API is currently unavailable"):
                asyncio.run(service.fetch_fixtures_by_date(date(2024, 6, 1)))
