import json
import logging
import re
from typing import Optional, List

import openai
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from models import AnalysisResult, LyricsData, ProfileData
from config import settings
from prompts.lyrics_generation import LYRICS_GENERATION_PROMPT, RHYME_CHECK_PROMPT, SIMPLE_ROAST_PROMPT

logger = logging.getLogger(__name__)


class LyricsGenerator:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        if settings.openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        if settings.anthropic_api_key:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    async def generate_lyrics_from_search(
        self, 
        search_result: dict,
        style: str = "playful"
    ) -> LyricsData:
        """Simplified lyrics generation directly from search results"""
        logger.info(f"Generating lyrics from search result: {search_result.get('title', 'Unknown')}")
        
        try:
            # Generate lyrics directly from search result
            lyrics = await self._generate_simple_lyrics(search_result, style)
            
            if not lyrics:
                return self._create_simple_fallback_lyrics(search_result, style)
            
            return lyrics
            
        except Exception as e:
            logger.error(f"Simple lyrics generation failed: {e}")
            return self._create_simple_fallback_lyrics(search_result, style)
    
    async def generate_lyrics(
        self, 
        profile: ProfileData, 
        analysis: AnalysisResult,
        style: str = "playful"
    ) -> LyricsData:
        """Main entry point for lyrics generation"""
        logger.info(f"Generating lyrics for {profile.name} in {style} style")
        
        try:
            # Generate initial lyrics
            lyrics = await self._generate_raw_lyrics(profile, analysis, style)
            
            if not lyrics:
                return self._create_fallback_lyrics(profile, analysis, style)
            
            # Refine rhyme scheme if needed
            lyrics = await self._refine_lyrics(lyrics)
            
            return lyrics
            
        except Exception as e:
            logger.error(f"Lyrics generation failed: {e}")
            return self._create_fallback_lyrics(profile, analysis, style)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _generate_simple_lyrics(self, search_result: dict, style: str) -> Optional[LyricsData]:
        """Generate lyrics directly from search results"""
        
        # Try OpenAI first
        if self.openai_client:
            try:
                return await self._generate_simple_with_openai(search_result, style)
            except Exception as e:
                logger.warning(f"OpenAI failed, trying Anthropic: {e}")
        
        # Fallback to Anthropic
        if self.anthropic_client:
            return await self._generate_simple_with_anthropic(search_result, style)
        
        return None
    
    async def _generate_simple_with_openai(self, search_result: dict, style: str) -> Optional[LyricsData]:
        """Generate simple lyrics using OpenAI GPT"""
        
        prompt = SIMPLE_ROAST_PROMPT.format(
            title=search_result.get("title", "Unknown"),
            description=search_result.get("description", "No description"),
            url=search_result.get("url", ""),
            style=style
        )
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional rap lyricist. Write clever, funny rap lyrics. Return valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        if not content:
            return None
        
        # Parse JSON response
        lyrics_data = json.loads(content)
        
        return LyricsData(
            intro=lyrics_data.get("intro", ""),
            verses=lyrics_data.get("verses", [""]),
            hook=lyrics_data.get("hook", ""),
            outro=lyrics_data.get("outro", ""),
            rhyme_scheme=lyrics_data.get("rhyme_scheme", "AABB"),
            bpm=lyrics_data.get("bpm", 90),
            style=style,
            wordplay_rating=lyrics_data.get("wordplay_rating", 0.7),
            full_lyrics=lyrics_data.get("full_lyrics", ""),
            timing_marks=[]
        )
    
    async def _generate_simple_with_anthropic(self, search_result: dict, style: str) -> Optional[LyricsData]:
        """Generate simple lyrics using Anthropic Claude"""
        
        prompt = SIMPLE_ROAST_PROMPT.format(
            title=search_result.get("title", "Unknown"),
            description=search_result.get("description", "No description"),
            url=search_result.get("url", ""),
            style=style
        )
        
        response = await self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            temperature=0.8,
            messages=[
                {
                    "role": "user",
                    "content": f"You are a professional rap lyricist. Write clever, funny rap lyrics. Return valid JSON only.\n\n{prompt}"
                }
            ]
        )
        
        content = response.content[0].text if response.content else None
        if not content:
            return None
        
        # Parse JSON response
        lyrics_data = json.loads(content)
        
        return LyricsData(
            intro=lyrics_data.get("intro", ""),
            verses=lyrics_data.get("verses", [""]),
            hook=lyrics_data.get("hook", ""),
            outro=lyrics_data.get("outro", ""),
            rhyme_scheme=lyrics_data.get("rhyme_scheme", "AABB"),
            bpm=lyrics_data.get("bpm", 90),
            style=style,
            wordplay_rating=lyrics_data.get("wordplay_rating", 0.7),
            full_lyrics=lyrics_data.get("full_lyrics", ""),
            timing_marks=[]
        )
    
    def _create_simple_fallback_lyrics(self, search_result: dict, style: str) -> LyricsData:
        """Create fallback lyrics when AI generation fails"""
        name = search_result.get("title", "Unknown Person").split("-")[0].split("|")[0].strip()
        
        intro = f"Yo, check it, we got {name} in the building\nTime to roast this LinkedIn legend\nGot their profile right here on the screen\nLet's break down what this really means"
        
        verse = f"{name} posted up thinking they run the game\nBut their profile's got us laughing all the same\nTalking bout synergy and innovation\nBuzzword champion of the corporation\nNetworking events and thought leadership\nCorporate speak that makes us want to quit\nLinkedIn influencer with the fake inspiration\nTime to bring you back down to your station\nYour bio reads like a robot wrote it\nProfessional headshot but we're not sold on it\nAnother day another humble brag post\nThat's why you're getting served this verbal roast"
        
        hook = f"{name}, {name}, what you really about?\nAll these buzzwords but we got you figured out\nProfessional network but you're just like the rest\nTime to put your corporate speak to the test"
        
        outro = f"That's a wrap on {name}'s roasting session\nHope you learned a valuable lesson\nKeep it real, drop the corporate facade\nThis has been your friendly roast squad"
        
        full_lyrics = f"[INTRO]\n{intro}\n\n[VERSE]\n{verse}\n\n[HOOK]\n{hook}\n\n[OUTRO]\n{outro}"
        
        return LyricsData(
            intro=intro,
            verses=[verse],
            hook=hook,
            outro=outro,
            rhyme_scheme="AABB",
            bpm=90,
            style=style,
            wordplay_rating=0.6,
            full_lyrics=full_lyrics,
            timing_marks=[]
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _generate_raw_lyrics(
        self, 
        profile: ProfileData, 
        analysis: AnalysisResult,
        style: str
    ) -> Optional[LyricsData]:
        """Generate lyrics using AI"""
        
        # Try OpenAI first
        if self.openai_client:
            try:
                return await self._generate_with_openai(profile, analysis, style)
            except Exception as e:
                logger.warning(f"OpenAI failed, trying Anthropic: {e}")
        
        # Fallback to Anthropic
        if self.anthropic_client:
            return await self._generate_with_anthropic(profile, analysis, style)
        
        return None
    
    async def _generate_with_openai(
        self, 
        profile: ProfileData, 
        analysis: AnalysisResult,
        style: str
    ) -> Optional[LyricsData]:
        """Generate lyrics using OpenAI GPT"""
        
        prompt = LYRICS_GENERATION_PROMPT.format(
            name=profile.name,
            roast_angles=", ".join(analysis.roast_angles[:6]),  # Limit for token usage
            personality_traits=", ".join(analysis.personality_traits),
            buzzwords=", ".join(analysis.buzzwords[:8]),
            style=style
        )
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional rap lyricist. Write clever, funny rap lyrics. Return valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        if not content:
            return None
        
        try:
            lyrics_data = json.loads(content)
            return self._parse_lyrics_response(lyrics_data, style, profile.name)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI lyrics JSON: {e}")
            return None
    
    async def _generate_with_anthropic(
        self, 
        profile: ProfileData, 
        analysis: AnalysisResult,
        style: str
    ) -> Optional[LyricsData]:
        """Generate lyrics using Anthropic Claude"""
        
        prompt = LYRICS_GENERATION_PROMPT.format(
            name=profile.name,
            roast_angles=", ".join(analysis.roast_angles[:6]),
            personality_traits=", ".join(analysis.personality_traits),
            buzzwords=", ".join(analysis.buzzwords[:8]),
            style=style
        )
        
        message = await self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            temperature=0.8,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        content = message.content[0].text
        
        try:
            lyrics_data = json.loads(content)
            return self._parse_lyrics_response(lyrics_data, style, profile.name)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude lyrics JSON: {e}")
            return None
    
    def _parse_lyrics_response(self, lyrics_data: dict, style: str, name: str) -> LyricsData:
        """Parse AI response into LyricsData model"""
        
        intro = lyrics_data.get("intro", "")
        verses = [lyrics_data.get("verse_1", ""), lyrics_data.get("verse_2", "")]
        hook = lyrics_data.get("hook", "")
        outro = lyrics_data.get("outro", "")
        full_lyrics = lyrics_data.get("full_lyrics", "")
        
        # If full_lyrics not provided, construct it
        if not full_lyrics:
            full_lyrics = self._format_complete_lyrics(intro, verses, hook, outro)
        
        # Calculate basic metrics
        wordplay_rating = self._calculate_wordplay_rating(full_lyrics)
        
        return LyricsData(
            intro=intro,
            verses=[v for v in verses if v],  # Filter empty verses
            hook=hook,
            outro=outro,
            rhyme_scheme="AABB",
            bpm=90,
            style=style,
            wordplay_rating=wordplay_rating,
            full_lyrics=full_lyrics,
            timing_marks=self._generate_timing_marks(full_lyrics)
        )
    
    def _format_complete_lyrics(self, intro: str, verses: List[str], hook: str, outro: str) -> str:
        """Format complete lyrics with section labels"""
        formatted = []
        
        if intro:
            formatted.append("[INTRO]")
            formatted.append(intro)
            formatted.append("")
        
        if verses and len(verses) > 0 and verses[0]:
            formatted.append("[VERSE 1]")
            formatted.append(verses[0])
            formatted.append("")
        
        if hook:
            formatted.append("[HOOK]")
            formatted.append(hook)
            formatted.append("")
        
        if verses and len(verses) > 1 and verses[1]:
            formatted.append("[VERSE 2]")
            formatted.append(verses[1])
            formatted.append("")
        
        if hook:  # Repeat hook
            formatted.append("[HOOK]")
            formatted.append(hook)
            formatted.append("")
        
        if outro:
            formatted.append("[OUTRO]")
            formatted.append(outro)
        
        return "\n".join(formatted)
    
    def _calculate_wordplay_rating(self, lyrics: str) -> float:
        """Calculate wordplay quality (basic heuristic)"""
        lines = [line.strip() for line in lyrics.split('\n') if line.strip() and not line.startswith('[')]
        
        if not lines:
            return 0.0
        
        # Count rhymes, alliteration, puns
        score = 0.0
        total_lines = len(lines)
        
        for i in range(0, len(lines), 2):  # Check couplets
            if i + 1 < len(lines):
                line1, line2 = lines[i], lines[i + 1]
                
                # Check end rhymes
                if self._lines_rhyme(line1, line2):
                    score += 0.2
                
                # Check internal rhymes
                if self._has_internal_rhymes(line1) or self._has_internal_rhymes(line2):
                    score += 0.1
                
                # Check alliteration
                if self._has_alliteration(line1) or self._has_alliteration(line2):
                    score += 0.05
        
        return min(score / total_lines * 10, 1.0)  # Normalize to 0-1
    
    def _lines_rhyme(self, line1: str, line2: str) -> bool:
        """Basic rhyme detection"""
        # Get last word of each line
        words1 = re.findall(r'\b\w+\b', line1.lower())
        words2 = re.findall(r'\b\w+\b', line2.lower())
        
        if not words1 or not words2:
            return False
        
        last_word1, last_word2 = words1[-1], words2[-1]
        
        # Simple suffix matching
        for suffix_len in [2, 3, 4]:
            if len(last_word1) >= suffix_len and len(last_word2) >= suffix_len:
                if last_word1[-suffix_len:] == last_word2[-suffix_len:]:
                    return True
        
        return False
    
    def _has_internal_rhymes(self, line: str) -> bool:
        """Check for internal rhymes"""
        words = re.findall(r'\b\w+\b', line.lower())
        
        for i, word1 in enumerate(words):
            for word2 in words[i + 1:]:
                if len(word1) >= 3 and len(word2) >= 3:
                    if word1[-2:] == word2[-2:] or word1[-3:] == word2[-3:]:
                        return True
        return False
    
    def _has_alliteration(self, line: str) -> bool:
        """Check for alliteration"""
        words = re.findall(r'\b\w+\b', line.lower())
        
        for i in range(len(words) - 1):
            if words[i][0] == words[i + 1][0]:
                return True
        return False
    
    def _generate_timing_marks(self, lyrics: str) -> List[dict]:
        """Generate basic timing marks for audio sync"""
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        
        timing_marks = []
        current_time = 0.0
        
        for line in lines:
            if line.startswith('[') and line.endswith(']'):
                # Section marker
                timing_marks.append({
                    "time": current_time,
                    "type": "section",
                    "text": line,
                    "duration": 0.5
                })
                current_time += 0.5
            else:
                # Lyrics line - estimate based on word count
                words = len(line.split())
                duration = max(words * 0.4, 2.0)  # ~0.4s per word, min 2s
                
                timing_marks.append({
                    "time": current_time,
                    "type": "lyric",
                    "text": line,
                    "duration": duration
                })
                current_time += duration
        
        return timing_marks
    
    async def _refine_lyrics(self, lyrics: LyricsData) -> LyricsData:
        """Refine lyrics for better rhyme scheme and flow"""
        try:
            if not self.openai_client:
                return lyrics
            
            prompt = RHYME_CHECK_PROMPT.format(lyrics=lyrics.full_lyrics)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Fix rap lyrics for better rhyme and flow. Return JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            if not content:
                return lyrics
            
            refined_data = json.loads(content)
            
            # Update lyrics with refined version
            lyrics.intro = refined_data.get("intro", lyrics.intro)
            lyrics.verses = [refined_data.get("verse_1", ""), refined_data.get("verse_2", "")]
            lyrics.hook = refined_data.get("hook", lyrics.hook)
            lyrics.outro = refined_data.get("outro", lyrics.outro)
            lyrics.full_lyrics = refined_data.get("full_lyrics", lyrics.full_lyrics)
            
            return lyrics
            
        except Exception as e:
            logger.warning(f"Lyrics refinement failed, using original: {e}")
            return lyrics
    
    def _create_fallback_lyrics(
        self, 
        profile: ProfileData, 
        analysis: AnalysisResult,
        style: str
    ) -> LyricsData:
        """Create basic fallback lyrics when AI fails"""
        logger.info("Using fallback lyrics generation")
        
        name = profile.name
        platform = profile.platform.title()
        
        intro = f"Yo, check it, we got {name} in the building\n{platform} champion, always business dealing\nTime to break down this social media legend\nFour bars to start, let the roast session begin"
        
        verse1 = f"{name} walking in thinking they run the game\nPosted 'thought leadership' but it's all the same\nTalking 'bout innovation while you follow the crowd\n'Synergy' and 'disruption' - yeah you say it proud\n\nProfessional headshot with that networking smile\nConnection requests flooding, been at it a while\nBuzzword champion, got the corporate speak down\nBut when it comes to real talk, you just fool around\n\nLinkedIn legend with the humble brag posts\n'Grateful for the opportunity' - that's what you boast most\n{name}, {name}, we see right through the act\nTime to face the music, that's a lyrical fact"
        
        hook = f"{name}, {name}, what you really about?\nAll these buzzwords but we got you figured out\nProfessional facade with that fake-ass smile\nBeen studying your {platform}, roasting you a while\n\n{name}, {name}, time to face the truth\nThis roast session gonna show your social media proof"
        
        verse2 = f"Let me dive deeper into your career display\n'Passionate about growth' - that's what you always say\nBut scrolling through your feed, it's the same old content\n{name}, your 'thought leadership' needs some real commitment\n\nEvery post sounds like you swallowed a business book\nTrying way too hard for that professional look\nWe get it, you work hard, you're climbing that ladder\nBut this roast right here just made your resume sadder\n\nNo hate though {name}, we're just having fun\nSocial media roasting, now this session is done"
        
        outro = f"{name}, this was fun, hope you learned today\nNext time think twice 'bout that buzzword display\nPeace out from the roast, keep posting your grind\nJust remember this track when you're wasting our time"
        
        full_lyrics = self._format_complete_lyrics(intro, [verse1, verse2], hook, outro)
        
        return LyricsData(
            intro=intro,
            verses=[verse1, verse2],
            hook=hook,
            outro=outro,
            rhyme_scheme="AABB",
            bpm=90,
            style=style,
            wordplay_rating=0.6,
            full_lyrics=full_lyrics,
            timing_marks=self._generate_timing_marks(full_lyrics)
        )