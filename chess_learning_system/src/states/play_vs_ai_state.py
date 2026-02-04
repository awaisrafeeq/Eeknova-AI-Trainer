# ai_chess_game_state_professional.py - Professional UI Version
# Enhanced with modern, professional styling matching other modules

import pygame
import sys
import threading
import queue
import time
import math

# Import the chess engine and AI from the same directory
try:
    from . import engine as ChessEngine
    from . import chessAi as ChessAI
except ImportError:
    # Fallback for direct execution
    import engine as ChessEngine
    import chessAi as ChessAI

# Try to import your base state class
try:
    from src.core.state_machine import BaseState
    from src.core.state_machine import GameState as ProjectGameState
except ImportError:
    # Fallback minimal base state
    class BaseState:
        def __init__(self, engine):
            self.engine = engine
            self.config = getattr(engine, 'config', None)
        def enter(self): pass
        def update(self, dt): pass
        def render(self, screen): pass
        def handle_event(self, event): pass
        def exit(self): pass
    
    class ProjectGameState:
        MAIN_MENU = 'main_menu'


class ProfessionalButton:
    """Professional styled button for the chess game"""
    
    def __init__(self, text, pos, size, callback, config, button_type='primary'):
        self.text = text
        self.pos = pos
        self.size = size
        self.callback = callback
        self.config = config
        self.button_type = button_type
        
        self.rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self.is_hovered = False
        self.is_pressed = False
        
        # Professional color schemes
        if button_type == 'primary':
            self.base_color = getattr(config, 'COLORS', {}).get('primary', (52, 152, 219))
            self.text_color = (255, 255, 255)
        elif button_type == 'secondary':
            self.base_color = getattr(config, 'COLORS', {}).get('secondary', (46, 204, 113))
            self.text_color = (255, 255, 255)
        elif button_type == 'danger':
            self.base_color = getattr(config, 'COLORS', {}).get('danger', (231, 76, 60))
            self.text_color = (255, 255, 255)
        elif button_type == 'info':
            self.base_color = (149, 165, 166)
            self.text_color = (255, 255, 255)
        else:
            self.base_color = (127, 140, 141)
            self.text_color = (255, 255, 255)
        
        self.hover_color = self._brighten_color(self.base_color, 1.2)
        self.pressed_color = self._darken_color(self.base_color, 0.8)
        
        # Font
        self.font = pygame.font.Font(None, 20)
    
    def _brighten_color(self, color, factor):
        return tuple(min(255, int(c * factor)) for c in color)
    
    def _darken_color(self, color, factor):
        return tuple(int(c * factor) for c in color)
    
    def update(self, dt, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.is_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_pressed and self.is_hovered:
                self.callback()
            self.is_pressed = False
    
    def render(self, screen):
        # Determine current color
        if self.is_pressed:
            color = self.pressed_color
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.base_color
        
        # Draw button with modern styling
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        
        # Add subtle shadow effect
        shadow_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 2, self.rect.width, self.rect.height)
        shadow_color = (0, 0, 0, 50)
        shadow_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, shadow_color, (0, 0, self.rect.width, self.rect.height), border_radius=8)
        screen.blit(shadow_surface, (shadow_rect.x, shadow_rect.y))
        
        # Draw main button
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        
        # Add border
        border_color = self._darken_color(color, 0.7)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=8)
        
        # Add inner highlight for 3D effect
        if not self.is_pressed:
            highlight_rect = pygame.Rect(self.rect.x + 1, self.rect.y + 1, self.rect.width - 2, self.rect.height // 3)
            highlight_color = self._brighten_color(color, 1.3)
            highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(highlight_surface, (*highlight_color, 80), (0, 0, highlight_rect.width, highlight_rect.height), border_radius=6)
            screen.blit(highlight_surface, highlight_rect.topleft)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class StatusPanel:
    """Professional status panel for game information"""
    
    def __init__(self, pos, size, config):
        self.pos = pos
        self.size = size
        self.config = config
        self.rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 28)
    
    def render(self, screen, title, content_lines, panel_type='info'):
        # Color scheme based on panel type
        if panel_type == 'info':
            bg_color = (236, 240, 241)
            border_color = (189, 195, 199)
            title_color = (44, 62, 80)
            text_color = (52, 73, 94)
        elif panel_type == 'warning':
            bg_color = (254, 249, 231)
            border_color = (241, 196, 15)
            title_color = (243, 156, 18)
            text_color = (212, 172, 13)
        elif panel_type == 'success':
            bg_color = (232, 248, 245)
            border_color = (26, 188, 156)
            title_color = (22, 160, 133)
            text_color = (22, 160, 133)
        elif panel_type == 'danger':
            bg_color = (253, 237, 236)
            border_color = (231, 76, 60)
            title_color = (192, 57, 43)
            text_color = (192, 57, 43)
        else:
            bg_color = (236, 240, 241)
            border_color = (189, 195, 199)
            title_color = (44, 62, 80)
            text_color = (52, 73, 94)
        
        # Draw panel background
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=10)
        
        # Draw title
        title_surface = self.title_font.render(title, True, title_color)
        title_rect = title_surface.get_rect(centerx=self.rect.centerx, top=self.rect.top + 10)
        screen.blit(title_surface, title_rect)
        
        # Draw content lines
        y_offset = title_rect.bottom + 15
        for line in content_lines:
            line_surface = self.font.render(line, True, text_color)
            line_rect = line_surface.get_rect(centerx=self.rect.centerx, top=y_offset)
            screen.blit(line_surface, line_rect)
            y_offset += 25


class AIChessGameState(BaseState):
    """
    Professional AI Chess Game with Enhanced UI
    """
    
    def __init__(self, engine):
        super().__init__(engine)
        
        # Original GitHub repo settings
        self.BOARD_WIDTH = self.BOARD_HEIGHT = 500
        self.MOVE_LOG_PANEL_WIDTH = 280
        self.MOVE_LOG_PANEL_HEIGHT = self.BOARD_HEIGHT
        self.DIMENSION = 8
        self.SQ_SIZE = self.BOARD_HEIGHT // self.DIMENSION
        self.MAX_FPS = 15
        
        # Enhanced UI positioning
        self.BOARD_OFFSET_X = 50
        self.BOARD_OFFSET_Y = 120
        
        # Game state variables
        self.gs = None
        self.validMoves = []
        self.moveMade = False
        self.animate = False
        self.gameOver = False
        
        # Player configuration
        self.playerOne = True   # True = Human, False = AI for White
        self.playerTwo = False  # True = Human, False = AI for Black
        
        # Move selection
        self.sqSelected = ()
        self.playerClicks = []
        
        # AI state management - FIXED VERSION
        self.ai_thinking = False
        self.ai_move_ready = False
        self.ai_move = None
        self.ai_thinking_start_time = 0
        self.min_ai_think_time = 1.0  # Minimum 1 second thinking time
        self.ai_thread = None
        self.move_queue = queue.Queue()
        
        # Images and fonts
        self.images = {}
        
        # Professional board colors (matching other modules)
        self.light_square_color = (240, 217, 181)  # Light squares
        self.dark_square_color = (181, 136, 99)    # Dark squares
        self.highlight_color = (255, 255, 100)     # Yellow highlight
        self.selected_color = (100, 149, 237)      # Blue selection
        self.valid_move_color = (144, 238, 144)    # Light green for valid moves
        
        # UI elements
        self.status_panel = None
        self.move_log_panel = None
        self.buttons = {}
        
        # Animation and effects
        self.board_animation_offset = 0
        self.title_glow = 0
        
        # Debug info
        self.debug_info = ""
    
    def enter(self):
        """Initialize the chess game with professional styling"""
        super().enter()
        
        print("=== Professional AI Chess Game Starting ===")
        
        # Initialize game state
        self.gs = ChessEngine.GameState()
        self.validMoves = self.gs.getValidMoves()
        self.moveMade = False
        self.animate = False
        self.gameOver = False
        
        # Reset player selections
        self.sqSelected = ()
        self.playerClicks = []
        
        # Reset AI state - IMPORTANT
        self.ai_thinking = False
        self.ai_move_ready = False
        self.ai_move = None
        self.ai_thinking_start_time = 0
        
        # Clean up any existing AI thread
        if self.ai_thread is not None and self.ai_thread.is_alive():
            self.ai_thread.join(timeout=1.0)
        self.ai_thread = None
        
        # Clear move queue
        while not self.move_queue.empty():
            try:
                self.move_queue.get_nowait()
            except queue.Empty:
                break
        
        # Load game resources
        self.loadImages()
        self.loadFonts()
        self.createUIElements()
        
        print(f"White: {'Human' if self.playerOne else 'AI'}")
        print(f"Black: {'Human' if self.playerTwo else 'AI'}")
        print("=== Professional Game Ready ===")
    
    def loadFonts(self):
        """Load professional fonts"""
        try:
            self.title_font = pygame.font.Font(None, 48)
            self.subtitle_font = pygame.font.Font(None, 32)
            self.instruction_font = pygame.font.Font(None, 24)
            self.info_font = pygame.font.Font(None, 20)
            self.small_font = pygame.font.Font(None, 16)
        except:
            self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
            self.subtitle_font = pygame.font.SysFont('Arial', 32)
            self.instruction_font = pygame.font.SysFont('Arial', 24)
            self.info_font = pygame.font.SysFont('Arial', 20)
            self.small_font = pygame.font.SysFont('Arial', 16)
    
    def createUIElements(self):
        """Create professional UI elements"""
        # Status panel
        self.status_panel = StatusPanel(
            (self.BOARD_OFFSET_X + self.BOARD_WIDTH + 20, self.BOARD_OFFSET_Y),
            (250, 150),
            self.config
        )
        
        # Move log panel
        self.move_log_panel = StatusPanel(
            (self.BOARD_OFFSET_X + self.BOARD_WIDTH + 20, self.BOARD_OFFSET_Y + 170),
            (250, 320),
            self.config
        )
        
        # Create professional buttons
        button_y = 60
        button_spacing = 90
        
        self.buttons = {
            'back': ProfessionalButton(
                "← Back", (20, 60), (80, 35), self.goBack, self.config, 'info'
            ),
            'reset': ProfessionalButton(
                "Reset Game", (120, 60), (100, 35), self.resetGame, self.config, 'danger'
            ),
            'undo': ProfessionalButton(
                "Undo Move", (245, 60), (90, 35), self.undoMove, self.config, 'secondary'
            ),
            'human_vs_ai': ProfessionalButton(
                "Human vs AI", (850, button_y +50), (120, 40), 
                 lambda: self.setPlayers(True, False), self.config, 'primary'
            ),
            'ai_vs_ai': ProfessionalButton(
               "AI vs AI", (850, button_y +100 ), (120, 40), 
               lambda: self.setPlayers(False, False), self.config, 'primary'
            ),
            'human_vs_human': ProfessionalButton(
               "Human vs Human", (850, button_y +150), (120, 40), 
               lambda: self.setPlayers(True, True), self.config, 'primary'
            )
        }
    
    def loadImages(self):
        """Load chess piece images with professional styling"""
        pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
        for piece in pieces:
            try:
                if hasattr(self.engine, 'resource_manager'):
                    color = 'white' if piece[0] == 'w' else 'black'
                    piece_type = piece[1].lower()
                    if piece_type == 'p': piece_type = 'pawn'
                    elif piece_type == 'r': piece_type = 'rook'
                    elif piece_type == 'n': piece_type = 'knight'
                    elif piece_type == 'b': piece_type = 'bishop'
                    elif piece_type == 'q': piece_type = 'queen'
                    elif piece_type == 'k': piece_type = 'king'
                    
                    self.images[piece] = self.engine.resource_manager.load_piece_image(
                        piece_type, color, (self.SQ_SIZE - 8, self.SQ_SIZE - 8)
                    )
                else:
                    raise AttributeError("No resource manager")
            except:
                self.images[piece] = self.createProfessionalPieceImage(piece)
    
    def createProfessionalPieceImage(self, piece):
        """Create professional piece image using text with shadow"""
        surface = pygame.Surface((self.SQ_SIZE, self.SQ_SIZE), pygame.SRCALPHA)
        
        piece_symbols = {
            'wp': '♙', 'wR': '♖', 'wN': '♘', 'wB': '♗', 'wQ': '♕', 'wK': '♔',
            'bp': '♟', 'bR': '♜', 'bN': '♞', 'bB': '♝', 'bQ': '♛', 'bK': '♚'
        }
        
        font = pygame.font.Font(None, int(self.SQ_SIZE * 0.8))
        symbol = piece_symbols.get(piece, piece)
        
        # Create shadow
        shadow_color = (0, 0, 0, 100)
        shadow_surface = font.render(symbol, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(center=(self.SQ_SIZE//2 + 2, self.SQ_SIZE//2 + 2))
        
        # Create main piece
        main_color = (255, 255, 255) if piece[0] == 'w' else (50, 50, 50)
        main_surface = font.render(symbol, True, main_color)
        main_rect = main_surface.get_rect(center=(self.SQ_SIZE//2, self.SQ_SIZE//2))
        
        # Composite the piece
        surface.blit(shadow_surface, shadow_rect)
        surface.blit(main_surface, main_rect)
        
        return surface
    
    def ai_worker(self, game_state_copy, valid_moves_copy):
        """AI worker function that runs in separate thread"""
        try:
            print(f"AI worker started for {'White' if game_state_copy.whiteToMove else 'Black'}")
            
            # Use the AI to find the best move
            best_move = ChessAI.findBestMove(game_state_copy, valid_moves_copy, None)
            
            if best_move is None:
                # Fallback to random move
                if len(valid_moves_copy) > 0:
                    best_move = ChessAI.findRandomMove(valid_moves_copy)
            
            print(f"AI worker found move: {best_move}")
            
            # Put the move in the queue
            self.move_queue.put(best_move)
            
        except Exception as e:
            print(f"AI worker error: {e}")
            self.move_queue.put(None)
    
    def start_ai_thinking(self):
        """Start AI thinking process - FIXED VERSION"""
        if self.ai_thinking or self.gameOver:
            return
        
        current_player = "White" if self.gs.whiteToMove else "Black"
        print(f"Starting AI thinking for {current_player}")
        
        # Set AI thinking state
        self.ai_thinking = True
        self.ai_move_ready = False
        self.ai_move = None
        self.ai_thinking_start_time = time.time()
        self.debug_info = f"AI ({current_player}) thinking..."
        
        # Create a copy of the game state for the AI thread
        gs_copy = ChessEngine.GameState()
        gs_copy.board = [row[:] for row in self.gs.board]  # Deep copy
        gs_copy.whiteToMove = self.gs.whiteToMove
        gs_copy.moveLog = self.gs.moveLog[:]
        gs_copy.whiteKingLocation = self.gs.whiteKingLocation
        gs_copy.blackKingLocation = self.gs.blackKingLocation
        gs_copy.checkmate = self.gs.checkmate
        gs_copy.stalemate = self.gs.stalemate
        gs_copy.enpassantPossible = self.gs.enpassantPossible
        gs_copy.currentCastlingRights = self.gs.currentCastlingRights
        
        # Copy valid moves
        valid_moves_copy = self.validMoves[:]
        
        # Start AI thread
        self.ai_thread = threading.Thread(
            target=self.ai_worker, 
            args=(gs_copy, valid_moves_copy),
            daemon=True
        )
        self.ai_thread.start()
    
    def check_ai_move(self):
        """Check if AI has finished thinking - FIXED VERSION"""
        if not self.ai_thinking:
            return
        
        # Check if enough time has passed
        thinking_time = time.time() - self.ai_thinking_start_time
        if thinking_time < self.min_ai_think_time:
            return  # Still thinking
        
        # Check if AI has a move ready
        try:
            ai_move = self.move_queue.get_nowait()
            
            if ai_move is not None and ai_move in self.validMoves:
                print(f"AI selected move: {ai_move}")
                self.ai_move = ai_move
                self.ai_move_ready = True
                self.debug_info = f"AI found: {ai_move}"
            else:
                print("AI returned invalid move, using random")
                if len(self.validMoves) > 0:
                    self.ai_move = ChessAI.findRandomMove(self.validMoves)
                    self.ai_move_ready = True
                    self.debug_info = f"AI random: {self.ai_move}"
                else:
                    self.ai_move = None
                    self.ai_move_ready = False
            
            # AI finished thinking
            self.ai_thinking = False
            
        except queue.Empty:
            # AI still thinking
            self.debug_info = f"AI thinking... {thinking_time:.1f}s"
    
    def execute_ai_move(self):
        """Execute the AI move - FIXED VERSION"""
        if self.ai_move_ready and self.ai_move is not None:
            print(f"Executing AI move: {self.ai_move}")
            
            # Make the move
            self.gs.makeMove(self.ai_move)
            self.moveMade = True
            self.animate = True
            
            # Reset AI state
            self.ai_move_ready = False
            self.ai_move = None
            self.debug_info = "Move executed"
            
            return True
        return False
    
    def is_ai_turn(self):
        """Check if it's AI's turn"""
        if self.gs.whiteToMove and not self.playerOne:
            return True  # White AI turn
        if not self.gs.whiteToMove and not self.playerTwo:
            return True  # Black AI turn
        return False
    
    def update(self, dt):
        """Main game loop update with professional animations"""
        super().update(dt)
        
        # Update animations
        self.title_glow = (self.title_glow + dt * 2) % (math.pi * 2)
        self.board_animation_offset = math.sin(time.time() * 0.5) * 2
        
        # Update buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons.values():
            button.update(dt, mouse_pos)
        
        if self.gameOver:
            return
        
        # Handle AI thinking
        if self.ai_thinking:
            self.check_ai_move()
        
        # Execute AI move if ready
        if self.ai_move_ready:
            self.execute_ai_move()
        
        # Handle move completion
        if self.moveMade:
            if self.animate:
                # Add a brief pause for move animation
                time.sleep(0.2)
                self.animate = False
            
            # Update valid moves
            self.validMoves = self.gs.getValidMoves()
            self.moveMade = False
            
            # Check for game over
            if self.gs.checkmate:
                self.gameOver = True
                winner = 'Black' if self.gs.whiteToMove else 'White'
                print(f'Checkmate! {winner} wins!')
                self.debug_info = f"Checkmate! {winner} wins!"
                return
            elif self.gs.stalemate:
                self.gameOver = True
                print('Stalemate!')
                self.debug_info = "Stalemate!"
                return
        
        # Start AI thinking if it's AI's turn and not already thinking
        if (not self.ai_thinking and not self.ai_move_ready and 
            not self.moveMade and self.is_ai_turn()):
            self.start_ai_thinking()
    
    def handle_event(self, event):
        """Handle events with professional UI"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z:  # undo
                self.undoMove()
            elif event.key == pygame.K_r:  # reset
                self.resetGame()
        
        # Handle button events
        for button in self.buttons.values():
            button.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                location = pygame.mouse.get_pos()
                
                # Board click handling - only for human players
                if (not self.gameOver and not self.ai_thinking and 
                    not self.ai_move_ready and not self.moveMade):
                    
                    # Check if click is on the board
                    board_rect = pygame.Rect(self.BOARD_OFFSET_X, self.BOARD_OFFSET_Y, 
                                           self.BOARD_WIDTH, self.BOARD_HEIGHT)
                    
                    if board_rect.collidepoint(location):
                        col = (location[0] - self.BOARD_OFFSET_X) // self.SQ_SIZE
                        row = (location[1] - self.BOARD_OFFSET_Y) // self.SQ_SIZE
                        
                        if 0 <= row < 8 and 0 <= col < 8:
                            # Check if it's human's turn
                            human_turn = ((self.gs.whiteToMove and self.playerOne) or 
                                        (not self.gs.whiteToMove and self.playerTwo))
                            
                            if human_turn:
                                self.handle_human_move(row, col)
    
    def handle_human_move(self, row, col):
        """Handle human player move with professional feedback"""
        if self.sqSelected == (row, col):
            # Deselect if same square clicked
            self.sqSelected = ()
            self.playerClicks = []
        else:
            self.sqSelected = (row, col)
            self.playerClicks.append(self.sqSelected)
        
        if len(self.playerClicks) == 2:
            # Try to make the move
            move = ChessEngine.Move(self.playerClicks[0], self.playerClicks[1], self.gs.board)
            
            move_found = False
            for valid_move in self.validMoves:
                if move == valid_move:
                    print(f"Human move: {valid_move}")
                    self.gs.makeMove(valid_move)
                    self.moveMade = True
                    self.animate = True
                    self.sqSelected = ()
                    self.playerClicks = []
                    move_found = True
                    break
            
            if not move_found:
                # Invalid move, keep last selection
                self.playerClicks = [self.sqSelected]
                print("Invalid move attempted")
    
    def setPlayers(self, white_human, black_human):
        """Set player types with professional feedback"""
        print(f"\nChanging players: White={'Human' if white_human else 'AI'}, Black={'Human' if black_human else 'AI'}")
        
        # Stop any AI thinking immediately
        self.stop_ai_thinking()
        
        # Set new player configuration
        self.playerOne = white_human
        self.playerTwo = black_human
        
        # Clear any pending moves
        self.moveMade = False
        self.animate = False
        self.sqSelected = ()
        self.playerClicks = []
        
        print("Player configuration updated")
    
    def stop_ai_thinking(self):
        """Stop AI thinking completely"""
        print("Stopping AI thinking...")
        
        self.ai_thinking = False
        self.ai_move_ready = False
        self.ai_move = None
        
        # Wait for AI thread to finish
        if self.ai_thread is not None and self.ai_thread.is_alive():
            self.ai_thread.join(timeout=2.0)
            if self.ai_thread.is_alive():
                print("Warning: AI thread did not stop gracefully")
        
        # Clear move queue
        while not self.move_queue.empty():
            try:
                self.move_queue.get_nowait()
            except queue.Empty:
                break
        
        self.debug_info = "AI stopped"
        print("AI thinking stopped")
    
    def undoMove(self):
        """Undo the last move with professional feedback"""
        if len(self.gs.moveLog) > 0 and not self.gameOver:
            print("Undoing move...")
            
            # Stop AI thinking
            self.stop_ai_thinking()
            
            # Undo the move
            self.gs.undoMove()
            self.validMoves = self.gs.getValidMoves()
            self.moveMade = False
            self.animate = False
            self.gameOver = False
            
            # Clear selections
            self.sqSelected = ()
            self.playerClicks = []
            
            print("Move undone")
    
    def resetGame(self):
        """Reset the game with professional feedback"""
        print("Resetting game...")
        
        # Stop AI thinking
        self.stop_ai_thinking()
        
        # Reset game state
        self.gs = ChessEngine.GameState()
        self.validMoves = self.gs.getValidMoves()
        self.sqSelected = ()
        self.playerClicks = []
        self.moveMade = False
        self.animate = False
        self.gameOver = False
        
        self.debug_info = "Game reset"
        print("Game reset complete")
    
    def render(self, screen):
        """Render the professional game interface"""
        # Get background color from config or use default
        try:
            bg_color = self.config.COLORS['background'] if self.config and hasattr(self.config, 'COLORS') else (248, 249, 250)
        except:
            bg_color = (248, 249, 250)
        
        screen.fill(bg_color)
        
        # Draw animated title
        self.drawTitle(screen)
        
        # Draw professional chess board
        self.drawProfessionalBoard(screen)
        
        # Draw pieces
        self.drawPieces(screen, self.gs.board)
        
        # Draw highlights and overlays
        self.drawBoardHighlights(screen)
        
        # Draw status panel
        self.drawStatusPanel(screen)
        
        # Draw move log panel
        self.drawMoveLogPanel(screen)
        
        # Draw professional UI buttons
        self.drawButtons(screen)
        
        # Draw game over overlay if needed
        if self.gameOver:
            self.drawGameOverOverlay(screen)
    
    def drawTitle(self, screen):
        """Draw animated title"""
        title_text = "Professional AI Chess"
        glow_intensity = int(50 + 30 * math.sin(self.title_glow))
        
        # Title with glow effect
        title_color = (44, 62, 80)
        glow_color = (52, 152, 219, glow_intensity)
        
        title_surface = self.title_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2 if self.config else 400, 40))
        
        # Draw glow
        glow_surface = self.title_font.render(title_text, True, (52, 152, 219))
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            screen.blit(glow_surface, (title_rect.x + offset[0], title_rect.y + offset[1]))
        
        # Draw main title
        screen.blit(title_surface, title_rect)
    
    def drawProfessionalBoard(self, screen):
        """Draw the professional chess board with matching colors"""
        # Board background with shadow
        shadow_rect = pygame.Rect(
            self.BOARD_OFFSET_X + 4 + self.board_animation_offset,
            self.BOARD_OFFSET_Y + 4,
            self.BOARD_WIDTH,
            self.BOARD_HEIGHT
        )
        pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=8)
        
        # Main board background
        board_bg_rect = pygame.Rect(
            self.BOARD_OFFSET_X + self.board_animation_offset,
            self.BOARD_OFFSET_Y,
            self.BOARD_WIDTH,
            self.BOARD_HEIGHT
        )
        pygame.draw.rect(screen, (60, 60, 60), board_bg_rect, border_radius=8)
        pygame.draw.rect(screen, (40, 40, 40), board_bg_rect, 3, border_radius=8)
        
        # Draw squares with professional colors (matching other modules)
        for row in range(self.DIMENSION):
            for col in range(self.DIMENSION):
                # Use the same colors as other modules
                if (row + col) % 2 == 0:
                    color = self.light_square_color  # (240, 217, 181)
                else:
                    color = self.dark_square_color   # (181, 136, 99)
                
                square_rect = pygame.Rect(
                    self.BOARD_OFFSET_X + col * self.SQ_SIZE + self.board_animation_offset,
                    self.BOARD_OFFSET_Y + row * self.SQ_SIZE,
                    self.SQ_SIZE,
                    self.SQ_SIZE
                )
                
                pygame.draw.rect(screen, color, square_rect)
                
                # Add subtle inner shadow for depth
                shadow_color = tuple(int(c * 0.9) for c in color)
                pygame.draw.rect(screen, shadow_color, square_rect, 1)
        
        # Draw coordinates
        self.drawCoordinates(screen)
    
    def drawCoordinates(self, screen):
        """Draw board coordinates professionally"""
        coord_color = (100, 100, 100)
        
        # Files (a-h)
        for col in range(8):
            letter = chr(ord('a') + col)
            text_surface = self.small_font.render(letter, True, coord_color)
            x = self.BOARD_OFFSET_X + col * self.SQ_SIZE + self.SQ_SIZE // 2 + self.board_animation_offset
            y = self.BOARD_OFFSET_Y + self.BOARD_HEIGHT + 5
            text_rect = text_surface.get_rect(center=(x, y))
            screen.blit(text_surface, text_rect)
        
        # Ranks (1-8)
        for row in range(8):
            number = str(8 - row)
            text_surface = self.small_font.render(number, True, coord_color)
            x = self.BOARD_OFFSET_X - 15 + self.board_animation_offset
            y = self.BOARD_OFFSET_Y + row * self.SQ_SIZE + self.SQ_SIZE // 2
            text_rect = text_surface.get_rect(center=(x, y))
            screen.blit(text_surface, text_rect)
    
    def drawBoardHighlights(self, screen):
        """Draw professional board highlights"""
        # Selected square highlight
        if self.sqSelected != ():
            row, col = self.sqSelected
            if self.gs.board[row][col][0] == ('w' if self.gs.whiteToMove else 'b'):
                highlight_rect = pygame.Rect(
                    self.BOARD_OFFSET_X + col * self.SQ_SIZE + self.board_animation_offset,
                    self.BOARD_OFFSET_Y + row * self.SQ_SIZE,
                    self.SQ_SIZE,
                    self.SQ_SIZE
                )
                
                # Create selection overlay
                selection_surface = pygame.Surface((self.SQ_SIZE, self.SQ_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(selection_surface, (*self.selected_color, 120), (0, 0, self.SQ_SIZE, self.SQ_SIZE))
                screen.blit(selection_surface, highlight_rect.topleft)
                
                # Selection border
                pygame.draw.rect(screen, self.selected_color, highlight_rect, 3)
                
                # Valid moves highlights
                for move in self.validMoves:
                    if move.startRow == row and move.startCol == col:
                        move_rect = pygame.Rect(
                            self.BOARD_OFFSET_X + move.endCol * self.SQ_SIZE + self.board_animation_offset,
                            self.BOARD_OFFSET_Y + move.endRow * self.SQ_SIZE,
                            self.SQ_SIZE,
                            self.SQ_SIZE
                        )
                        
                        # Valid move overlay
                        move_surface = pygame.Surface((self.SQ_SIZE, self.SQ_SIZE), pygame.SRCALPHA)
                        pygame.draw.rect(move_surface, (*self.valid_move_color, 80), (0, 0, self.SQ_SIZE, self.SQ_SIZE))
                        screen.blit(move_surface, move_rect.topleft)
                        
                        # Valid move border
                        pygame.draw.rect(screen, self.valid_move_color, move_rect, 2)
    
    def drawPieces(self, screen, board):
        """Draw chess pieces with professional styling"""
        for row in range(self.DIMENSION):
            for col in range(self.DIMENSION):
                piece = board[row][col]
                if piece != "--":
                    piece_rect = pygame.Rect(
                        self.BOARD_OFFSET_X + col * self.SQ_SIZE + 4 + self.board_animation_offset,
                        self.BOARD_OFFSET_Y + row * self.SQ_SIZE + 4,
                        self.SQ_SIZE - 8,
                        self.SQ_SIZE - 8
                    )
                    screen.blit(self.images[piece], piece_rect)
    
    def drawStatusPanel(self, screen):
        """Draw professional status panel"""
        # Determine current game status
        current_player = "White" if self.gs.whiteToMove else "Black"
        player_type = " (AI)" if self.is_ai_turn() else " (Human)"
        
        if self.gameOver:
            if self.gs.checkmate:
                winner = "Black" if self.gs.whiteToMove else "White"
                title = "Game Over"
                content = [f"Checkmate!", f"{winner} Wins!"]
                panel_type = 'success'
            elif self.gs.stalemate:
                title = "Game Over"
                content = ["Stalemate!", "It's a Draw!"]
                panel_type = 'info'
        else:
            title = "Game Status"
            content = [
                f"Turn: {current_player}{player_type}",
                f"Moves: {len(self.gs.moveLog)}",
                f"Valid moves: {len(self.validMoves)}"
            ]
            
            if self.ai_thinking:
                panel_type = 'warning'
                content.append("AI is thinking...")
            elif self.debug_info:
                content.append(self.debug_info)
                panel_type = 'info'
            else:
                panel_type = 'info'
        
        self.status_panel.render(screen, title, content, panel_type)
    
    def drawMoveLogPanel(self, screen):
        """Draw professional move log panel"""
        title = "Move History"
        
        # Format move log
        move_texts = []
        moveLog = self.gs.moveLog
        
        for i in range(0, len(moveLog), 2):
            move_number = i // 2 + 1
            white_move = str(moveLog[i]) if i < len(moveLog) else ""
            black_move = str(moveLog[i + 1]) if i + 1 < len(moveLog) else ""
            
            if black_move:
                move_texts.append(f"{move_number}. {white_move} {black_move}")
            elif white_move:
                move_texts.append(f"{move_number}. {white_move}")
        
        # Show last 10 moves
        content = move_texts[-10:] if move_texts else ["No moves yet"]
        
        self.move_log_panel.render(screen, title, content, 'info')
    
    def drawButtons(self, screen):
        """Draw all professional buttons"""
        for button_name, button in self.buttons.items():
            # Highlight active mode button
            if button_name in ['human_vs_ai', 'ai_vs_ai', 'human_vs_human']:
                if ((button_name == 'human_vs_ai' and self.playerOne and not self.playerTwo) or
                    (button_name == 'ai_vs_ai' and not self.playerOne and not self.playerTwo) or
                    (button_name == 'human_vs_human' and self.playerOne and self.playerTwo)):
                    button.button_type = 'secondary'
                else:
                    button.button_type = 'primary'
            
            button.render(screen)
    
    def drawGameOverOverlay(self, screen):
        """Draw professional game over overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 150), overlay.get_rect())
        screen.blit(overlay, (0, 0))
        
        # Game over panel
        panel_width, panel_height = 400, 200
        panel_x = (screen.get_width() - panel_width) // 2
        panel_y = (screen.get_height() - panel_height) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (255, 255, 255), panel_rect, border_radius=15)
        pygame.draw.rect(screen, (52, 152, 219), panel_rect, 3, border_radius=15)
        
        # Game over text
        if self.gs.checkmate:
            winner = "Black" if self.gs.whiteToMove else "White"
            main_text = f"Checkmate!"
            sub_text = f"{winner} Wins!"
            text_color = (22, 160, 133)
        else:
            main_text = "Stalemate!"
            sub_text = "It's a Draw!"
            text_color = (52, 152, 219)
        
        main_surface = self.subtitle_font.render(main_text, True, text_color)
        main_rect = main_surface.get_rect(center=(panel_x + panel_width // 2, panel_y + 60))
        screen.blit(main_surface, main_rect)
        
        sub_surface = self.instruction_font.render(sub_text, True, text_color)
        sub_rect = sub_surface.get_rect(center=(panel_x + panel_width // 2, panel_y + 100))
        screen.blit(sub_surface, sub_rect)
        
        # Instructions
        inst_text = "Press 'R' to reset or click Reset Game"
        inst_surface = self.info_font.render(inst_text, True, (100, 100, 100))
        inst_rect = inst_surface.get_rect(center=(panel_x + panel_width // 2, panel_y + 140))
        screen.blit(inst_surface, inst_rect)
    
    def goBack(self):
        """Return to main menu with professional transition"""
        try:
            self.stop_ai_thinking()
            
            if hasattr(self.engine, 'change_state'):
                self.engine.change_state(ProjectGameState.MAIN_MENU)
            else:
                print("Back to main menu (no state manager found)")
        except Exception as e:
            print(f"Error going back: {e}")
    
    def exit(self):
        """Clean up when exiting"""
        print("Exiting Professional AI Chess state...")
        self.stop_ai_thinking()
        super().exit()


# Registration function
def register_ai_chess_state(engine):
    """Register the professional AI chess state with your game engine"""
    try:
        state_name = 'ai_chess_game_professional'
        engine.states[state_name] = AIChessGameState(engine)
        
        print("✅ Professional AI Chess state registered successfully")
        print(f"   State name: {state_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to register Professional AI Chess state: {e}")
        return False


# For testing
if __name__ == "__main__":
    print("Testing Professional AI Chess Module...")
    
    pygame.init()
    screen = pygame.display.set_mode((1000, 750))
    pygame.display.set_caption("Professional AI Chess")
    clock = pygame.time.Clock()
    
    class TestConfig:
        SCREEN_WIDTH = 1000
        SCREEN_HEIGHT = 750
        COLORS = {
            'background': (248, 249, 250),
            'primary': (52, 152, 219),
            'secondary': (46, 204, 113),
            'danger': (231, 76, 60),
            'text_dark': (44, 62, 80)
        }
    
    class TestEngine:
        def __init__(self):
            self.config = TestConfig()
            self.states = {}
            self.screen = screen
        
        def change_state(self, state_name):
            print(f"Would change to state: {state_name}")
    
    engine = TestEngine()
    chess_state = AIChessGameState(engine)
    chess_state.enter()
    
    print("🎮 Professional AI Chess Test Running!")
    print("✨ Now with professional styling!")
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            chess_state.handle_event(event)
        
        chess_state.update(dt)
        chess_state.render(screen)
        
        pygame.display.flip()
    
    chess_state.exit()
    pygame.quit()