#!/usr/bin/env python3
"""
LLM Query Generator for Dynamic Image Search

Generates contextual image queries from LinkedIn profile data for:
- DALL-E image generation (2 prompts)
- Brave search query (1 query)

Input: Simple scraper result (title + description)
Output: 3 targeted image queries
"""

import logging
from typing import Dict, List
import json

from config import settings

logger = logging.getLogger(__name__)


class LLMQueryGenerator:
    def __init__(self):
        # Initialize LLM clients
        self.openai_client = None
        self.anthropic_client = None
        
        if settings.openai_api_key:
            import openai
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        
        if settings.anthropic_api_key:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    
    async def generate_image_queries(self, search_result: dict) -> Dict[str, str]:
        """
        Generate 3 image queries from LinkedIn profile data
        
        Returns:
        {
            'dalle_roast_1': 'humorous DALL-E prompt',
            'dalle_roast_2': 'professional satire DALL-E prompt', 
            'brave_search': 'contextual search query'
        }
        """
        title = search_result.get('title', 'Unknown Professional')
        description = search_result.get('description', 'No description available')
        
        logger.info(f"Generating image queries for: {title}")
        
        try:
            # Try OpenAI first
            if self.openai_client:
                return await self._generate_with_openai(title, description)
            elif self.anthropic_client:
                return await self._generate_with_anthropic(title, description)
            else:
                logger.warning("No LLM available, using fallback queries")
                return self._generate_fallback_queries(title, description)
                
        except Exception as e:
            logger.error(f"LLM query generation failed: {e}")
            return self._generate_fallback_queries(title, description)
    
    async def _generate_with_openai(self, title: str, description: str) -> Dict[str, str]:
        """Generate queries using OpenAI"""
        
        prompt = f"""
Based on this LinkedIn profile, generate 3 image search queries for a humorous roast video:

Profile Title: {title}
Profile Description: {description}

Generate exactly 3 queries in this JSON format:
{{
    "dalle_roast_1": "A creative, humorous DALL-E prompt that visually represents roasting this person's professional image (surreal/artistic style)",
    "dalle_roast_2": "A second DALL-E prompt focusing on their industry/role with comedic elements (cinematic/dramatic style)", 
    "brave_search": "A simple search term for finding relevant professional background images (company name, industry, office type, etc.)"
}}

Make the DALL-E prompts creative but not mean-spirited. Focus on professional humor and industry stereotypes.
Keep the Brave search practical and professional.

Example for a "Data Scientist at Google":
{{
    "dalle_roast_1": "data scientist drowning in endless spreadsheets and charts, surrounded by confused algorithms, digital art style",
    "dalle_roast_2": "Google office with servers on fire while confused engineers hold useless pie charts, cinematic lighting",
    "brave_search": "Google headquarters office interior"
}}

Now generate for the given profile:
"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.8
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            queries = json.loads(result_text)
            return queries
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON, extracting manually")
            return self._extract_queries_from_text(result_text)
    
    async def _generate_with_anthropic(self, title: str, description: str) -> Dict[str, str]:
        """Generate queries using Anthropic"""
        
        prompt = f"""
Based on this LinkedIn profile, generate 3 image search queries for a humorous roast video:

Profile Title: {title}
Profile Description: {description}

Generate exactly 3 queries in this JSON format:
{{
    "dalle_roast_1": "A creative, humorous DALL-E prompt that visually represents roasting this person's professional image",
    "dalle_roast_2": "A second DALL-E prompt focusing on their industry/role with comedic elements", 
    "brave_search": "A simple search term for finding relevant professional background images"
}}

Make the DALL-E prompts creative but not mean-spirited. Focus on professional humor.
"""
        
        message = self.anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = message.content[0].text.strip()
        
        # Parse JSON response
        try:
            queries = json.loads(result_text)
            return queries
        except json.JSONDecodeError:
            return self._extract_queries_from_text(result_text)
    
    def _extract_queries_from_text(self, text: str) -> Dict[str, str]:
        """Extract queries from non-JSON LLM response"""
        # Simple extraction logic
        lines = text.split('\n')
        queries = {
            'dalle_roast_1': 'professional person overwhelmed by work, digital art style',
            'dalle_roast_2': 'corporate office chaos with papers flying, cinematic style',
            'brave_search': 'corporate office professional'
        }
        
        # Try to extract actual content
        for line in lines:
            if 'dalle_roast_1' in line.lower() or 'first' in line.lower():
                if ':' in line:
                    queries['dalle_roast_1'] = line.split(':', 1)[1].strip(' "')
            elif 'dalle_roast_2' in line.lower() or 'second' in line.lower():
                if ':' in line:
                    queries['dalle_roast_2'] = line.split(':', 1)[1].strip(' "')
            elif 'brave' in line.lower() or 'search' in line.lower():
                if ':' in line:
                    queries['brave_search'] = line.split(':', 1)[1].strip(' "')
        
        return queries
    
    def _generate_fallback_queries(self, title: str, description: str) -> Dict[str, str]:
        """Generate basic queries when LLM is not available"""
        
        # Extract key terms
        title_lower = title.lower()
        description_lower = description.lower()
        
        # Determine role and company
        role = "professional"
        company = "office"
        
        if "engineer" in title_lower or "developer" in title_lower:
            role = "software engineer"
        elif "manager" in title_lower:
            role = "manager"
        elif "analyst" in title_lower or "data" in title_lower:
            role = "data analyst"
        elif "designer" in title_lower:
            role = "designer"
        elif "scientist" in title_lower:
            role = "data scientist"
        
        if "microsoft" in title_lower or "microsoft" in description_lower:
            company = "Microsoft office"
        elif "google" in title_lower or "google" in description_lower:
            company = "Google headquarters"
        elif "amazon" in title_lower or "amazon" in description_lower:
            company = "Amazon office"
        elif "meta" in title_lower or "facebook" in title_lower:
            company = "Meta office"
        
        return {
            'dalle_roast_1': f"{role} drowning in endless meetings and spreadsheets, surrounded by confused algorithms, digital art style",
            'dalle_roast_2': f"{company} with computers on fire while confused employees hold useless charts, cinematic lighting, dramatic",
            'brave_search': f"{company} interior workspace"
        }


# Global instance
query_generator = LLMQueryGenerator()


async def generate_image_queries(search_result: dict) -> Dict[str, str]:
    """
    Convenience function to generate image queries
    
    Args:
        search_result: Dict with 'title' and 'description' keys
        
    Returns:
        Dict with 'dalle_roast_1', 'dalle_roast_2', 'brave_search' keys
    """
    return await query_generator.generate_image_queries(search_result)