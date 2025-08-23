import json
import logging
from typing import Optional
import asyncio

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from models import AnalysisResult
from config import settings

logger = logging.getLogger(__name__)


class GeminiAnalyzer:
    """Gemini-based profile analyzer using PDF input"""
    
    def __init__(self, api_key: str):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai package not installed")
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = settings.gemini_model
        
        logger.info(f"Initialized GeminiAnalyzer with model: {self.model_id}")
    
    async def analyze_profile_pdf(self, pdf_bytes: bytes, name: str) -> AnalysisResult:
        """Analyze profile PDF using Gemini"""
        logger.info(f"Analyzing profile PDF for {name} using Gemini")
        
        try:
            prompt = self._create_analysis_prompt()
            
            # Create content with PDF and prompt
            response = await self._call_gemini(pdf_bytes, prompt)
            
            # Parse response
            analysis = self._parse_gemini_response(response, name)
            
            logger.info(f"Gemini analysis completed: {len(analysis.roast_angles)} roast angles found")
            return analysis
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            # Return fallback analysis
            return self._create_fallback_analysis(name)
    
    async def _call_gemini(self, pdf_bytes: bytes, prompt: str) -> str:
        """Call Gemini API with PDF and prompt"""
        try:
            # Prepare content parts
            content_parts = [
                types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type="application/pdf"
                ),
                types.Part.from_text(prompt)
            ]
            
            # Create content
            content = types.Content(
                role="user",
                parts=content_parts
            )
            
            # Generate response
            response = await self.client.models.generate_content(
                model=self.model_id,
                contents=[content],
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    candidate_count=1,
                    max_output_tokens=2000,
                    system_instruction="You are a witty comedy writer analyzing social media profiles to create humorous roasts. Be clever and observant, not mean-spirited."
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _create_analysis_prompt(self) -> str:
        """Create analysis prompt for Gemini"""
        return """
        Analyze this social media profile PDF and extract information for creating a humorous rap roast.
        
        Focus on these areas:
        
        1. **Personality Traits** (5 traits that stand out):
           - Professional personas they project
           - Communication style
           - Values they emphasize
           - Personal quirks visible in posts
        
        2. **Roast Angles** (6-8 specific, funny observations):
           - Contradictions in their profile (says X but does Y)
           - Overly serious or pretentious elements
           - Industry stereotypes they embody perfectly
           - Humble brags disguised as modesty
           - Buzzword overuse or corporate speak
           - Career/life choices that are amusingly predictable
        
        3. **Buzzwords** (8-10 words they overuse):
           - Corporate jargon
           - Industry-specific terms
           - Trendy phrases
           - Motivational speak
        
        4. **Key Achievements** (3-4 things they're most proud of):
           - Career milestones they highlight
           - Education credentials they mention
           - Awards or recognition they showcase
           - Status symbols they display
        
        5. **Insecurity Points** (2-4 areas they might be defensive about):
           - Things they're trying too hard to prove
           - Gaps or weaknesses they're compensating for
           - Areas where they seem less confident
        
        6. **Humor Style Recommendation**:
           - "aggressive": For overly confident/arrogant profiles
           - "playful": For likeable people with amusing quirks  
           - "witty": For intelligent but pretentious profiles
        
        **IMPORTANT**: Be clever and observant, not cruel. Focus on professional personas and funny contradictions rather than personal attacks.
        
        Return your analysis as valid JSON with exactly this structure:
        ```json
        {
            "personality_traits": ["specific trait 1", "specific trait 2", "..."],
            "roast_angles": ["specific observation 1", "specific observation 2", "..."],
            "buzzwords": ["word1", "word2", "phrase", "..."],
            "key_achievements": ["achievement 1", "achievement 2", "..."],
            "insecurity_points": ["point 1", "point 2", "..."],
            "humor_style": "playful|aggressive|witty",
            "confidence_score": 0.7,
            "analysis_summary": "2-3 sentence summary of why this person is roastable and what makes them funny"
        }
        ```
        
        Make sure each field contains specific, actionable content that can be used to write personalized rap lyrics.
        """
    
    def _parse_gemini_response(self, response_text: str, name: str) -> AnalysisResult:
        """Parse Gemini JSON response into AnalysisResult"""
        try:
            # Clean response text (remove markdown formatting if present)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # Parse JSON
            analysis_data = json.loads(cleaned_text)
            
            return AnalysisResult(
                personality_traits=analysis_data.get("personality_traits", []),
                roast_angles=analysis_data.get("roast_angles", []),
                buzzwords=analysis_data.get("buzzwords", []),
                key_achievements=analysis_data.get("key_achievements", []),
                insecurity_points=analysis_data.get("insecurity_points", []),
                humor_style=analysis_data.get("humor_style", "playful"),
                confidence_score=float(analysis_data.get("confidence_score", 0.7)),
                analysis_summary=analysis_data.get("analysis_summary", f"Analysis of {name} completed")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}...")
            
            # Try to extract information from non-JSON response
            return self._extract_from_text_response(response_text, name)
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return self._create_fallback_analysis(name)
    
    def _extract_from_text_response(self, response_text: str, name: str) -> AnalysisResult:
        """Extract analysis from non-JSON text response"""
        logger.info("Attempting to extract analysis from text response")
        
        # Simple text parsing as fallback
        traits = []
        angles = []
        buzzwords = []
        
        lines = response_text.lower().split('\n')
        for line in lines:
            if 'trait' in line or 'personality' in line:
                if any(word in line for word in ['professional', 'corporate', 'ambitious', 'networker']):
                    traits.append(line.strip())
            elif 'roast' in line or 'angle' in line:
                if len(line.strip()) > 10:
                    angles.append(line.strip())
            elif any(word in line for word in ['synergy', 'innovation', 'passionate', 'thought leader']):
                buzzwords.extend(line.split())
        
        # Clean and limit results
        traits = [t for t in traits[:5] if t]
        angles = [a for a in angles[:6] if a]
        buzzwords = list(set([w for w in buzzwords if len(w) > 3]))[:8]
        
        return AnalysisResult(
            personality_traits=traits or ["professional", "social media active"],
            roast_angles=angles or ["posts frequently on LinkedIn", "uses corporate buzzwords"],
            buzzwords=buzzwords or ["synergy", "innovation", "passionate", "growth"],
            key_achievements=["Being on social media"],
            insecurity_points=["Trying too hard to sound professional"],
            humor_style="playful",
            confidence_score=0.6,
            analysis_summary=f"Text-based analysis of {name} - limited extraction from non-JSON response"
        )
    
    def _create_fallback_analysis(self, name: str) -> AnalysisResult:
        """Create basic fallback analysis when Gemini fails"""
        logger.info("Creating fallback analysis for Gemini failure")
        
        return AnalysisResult(
            personality_traits=[
                "active on social media",
                "professional networker", 
                "buzzword enthusiast",
                "thought leadership aspirant"
            ],
            roast_angles=[
                "posts motivational quotes but complains about Mondays",
                "claims to 'disrupt' industries that haven't changed in decades",
                "has 'entrepreneur' in bio but works a regular job",
                "uses 'passionate about synergy' unironically",
                "shares articles about productivity while scrolling social media",
                "calls meetings to discuss having fewer meetings"
            ],
            buzzwords=[
                "synergy", "innovation", "passionate", "disruptive",
                "thought leadership", "growth mindset", "optimization",
                "paradigm shift", "best practices", "circle back"
            ],
            key_achievements=[
                "Has a LinkedIn profile",
                "Completed online courses",
                "Attended networking events"
            ],
            insecurity_points=[
                "Trying too hard to sound important",
                "Overuses business jargon to seem smart"
            ],
            humor_style="playful",
            confidence_score=0.7,
            analysis_summary=f"Fallback analysis for {name} - using common professional stereotypes for roasting material"
        )


async def test_gemini_analyzer():
    """Test function for Gemini analyzer"""
    if not GEMINI_AVAILABLE:
        print("❌ google-genai not available")
        return
    
    if not settings.google_api_key:
        print("❌ GOOGLE_API_KEY not configured")
        return
    
    try:
        analyzer = GeminiAnalyzer(settings.google_api_key)
        
        # Test with sample PDF (would need actual PDF bytes)
        print("✅ GeminiAnalyzer initialized successfully")
        print(f"Using model: {analyzer.model_id}")
        
    except Exception as e:
        print(f"❌ GeminiAnalyzer test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_gemini_analyzer())