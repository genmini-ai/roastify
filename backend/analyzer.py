import json
import logging
from typing import Optional
import asyncio

import openai
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from models import ProfileData, AnalysisResult
from config import settings
from prompts.profile_analysis import PROFILE_ANALYSIS_PROMPT, ROAST_ANGLES_PROMPT

logger = logging.getLogger(__name__)

# Import Gemini analyzer with fallback
try:
    from gemini_analyzer import GeminiAnalyzer
    GEMINI_AVAILABLE = True
except ImportError as e:
    GEMINI_AVAILABLE = False
    logger.warning(f"Gemini not available: {e}")


class LLMAnalyzer:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_analyzer = None
        
        # Initialize Gemini (preferred for profile analysis)
        if settings.google_api_key and GEMINI_AVAILABLE:
            try:
                self.gemini_analyzer = GeminiAnalyzer(settings.google_api_key)
                logger.info("Gemini analyzer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")
        
        # Initialize OpenAI
        if settings.openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized")
        
        # Initialize Anthropic
        if settings.anthropic_api_key:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            logger.info("Anthropic client initialized")
    
    async def analyze_profile(self, profile: ProfileData, pdf_bytes: Optional[bytes] = None) -> AnalysisResult:
        """Main entry point for profile analysis with optional PDF"""
        logger.info(f"Analyzing profile for {profile.name} (PDF: {pdf_bytes is not None})")
        
        try:
            # Try Gemini first if we have PDF (best for document understanding)
            if pdf_bytes and self.gemini_analyzer:
                try:
                    logger.info("Using Gemini for PDF-based analysis")
                    analysis = await self.gemini_analyzer.analyze_profile_pdf(pdf_bytes, profile.name)
                    return analysis
                except Exception as e:
                    logger.warning(f"Gemini analysis failed: {e}")
            
            # Fallback to text-based analysis with OpenAI/Anthropic
            analysis = await self._analyze_with_openai(profile)
            if not analysis:
                analysis = await self._analyze_with_anthropic(profile)
            
            if not analysis:
                # Ultimate fallback - create basic analysis
                return self._create_fallback_analysis(profile)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._create_fallback_analysis(profile)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _analyze_with_openai(self, profile: ProfileData) -> Optional[AnalysisResult]:
        """Analyze profile using OpenAI GPT"""
        if not self.openai_client:
            return None
        
        try:
            prompt = PROFILE_ANALYSIS_PROMPT.format(
                name=profile.name,
                platform=profile.platform,
                bio=profile.bio or "No bio available",
                work_history="\n".join(profile.work_history) if profile.work_history else "No work history",
                education="\n".join(profile.education) if profile.education else "No education info",
                raw_text=(profile.raw_text or "")[:2000]  # Limit token usage
            )
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert personality analyst and comedian. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            if not content:
                return None
            
            # Parse JSON response
            analysis_data = json.loads(content)
            
            return AnalysisResult(
                personality_traits=analysis_data.get("personality_traits", []),
                roast_angles=analysis_data.get("roast_angles", []),
                buzzwords=analysis_data.get("buzzwords", []),
                key_achievements=analysis_data.get("key_achievements", []),
                insecurity_points=analysis_data.get("insecurity_points", []),
                humor_style=analysis_data.get("humor_style", "playful"),
                confidence_score=analysis_data.get("confidence_score", 0.5),
                analysis_summary=analysis_data.get("analysis_summary", "")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            raise
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _analyze_with_anthropic(self, profile: ProfileData) -> Optional[AnalysisResult]:
        """Analyze profile using Anthropic Claude"""
        if not self.anthropic_client:
            return None
        
        try:
            prompt = PROFILE_ANALYSIS_PROMPT.format(
                name=profile.name,
                platform=profile.platform,
                bio=profile.bio or "No bio available",
                work_history="\n".join(profile.work_history) if profile.work_history else "No work history",
                education="\n".join(profile.education) if profile.education else "No education info",
                raw_text=(profile.raw_text or "")[:2000]
            )
            
            message = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            content = message.content[0].text
            analysis_data = json.loads(content)
            
            return AnalysisResult(
                personality_traits=analysis_data.get("personality_traits", []),
                roast_angles=analysis_data.get("roast_angles", []),
                buzzwords=analysis_data.get("buzzwords", []),
                key_achievements=analysis_data.get("key_achievements", []),
                insecurity_points=analysis_data.get("insecurity_points", []),
                humor_style=analysis_data.get("humor_style", "playful"),
                confidence_score=analysis_data.get("confidence_score", 0.5),
                analysis_summary=analysis_data.get("analysis_summary", "")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            raise
    
    def _create_fallback_analysis(self, profile: ProfileData) -> AnalysisResult:
        """Create basic analysis when AI fails"""
        logger.info("Using fallback analysis")
        
        # Extract basic info from profile
        traits = ["professional", "active on social media"]
        angles = ["posts a lot on LinkedIn", "probably uses buzzwords"]
        buzzwords = ["synergy", "innovation", "passionate", "growth mindset"]
        
        if profile.platform == "linkedin":
            traits.append("career-focused")
            angles.append("has a professional headshot")
            buzzwords.extend(["thought leadership", "networking", "disruption"])
        
        if profile.work_history:
            traits.append("experienced professional")
            angles.append("lists every job they've ever had")
        
        return AnalysisResult(
            personality_traits=traits,
            roast_angles=angles,
            buzzwords=buzzwords,
            key_achievements=["Being on LinkedIn"],
            insecurity_points=["Probably takes themselves too seriously"],
            humor_style="playful",
            confidence_score=0.6,
            analysis_summary=f"{profile.name} seems like a typical social media professional with lots of buzzwords to roast."
        )
    
    async def generate_roast_angles(self, analysis: AnalysisResult) -> list[str]:
        """Generate specific roast angles for lyrics"""
        try:
            if self.openai_client:
                return await self._generate_angles_openai(analysis)
            elif self.anthropic_client:
                return await self._generate_angles_anthropic(analysis)
            else:
                return analysis.roast_angles  # Use existing angles
                
        except Exception as e:
            logger.error(f"Failed to generate roast angles: {e}")
            return analysis.roast_angles
    
    async def _generate_angles_openai(self, analysis: AnalysisResult) -> list[str]:
        """Generate angles using OpenAI"""
        prompt = ROAST_ANGLES_PROMPT.format(analysis=analysis.model_dump())
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Generate specific, funny roast angles for rap lyrics."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        if not content:
            return analysis.roast_angles
        
        # Parse numbered list
        angles = []
        for line in content.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering and clean up
                angle = line.split('.', 1)[-1].strip()
                angle = angle.lstrip('- ').strip()
                if angle:
                    angles.append(angle)
        
        return angles if angles else analysis.roast_angles
    
    async def _generate_angles_anthropic(self, analysis: AnalysisResult) -> list[str]:
        """Generate angles using Claude"""
        prompt = ROAST_ANGLES_PROMPT.format(analysis=analysis.model_dump())
        
        message = await self.anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            temperature=0.8,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        content = message.content[0].text
        
        # Parse numbered list
        angles = []
        for line in content.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                angle = line.split('.', 1)[-1].strip()
                angle = angle.lstrip('- ').strip()
                if angle:
                    angles.append(angle)
        
        return angles if angles else analysis.roast_angles