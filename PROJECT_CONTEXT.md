# Eeknova AI Trainer - Complete Project Context

## Project Overview

**Eeknova AI Trainer** is a multi-module fitness and learning platform with AI-powered features. The project consists of:
- **Backend**: FastAPI (Python) - Yoga pose detection, Chess learning, Zumba
- **Frontend**: Next.js 16 (React 19 + TypeScript) - Web interface
- **Database**: SQLite for user data, sessions, and progress tracking

## Technology Stack

### Backend
- **Framework**: FastAPI with WebSocket support
- **AI/ML**: YOLOv11 for pose detection, MediaPipe for skeleton analysis
- **Authentication**: JWT tokens with bcrypt
- **Database**: SQLite (yoga_users.db, database.db)
- **Port**: 8002 (updated from 8000)

### Frontend
- **Framework**: Next.js 16.0.0 with App Router
- **UI Library**: React 19.2.0
- **Styling**: Tailwind CSS 4
- **3D Rendering**: Three.js + React Three Fiber (@react-three/fiber 9.4.0)
- **Animations**: Framer Motion 12.23.24
- **Icons**: Lucide React
- **Port**: 3000

---

## Project Structure

```
e:\nalla/
├── README.md                          # Project setup instructions
├── .gitignore                         # Git ignore rules
├── .gitattributes                     # Git LFS settings
├── yoga_users.db                      # SQLite database (user data)
│
├── yoga_project/                      # BACKEND - FastAPI
│   ├── main.py                        # Main FastAPI app (1347 lines) - All APIs and WebSocket
│   ├── database.py                    # Database operations (31801 bytes)
│   ├── Yoga_pose_estimation_YOLO.py   # YOLO pose detection (99KB)
│   ├── Yoga_pose_estimation_mediapipe.py # MediaPipe fallback (94KB)
│   ├── requirements.txt               # Python dependencies
│   ├── angles_final.pkl               # Pose angle data
│   ├── pose correction.pkl            # Pose correction ML model (4.6MB)
│   ├── yoga_instructions.json         # Yoga pose instructions
│   ├── yoga_instructions.py           # Instruction generation
│   ├── chess_api.py                   # Chess learning APIs
│   ├── chess_engine.py                # Chess game engine
│   ├── zumba_processor.py             # Zumba dance processing
│   ├── database.db                    # SQLite database
│   ├── models/                        # ML models folder
│   └── api/                           # Additional API modules
│
├── frontend/                          # FRONTEND - Next.js
│   ├── package.json                   # Node dependencies
│   ├── next.config.js                 # Next.js configuration
│   ├── tsconfig.json                  # TypeScript config
│   ├── .env.local                     # Environment variables
│   ├── README.md                      # Frontend docs
│   │
│   ├── public/                        # Static assets (81 items)
│   │   ├── animations/                # 3D avatar animations
│   │   ├── poses/                     # Yoga pose images
│   │   ├── warm-up/                   # Warm-up animation files
│   │   └── cool-down/                 # Cool-down animation files
│   │
│   └── src/                           # Source code
│       ├── app/                       # Next.js App Router
│       │   ├── layout.tsx             # Root layout (with AssistantShell)
│       │   ├── page.tsx               # Landing page
│       │   ├── globals.css            # Global styles
│       │   │
│       │   ├── yoga/
│       │   │   └── page.tsx           # YOGA MODULE (1538 lines) - Main yoga interface
│       │   ├── chess/
│       │   │   ├── page.tsx           # Chess learning module
│       │   │   └── page_backup.tsx    # Chess backup
│       │   ├── zumba/
│       │   │   └── page.tsx           # Zumba dance module
│       │   ├── dashboard/
│       │   │   └── page.tsx           # User dashboard
│       │   ├── module-selection/
│       │   │   └── page.tsx           # Module selection screen
│       │   ├── auth/
│       │   │   └── page.tsx           # Authentication page
│       │   ├── settings/
│       │   │   └── page.tsx           # User settings
│       │   └── api/                   # API routes
│       │       └── auth/
│       │           └── me/
│       │               └── route.ts     # Auth API route
│       │
│       ├── components/                # React components
│       │   ├── Avatar3D.tsx          # 3D avatar component (Three.js)
│       │   ├── YogaCamera.tsx         # Webcam pose detection
│       │   ├── ZumbaCamera.tsx        # Zumba camera component
│       │   ├── EnhancedChessBoard.tsx # Chess board UI
│       │   ├── AssistantShell.tsx     # AI assistant overlay
│       │   ├── AuthGuard.tsx          # Route protection
│       │   ├── HttpPoseDetection.tsx  # HTTP-based pose detection
│       │   ├── Icons.tsx              # Custom icons
│       │   └── Walktour.tsx           # Onboarding tour
│       │
│       ├── lib/                       # Utility libraries
│       │   ├── auth.ts                # Authentication utilities
│       │   ├── yogaApi.ts             # Yoga API client (605 lines)
│       │   ├── chessApi.ts            # Chess API client
│       │   ├── chessFrontendTypes.ts  # Chess type definitions
│       │   └── zumbaApi.ts            # Zumba API client
│       │
│       ├── hooks/                     # Custom React hooks
│       │   └── useAuth.ts             # Auth hook
│       │
│       ├── contexts/                  # React contexts
│       │   └── AuthContext.tsx        # Auth context provider
│       │
│       ├── middleware.ts              # Next.js middleware (auth)
│       └── config/                    # Configuration files
│
├── Zumba/                             # ZUMBA MODULE
│   └── feedback_generation_real_time/
│       ├── main.py                    # Zumba main processor
│       ├── feedback_processor.py      # Feedback generation
│       ├── skeleton_processor.py      # Skeleton analysis
│       ├── yolo11x-pose.pt            # YOLO model (118MB)
│       └── src/                       # Source modules
│
└── chess_learning_system/             # CHESS MODULE (84 items)
    ├── main.py                        # Chess learning main
    ├── chess_api.py                   # Chess API
    ├── generate_assets.py             # Asset generation
    ├── assets/                        # Chess assets (sounds, images)
    │   └── sounds/
    │       └── music/                 # Background music
    ├── requirements.txt               # Dependencies
    └── readme.md                      # Chess module docs
```

---

## Key Files - Detailed Description

### Backend Files (yoga_project/)

| File | Description | Key Data/Functions |
|------|-------------|-------------------|
| **main.py** | Main FastAPI application | All REST APIs, WebSocket endpoints, JWT auth, pose analysis integration |
| **database.py** | Database operations | SQLite CRUD, user management, session tracking, progress stats |
| **Yoga_pose_estimation_YOLO.py** | YOLO pose detection | YOLO model loading, angle calculation, pose comparison, feedback generation |
| **database.db** | SQLite database | Users, sessions, poses, progress data |
| **pose correction.pkl** | ML model | Trained model for pose correction feedback (4.6MB) |
| **angles_final.pkl** | Reference data | Ground truth angles for yoga poses |
| **chess_api.py** | Chess backend | Chess progress tracking, lesson management |
| **zumba_processor.py** | Zumba backend | Dance analysis, feedback generation |

### Frontend Files (frontend/src/)

#### Core Application Files

| File | Description | Key Data/Functions |
|------|-------------|-------------------|
| **app/layout.tsx** | Root layout | Geist fonts, global providers, AssistantShell integration |
| **app/page.tsx** | Landing page | Home screen, module navigation |
| **app/globals.css** | Global styles | CSS variables, dark theme, Tailwind base |
| **middleware.ts** | Route middleware | JWT validation, protected routes |

#### Module Pages

| File | Description | Key Data/Functions |
|------|-------------|-------------------|
| **app/yoga/page.tsx** | Yoga module (1538 lines) | Main yoga interface, session management, Avatar3D integration, timer, phases (setup/warmup/pose/release/cooldown), TTS integration |
| **app/chess/page.tsx** | Chess module | Chess learning interface, game board |
| **app/zumba/page.tsx** | Zumba module | Dance workout interface |
| **app/dashboard/page.tsx** | Dashboard | User stats, progress overview, streak display |
| **app/auth/page.tsx** | Authentication | Login/register forms |
| **app/module-selection/page.tsx** | Module picker | Yoga/Chess/Zumba selection |
| **app/settings/page.tsx** | Settings | User preferences |

#### Components

| File | Description | Key Data/Functions |
|------|-------------|-------------------|
| **components/Avatar3D.tsx** | 3D Avatar | Three.js canvas, GLB model loading, animation sequencing (IN/MAIN/OUT), camera control |
| **components/YogaCamera.tsx** | Pose detection | Webcam integration, real-time analysis, WebSocket communication |
| **components/ZumbaCamera.tsx** | Zumba camera | Dance analysis, feedback display |
| **components/EnhancedChessBoard.tsx** | Chess board | Interactive chess UI, move validation |
| **components/AssistantShell.tsx** | AI Assistant | Floating chat interface |
| **components/AuthGuard.tsx** | Route guard | Authentication protection |

#### API Libraries

| File | Description | Key Data/Functions |
|------|-------------|-------------------|
| **lib/yogaApi.ts** | Yoga API client | Session management, pose analysis, WebSocket connection (port 8002) |
| **lib/chessApi.ts** | Chess API client | Chess progress, lessons |
| **lib/zumbaApi.ts** | Zumba API client | Dance sessions, feedback |
| **lib/auth.ts** | Auth utilities | Token management, JWT handling, localStorage/cookie sync |
| **lib/chessFrontendTypes.ts** | Type definitions | Chess-specific TypeScript interfaces |

#### Contexts & Hooks

| File | Description | Key Data/Functions |
|------|-------------|-------------------|
| **contexts/AuthContext.tsx** | Auth state | Global authentication state, user data |
| **hooks/useAuth.ts** | Auth hook | useAuth hook for components |

---

## Yoga Module - Detailed Architecture

### Flow Stages (flowStage state)
1. **setup** - Pose selection, session configuration
2. **warmup** - Warm-up animations (4 steps)
3. **instructions** - Initial TTS instructions
4. **pose** - Main pose session with detection
5. **release** - Exit TTS instructions
6. **cooldown** - Cool-down animations (3 steps)

### Key State Variables (Yoga Page)
- `isSessionStarted` - Session active flag
- `flowStage` - Current stage in flow
- `currentPhase` - IN/hold/OUT phase
- `timeLeft` - Session timer
- `currentAccuracy` - Pose accuracy percentage
- `corrections` - Feedback messages
- `isPortraitDisplay` - Responsive layout mode
- `isStageTransitioning` - Animation transition flag

### Avatar3D Props
- `selectedPose` - Current yoga pose name
- `playAnimationPath` - Path to animation file
- `staticMode` - Static vs animated display
- `cameraZoom` - Camera zoom level (pose-specific)
- `cameraTargetYOffset` - Vertical camera offset
- `onlyInAnimation` - Play only IN animation
- `onlyOutAnimation` - Play only OUT animation
- `onPhaseChange` - Phase change callback
- `onSessionEnd` - Session end callback

### Animation Folders
- `/public/animations/` - Pose animations (IN/MAIN/OUT)
- `/public/warm-up/` - Warm-up animations
- `/public/cool-down/` - Cool-down animations

---

## Database Schema (SQLite)

### Tables
- **users** - User accounts (id, email, password_hash, name, created_at)
- **yoga_sessions** - Session history (id, user_id, pose_name, duration, accuracy, timestamp)
- **yoga_streaks** - Streak tracking (user_id, current_streak, last_yoga_date)
- **chess_progress** - Chess learning (user_id, level, completed_lessons)
- **zumba_progress** - Zumba progress (user_id, sessions_completed)
- **yoga_instructions** - Pose instructions (pose_name, instruction_text)

---

## API Endpoints (Backend)

### REST Endpoints
```
POST   /auth/register
POST   /auth/login
GET    /auth/me
POST   /yoga/session/start
POST   /yoga/session/end
GET    /yoga/dashboard
GET    /yoga/stats
GET    /chess/progress
POST   /chess/progress/update
GET    /zumba/progress
```

### WebSocket Endpoints
```
WS     /yoga/ws/analyze      - Real-time pose analysis
WS     /yoga/ws/camera      - Camera feed processing
```

---

## Environment Variables

### Backend (.env)
```
PORT=8002
DATABASE_URL=sqlite:///./yoga_users.db
JWT_SECRET=your-secret-key
OPENAI_API_KEY=optional-for-tts
```

### Frontend (.env.local)
```
NEXT_PUBLIC_YOGA_API_URL=http://localhost:8002
NEXT_PUBLIC_YOGA_WS_URL=ws://localhost:8002
OPENAI_API_KEY=your-key-here
```

---

## Recent Changes (Yoga Timer Fixes Branch)

### Completed Features
1. **Backend port updated** from 8000 → 8002
2. **Timer behavior** - Only shows during MAIN (hold) phase
3. **TTS integration** - Abort feedback when transitioning to release
4. **Session end** - Wait for TTS completion before ending
5. **Transparent background** during yoga session
6. **Avatar sizing** - Consistent size across all states
7. **Warm-up/Cool-down** - 4-step warm-up, 3-step cool-down integration
8. **UI Layout** - Avatar left + content right in setup, centered during session

### Key Files Modified
- `yoga_project/main.py` - Backend APIs
- `frontend/src/app/yoga/page.tsx` - Main yoga UI
- `frontend/src/app/api/auth/me/route.ts` - Auth port update
- `frontend/src/components/Avatar3D.tsx` - Avatar component

---

## Assets and Models

### 3D Models
- **Avatar GLB** - `/public/avatar/` - 3D character model with animations
- **Pose Animations** - `/public/animations/` - IN/MAIN/OUT sequences per pose

### ML Models
- **YOLO** - `yoga_project/yolo11x-pose.pt` (118MB) - Pose detection
- **Pose Correction** - `yoga_project/pose correction.pkl` (4.6MB) - Feedback model

### Chess Assets
- **Sounds** - `/chess_learning_system/assets/sounds/music/` - Background themes

---

## Git Repository

- **URL**: https://github.com/awaisrafeeq/Eeknova-AI-Trainer.git
- **Branch**: `yoga-timer-fixes` (current working branch)
- **Main Branch**: `main`

---

## Notes for Claude

1. **Yoga Page** is the most complex file (1538 lines) - handles all yoga flow states
2. **Avatar3D** uses Three.js and requires GLB animation files
3. **Backend uses port 8002** - updated from original 8000
4. **Authentication** uses JWT with localStorage + cookies
5. **WebSocket** used for real-time pose analysis
6. **Warm-up/Cool-down** integrated into session flow before IN and after OUT
7. **All modules** (Yoga, Chess, Zumba) share the same authentication system
