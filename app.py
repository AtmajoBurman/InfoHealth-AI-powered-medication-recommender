import streamlit as st

# Config
st.set_page_config(
    page_title="Info-Health",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# =========================
# ENV + IMPORTS
# =========================
import os
os.environ["THINC_OPS"] = "numpy"

import spacy
from youtube_videos2 import YouTubeExtractor
from medical_finder import NearbyMedicalFinder

import folium
from streamlit_folium import st_folium
import requests
from get_coordinates import get_device_coordinates
# =========================
# LOAD spaCy SAFELY
# =========================
@st.cache_resource
def load_spacy_model():
    return spacy.load("en_ner_bc5cdr_md")

sci_nlp = load_spacy_model()
print("✅ Medical NLP model loaded successfully.")
# =========================
# UTILS
# =========================
def process_text(text: str) -> bool:
    if not text or len(text) > 100:
        return False
    doc = sci_nlp(text)
    return any(ent.label_ == "DISEASE" for ent in doc.ents)

# Add network connectivity check function
def check_network_connectivity():
    """Test network connectivity without using Gemini credits"""
    test_urls = [
        "https://www.google.com",
        "https://www.cloudflare.com",
        "https://httpbin.org/get"
    ]
    
    for url in test_urls:
        try:
            # Quick HEAD request (no data transfer)
            response = requests.head(url, timeout=3)
            if response.status_code < 500:
                return True
        except:
            continue
    
    return False



# Custom CSS (Dark theme + golden tabs)
st.markdown("""
<style>
    /* Dark theme */
    .main {background-color: #0e1117;}
    .stApp {background-color: #0e1117;}
    
    /* Header */
    .header {
        background: linear-gradient(90deg, #6B2D87 0%, #2D1B4A 100%);
        padding: 1rem; border-radius: 15px; margin-bottom: 2rem;
    }
    
    /* Golden tab effect */
    .tab-active {
        box-shadow: 0 0 25px #FFD700 !important;
        border: 3px solid #FFD700 !important;
        background: linear-gradient(45deg, #FFD700, #FFA500) !important;
        color: #000 !important;
        font-weight: bold;
    }
    
    /* Video cards - WHITE TEXT */
    .video-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border-radius: 15px; 
        padding: 1.5rem; 
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        color: white !important;  /* WHITE TEXT */
        border-left: 4px solid #6B2D87;
    }
    
    /* Thumbnail styling */
    .thumbnail-img {
        width: 200px; 
        height: 120px; 
        object-fit: cover; 
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    /* Hover effects */
    button:hover {transform: scale(1.02); transition: 0.3s;}
    .video-card:hover {transform: translateY(-5px); transition: 0.3s;}
    
    /* Connectivity warning */
    .connection-warning {
        background: linear-gradient(90deg, #ff6b6b, #ff8e8e);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 0.8; }
        50% { opacity: 1; }
        100% { opacity: 0.8; }
    }
</style>
""", unsafe_allow_html=True)

# Load secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]

# Initialize
@st.cache_resource
def init_youtube():
    return YouTubeExtractor(GEMINI_API_KEY, YOUTUBE_API_KEY)

@st.cache_resource
def init_medical():
    return NearbyMedicalFinder(GOOGLE_MAPS_API_KEY)

# Check network connectivity ONCE at startup
if 'network_checked' not in st.session_state:
    with st.spinner("🔧 Checking network connectivity..."):
        st.session_state.network_ok = check_network_connectivity()
        st.session_state.network_checked = True

# Only initialize if network is OK
if st.session_state.network_ok:
    yt_extractor = init_youtube()
    medical_finder = init_medical()
else:
    # Show warning but don't crash
    st.markdown("""
    <div class="connection-warning">
        ⚠️ <strong>Network Issue Detected</strong><br>
        Please check your internet connection and refresh the page.
    </div>
    """, unsafe_allow_html=True)
    # Create dummy objects to prevent crashes
    yt_extractor = None
    medical_finder = None

# Rest of your code continues...
# Cache videos in session state
if 'cached_videos' not in st.session_state:
    st.session_state.cached_videos = None
if 'cached_keywords' not in st.session_state:
    st.session_state.cached_keywords = None
if 'last_query' not in st.session_state:
    st.session_state.last_query = None

if 'cached_medical_keywords' not in st.session_state:
    st.session_state.cached_medical_keywords = None
    
if 'cached_clinics' not in st.session_state:
    st.session_state.cached_clinics = None

# Header
st.markdown(
    '<div style="background:#2D1B4A;padding:1rem;border-radius:15px">'
    '<h1 style="color:white;text-align:center">🩺 Info-Heal<span style="color:red">+</span>h</h1>'
    '</div>',
    unsafe_allow_html=True
)

# Search + Tabs row
search_col, gps_col = st.columns([3, 1])
# Add custom CSS
st.markdown("""
    <style>
    label[data-testid="stWidgetLabel"] {
        color: white !important;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# Your input field
symptoms = search_col.text_input(
    "🔍 Enter symptoms (e.g., pain in right elbow, my wisdom teeth is paining, etc.)",
    placeholder="Type your symptoms here..."
)


if not process_text(symptoms):
        st.warning("Sorry, We could not detect any medical keywords. We request you to be a bit more specific 🙁")
        symptoms = ""
        # st.session_state.cached_videos = []

#////////////////////////////////////////
# GPS Button Locking
if "gps_locked" not in st.session_state:
    st.session_state.gps_locked = False
#////////////////////////////////////////
# GPS Button
if gps_col.button(
    "📍 LIVE GPS",
    use_container_width=True,
    disabled=st.session_state.gps_locked
):
    st.session_state.use_gps = True
    
if st.session_state.get("use_gps", False):
    lat, lng = get_device_coordinates()

    if lat is None and lng is None:
        st.info("📍 Waiting for GPS permission...")
    elif lat == -1 and lng == -1:
        st.error("📍 GPS not available")
        st.session_state.use_gps = False
    else:
        st.session_state.current_lat = lat
        st.session_state.current_lng = lng
        st.session_state.use_gps = False
        st.session_state.gps_locked = True  # Lock button after use
        st.success(f"📍 GPS: {lat:.4f}, {lng:.4f}")


# Tab system
col1, col2 = st.columns(2)
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "videos"

with col1:
    if st.button("🎬 VIDEOS", key="videos_btn", use_container_width=True,
                 help="Educational videos for your symptoms"):
        st.session_state.active_tab = "videos"
        st.markdown('<button class="tab-active">', unsafe_allow_html=True)

with col2:
    if st.button("🏥 CLINICS", key="clinics_btn", use_container_width=True,
                 help="Nearest medical facilities"):
        st.session_state.active_tab = "clinics"
        st.markdown('<button class="tab-active">', unsafe_allow_html=True)


search_clicked = st.button("🔍 SEARCH")

# Content based on tab
if search_clicked or symptoms:
    if symptoms: 
        if symptoms != st.session_state.last_query:
            # Initialize all variables to safe defaults
            videos = []
            yt_keywords = []
            medical_keywords = []
            clinics = []  # Add this!
            
            try:
                with st.spinner(" Analyzing Symptoms"):
                    videos, yt_keywords, medical_keywords = yt_extractor.symptom_to_videos(symptoms)
                    # Cache ALL results
                    st.session_state.cached_clinics = None
                    st.session_state.cached_videos = videos
                    st.session_state.cached_keywords = yt_keywords
                    st.session_state.cached_medical_keywords = medical_keywords
                    st.session_state.last_query = symptoms
          
            except requests.exceptions.SSLError:
                st.error("🔒 **SSL Connection Issue** 😅")
                st.info("👉 **Would you mind clicking the search button again please?** 🙏")
                st.session_state.cached_videos = []
                st.session_state.cached_clinics = None
                videos = []  # CRITICAL: Set videos to empty list
                
            except requests.exceptions.HTTPError as e:
                if "quota" in str(e).lower() or "429" in str(e):
                    st.error("⏳ **Service Busy** 😔")
                    st.info("**We are sorry for the inconvenience. We have exceeded the maximum number of requests we could handle. Please try a little later.**")
                else:
                    st.error(f"🌐 **Network hiccup** 😅 - {str(e)}")
                    st.info("👉 **Please click SEARCH again!**")
                st.session_state.cached_videos = []
                st.session_state.cached_clinics = None
                videos = []  # CRITICAL: Set videos to empty list
                
            except Exception as e:
                st.error("⚠️ **Oops! Something went wrong** ")
                st.info("👉 **Would you mind clicking SEARCH again?** 🙏")
                print(f"DEBUG ERROR: {e}")
                st.session_state.cached_videos = []
                st.session_state.cached_clinics = None
                videos = []  # CRITICAL: Set videos to empty list
        else:
            # Use cached results
            videos = st.session_state.cached_videos or []
            medical_keywords = st.session_state.cached_medical_keywords or []
            clinics = st.session_state.cached_clinics or []  # FIX: Initialize clinics
        
        # ✅ DISPLAY VIDEOS/CLINICS (moved outside if/else)
        if st.session_state.active_tab == "videos":
                if videos:
                    st.markdown(
                                    """
                                    <h1 style='color: white; text-shadow: 0 0 1px #ffffff, 0 0 2px #ffffff; font-weight: bold;'>
                                        🎬 Recommended Videos
                                    </h1>
                                    """,
                                    unsafe_allow_html=True
                                )

                    
                    # Intro message
                    st.markdown(
                                    """
                                    <p style='color: yellow; font-size:16px; font-weight: bold;'>
                                        ✅ Okay, based on your symptoms, we've found helpful educational videos.
                                    </p>
                                    """,
                                    unsafe_allow_html=True
                                )

                    
                    # Normalize score out of 100
                    def normalize_score(score, max_score):
                        return min(100, (score / max_score) * 100) if max_score > 0 else 0

                    max_score = max(v[1]['score'] for v in enumerate(videos)) if videos else 0

                    if len(videos) >= 5:
                        max_views = max(videos, key=lambda x: x['views'])
                        max_views_idx = next(i for i, v in enumerate(videos) if v == max_views)
                        max_likes = max(videos, key=lambda x: x['likes'])
                        max_likes_idx = next(i for i, v in enumerate(videos) if v == max_likes)
                        
                        st.markdown(f"""
                        <div style='background: linear-gradient(90deg, #FFD700, #FFA500); 
                                    padding: 1.5rem; border-radius: 15px; margin: 1rem 0; color: #000; 
                                    box-shadow: 0 8px 25px rgba(255,215,0,0.4);'>
                            ✨ <strong>Top picks:</strong><br>
                            Most views: <strong>Suggested Video - {max_views_idx+1}</strong> | 
                            Most likes: <strong>Suggested Video - {max_likes_idx+1}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Single column video cards (1 per row)
                    for i, video in enumerate(videos, 1):
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            if video['thumbnail']:
                                st.markdown(f"""
                                <img src="{video['thumbnail']}" class="thumbnail-img" alt="Video thumbnail">
                                """, unsafe_allow_html=True)  # ✅ Fixed
                            else:
                                st.markdown("🖼️ No thumbnail")
                        
                        with col2:
                            st.markdown(f"""
                            <div class="video-card">
                                <h3 style='color: white; margin: 0;'>📺 Suggested Video - {i}</h3>
                                <p style='color: #ccc; font-size: 0.9rem;'>
                                    <strong>👀 Views:</strong> {video['views']:,} | 
                                    <strong>👍 Likes:</strong> {video['likes']:,} | 
                                    <strong>📊 Engagement:</strong> {normalize_score(video['score'], max_score):.0f}%
                                </p>
                                <a href="{video['url']}" target="_blank" style='color: #FFD700; font-weight: bold; text-decoration: none;'>
                                    ▶️ Watch on YouTube
                                </a>
                            </div>
                            """, unsafe_allow_html=True)  
                        
                        st.divider()
                else:
                    st.warning("No videos found for the given symptoms.")
        # Clinics placeholder
        if st.session_state.active_tab == "clinics":
                st.markdown(
                    """
                    <h1 style='color: white; text-shadow: 0 0 1px #ffffff, 0 0 2px #ffffff; font-weight: bold;'>
                        🏥 Nearest Clinics
                    </h1>
                    """,
                    unsafe_allow_html=True
                )
                
                # ALWAYS define lat and lng variables at the start
                lat = st.session_state.get('current_lat', 23.5224)  # Default to Durgapur
                lng = st.session_state.get('current_lng', 87.3233)  # Default to Durgapur
                
                if 'current_lat' not in st.session_state:
                    st.warning("👆 **Please press LIVE GPS button first** to find clinics near you!")
                    st.info("📍 GPS gives accurate nearby clinics (uses your IP location)")
                    clinics = []
                elif medical_keywords and st.session_state.cached_clinics:
                    # Use cached clinics
                    clinics = st.session_state.cached_clinics
                elif medical_keywords:
                    # Generate clinics ONCE
                    symptoms_list = symptoms.split()
                    with st.spinner("🔍 Finding clinics near you..."):
                        clinics = medical_finder.recommend_care(symptoms_list, medical_keywords, lat, lng)
                        st.session_state.cached_clinics = clinics  # CACHE!
                    # Show coords used
                    st.success(f"📍 Searched around {lat:.4f}, {lng:.4f}")
                else:
                    st.warning("Enter symptoms first!")
                    clinics = []
                
                if clinics:
                    # Display clinics
                    for i, clinic in enumerate(clinics, 1):
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            format_distance = lambda d: f"{d}m" if d < 1000 else f"{d/1000:.2f}km"
                            st.markdown(
                                f"""
                                <div style='color: white; 
                                            text-shadow: 0 0 2px #ffffff, 0 0 1px #ffffff, 0 0 2px #ffffff; 
                                            font-weight: bold; 
                                            font-size: 40px;'>
                                    #{i} — {format_distance(clinic.distance_m)}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        with col2:
                            st.markdown(f"""
                            <div class="video-card">
                                <h3 style='color: white; margin: 0;'>
                                    🏥 {clinic.name}
                                </h3>
                                <p style='color: #ccc;'>
                                    ⭐ {clinic.rating} ({clinic.user_ratings_total:,} reviews) | 
                                    Match: {clinic.match_percent:.2f}%
                                </p>
                                <p style='color: #aaa; font-size: 0.85rem;'>
                                    📍 {clinic.address[:80]}...
                                </p>
                                <a href="{clinic.url}" target="_blank" style='color: #FFD700; font-weight: bold;'>
                                    📱 Get Directions
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                        st.divider()
                    
                    # Create Folium map (centered)
                    # Use session state coordinates if available, otherwise use the defaults
                    center_lat = st.session_state.get('current_lat', lat)
                    center_lng = st.session_state.get('current_lng', lng)
                    
                    m = folium.Map(
                        location=[center_lat, center_lng],
                        zoom_start=13,
                        tiles="OpenStreetMap"
                    )
                    
                    # 🔴 RED USER LOCATION (priority)
                    if 'current_lat' in st.session_state:
                        folium.Marker(
                            [st.session_state.current_lat, st.session_state.current_lng],
                            popup="📍 YOU ARE HERE",
                            tooltip="Your Location",
                            icon=folium.Icon(color="red", icon="user", prefix="fa")
                        ).add_to(m)
                    
                    # 🔵 BLUE CLINIC MARKERS
                    for i, clinic in enumerate(clinics, 1):
                        folium.Marker(
                            [clinic.lat, clinic.lng],
                            popup=f"""
                            <b>#{i} {clinic.name}</b><br>
                            ⭐ {clinic.rating} ({clinic.user_ratings_total} reviews)<br>
                            📏 {clinic.distance_m}m | Match: {clinic.match_percent}%<br>
                            📍 {clinic.address[:60]}...
                            """,
                            tooltip=f"#{i} {clinic.name}",
                            icon=folium.Icon(color="blue", icon="hospital", prefix="fa")
                        ).add_to(m)
                    
                    st.markdown(
                        """
                        <div style='display: flex; justify-content: center;'>
                        """, 
                        unsafe_allow_html=True
                    )
                    st_folium(m, width=900, height=500, returned_objects=[])
                    st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.warning("Please enter symptoms first!")
if __name__ == "__main__":
    st.markdown("---")
    st.markdown("*Made with ❤️ by Atmajo Burman*")


