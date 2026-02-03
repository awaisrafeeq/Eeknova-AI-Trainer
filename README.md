# Eeknova AI Trainer - Complete Zumba Integration

## 🎯 Project Overview
Advanced AI-powered fitness trainer with real-time Zumba dance analysis, pose detection, and personalized feedback.

## 🚀 Features

### ✅ Completed Features
- **Real-time Zumba Pose Detection** using YOLO models
- **WebSocket Communication** for low-latency analysis
- **Multi-Module Support**: Yoga, Chess, Zumba
- **Performance Optimized** for integrated GPUs
- **React Frontend** with TypeScript
- **FastAPI Backend** with Python
- **Session Management** with detailed analytics

### 🎮 Zumba Module Features
- **30 FPS Camera Capture** with optimized processing
- **Real-time Feedback Generation** 
- **Pose Accuracy Tracking**
- **Movement Analysis** with joint-specific corrections
- **Session Summaries** with performance metrics
- **Skeleton Visualization** (testing enabled)

## 🖥️ Technology Stack

### Frontend
- **React 18** with TypeScript
- **TailwindCSS** for styling
- **WebSocket Client** for real-time communication
- **HTML5 Canvas** for video processing

### Backend
- **FastAPI** (Python 3.11)
- **WebSocket Server** for real-time communication
- **OpenCV** for computer vision
- **YOLO Pose Detection** models
- **NumPy** for data processing

### AI/ML
- **GuidedZumbaAnalyzer** for pose analysis
- **Real-time Feedback Generation**
- **Angle Calculation** and movement comparison
- **Reference-based Analysis** with 10+ Zumba moves

### 🔐 Authentication System
- **JWT-based authentication** with secure token management
- **User registration and login** with password hashing
- **Profile management** with fitness tracking
- **Protected routes** with automatic redirect

### 📱 Training Modules
- **Yoga**: Real-time AI pose analysis and correction feedback
- **Zumba**: Dance fitness with rhythm tracking
- **Chess**: Mental fitness with strategic games
- **Dashboard**: Progress tracking and analytics
- **Settings**: User profile and preferences management

### 🎯 Interactive Walktour
- **First-time user guidance** with popup tutorials
- **Module overviews** with detailed descriptions
- **Skip/Next navigation** for user control
- **LocalStorage persistence** to track tour completion

### 🎨 Modern UI/UX
- **Glassmorphic design** with beautiful gradients
- **Responsive layout** for all screen sizes
- **Smooth animations** and transitions
- **Dark theme** with neon accents

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## 🛠️ Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd yoga_project
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the FastAPI server:
```bash
python main.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the Next.js development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 🔗 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user profile
- `PUT /api/auth/profile` - Update user profile

### Yoga Analysis
- `POST /api/session/start` - Start pose analysis session
- `POST /api/analyze-frame` - Analyze single frame
- `GET /api/poses/available` - Get supported poses
- `GET /api/model/status` - Check model status

### WebSocket
- `WS /ws/pose-analysis` - Real-time pose analysis

## 🧪 Testing

### Authentication Test
Run the authentication test script to verify JWT functionality:
```bash
cd yoga_project
python test_auth.py
```

### Manual Testing
1. Open `http://localhost:3000/auth` in your browser
2. Register a new account
3. Login with your credentials
4. Experience the interactive walktour
5. Explore all modules and settings

## 📁 Project Structure

```
yoga_project/
├── main.py                 # FastAPI backend with JWT auth
├── requirements.txt        # Python dependencies
├── test_auth.py           # Authentication test script
└── ...                    # ML models and pose analysis files

frontend/
├── src/
│   ├── app/
│   │   ├── auth/          # Login/registration page
│   │   ├── settings/      # User profile settings
│   │   ├── module-selection/ # Main dashboard with walktour
│   │   └── ...           # Other module pages
│   └── components/
│       ├── Walktour.tsx   # Interactive tour component
│       ├── AuthGuard.tsx  # Route protection
│       ├── Icons.tsx      # UI icons
│       └── Avatar3D.tsx   # 3D avatar component
├── package.json          # Node.js dependencies
└── ...                   # Next.js configuration
```

## 🔧 Configuration

### Backend Configuration
- `SECRET_KEY`: Change the JWT secret key in production
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Adjust token expiration time
- Database: Currently uses in-memory storage (upgrade to PostgreSQL/MySQL for production)

### Frontend Configuration
- API endpoints configured for `localhost:8000`
- CSS variables defined in `globals.css`
- AuthGuard protects all authenticated routes

## 🚀 Deployment

### Backend Deployment
```bash
# Production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Deployment
```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **Backend not starting**: Check Python version and dependencies
2. **Frontend build errors**: Verify Node.js version and clear npm cache
3. **Authentication not working**: Ensure backend is running and CORS is configured
4. **Walktour not showing**: Clear localStorage and refresh page

### Debug Commands
```bash
# Backend logs
python main.py --log-level debug

# Frontend development mode
npm run dev -- --verbose

# Clear npm cache
npm cache clean --force
```

## 📞 Support

For support and questions, please open an issue in the repository or contact the development team.

---

**Built with ❤️ using FastAPI, Next.js, and modern web technologies**
