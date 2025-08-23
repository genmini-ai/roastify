SIMPLE_ROAST_PROMPT = """
Create a funny rap roast based on this LinkedIn profile search result:

Profile Title: {title}
Profile Description: {description}
URL: {url}
Style: {style}

Write a short, clever rap diss track that roasts this person based on their profile. Structure:
- INTRO (4 bars)
- VERSE (16 bars) 
- HOOK (8 bars)
- OUTRO (4 bars)

Guidelines:
- Extract and use their name from the title
- Make fun of their job title, company buzzwords, and corporate speak
- Reference specific things from their description
- Keep it playful and funny, not mean-spirited
- Use AABB rhyme scheme (couplets)
- Target BPM: 90

Style guidance:
- "aggressive": More direct, harder hitting
- "playful": Light-hearted, silly
- "witty": Clever wordplay, intellectual humor

Return ONLY valid JSON in this format:
{{
  "intro": "4 bars of intro lyrics",
  "verses": ["16 bars of verse lyrics"],
  "hook": "8 bars of hook/chorus lyrics", 
  "outro": "4 bars of outro lyrics",
  "rhyme_scheme": "AABB",
  "bpm": 90,
  "style": "{style}",
  "wordplay_rating": 0.8,
  "full_lyrics": "Complete formatted lyrics with [INTRO], [VERSE], [HOOK], [OUTRO] sections"
}}
"""

LYRICS_GENERATION_PROMPT = """
You are a professional rap lyricist creating a personalized diss track. Write clever, witty bars that roast this person based on their profile.

TARGET INFO:
Name: {name}
Roast Angles: {roast_angles}
Personality Traits: {personality_traits}
Buzzwords: {buzzwords}
Style: {style}

REQUIREMENTS:
1. Structure: Intro (4 bars) → Verse 1 (16 bars) → Hook (8 bars) → Verse 2 (16 bars) → Outro (4 bars)
2. Rhyme scheme: AABB (couplets) for easy flow
3. BPM: 90 (moderate rap tempo)
4. Style: {style} - adjust aggression level accordingly
5. Use their NAME frequently (at least once per verse)
6. Include specific ROAST ANGLES and BUZZWORDS
7. Keep it clever and funny, not genuinely mean

RAP WRITING GUIDELINES:
- Use internal rhymes and wordplay
- Reference their industry/profession
- Make fun of buzzwords and corporate speak
- Include relatable observations
- Build to a climactic roast in verse 2
- End with a memorable punchline

EXAMPLE STRUCTURE:

[INTRO]
Yo, check it, we got [NAME] in the building
Corporate buzzword champion, always business dealing
Time to break down this LinkedIn legend
Four bars to set the scene, let the roast begin

[VERSE 1 - 16 bars]
[NAME] walking in thinking they run the game
Posted 'thought leadership' but it's all the same
Talking 'bout disruption while you follow the crowd
'Synergy' and 'innovation' - yeah you say it proud
...continuing for 16 bars total

[HOOK - 8 bars]
[NAME], [NAME], what you really about?
All these buzzwords but we got you figured out
Professional headshot with that fake-ass smile
Been studying your profile, roasting you a while

[VERSE 2 - 16 bars]
Let me dive deeper into your career facade
'Passionate about growth' - man, that hits hard
...continuing for 16 bars with stronger roasts

[OUTRO]
[NAME], this was fun, hope you learned today
Next time think twice before you buzzword display

Generate the complete lyrics following this structure. Make it FUNNY and CLEVER, not mean-spirited.
Focus on professional personas and industry humor.

Return in this format:
{
    "intro": "[4 bars]",
    "verse_1": "[16 bars]",
    "hook": "[8 bars]",
    "verse_2": "[16 bars]",
    "outro": "[4 bars]",
    "full_lyrics": "[Complete formatted lyrics with sections labeled]"
}
"""


RHYME_CHECK_PROMPT = """
Review these rap lyrics for rhyme scheme and flow. Fix any issues:

LYRICS:
{lyrics}

Check for:
1. Consistent AABB rhyme scheme (couplets)
2. Proper syllable count for 90 BPM
3. Good internal rhymes
4. Natural word flow
5. Clear pronunciation for TTS

If you find issues, provide corrected versions. If it's good, return the original.
Focus on making it sound natural when spoken aloud.

Return the improved lyrics in the same JSON format.
"""