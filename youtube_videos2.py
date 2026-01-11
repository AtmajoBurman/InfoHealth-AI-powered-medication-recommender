import google.generativeai as genai
import googleapiclient.discovery
from typing import List, Dict
import operator

class YouTubeExtractor:
    def __init__(self, gemini_key: str, yt_key: str):
        genai.configure(api_key=gemini_key)
        self.model = genai.GenerativeModel("models/gemini-2.5-flash")
        self.youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=yt_key)
    
    def symptom_to_videos(self, user_symptoms: str) -> tuple[List[Dict], List[str], List[str]]:
        """Returns: videos, youtube_keywords, medical_keywords"""
        
        # SINGLE Gemini call - extract BOTH keyword types
        prompt = f"""
    You are a medical keyword extraction system.

    User symptoms: {user_symptoms}

    Return TWO lists in JSON format:
    1. YOUTUBE_KEYWORDS (8-12): "chest pain management", "cardiac care awareness"
    2. MEDICAL_KEYWORDS assuming you are a medical search assistant for Google Places API (5-8): "cardiologist", "cardiac clinic", "heart hospital"

    {{"youtube_keywords": ["keyword1", "keyword2"], "medical_keywords": ["clinic1", "clinic2"]}}
    """
        
        response = self.model.generate_content(prompt)
        # Parse JSON response
        import json
        import re

        response_text = response.text.strip()
        print(f"🎯 Gemini response: {response_text[:200]}...")

        # Extract JSON from ```json ... ``` markdown
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            keyword_data = json.loads(json_str)
            print("✅ Regex JSON extracted!")
        else:
            # Fallback if no markdown
            keyword_data = json.loads(response_text)
            print("✅ Direct JSON parsed!")

        youtube_keywords = keyword_data.get("youtube_keywords", [])
        medical_keywords = keyword_data.get("medical_keywords", [])
        
        print(f"🎯 YouTube: {' | '.join(youtube_keywords[:5])}")
        print(f"🏥 Medical: {' | '.join(medical_keywords[:5])}")
        
        # Continue with YouTube search using youtube_keywords (unchanged)
        query = ' '.join(youtube_keywords)
        # ... rest of your existing YouTube code ...
        search_response = self.youtube.search().list(
            q=query, part='id,snippet', maxResults=25, type='video', order='relevance'
        ).execute()
        
        videos = []
        for item in search_response.get('items', []):
            video_id = item['id']['videoId']
            stats_response = self.youtube.videos().list(part='statistics,snippet', id=video_id).execute()
            
            if stats_response['items']:
                stats = stats_response['items'][0]['statistics']
                snippet = stats_response['items'][0]['snippet']
                thumbnail = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                
                videos.append({
                    'title': snippet['title'][:70] + '...',
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'video_id': video_id,
                    'thumbnail': thumbnail,
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'score': int(stats.get('viewCount', 0)) + int(stats.get('likeCount', 0)) * 2
                })
        
        top_videos = sorted(videos, key=operator.itemgetter('score'), reverse=True)[:10]
        return top_videos, youtube_keywords, medical_keywords  # Return 3 items!
