# SPECTRUM CARE (CHROMA CONTEXT) — COMPLETE UML DIAGRAMS SPECIFICATION

This document provides the complete, updated Unified Modeling Language (UML) specifications reflecting all components implemented in the project, including the **Administrator Task Validation & Management Module**, **YOLOv8 Deep Learning Detector**, **CIELAB Perceptual Colour Engine**, **Daltonized CVD Simulation**, and **Web Speech Voice Assistant**.

---

## 1. Use Case Diagram

### Actors:
- **Registered User (CVD Learner/Individual)**: Registers, uploads/captures images, views spatial contextual results, listens to voice guidance, and manages CVD profiles.
- **Administrator**: Validates analysis tasks, reviews detection accuracy, manages user account access, and configures AI model detection thresholds.

```mermaid
flowchart LR
    User((User))
    Admin((Administrator))

    subgraph ChromaContextSystem ["Chroma Context / Spectrum Care System"]
        UC1(["Register & Login"])
        UC2(["Manage Vision Profile (Deuteranopia/Protanopia/Tritanopia)"])
        UC3(["Upload / Capture Image"])
        UC4(["Inspect Contextual Detections & Colour Swatches"])
        UC5(["View Side-by-Side Split-View CVD Simulation"])
        UC6(["Listen to Voice Guidance (Web Speech)"])
        UC7(["Export Diagnostic Report (PDF/CSV/JSON)"])
        UC8(["Browse Personal History"])
        
        UC9(["Validate & Review Analysis Tasks"])
        UC10(["Manage User Accounts (Activate/Suspend/Role)"])
        UC11(["Configure AI Detection Thresholds (Conf/IoU)"])
        UC12(["Monitor Subsystem Health & Status"])
    end

    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC6
    User --> UC7
    User --> UC8

    Admin --> UC1
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
```

---

## 2. Activity Diagram (End-to-End Task & Analysis Workflow)

```mermaid
flowchart TD
    Start([User Starts Application]) --> Login{Authenticated?}
    Login -- No --> AuthForm[Register or Log in via JWT]
    AuthForm --> Dashboard[Open Dashboard]
    Login -- Yes --> Dashboard

    Dashboard --> Choice{Select Action}
    Choice -- Update Vision Profile --> VisionSettings[Configure CVD Type & Preferences]
    Choice -- Upload Image --> Ingestion[Select Image File or Camera Capture]
    
    Ingestion --> Validation{File Valid? < 10MB, JPG/PNG}
    Validation -- No --> ShowErr[Display Friendly Error & Retry]
    ShowErr --> Ingestion
    
    Validation -- Yes --> SaveStorage[Store Raw Asset & Create Task Record]
    
    subgraph AIPipeline ["Core Vision & Accessibility Pipeline"]
        SaveStorage --> YOLO[Run YOLOv8 Object Detection]
        YOLO --> Masking[Contour Foreground Isolation]
        Masking --> CIELAB[Extract Dominant CIELAB L*a*b* Colour]
        CIELAB --> SpatialGrid[Map 9-Quadrant Spatial Location]
        SpatialGrid --> TrafficCheck{Is Traffic Light?}
        TrafficCheck -- Yes --> MultiZone[Analyze Top-Red / Mid-Yellow / Bot-Green Zones]
        TrafficCheck -- No --> ContextSynthesize[Synthesize Context: 'Red Apple on middle-center']
        MultiZone --> ContextSynthesize
        ContextSynthesize --> CVDSim[Generate Daltonized CVD Simulation Matrix]
    end

    CVDSim --> DisplayResults[Display Split-View Comparison & Detections]
    DisplayResults --> AudioPrompt{Listen to Audio?}
    AudioPrompt -- Yes --> WebSpeech[Browser Web Speech Synthesizes Scene Aloud]
    AudioPrompt -- No --> ReportPrompt{Download Report?}
    WebSpeech --> ReportPrompt
    
    ReportPrompt -- Yes --> GenReport[Export PDF / CSV / JSON]
    ReportPrompt -- No --> EndUser([User Complete])
    GenReport --> EndUser

    subgraph AdminWorkflow ["Administrator Task Validation"]
        AdminStart([Admin Logs In]) --> OpenAdmin[Open Admin Console]
        OpenAdmin --> ReviewTasks[Review User Analysis Tasks]
        ReviewTasks --> InspectTask{Inspect Accuracy}
        InspectTask -- Approved --> MarkVerified[Mark Task as Verified]
        InspectTask -- Inaccurate --> MarkFlagged[Flag Task for Review]
        MarkVerified --> EndAdmin([Admin Complete])
        MarkFlagged --> EndAdmin
    end
```

---

## 3. Class Diagram

```mermaid
classDiagram
    class User {
        +String user_id
        +String first_name
        +String last_name
        +String email
        +String pass_hash
        +String role
        +DateTime created_on
        +DateTime last_login
        +String status
        +register()
        +login()
        +logout()
    }

    class Profile {
        +String pro_id
        +String user_id
        +Date dob
        +String gender
        +String phone
        +updateProfile()
    }

    class CVDProfile {
        +String cvd_id
        +String pro_id
        +String type
        +String severity
        +Date diag_on
        +updateCVDDetails()
    }

    class Analysis {
        +String ana_id
        +String pro_id
        +DateTime ana_date
        +String img_url
        +String status
        +Float comp_time
        +Integer det_count
        +String result_overall
        +startAnalysis()
        +validateTask(status)
    }

    class Detection {
        +String det_no
        +String ana_id
        +String label
        +Float bbox_x
        +Float bbox_y
        +Float bbox_w
        +Float bbox_h
        +Float conf
        +String color
        +String hex
        +String pos
    }

    class Scene {
        +String sce_id
        +String ana_id
        +String desc
        +String text
        +generateDescription()
    }

    class AdminController {
        +getOverview()
        +listUsers()
        +updateUserStatus(userId, status)
        +updateUserRole(userId, role)
        +validateAnalysisTask(anaId, status)
        +getServicesStatus()
        +updateModelConfig(conf, iou)
    }

    class YOLOv8Detector {
        +Float conf_threshold
        +Float iou_threshold
        +detect_objects(image)
        +get_detector_config()
        +update_detector_config()
    }

    User "1" --> "1" Profile : owns
    Profile "1" --> "1" CVDProfile : has
    Profile "1" --> "*" Analysis : performs
    Analysis "1" --> "*" Detection : contains
    Analysis "1" --> "1" Scene : generates
    AdminController ..> User : manages
    AdminController ..> Analysis : validates
    AdminController ..> YOLOv8Detector : configures
```

---

## 4. Sequence Diagram (User Analysis & Admin Validation)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as React Frontend
    participant API as FastAPI Gateway
    participant Pipe as Vision Pipeline
    participant DB as SQLite Database
    actor Admin

    User->>UI: Selects & uploads image
    UI->>API: POST /api/analysis/upload (multipart, JWT)
    API->>API: Validate file format (<10MB, JPG/PNG)
    API->>Pipe: run_pipeline(image_bytes)
    Pipe->>Pipe: YOLOv8 Object Detection (Boxes & Labels)
    Pipe->>Pipe: CIELAB L*a*b* Perceptual Colour Extraction
    Pipe->>Pipe: Map 9-Quadrant Position & Context String
    Pipe->>Pipe: Daltonization Matrix Simulation
    Pipe-->>API: Returns detections, colours, scene text
    API->>DB: Store Analysis, Detections, Scene records
    API-->>UI: 200 OK (Analysis payload + image URLs)
    UI->>User: Displays Split Slider & Detected Swatches
    
    opt Voice Audio Feedback
        User->>UI: Clicks "Read Scene Aloud"
        UI->>UI: window.speechSynthesis.speak(sceneText)
    end

    Note over Admin, DB: Administrative Task Validation
    Admin->>UI: Opens Admin Console (/admin)
    UI->>API: GET /api/admin/audit-logs
    API->>DB: Fetch recent user analysis tasks
    DB-->>API: Return task records
    API-->>UI: Display Task Validation Table
    Admin->>UI: Inspects detection and clicks "Approve"
    UI->>API: PATCH /api/admin/analyses/{id}/validate (status: "verified")
    API->>DB: Update analysis status to 'verified'
    DB-->>API: Success
    API-->>UI: Task verified badge updated
```

---

## 5. Component Diagram

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Presentation Layer (React + Vite)"]
        UI_Nav["Sidebar & Navigation"]
        UI_Dash["Accessibility Dashboard"]
        UI_Upload["Upload & Camera Viewport"]
        UI_Results["Split Slider & Swatch Inspector"]
        UI_Admin["Admin Task Management & Validation Console"]
        UI_Speech["Web Speech Synthesis Controller"]
    end

    subgraph APILayer ["FastAPI Routing & Service Layer"]
        R_Auth["/api/auth (Login, Register, JWT)"]
        R_Analysis["/api/analysis (Upload, Results, Reports)"]
        R_Profile["/api/profile (CVD Type, Settings)"]
        R_Admin["/api/admin (Tasks, Users, Models, Health)"]
    end

    subgraph AIEngine ["AI & Computer Vision Subsystem"]
        YOLO_Mod["YOLOv8 Object Detector"]
        Color_Mod["CIELAB Colour Extraction (Delta E)"]
        Signal_Mod["Multi-Zone Traffic Light Analyzer"]
        CVD_Mod["Daltonization CVD Simulator (Machado/Brettel)"]
        OCR_Mod["Tesseract OCR Text Reader"]
    end

    subgraph StorageLayer ["Persistence & Storage Layer"]
        DB_Engine[("SQLite Database (17 Normalized Tables)")]
        File_Store["Local Asset File Store (Uploads & Annotated)"]
    end

    ClientLayer -->|HTTPS / JSON REST| APILayer
    R_Analysis --> AIEngine
    R_Admin --> AIEngine
    APILayer --> StorageLayer
```

---

## 6. Deployment Diagram

```mermaid
flowchart TD
    subgraph ClientDevice ["User & Administrator Client Workstation"]
        Browser["Modern Web Browser (Chrome / Edge / Firefox / Safari)"]
        Audio["Audio Output Device (Speaker / Headphones)"]
        Camera["Built-in Webcam / Smartphone Camera"]
        Browser --> Audio
        Camera --> Browser
    end

    subgraph ServerNode ["Application Server Node"]
        direction TB
        Nginx["Vite Frontend Server / Nginx Reverse Proxy (Port 5173 / 80)"]
        FastAPIApp["Uvicorn ASGI Server - FastAPI Application (Port 8000)"]
        PythonEnv["Python 3.11+ Virtual Environment"]
        
        FastAPIApp --> PythonEnv
        PythonEnv --> TorchLib["PyTorch Runtime & Ultralytics YOLOv8"]
        PythonEnv --> CVLib["OpenCV & NumPy Vision Engine"]
    end

    subgraph StorageNode ["Data & Asset Storage"]
        SQLiteDB[("cvd_assistant.db (SQLite Database)")]
        AssetDir["/storage/uploads & /storage/annotated"]
    end

    Browser -->|HTTP/HTTPS Request| Nginx
    Nginx -->|Proxy API Requests| FastAPIApp
    FastAPIApp --> SQLiteDB
    FastAPIApp --> AssetDir
```

---

## 7. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    USERS ||--|| PROFILES : owns
    PROFILES ||--o| CVD_PROFILES : has
    PROFILES ||--o{ ANALYSES : performs
    ANALYSES ||--o{ DETECTIONS : contains
    ANALYSES ||--o{ SCENES : generates
    ANALYSES ||--o{ REPORTS : generates
    ANALYSES ||--o{ OCR_RESULTS : includes

    USERS {
        string user_id PK
        string first_name
        string last_name
        string email
        string pass_hash
        string role
        datetime created_on
        string status
    }

    PROFILES {
        string pro_id PK
        string user_id FK
        datetime dob
        string gender
        string phone
    }

    CVD_PROFILES {
        string cvd_id PK
        string pro_id FK
        string type
        string severity
        datetime diag_on
    }

    ANALYSES {
        string ana_id PK
        string pro_id FK
        datetime ana_date
        string img_url
        string status
        float comp_time
        int det_count
        string result_overall
    }

    DETECTIONS {
        string det_no PK
        string ana_id FK
        string label
        float bbox_x
        float bbox_y
        float bbox_w
        float bbox_h
        float conf
        string color
        string hex
        string pos
    }

    SCENES {
        string sce_id PK
        string ana_id FK
        string desc
        string text
    }

    REPORTS {
        string rpt_id PK
        string ana_id FK
        string fmt
        string url
        datetime gen_on
    }

    OCR_RESULTS {
        string ocr_id PK
        string ana_id FK
        string text
        float conf
    }
```

---

## 8. State Machine Diagram (Analysis Task Lifecycle)

```mermaid
stateDiagram-v2
    [*] --> Idle : User launches app
    Idle --> Authenticated : Log in with JWT
    Authenticated --> ImageSelected : User selects/captures image
    ImageSelected --> Validating : Upload image
    Validating --> Error : Invalid type or size > 10MB
    Error --> ImageSelected : Retry with valid file
    
    Validating --> Processing : File accepted
    
    state Processing {
        [*] --> DetectingObjects : YOLOv8 forward pass
        DetectingObjects --> ExtractingColors : CIELAB delta-E matching
        ExtractingColors --> SpatialMapping : Compute 9-quadrant position
        SpatialMapping --> SimulatingCVD : Apply Daltonization matrix
        SimulatingCVD --> [*]
    }
    
    Processing --> Completed : Pipeline finished (<3s)
    Completed --> ViewingResults : User reviews split view & swatches
    
    state "Administrative Task Management" as AdminTasks {
        Completed --> PendingAdminReview : Task queued in admin ledger
        PendingAdminReview --> Verified : Admin clicks 'Approve'
        PendingAdminReview --> Flagged : Admin clicks 'Flag'
    }

    ViewingResults --> Authenticated : Navigate to dashboard
    Verified --> [*]
    Flagged --> [*]
```

---

## 9. Package Diagram

```mermaid
flowchart TD
    subgraph FrontendPackage ["frontend/src/"]
        Pages["pages/ (Login, Register, Dashboard, Upload, Results, History, Settings, Admin)"]
        Components["components/ (Sidebar, SplitViewSlider, WardrobeContrastAdvisor, CameraCapture)"]
        APIClient["api/ (http, auth, analysis, profile, stats, admin)"]
        Styles["styles/ (global.css, bootstrap)"]
        
        Pages --> Components
        Pages --> APIClient
        Components --> Styles
    end

    subgraph BackendPackage ["backend/app/"]
        Routers["routers/ (auth.py, analysis.py, profile.py, admin.py)"]
        MLPackage["ml/ (detector.py, color_extract.py, cvd.py, pipeline.py, ocr.py)"]
        DataPackage["models.py, schemas.py, database.py, auth.py"]
        StorageDir["storage/ (uploads/, annotated/)"]

        Routers --> MLPackage
        Routers --> DataPackage
        Routers --> StorageDir
        MLPackage --> StorageDir
    end

    FrontendPackage -->|REST Calls /api/*| BackendPackage
```
