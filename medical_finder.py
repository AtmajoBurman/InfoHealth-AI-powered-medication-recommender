import requests
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from dataclasses import dataclass

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')


@dataclass
class CarePlace:
    name: str
    address: str
    rating: float
    user_ratings_total: int
    distance_m: float
    match_percent: float
    place_id: str
    url: str
    lat: float
    lng: float
    matched_keywords: List[str]


class NearbyMedicalFinder:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.symptom_embedding = None


    # def generate_medical_queries(self, symptoms: List[str]) -> List[str]:
    #     pass


    def embed_text(self, text: str) -> np.ndarray:
        return model.encode(text)


    def geocode_address(self, address: str) -> tuple:
        """Convert address to lat/lng using Geocoding API"""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": self.api_key
        }
        try:
            response = requests.get(url, params=params)
            data = response.json()
            if data["status"] == "OK" and data["results"]:
                loc = data["results"][0]["geometry"]["location"]
                return loc["lat"], loc["lng"]
        except:
            pass
        return 23.5224, 87.3233  # Durgapur default


    
    def find_nearby_places_new(self, lat: float, lng: float, queries: List[str],
                            radius: int = 5000) -> List[Dict]:
        """Places API (New) - Text Search + Nearby Search combo
        Returns TOP 10 places with ≥2 stars rating only
        """
        all_places = []

        # TEXT SEARCH endpoint for specialty queries
        text_url = "https://places.googleapis.com/v1/places:searchText"
        nearby_url = "https://places.googleapis.com/v1/places:searchNearby"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.types,places.rating,places.userRatingCount,places.formattedAddress"
        }

        # 1. TEXT SEARCH for specialty (e.g. "cardiologist")
        for query in queries[:3]:  # Limit to top 3
            text_payload = {
                "textQuery": f"{query}",
                "locationBias": {
                    "circle": {
                        "center": {"latitude": lat, "longitude": lng},
                        "radius": radius
                    }
                },
                "maxResultCount": 10
            }
            try:
                response = requests.post(text_url, headers=headers, json=text_payload)
                if response.status_code == 200:
                    data = response.json()
                    all_places.extend(data.get("places", []))
                    print(f"✅ TextSearch: {len(data.get('places', []))} for '{query}'")
            except Exception as e:
                print(f"❌ TextSearch error: {e}")

        # 2. NEARBY SEARCH for general medical places
        nearby_payload = {
            "includedTypes": ["hospital", "doctor", "pharmacy"],
            "maxResultCount": 10,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": radius
                }
            }
        }
        try:
            response = requests.post(nearby_url, headers=headers, json=nearby_payload)
            if response.status_code == 200:
                data = response.json()
                all_places.extend(data.get("places", []))
                print(f"✅ NearbySearch: {len(data.get('places', []))} medical places")
        except Exception as e:
            print(f"❌ NearbySearch error: {e}")

        # 🔥 NEW: Filter ≥2 stars + Dedupe
        seen_ids = set()
        good_places = []
        
        for place in all_places:
            place_id = place["id"]
            rating = place.get("rating", 0)
            
            # ✅ FILTER: Skip <2 stars
            if rating < 2.0:
                print(f"⏭️ Skipped {place['displayName']['text']}: {rating}⭐ (<2)")
                continue
                
            if place_id not in seen_ids:
                seen_ids.add(place_id)
                legacy_place = {
                    "place_id": place_id,
                    "name": place["displayName"]["text"],
                    "geometry": {
                        "location": {
                            "lat": place["location"]["latitude"],
                            "lng": place["location"]["longitude"]
                        }
                    },
                    "types": place.get("types", []),
                    "rating": rating,
                    "user_ratings_total": place.get("userRatingCount", 0),
                    "vicinity": place.get("formattedAddress", "")
                }
                good_places.append(legacy_place)
                print(f"✅ Kept {legacy_place['name']}: {rating}⭐")

        # ✅ Return TOP 15 only (already sorted by relevance)
        return good_places[:15]

    def score_places(self, places: List[Dict], symptom_text: str, lat: float, lng: float, medical_keywords: List[str] = None) -> List[CarePlace]:
      """Sort by DISTANCE first, then relevance boost"""
      self.symptom_embedding = self.embed_text(symptom_text)
      queries = medical_keywords or self.generate_medical_queries([symptom_text.split()])

      scored_places = []
      for place in places:
          place_loc = place.get("geometry", {}).get("location", {})
          if not place_loc:
              continue

          distance = self.haversine(lat, lng, place_loc["lat"], place_loc["lng"])

          # Place text for relevance scoring
          place_text = f"{place.get('name', '')} {' '.join(place.get('types', []))}"

          # Keyword matches (e.g. "cardiology" in name/types)
          keyword_boost = sum(1 for q in queries if q.lower() in place_text.lower())

          # Text similarity
          place_embedding = self.embed_text(place_text)
          sim = np.dot(self.symptom_embedding, place_embedding) / (
              np.linalg.norm(self.symptom_embedding) * np.linalg.norm(place_embedding)
          )

          # Rating normalization
          rating_norm = min(place.get("rating", 0) / 5.0, 1.0)

          # RELEVANCE SCORE (0-100%) - ignores distance for sorting
          relevance_score = 50 * sim + 30 * rating_norm + 20 * keyword_boost
          match_pct = max(0, min(100, relevance_score))

          matched_keywords = [q for q in queries if q.lower() in place_text.lower()]

          care_place = CarePlace(
              name=place.get("name", "Unknown"),
              address=place.get("vicinity", ""),
              rating=place.get("rating", 0),
              user_ratings_total=place.get("user_ratings_total", 0),
              distance_m=round(distance),
              match_percent=round(match_pct, 1),
              place_id=place["place_id"],
              url=f"https://www.google.com/maps/place/?q=place_id:{place['place_id']}",
              lat=place_loc["lat"],
              lng=place_loc["lng"],
              matched_keywords=matched_keywords[:3]
          )
          scored_places.append(care_place)

      # ✅ KEY FIX: Sort by DISTANCE first, then relevance
      return sorted(scored_places, key=lambda p: (p.distance_m, p.match_percent))[:15]



    def get_live_location(self) -> tuple:
      """Get approximate location from IP - works everywhere"""
      try:
          # Free IP geolocation (no API key needed)
          response = requests.get('https://ipinfo.io/json')
          data = response.json()
          loc = data['loc'].split(',')
          lat, lng = float(loc[0]), float(loc[1])
          print(f"📍 Auto-detected: {data.get('city', 'Unknown')}")
          return lat, lng
      except:
          # Fallback to Durgapur
          print("📍 Using Durgapur default")
          return 23.5224, 87.3233


    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi, dlambda = np.radians(lat2-lat1), np.radians(lon2-lon1)
        a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
        return 2 * R * np.arcsin(np.sqrt(a))


    def recommend_care(self, symptoms: List[str], medical_keywords: List[str], lat: float = None, 
                    lng: float = None, address: str = None, radius: int = 50000) -> List[CarePlace]:
        """Accept pre-generated medical keywords from YouTube"""
        
        if address and (lat is None or lng is None):
            lat, lng = self.geocode_address(address)

        if lat is None or lng is None:
            lat, lng = 23.5224, 87.3233  # Durgapur

        symptom_text = " ".join(symptoms)
        
        print(f"🔍 Symptom text: {symptom_text}")
        print(f"🏥 Using YouTube-generated keywords: {medical_keywords}")

        places = self.find_nearby_places_new(lat, lng, medical_keywords, radius)
        scored = self.score_places(places, symptom_text, lat, lng, medical_keywords)
        
        print(f"✅ Found {len(scored)} scored recommendations")
        return scored

