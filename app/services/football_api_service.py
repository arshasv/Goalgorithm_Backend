import logging
from datetime import date
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class FootballAPIError(Exception):
    pass


class FootballAPIService:
    def __init__(self):
        self.api_key = settings.football_api_key
        self.base_url = settings.football_api_base_url
        self.headers = {
            "x-apisports-key": self.api_key,
        }
        self.allowed_leagues = settings.football_allowed_leagues
        self.timezone = settings.football_timezone

    async def fetch_fixtures_by_date(self, target_date: date) -> list[dict[str, Any]]:
        if not self.api_key:
            raise FootballAPIError("Football API key is not configured.")

        url = f"{self.base_url}/fixtures"
        params = {
            "date": target_date.isoformat(),
            "timezone": self.timezone
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data and data["errors"]:
                    logger.error(f"Football API returned errors: {data['errors']}")
                    errors = data["errors"]
                    error_msg = "Unknown API error"
                    if isinstance(errors, dict):
                        err_values = list(errors.values())
                        error_msg = err_values[0] if err_values else "Unknown API error"
                    elif isinstance(errors, list):
                        error_msg = errors[0] if errors else "Unknown API error"
                    else:
                        error_msg = str(errors)
                    raise FootballAPIError(f"Football API Error: {error_msg}")
                    
                fixtures = data.get("response", [])
                
                normalized = []
                for f in fixtures:
                    league_info = f.get("league", {})
                    league_id = str(league_info.get("id"))
                    
                    if self.allowed_leagues and league_id not in self.allowed_leagues:
                        continue
                        
                    fixture_info = f.get("fixture", {})
                    teams_info = f.get("teams", {})
                    
                    normalized.append({
                        "external_api_id": str(fixture_info.get("id")),
                        "home_team_name": teams_info.get("home", {}).get("name", "Unknown Home"),
                        "away_team_name": teams_info.get("away", {}).get("name", "Unknown Away"),
                        "scheduled_at": fixture_info.get("date"),
                        "competition_name": league_info.get("name"),
                        "status": fixture_info.get("status", {}).get("short"),
                    })
                return normalized

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching fixtures: {e.response.status_code}")
            if e.response.status_code == 401:
                raise FootballAPIError("Invalid Football API Key.") from e
            elif e.response.status_code == 429:
                raise FootballAPIError("Football API quota exceeded.") from e
            elif e.response.status_code >= 500:
                raise FootballAPIError("Football API is currently unavailable.") from e
            raise FootballAPIError(f"Football API HTTP error: {e.response.status_code}") from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching fixtures: {e}")
            raise FootballAPIError("Football API is responding too slowly (Timeout).") from e
        except httpx.RequestError as e:
            logger.error(f"Network error fetching fixtures: {e}")
            raise FootballAPIError("Failed to communicate with Football API (Network Error).") from e
        except FootballAPIError:
            raise
        except Exception as e:
            logger.exception("Unexpected error fetching fixtures")
            raise FootballAPIError("Unexpected error fetching external fixtures") from e

    async def fetch_fixtures_by_ids(self, fixture_ids: list[str]) -> list[dict[str, Any]]:
        if not self.api_key:
            raise FootballAPIError("Football API key is not configured.")
        if not fixture_ids:
            return []
            
        url = f"{self.base_url}/fixtures"
        all_normalized = []
        
        for i in range(0, len(fixture_ids), 20):
            chunk = fixture_ids[i:i+20]
            params = {
                "ids": "-".join(chunk),
                "timezone": self.timezone
            }
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=self.headers, params=params, timeout=10.0)
                    response.raise_for_status()
                    data = response.json()
                    
                    if "errors" in data and data["errors"]:
                        logger.error(f"Football API returned errors: {data['errors']}")
                        errors = data["errors"]
                        error_msg = "Unknown API error"
                        if isinstance(errors, dict):
                            err_values = list(errors.values())
                            error_msg = err_values[0] if err_values else "Unknown API error"
                        elif isinstance(errors, list):
                            error_msg = errors[0] if errors else "Unknown API error"
                        else:
                            error_msg = str(errors)
                        raise FootballAPIError(f"Football API Error: {error_msg}")
                        
                    fixtures = data.get("response", [])
                    
                    for f in fixtures:
                        fixture_info = f.get("fixture", {})
                        teams_info = f.get("teams", {})
                        goals_info = f.get("goals", {})
                        
                        winner_str = "draw"
                        home_goals = goals_info.get("home")
                        away_goals = goals_info.get("away")
                        
                        if home_goals is not None and away_goals is not None:
                            if home_goals > away_goals:
                                winner_str = "home"
                            elif away_goals > home_goals:
                                winner_str = "away"
                                
                        all_normalized.append({
                            "external_api_id": str(fixture_info.get("id")),
                            "status": fixture_info.get("status", {}).get("short"),
                            "home_goals": home_goals,
                            "away_goals": away_goals,
                            "winner": winner_str
                        })
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching fixtures: {e.response.status_code}")
                if e.response.status_code == 401:
                    raise FootballAPIError("Invalid Football API Key.") from e
                elif e.response.status_code == 429:
                    raise FootballAPIError("Football API quota exceeded.") from e
                elif e.response.status_code >= 500:
                    raise FootballAPIError("Football API is currently unavailable.") from e
                raise FootballAPIError(f"Football API HTTP error: {e.response.status_code}") from e
            except httpx.TimeoutException as e:
                logger.error(f"Timeout fetching fixtures: {e}")
                raise FootballAPIError("Football API is responding too slowly (Timeout).") from e
            except httpx.RequestError as e:
                logger.error(f"Network error fetching fixtures: {e}")
                raise FootballAPIError("Failed to communicate with Football API (Network Error).") from e
            except FootballAPIError:
                raise
            except Exception as e:
                logger.error(f"Error fetching fixture chunk: {e}")
                raise FootballAPIError("Unexpected error syncing external results") from e
                
        return all_normalized
