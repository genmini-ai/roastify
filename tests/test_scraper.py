#!/usr/bin/env python3
"""
LinkedIn Profile Scraper Test

Tests LinkedIn profile scraping using Brave Search API.

Usage:
    python test_scraper.py --url https://www.linkedin.com/in/username
    python test_scraper.py --url https://www.linkedin.com/in/username --verbose
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Test imports
from models import ProfileData
from scraper import ProfileScraper
from config import setup_logging

# Test configuration
TEST_OUTPUTS_DIR = Path(__file__).parent / "outputs"


class LinkedInTester:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.scraper = ProfileScraper()
        self.test_outputs = TEST_OUTPUTS_DIR
        self.test_outputs.mkdir(exist_ok=True)
        
        # Setup logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    async def test_linkedin_scraping(self, url: str) -> bool:
        """Test LinkedIn profile scraping with Brave Search API"""
        if not url:
            self.logger.error("❌ No LinkedIn URL provided")
            return False
        
        self.logger.info(f"🔍 Testing LinkedIn scraping for: {url}")
        
        try:
            start_time = time.time()
            
            # Test scraping with new simple method
            search_result = await self.scraper.scrape_profile_simple(url)
            
            duration = time.time() - start_time
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.test_outputs / f"linkedin_scrape_{timestamp}.json"
            
            # Save search result data
            with open(output_file, 'w') as f:
                json.dump({
                    'url': url,
                    'duration': duration,
                    'search_result': search_result,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            # Results
            success = "error" not in search_result and search_result.get("title", "") != "No API Key"
            
            if success:
                self.logger.info(f"✅ LinkedIn scraping completed in {duration:.2f}s")
                self.logger.info(f"📄 Title: {search_result.get('title', 'No title')}")
                self.logger.info(f"📝 Description: {search_result.get('description', 'No description')[:100]}...")
                self.logger.info(f"🏢 Platform: {search_result.get('platform', 'unknown')}")
                
                # Show debug info if available
                full_results = search_result.get("full_results", {})
                if "web" in full_results:
                    web_results = full_results["web"].get("results", [])
                    self.logger.info(f"🔍 Found {len(web_results)} total search results")
            else:
                error_msg = search_result.get("error", "Unknown error")
                self.logger.warning(f"⚠️  Search failed: {error_msg}")
                if "api_key" in error_msg.lower():
                    self.logger.warning("💡 Add BRAVE_API_KEY to your .env file")
                
            self.logger.info(f"📁 Results saved: {output_file}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ LinkedIn scraping failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    async def cleanup(self):
        """Cleanup test resources"""
        if self.scraper:
            await self.scraper.cleanup()


async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test LinkedIn profile scraper with Brave Search API")
    
    parser.add_argument('--url', required=True, help='LinkedIn URL to test scraping with')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    tester = LinkedInTester(verbose=args.verbose)
    
    try:
        success = await tester.test_linkedin_scraping(args.url)
        if success:
            print("\n🎉 Test completed successfully!")
        else:
            print("\n❌ Test failed - check logs above")
            sys.exit(1)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())