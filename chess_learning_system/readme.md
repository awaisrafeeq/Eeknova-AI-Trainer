# Chess Learning System for Kids 🎮♟️

An educational chess system designed specifically for children (ages 4-12) to learn chess in a fun, interactive, and progressive way. Built with Python and Pygame, this system features gamified learning modules, adaptive difficulty, visual rewards, and comprehensive progress tracking.

## 🌟 Features

### Educational Modules
- **Identify Pieces**: Learn to recognize all chess pieces with visual and audio feedback
- **Board Setup**: Practice proper chess board arrangement
- **Piece Movement Training**: Individual modules for each piece type
  - Pawn Movement Game
  - Rook Movement Drill
  - Knight Jump Challenge
  - Bishop Diagonal Path
  - Queen Combo Moves
  - King and Check Understanding
- **Mini-Match (Pawn Wars)**: Simplified chess variant focusing on pawn strategy
- **Capture the Piece Game**: Learn piece interactions and capturing rules

### Child-Friendly Design
- Large, colorful buttons and UI elements
- Gentle audio feedback (no harsh sounds)
- Visual celebrations and rewards
- Age-appropriate language and instructions
- Break reminders for healthy gaming habits
- Accessibility features

### Adaptive Learning System
- Dynamic difficulty adjustment based on performance
- Personalized learning paths
- Hint system that activates after struggling
- Progress tracking across multiple student profiles
- Achievement and reward system

### Technical Features
- Modular architecture for easy expansion
- Performance optimized for smooth gameplay
- Save/load system for multiple children
- Comprehensive logging for educators/parents
- Placeholder asset generation for development

## 📋 Requirements

- Python 3.7 or higher
- pygame 2.5.2
- numpy 1.24.3
- Pillow 10.0.0
- 100MB free disk space
- 1024x768 minimum screen resolution

## 🚀 Quick Start

### 1. Clone or Download the Project
```bash
git clone https://github.com/yourusername/chess-learning-system.git
cd chess-learning-system
```

### 2. Run the Setup Script
```bash
python setup.py
```

This will:
- Install all required dependencies
- Create the directory structure
- Generate placeholder assets
- Create configuration files
- Test the installation

### 3. Start the Application
```bash
python main.py
```

## 📁 Project Structure

```
chess_learning_system/
├── main.py                 # Entry point
├── setup.py               # Setup script
├── generate_assets.py     # Asset generator
├── README.md             # This file
├── config.ini            # Configuration
│
├── assets/               # Game assets
│   ├── images/
│   │   ├── pieces/      # Chess piece images
│   │   ├── backgrounds/ # Background images
│   │   └── ui/         # UI elements
│   ├── sounds/
│   │   ├── feedback/   # Sound effects
│   │   └── music/      # Background music
│   └── fonts/          # Custom fonts
│
├── data/                # User data
│   └── profiles/       # Student profiles
│
└── src/                 # Source code
    ├── core/           # Core engine components
    ├── modules/        # Learning modules
    ├── states/         # Game states
    ├── ui/            # UI components
    ├── education/     # Educational systems
    ├── chess/         # Chess logic
    ├── audio/         # Audio management
    └── utils/         # Utilities
```

## 🎮 How to Use

### For Children

1. **Start the Game**: Click "Start Learning" on the welcome screen
2. **Choose a Module**: Select from available learning activities
3. **Follow Instructions**: Each module has clear, simple instructions
4. **Earn Stars**: Complete activities to earn stars and unlock new modules
5. **Take Breaks**: The system will remind you to take breaks every 15 minutes

### For Parents/Educators

1. **Create Profiles**: Set up individual profiles for each child
2. **Monitor Progress**: Check the progress tracking to see improvement
3. **Adjust Settings**: Customize difficulty, hint frequency, and session length
4. **View Analytics**: See detailed learning analytics and areas needing attention

## ⚙️ Configuration

Edit `config.ini` to customize:

```ini
[Display]
width = 1024
height = 768
fullscreen = false

[Audio]
master_volume = 0.8
music_volume = 0.6

[Education]
hint_delay = 5.0
break_reminder_minutes = 15
```

## 🔧 Development

### Adding New Modules

1. Create a new directory in `src/modules/your_module/`
2. Implement the module state in `src/states/your_module_state.py`
3. Register the state in `game_engine.py`
4. Add module info to `main_menu_state.py`

### Creating Custom Assets

Replace placeholder assets in the `assets/` directory with your own:
- Images: PNG format, appropriate sizes
- Sounds: WAV for effects, OGG for music
- Fonts: TTF format

### Architecture Overview

The system uses:
- **MVC Pattern**: Separation of game logic, state management, and rendering
- **State Machine**: Clean state transitions between modules
- **Event System**: Decoupled communication between components
- **Resource Manager**: Efficient asset loading and caching

## 🐛 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure you're running from the project root directory
   - Check that all dependencies are installed: `pip install -r requirements.txt`

2. **No sound playing**
   - Check system volume settings
   - Verify audio files exist in `assets/sounds/`
   - Try reinitializing pygame mixer

3. **Performance issues**
   - Lower the FPS in config.ini
   - Reduce visual effects in settings
   - Close other applications

4. **Assets not loading**
   - Run `python generate_assets.py` to regenerate placeholders
   - Check file paths in `config.py`

## 📈 Progress Tracking

The system tracks:
- Individual module completion and mastery
- Time spent learning
- Accuracy and improvement trends
- Favorite activities
- Achievement unlocks
- Areas needing additional practice

Data is stored locally in `data/profiles/` as JSON files.

## 🎨 Customization

### Visual Themes
Modify colors in `src/core/config.py`:
```python
COLORS = {
    'primary': (52, 152, 219),
    'secondary': (46, 204, 113),
    # ... etc
}
```

### Difficulty Levels
Adjust in module configurations:
```python
MODULES = {
    'identify_pieces': {
        'questions_per_session': 10,
        'hint_after_attempts': 2,
    }
}
```

## 🤝 Contributing

We welcome contributions! Areas where help is needed:
- Real audio asset creation
- Additional learning modules
- Language translations
- Accessibility improvements
- Educational content writing

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Chess piece movement rules from standard FIDE regulations
- Educational methodology based on child development research
- UI/UX principles adapted from children's software design guidelines

## 📞 Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Email: support@chessforkids.example.com
- Documentation: [Wiki Link]

---

**Happy Learning! May every child discover the joy of chess through play.** ♟️✨