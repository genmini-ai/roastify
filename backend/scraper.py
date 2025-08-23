import asyncio
import json
import logging
import os
import re
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

from models import ProfileData

# Load environment variables
load_dotenv()

# Minimal config for scraper - no API validation needed
class ScraperSettings:
    brave_api_key: str = os.getenv("BRAVE_API_KEY", "")

# Use minimal settings to avoid API key validation
scraper_settings = ScraperSettings()

logger = logging.getLogger(__name__)


class ProfileScraper:
    def __init__(self):
        pass
        
    async def scrape_profile_simple(self, url: str) -> dict:
        """Simplified scraping that returns search result dict directly"""
        try:
            platform = self._detect_platform(url)
            
            # Use Brave Search API 
            return await self._scrape_with_brave_search_simple(url, platform)
                
        except Exception as e:
            logger.error(f"Profile search failed for {url}: {e}")
            # Return minimal fallback
            return {
                "url": url,
                "platform": platform,
                "title": "Search Failed",
                "description": f"Could not find profile information for: {url}",
                "error": str(e)
            }
    
    async def scrape_profile(self, url: str) -> ProfileData:
        """Main scraping method that returns ProfileData"""
        try:
            platform = self._detect_platform(url)
            profile, _ = await self._scrape_with_brave_search(url, platform)
            return profile
        except Exception as e:
            logger.error(f"Profile scraping failed for {url}: {e}")
            # Return minimal fallback ProfileData
            return ProfileData(
                url=url,
                platform=self._detect_platform(url),
                name="Unknown Profile",
                bio="Profile scraping failed",
                raw_text=f"Failed to scrape profile from {url}: {str(e)}"
            )

    async def scrape_profile_legacy(self, url: str) -> ProfileData:
        """Legacy method for backward compatibility"""
        return await self.scrape_profile(url)
    
    def _detect_platform(self, url: str) -> str:
        """Detect the social media platform from URL"""
        domain = urlparse(url).netloc.lower()
        
        if "linkedin" in domain:
            return "linkedin"
        elif "twitter" in domain or "x.com" in domain:
            return "twitter"
        else:
            return "generic"
    
    async def _scrape_with_brave_search_simple(self, url: str, platform: str) -> dict:
        """Simplified Brave Search that returns just title and description"""
        
        if not scraper_settings.brave_api_key:
            logger.warning("No Brave API key found.")
            return {
                "url": url,
                "platform": platform,
                "title": "No API Key",
                "description": "No Brave API key configured. Please add BRAVE_API_KEY to .env file.",
                "error": "missing_api_key"
            }
        
        try:
            search_query = self._extract_search_query(url, platform)
            
            headers = {
                "X-Subscription-Token": scraper_settings.brave_api_key,
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": search_query, "count": 3},
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise Exception(f"Brave API error: {response.status_code} - {response.text}")
                
                search_results = response.json()
                web_results = search_results.get("web", {}).get("results", [])
                
                if not web_results:
                    return {
                        "url": url,
                        "platform": platform,
                        "title": "No Results Found",
                        "description": "No search results found for this URL",
                        "full_results": search_results
                    }
                
                # Get the top result
                top_result = web_results[0]
                title = top_result.get("title", "No Title")
                description = top_result.get("description", "No Description")
                
                return {
                    "url": url,
                    "platform": platform,
                    "title": title,
                    "description": description,
                    "full_results": search_results  # for debugging
                }
                
        except Exception as e:
            logger.error(f"Brave Search API failed: {e}")
            return {
                "url": url,
                "platform": platform,
                "title": "Search Failed", 
                "description": f"Could not search for profile: {str(e)}",
                "error": str(e)
            }
    
    async def _scrape_with_brave_search(self, url: str, platform: str) -> Tuple[ProfileData, Optional[bytes]]:
        """Use Brave Search API to find profile information"""
        
        if not scraper_settings.brave_api_key:
            logger.warning("No Brave API key found. Using fallback manual profile.")
            return ProfileData(
                url=url,
                platform="manual",
                name="Manual Input Required",
                raw_text=f"No Brave API key configured. Please provide profile information manually for: {url}"
            ), None
        
        try:
            # Extract name from URL for better search
            search_query = self._extract_search_query(url, platform)
            
            
            headers = {
                "X-Subscription-Token": scraper_settings.brave_api_key,
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": search_query, "count": 3},  # Get top 3 results
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise Exception(f"Brave API error: {response.status_code} - {response.text}")
                
                search_results = response.json()
                
                # Return simplified profile with full search results for debugging
                search_results_json = json.dumps(search_results, indent=2)
                pdf_bytes = search_results_json.encode('utf-8')
                
                # Create minimal profile with search results
                profile = ProfileData(
                    url=url,
                    platform=platform,
                    name="Search Results",
                    bio="Brave Search API Results",
                    raw_text=search_results_json
                )
                
                return profile, pdf_bytes
                
        except Exception as e:
            logger.error(f"Brave Search API failed: {e}")
            # Return fallback profile
            return ProfileData(
                url=url,
                platform="manual", 
                name="Search Failed",
                raw_text=f"Could not find profile information via search for: {url}. Error: {str(e)}"
            ), None
    
    def _extract_search_query(self, url: str, platform: str) -> str:
        """Use the original URL as search query"""
        return url
    
    
    async def cleanup(self):
        """Cleanup resources (no-op for API-based scraping)"""
        pass


def create_manual_profile(text: str, name: str = "Manual User") -> ProfileData:
    """Create profile from manual text input"""
    return ProfileData(
        url="manual://input",
        platform="manual",
        name=name,
        raw_text=text
    )