PROFILE_ANALYSIS_PROMPT = """
You are an expert personality analyst and comedian tasked with analyzing a social media profile to identify roast-worthy content.

PROFILE DATA:
Name: {name}
Platform: {platform}
Bio: {bio}
Work History: {work_history}
Education: {education}
Raw Content: {raw_text}

Your task is to analyze this profile and identify:

1. PERSONALITY TRAITS (3-5 traits):
   - Professional personas they project
   - Personal quirks or habits
   - Communication style
   - Values they emphasize

2. ROAST ANGLES (4-6 angles):
   - Funny contradictions in their profile
   - Overly serious or pretentious elements
   - Industry-specific stereotypes they fit
   - Humble brags or self-promotion
   - Buzzword overuse
   - Career/life choices that are roast-worthy

3. BUZZWORDS (5-10 words):
   - Corporate speak they use
   - Industry jargon
   - Overused phrases
   - Trendy terms they abuse

4. KEY ACHIEVEMENTS (2-4 items):
   - Things they're most proud of
   - Accomplishments they highlight
   - Status symbols they display

5. INSECURITY POINTS (2-4 items):
   - Things they might be defensive about
   - Areas where they're trying too hard
   - Gaps or weaknesses in their profile

6. HUMOR STYLE RECOMMENDATION:
   - aggressive: For people who seem overly confident/arrogant
   - playful: For people who seem likeable but have funny quirks
   - witty: For people who are intelligent but pretentious

Provide your analysis in this JSON format:
{
    "personality_traits": ["trait1", "trait2", ...],
    "roast_angles": ["angle1", "angle2", ...],
    "buzzwords": ["word1", "word2", ...],
    "key_achievements": ["achievement1", "achievement2", ...],
    "insecurity_points": ["point1", "point2", ...],
    "humor_style": "playful|aggressive|witty",
    "confidence_score": 0.7,
    "analysis_summary": "2-3 sentence summary of this person's roast-ability"
}

Remember: The goal is to create funny, clever content that pokes fun without being truly mean-spirited. Focus on professional personas, buzzwords, and funny contradictions rather than personal attacks.
"""


ROAST_ANGLES_PROMPT = """
Based on this profile analysis, generate specific roast angles for rap lyrics:

ANALYSIS:
{analysis}

Generate 6-8 specific roast angles that can be turned into rap bars. Each should be:
- Funny but not cruel
- Specific to this person
- Relatable to the audience
- Suitable for rap/hip-hop format

Examples of good roast angles:
- "Claims to be 'disrupting' an industry that's been the same for decades"
- "Has 'entrepreneur' in bio but still works a 9-5"
- "Posts motivational quotes but complains about Monday mornings"
- "Says they're 'passionate about synergy' with a straight face"

Format as a simple list:
1. [Specific roast angle]
2. [Specific roast angle]
...

Focus on professional personas, buzzwords, and career contradictions.
"""