# InfoHealth-AI-powered-medication-recommender
InfoHealth is an AI-powered health information system that extracts medical entities from user symptoms, matches them with reliable sources, and recommends relevant medications and videos with a confidence-based similarity score.

## 🚀 Live Demo & Project Showcase

🔗 **Live Application (Streamlit Deployment)**  
👉 **[Access the InfoHealth App](https://infohealth-ai-powered-med-recommender-atmajo.streamlit.app/)**  
Experience the complete InfoHealth system live, including symptom input, AI-powered keyword refinement, and medical resource recommendations.

🎥 **Project Presentation (Must-Watch | 1 Minute)**  
⭐ **[Watch the AI-Generated Presentation Video](https://youtu.be/M91axJi6AJE?si=RUXKJRsw7Fo3TJ6j)** ⭐  
This short video is the **official project walkthrough**, created from the Google Slides presentation.  
📌 *Highly recommended for recruiters and evaluators to quickly understand the project’s motivation, architecture, and outcomes.*

🧪 **Hands-on Demonstration Video**  
▶️ **[Watch the Practical Demo](https://youtu.be/pUirCVp8oJA?si=QmmHyfWyjON6DIgg)**  
A real-time demonstration showcasing how users interact with the application and how recommendations are generated.

---

---
## System Architecture

```mermaid
graph TB
    subgraph USER["User Browser"]
        UI_INPUT["Symptom Text Input"]
        GPS_BTN["LIVE GPS Button"]
        TAB_VID["Videos Tab"]
        TAB_CLIN["Clinics Tab"]
    end

    subgraph APP["Streamlit Server — app.py"]
        direction TB
        NET_CHK["Network Connectivity Check\nrequests.head"]
        SPACY["spaCy NER Validator\nen_ner_bc5cdr_md\n@cache_resource"]
        SESSION["Session State Cache\ncached_videos\ncached_keywords\ncached_medical_keywords\ncached_clinics"]
        COORD["get_coordinates.py\nBrowser Geolocation API\nst_javascript"]
    end

    subgraph YT_MOD["YouTubeExtractor — youtube_videos2.py"]
        GEMINI["Gemini 2.5 Flash LLM\ngoogle.generativeai\nKeyword Extractor"]
        YT_API["YouTube Data API v3\ngoogleapiclient\nSearch + Statistics"]
        SCORER_VID["Video Scorer\nscore = views + 2 x likes\nTop 10 returned"]
    end

    subgraph MED_MOD["NearbyMedicalFinder — medical_finder.py"]
        SENT_TRANS["Sentence-Transformer\nall-MiniLM-L6-v2\nCosine Similarity"]
        PLACES_TEXT["Places API searchText\nSpecialty clinic queries"]
        PLACES_NEAR["Places API searchNearby\nhospital, doctor, pharmacy"]
        DEDUP["Dedup and Filter\nrating >= 2.0\nHaversine distance"]
        SCORER_CLIN["Clinic Scorer\n50pct semantic sim\n30pct rating\n20pct keyword boost\nTop 15 by distance"]
    end

    subgraph MAP["Interactive Map"]
        FOLIUM["Folium Map\nOpenStreetMap tiles"]
        ST_FOLIUM["streamlit-folium\nEmbedded in UI"]
    end

    subgraph EXTERNAL["External APIs"]
        GEMINI_API["Google Gemini API"]
        YT_EXT["YouTube Data API v3"]
        PLACES_API["Google Places API New"]
        BROWSER_GEO["Browser Geolocation API"]
    end

    UI_INPUT -->|symptom text| NET_CHK
    GPS_BTN -->|trigger| COORD
    COORD -->|lat and lng| SESSION

    NET_CHK -->|ok| SPACY
    SPACY -->|DISEASE entity found| YT_MOD
    SPACY -->|invalid input| UI_INPUT

    GEMINI -->|youtube_keywords and medical_keywords| GEMINI_API
    GEMINI_API -->|JSON keyword response| GEMINI
    GEMINI --> YT_API
    YT_API -->|search and stats| YT_EXT
    YT_EXT -->|video items| YT_API
    YT_API --> SCORER_VID
    SCORER_VID -->|top 10 videos| SESSION

    SESSION -->|cached_medical_keywords| MED_MOD
    SESSION -->|lat and lng| MED_MOD
    PLACES_TEXT -->|POST searchText| PLACES_API
    PLACES_NEAR -->|POST searchNearby| PLACES_API
    PLACES_API -->|place results| DEDUP
    SENT_TRANS --> SCORER_CLIN
    DEDUP --> SCORER_CLIN
    SCORER_CLIN -->|top 15 CarePlace| SESSION

    SESSION -->|cached_videos| TAB_VID
    SESSION -->|cached_clinics| TAB_CLIN
    TAB_CLIN --> FOLIUM
    FOLIUM --> ST_FOLIUM
    ST_FOLIUM --> TAB_CLIN

    COORD -.->|navigator.geolocation| BROWSER_GEO
    BROWSER_GEO -.->|lat and lng| COORD

    classDef userNode fill:#2D1B4A,stroke:#6B2D87,color:#fff
    classDef appNode fill:#1a1a2e,stroke:#4a4a8a,color:#fff
    classDef ytNode fill:#1a0a0a,stroke:#cc0000,color:#fff
    classDef medNode fill:#0a1a0a,stroke:#006600,color:#fff
    classDef extNode fill:#0a0a1a,stroke:#FFD700,color:#FFD700
    classDef cacheNode fill:#2a1a00,stroke:#FFA500,color:#FFA500
    classDef mapNode fill:#001a2a,stroke:#0088cc,color:#fff

    class UI_INPUT,GPS_BTN,TAB_VID,TAB_CLIN userNode
    class NET_CHK,SPACY,COORD appNode
    class SESSION cacheNode
    class GEMINI,YT_API,SCORER_VID ytNode
    class SENT_TRANS,PLACES_TEXT,PLACES_NEAR,DEDUP,SCORER_CLIN medNode
    class GEMINI_API,YT_EXT,PLACES_API,BROWSER_GEO extNode
    class FOLIUM,ST_FOLIUM mapNode
```

---

### 👀 For Readers
If you are short on time, we strongly recommend watching the **1-minute presentation video first**, followed by the **live application demo**, to get a complete understanding of the project in under **3 minutes**.

## **📸 APPLICATION SCREENSHOTS**

### How it opens up 😊
![Front Page](https://github.com/AtmajoBurman/InfoHealth-AI-powered-medication-recommender/blob/main/InfoHealth_SS/front.png)
### Videos have been retrieved 😊
![Videos Retrieval](https://github.com/AtmajoBurman/InfoHealth-AI-powered-medication-recommender/blob/main/InfoHealth_SS/videos.png)
### Process of Clinics retrieval going on 😊
![Clinics Search](https://github.com/AtmajoBurman/InfoHealth-AI-powered-medication-recommender/blob/main/InfoHealth_SS/clin_s.png)
### Clinics have been retrieved 😊
![Clinics Display](https://github.com/AtmajoBurman/InfoHealth-AI-powered-medication-recommender/blob/main/InfoHealth_SS/clin_sh.png)
### See on map how far are you from each of the clinics 😊
![Interactive Map Display](https://github.com/AtmajoBurman/InfoHealth-AI-powered-medication-recommender/blob/main/InfoHealth_SS/maps.png)

# What made us think about Info-Health? 🩺

Modern information platforms such as **YouTube** and **map-based services** deliver highly relevant results when users provide **precise and well-defined keywords**. However, in medical contexts, this requirement introduces a significant **usability gap** ⚠️. Most users do not have a medical background and are often unfamiliar with the correct **clinical terminology** needed to describe their symptoms accurately.

🗣️ While users may struggle to name probable diseases or formal symptom terms, they are generally capable of expressing their **physical discomfort, pain intensity, and affected body parts** in simple, natural English. This creates an opportunity for **Artificial Intelligence (AI)** to function as an **intelligent intermediary** between human language and structured information retrieval systems.

🔍 In **InfoHealth**, the **Large Language Model (LLM)** bridges this gap by converting **human-expressed symptom descriptions** into **context-aware, platform-relevant keywords**. Instead of forcing users to search using **medical jargon**, the system allows them to describe their condition naturally. The LLM then assists in identifying the **most probable medical concepts** and refining them into keywords suitable for **educational video retrieval** and **location-based clinic searches**.

📊 From an evaluation perspective, the effectiveness of the **LLM** is assessed based on its ability to **improve the relevance and usefulness of retrieved results**. Compared to direct keyword-based searches, **LLM-refined queries** consistently produce more **focused and meaningful recommendations**, improving alignment between **user intent** and retrieved medical content.

🌍 By integrating **AI** with two of the most **trusted and widely used platforms**—**video-based information systems** and **map-based location services**—**InfoHealth** enhances both **accessibility and reliability** in healthcare information discovery. This approach prioritizes **speed, relevance, and clarity**, which are critical in **medical decision-support scenarios**. Importantly, the system does **not replace medical professionals** 🚑 but instead **empowers users** to seek accurate information and appropriate care more efficiently.

## 📁 Project Structure

```text
InfoHealth/
│
├── requirements.txt           # Project dependencies
├── app.py                     # Main application entry point
├── medical_finder.py          # Medical entity extraction and processing logic
├── youtube_videos2.py         # YouTube video retrieval based on refined keywords
├── secrets.toml               # API keys and sensitive configuration (gitignored)
│
├── .gitignore                 # Excludes secrets.toml and other sensitive files
└── README.md                  # Project documentation
```
```text
For Testing we have attached two notebooks and a Reports markdown file:
├── MedicationRecommender.ipynb
├── sciSpacy_usage.ipynb
├── Reports.md
```

## 📜 **License**

This project is open-source and available under the MIT License.

_Made with love by **Atmajo Burman** ❤️_

