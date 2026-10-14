# InfoHealth — Architecture

## Overview

InfoHealth is a **Streamlit-based AI health information system** that bridges the gap between natural language symptom descriptions and structured medical information retrieval. It provides two core services:

1. **Top-10 relevant YouTube videos** for a given symptom description.
2. **Top-15 nearby clinics** ranked by distance and semantic relevance.

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

## Data Flow — Step by Step

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit UI
    participant spaCy as spaCy NER
    participant Gemini as Gemini 2.5 Flash
    participant YT as YouTube API v3
    participant Places as Google Places API
    participant ST as Sentence-Transformer
    participant Cache as Session State Cache

    User->>UI: Enter symptom text
    UI->>spaCy: Validate input (DISEASE entity check)

    alt No medical entity detected
        spaCy-->>UI: Warning: be more specific
    else Valid medical input
        spaCy-->>UI: Entity found

        UI->>Cache: Check cached_keywords for same query
        alt Cache miss (new query)
            UI->>Gemini: Extract youtube_keywords + medical_keywords
            Gemini-->>UI: JSON with youtube_keywords and medical_keywords
            UI->>Cache: Store keywords

            UI->>YT: search().list(q=youtube_keywords, maxResults=25)
            YT-->>UI: Video IDs
            UI->>YT: videos().list(statistics + snippet per video)
            YT-->>UI: Views, Likes, Thumbnails
            UI->>Cache: Store top-10 videos (score = views + 2 x likes)
        else Cache hit
            Cache-->>UI: Return cached_videos and cached_keywords
        end

        UI-->>User: Display top-10 Videos tab

        User->>UI: Click LIVE GPS then switch to Clinics tab
        UI->>UI: navigator.geolocation returns lat and lng

        UI->>Cache: Check cached_clinics
        alt Clinics not cached
            UI->>Places: POST searchText (medical_keywords, location)
            Places-->>UI: Specialty clinic results
            UI->>Places: POST searchNearby (hospital/doctor/pharmacy)
            Places-->>UI: General medical places
            UI->>UI: Deduplicate, filter rating >= 2.0, Haversine distance
            UI->>ST: Embed symptom text + clinic text
            ST-->>UI: Cosine similarity scores
            UI->>UI: Score = 50pct x sim + 30pct x rating + 20pct x keyword_boost
            UI->>Cache: Store top-15 CarePlace objects
        else Clinics cached
            Cache-->>UI: Return cached_clinics
        end

        UI-->>User: Display top-15 Clinics + Folium Map
    end
```

---

## Module Breakdown

```mermaid
graph LR
    subgraph Files["Project Files"]
        APP["app.py\nStreamlit Entry Point"]
        YT2["youtube_videos2.py\nYouTubeExtractor class"]
        MF["medical_finder.py\nNearbyMedicalFinder class\nCarePlace dataclass"]
        GC["get_coordinates.py\nget_device_coordinates()"]
    end

    subgraph Models["ML Models loaded once per session"]
        SPACY_M["en_ner_bc5cdr_md\nBiomedical NER"]
        SBERT["all-MiniLM-L6-v2\nSentence Embeddings"]
        GEM["Gemini 2.5 Flash\nKeyword Extraction LLM"]
    end

    subgraph APIs["External APIs"]
        YT_A["YouTube Data API v3"]
        PL_A["Google Places API New\nsearchText + searchNearby"]
        GEO["Browser Geolocation\nnavigator.geolocation"]
    end

    APP --> YT2
    APP --> MF
    APP --> GC
    APP --> SPACY_M

    YT2 --> GEM
    YT2 --> YT_A

    MF --> SBERT
    MF --> PL_A

    GC --> GEO
```

---

## Caching Strategy

```mermaid
graph TD
    Q["User Query"]

    Q --> K{"Same as last_query?"}
    K -->|"No — cache miss"| GEMINI_CALL["Call Gemini API\nextract keywords"]
    K -->|"Yes — cache hit"| HIT["Read from\nst.session_state"]

    GEMINI_CALL --> CACHE_KW["Cache: cached_keywords\ncached_medical_keywords"]
    CACHE_KW --> YT_CALL["Call YouTube API\nfetch top-10 videos"]
    YT_CALL --> CACHE_VID["Cache: cached_videos"]

    CACHE_VID --> VID_TAB["Videos Tab\nreads cached_videos"]

    HIT --> VID_TAB
    HIT --> CLIN_CHECK

    CACHE_KW --> CLIN_CHECK{"cached_clinics exists?"}
    CLIN_CHECK -->|No| PLACES_CALL["Call Google Places API\nscore clinics"]
    PLACES_CALL --> CACHE_CLIN["Cache: cached_clinics"]
    CACHE_CLIN --> CLIN_TAB["Clinics Tab\nreads cached_clinics"]
    CLIN_CHECK -->|Yes| CLIN_TAB

    style CACHE_KW fill:#2a1a00,stroke:#FFA500,color:#FFA500
    style CACHE_VID fill:#2a1a00,stroke:#FFA500,color:#FFA500
    style CACHE_CLIN fill:#2a1a00,stroke:#FFA500,color:#FFA500
    style HIT fill:#2a1a00,stroke:#FFA500,color:#FFA500
```

---

## Clinic Scoring Formula

```mermaid
graph LR
    A["Symptom Text"] --> E1["Sentence-Transformer\nEmbed symptom"]
    B["Clinic Name + Types"] --> E2["Sentence-Transformer\nEmbed clinic"]
    E1 & E2 --> SIM["Cosine Similarity\n(sim)"]

    C["Clinic Rating divided by 5.0"] --> RAT["Rating Norm\n(rating_norm)"]
    D["Medical Keywords\nin clinic name/types"] --> KW["Keyword Boost\n(keyword_boost)"]

    SIM -->|"x 50"| SCORE
    RAT -->|"x 30"| SCORE
    KW -->|"x 20"| SCORE

    SCORE["match_percent = 50 x sim + 30 x rating_norm + 20 x keyword_boost"]
    SCORE --> SORT["Sort by distance_m\nthen match_percent"]
    SORT --> TOP15["Top 15 CarePlace objects"]
```

---

## Component Summary

| Component | File | Role | Key Tech |
|-----------|------|------|----------|
| **Streamlit UI** | `app.py` | Entry point, session state, routing, rendering | `streamlit`, custom CSS, `folium` |
| **NER Validator** | `app.py` | Ensures input contains a medical entity | `spacy` — `en_ner_bc5cdr_md` |
| **Keyword Extractor** | `youtube_videos2.py` | LLM call → dual keyword lists | `google.generativeai` (Gemini 2.5 Flash) |
| **Video Retriever** | `youtube_videos2.py` | Search + rank top-10 videos | `googleapiclient` — YouTube Data API v3 |
| **Clinic Finder** | `medical_finder.py` | Fetch, filter, deduplicate, score clinics | `requests` — Google Places API (New) |
| **Semantic Scorer** | `medical_finder.py` | Embed text, cosine similarity for relevance | `sentence_transformers` — MiniLM-L6-v2 |
| **GPS Module** | `get_coordinates.py` | Retrieve browser geolocation via JS | `streamlit_javascript`, `navigator.geolocation` |
| **Map Renderer** | `app.py` | Interactive clinic + user position map | `folium`, `streamlit_folium` |

---

## Diagram Legend

| Symbol | Meaning |
|--------|---------|
| **Solid arrows** `-->` | Synchronous data flow |
| **Dashed arrows** `-.->` | Asynchronous / browser-side calls |
| 🟡 **Gold nodes** | Session-state caching layers |
| 🔴 **Red nodes** | YouTube pipeline |
| 🟢 **Green nodes** | Medical / clinic pipeline |
| 🔵 **Blue nodes** | Map rendering |
| 🟣 **Purple nodes** | User-facing UI elements |
