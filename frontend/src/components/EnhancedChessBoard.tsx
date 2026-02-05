// EnhancedChessBoard.tsx - Complete chess board with proper labels and pygame functionality
'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChessExerciseState } from '@/lib/chessApi';

interface EnhancedChessBoardProps {
    exercise: ChessExerciseState;
    onSquareClick: (square: string) => void;
    onAction: (type: string, payload?: any) => void;
}

export default function EnhancedChessBoard({ exercise, onSquareClick, onAction }: EnhancedChessBoardProps) {
    const [selectedSquare, setSelectedSquare] = useState<string | null>(null);
    const [hoveredSquare, setHoveredSquare] = useState<string | null>(null);
    const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
    const [showFeedback, setShowFeedback] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Reset states when exercise changes
    useEffect(() => {
        console.log('🔍 DEBUG: Exercise changed, resetting states');
        console.log('🔍 DEBUG: New exercise ID:', exercise?.exercise_id);
        console.log('🔍 DEBUG: Previous selectedAnswer:', selectedAnswer);
        console.log('🔍 DEBUG: Previous showFeedback:', showFeedback);
        console.log('🔍 DEBUG: Previous isSubmitting:', isSubmitting);
        
        setSelectedAnswer(null);
        setShowFeedback(false);
        setSelectedSquare(null);
        setHoveredSquare(null);
        setIsSubmitting(false);
    }, [exercise?.exercise_id, exercise?.progress_current]); // Add progress_current as trigger

    // Check if this is an identify pieces exercise
    const isIdentifyPiecesExercise = exercise?.exercise_type === 'identify_pieces';
    
    // Check if this is a board setup exercise
    const isBoardSetupExercise = exercise?.exercise_type === 'board_setup';
    
    // Calculate progress for Board Setup
    const boardSetupProgress = isBoardSetupExercise ? 
        Math.round((exercise.progress_current / exercise.progress_total) * 100) : 0;

    // Parse options for identify pieces exercises
    const getIdentifyPiecesOptions = () => {
        if (!isIdentifyPiecesExercise || !exercise?.instructions) return [];
        const parts = exercise.instructions.split('|');
        const options = parts[1]?.split(',') || ["Pawn", "Rook", "Knight", "Bishop", "Queen", "King"];
        return options;
    };

    const handleAnswerSelect = (answer: string) => {
        console.log('🔍 DEBUG: handleAnswerSelect called');
        console.log('🔍 DEBUG: Answer:', answer);
        console.log('🔍 DEBUG: showFeedback:', showFeedback);
        console.log('🔍 DEBUG: selectedAnswer:', selectedAnswer);
        console.log('🔍 DEBUG: exercise.module_completed:', exercise.module_completed);
        console.log('🔍 DEBUG: exercise.exercise_completed:', exercise.exercise_completed);
        console.log('🔍 DEBUG: progress_current:', exercise.progress_current);
        console.log('🔍 DEBUG: progress_total:', exercise.progress_total);
        console.log('🔍 DEBUG: isSubmitting:', isSubmitting);
        
        // PREVENT ANY ACTIONS IF MODULE IS COMPLETED
        if (exercise.module_completed) {
            console.log('🔍 DEBUG: Module already completed, ignoring all interactions');
            return;
        }
        
        // PREVENT ANY ACTIONS IF EXERCISE IS COMPLETED AT 100%
        if (exercise.exercise_completed && exercise.progress_current === exercise.progress_total) {
            console.log('🔍 DEBUG: Exercise completed at 100%, ignoring all interactions');
            return;
        }
        
        // PREVENT MULTIPLE SUBMISSIONS
        if (isSubmitting) {
            console.log('🔍 DEBUG: Already submitting, ignoring duplicate click');
            return;
        }
        
        // Prevent multiple submissions for the same answer
        if (selectedAnswer === answer) {
            console.log('🔍 DEBUG: Same answer already selected, ignoring');
            return;
        }
        
        // Set feedback immediately to prevent double-clicks
        if (showFeedback) {
            console.log('🔍 DEBUG: Already showing feedback, ignoring click');
            return;
        }
        
        // Set submitting flag immediately
        setIsSubmitting(true);
        setShowFeedback(true);
        setSelectedAnswer(answer);
        
        console.log('🔍 DEBUG: Setting selectedAnswer to:', answer);
        console.log('🔍 DEBUG: Setting showFeedback to true');
        console.log('🔍 DEBUG: Setting isSubmitting to true');
        
        // Submit answer only once
        console.log('🔍 DEBUG: Submitting answer to backend');
        onAction('submit_answer', { answer });
        
        // Auto-progress after showing feedback
        setTimeout(() => {
            // PREVENT AUTO-PROGRESS IF MODULE IS COMPLETED
            if (exercise.module_completed) {
                console.log('🔍 DEBUG: Module completed, not auto-progressing');
                return;
            }
            
            // PREVENT AUTO-PROGRESS IF EXERCISE IS COMPLETED AT 100%
            if (exercise.exercise_completed && exercise.progress_current === exercise.progress_total) {
                console.log('🔍 DEBUG: Exercise completed at 100%, not auto-progressing');
                return;
            }
            
            // AUTO-PROGRESS ON CORRECT ANSWER
            if (exercise.exercise_completed && !exercise.module_completed) {
                console.log('🔍 DEBUG: Auto-progressing to next exercise');
                onAction('next');
            }
        }, 2000);
    };

    const handleSquareInteraction = (square: string) => {
        console.log('Square clicked:', square);
        console.log('Target squares:', exercise.target_squares);
        console.log('Is target:', exercise.target_squares.includes(square));
        
        if (isIdentifyPiecesExercise) {
            // For identify pieces, don't handle square clicks - only answer buttons
            return;
        }
        
        if (isBoardSetupExercise) {
            // For board setup, handle piece placement
            onAction('place_piece', { square });
            return;
        }
        
        setSelectedSquare(square);
        onSquareClick(square);
    };

    // Board setup specific functions
    const handlePieceSelection = (pieceType: string) => {
        console.log('Piece selected:', pieceType);
        onAction('select_piece', { piece_type: pieceType });
    };

    const getBoardSetupPieces = () => {
        if (!isBoardSetupExercise || !exercise?.pieces_inventory) {
            console.log('🔍 DEBUG: No pieces_inventory or not board setup exercise');
            return [];
        }
        
        const pieces = Object.entries(exercise.pieces_inventory).map(([type, info]: [string, any]) => {
            // Extract piece name with color symbol
            const colorSymbol = type.includes('white') ? '⚪' : '⚫';
            const pieceName = type.replace(/^(white|black)_/, '').replace(/\b\w/g, l => l.toUpperCase());
            const fullName = `${colorSymbol} ${pieceName}`;
            // console.log('🔍 DEBUG: Piece type:', type, '→ Name:', fullName);
            
            return {
                type,
                name: fullName, // "⚪ Pawn", "⚫ Knight", etc.
                count: info.count,
                symbol: info.symbol,
                color: info.color
            };
        });
        
        console.log('🔍 DEBUG: All pieces:', pieces);
        return pieces;
    };

    const getPlacedPiecesCount = (pieceType: string) => {
        if (!exercise?.placed_pieces) return 0;
        return Object.values(exercise.placed_pieces).filter((p: any) => p.type === pieceType).length;
    };

    const getPieceSymbol = (piece: any): string => {
        const symbols: { [key: string]: { [key: string]: string } } = {
            white: {
                king: '♔', queen: '♕', rook: '♖', bishop: '♗', knight: '♘', pawn: '♙'
            },
            black: {
                king: '♚', queen: '♛', rook: '♜', bishop: '♝', knight: '♞', pawn: '♟'
            }
        };
        return symbols[piece.color]?.[piece.type] || '';
    };

    const getSquareColor = (square: any): string => {
        // For identify pieces, highlight the highlighted square
        if (isIdentifyPiecesExercise && exercise?.highlighted_squares?.includes(square.name)) {
            return '#FFD700'; // Bright yellow
        }
        
        // For regular exercises
        if (square.is_highlighted) return '#FFD700'; // Yellow highlight
        if (square.is_selected) return '#4169E1'; // Blue for selected
        if (hoveredSquare === square.name) return '#FFD700'; // Gold hover
        return square.color;
    };

    const isTargetSquare = (squareName: string): boolean => {
        return exercise?.target_squares?.includes(squareName) || false;
    };

    const isHighlightedSquare = (squareName: string): boolean => {
        return exercise?.highlighted_squares?.includes(squareName) || false;
    };

    const isInvalidSquare = (squareName: string): boolean => {
        return exercise?.invalid_squares?.includes(squareName) || false;
    };

    const renderSquare = (square: any, index: number) => {
        // For gameplay, show all pieces from board_position
        // For lessons, show only exercise pieces
        let piece = null;
        if (exercise?.module_id === 'gameplay') {
            // Show all pieces from board_position
            piece = exercise?.board_position?.pieces?.find((p: any) => {
                const pieceSquare = typeof p.square === 'string' ? p.square : 
                    `${p.square.file}${p.square.rank}`;
                return pieceSquare === square.name;
            });
        } else {
            // Only show pieces that are actually on the board in the exercise
            piece = exercise?.board_position?.pieces?.find((p: any) => {
                const pieceSquare = typeof p.square === 'string' ? p.square : 
                    `${p.square.file}${p.square.rank}`;
                return pieceSquare === square.name;
            });
            
            // For board setup, also check placed_pieces
            if (isBoardSetupExercise && exercise?.placed_pieces?.[square.name]) {
                const placedPiece = exercise.placed_pieces[square.name];
                // Convert placed piece to the expected format
                piece = {
                    type: placedPiece.type.replace(/^(white|black)_/, ''),
                    color: placedPiece.color,
                    symbol: placedPiece.symbol,
                    square: square.name
                };
            }
        }
        
        // Check if square is a legal move for the selected piece
        let isLegalMove = false;
        if (exercise?.module_id === 'gameplay' && exercise?.selected_square) {
            // Only show legal moves if a piece is selected
            console.log('Selected square:', exercise.selected_square);
            console.log('Legal moves:', exercise.board_position?.legal_moves);
            console.log('Checking square:', square.name);
            
            isLegalMove = exercise?.board_position?.legal_moves?.some((move: any) => {
                const moveStr = typeof move === 'string' ? move : move.toString();
                const isMatch = moveStr.startsWith(exercise.selected_square) && moveStr.endsWith(square.name);
                if (isMatch) {
                    console.log('Found legal move:', moveStr);
                }
                return isMatch;
            }) || false;
        }
        
        const isTarget = isTargetSquare(square.name);
        const isInvalid = isInvalidSquare(square.name);
        const isSelected = selectedSquare === square.name;
        const isHighlighted = isHighlightedSquare(square.name);

        return (
            <motion.div
                key={square.name}
                className={`relative flex items-center justify-center cursor-pointer transition-all duration-200 ${
                    square.is_light ? 'border-gray-300' : 'border-gray-600'
                }`}
                style={{
                    backgroundColor: getSquareColor(square),
                    width: '60px',
                    height: '60px',
                    border: '1px solid',
                    boxShadow: isHighlighted && isIdentifyPiecesExercise ? '0 0 20px rgba(255, 215, 0, 0.6)' : 
                             isTarget ? '0 0 10px rgba(0, 255, 0, 0.5)' : 
                             isInvalid ? '0 0 10px rgba(255, 0, 0, 0.5)' :
                             isLegalMove && exercise.module_id === 'gameplay' ? '0 0 10px rgba(0, 200, 0, 0.3)' : 'none',
                    transform: isHighlighted && isIdentifyPiecesExercise ? 'scale(1.05)' : 'scale(1)',
                    cursor: isIdentifyPiecesExercise ? 'default' : 'pointer'
                }}
                whileHover={!isIdentifyPiecesExercise ? { scale: 1.05 } : {}}
                whileTap={!isIdentifyPiecesExercise ? { scale: 0.95 } : {}}
                onClick={() => handleSquareInteraction(square.name)}
                onMouseEnter={() => setHoveredSquare(square.name)}
                onMouseLeave={() => setHoveredSquare(null)}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.02 }}
            >
                {/* Legal move indicators for gameplay */}
                {exercise.module_id === 'gameplay' && isLegalMove && (
                    <motion.div
                        className="absolute inset-0 bg-green-400 opacity-40 rounded-full"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 300 }}
                    />
                )}

                {/* Selected piece indicator */}
                {isSelected && (
                    <motion.div
                        className="absolute inset-0 bg-blue-400 opacity-50 rounded"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 300 }}
                    />
                )}

                {/* Target square indicator */}
                {isTarget && (
                    <motion.div
                        className="absolute inset-0 bg-green-400 opacity-30 rounded"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 300 }}
                    />
                )}

                {/* Invalid square indicator */}
                {isInvalid && (
                    <motion.div
                        className="absolute inset-0 bg-red-400 opacity-20 rounded"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 300 }}
                    />
                )}

                {/* Chess piece */}
                {piece && (
                    <span style={{ 
                        color: piece.color === 'white' ? '#FFFFFF' : '#000000',
                        textShadow: piece.color === 'white' ? '0 0 3px rgba(0,0,0,0.8)' : '0 0 3px rgba(255,255,255,0.8)',
                        fontSize: '32px',
                        fontWeight: 'bold'
                    }}>
                        {getPieceSymbol(piece)}
                    </span>
                )}

                {/* Highlight border for identify pieces */}
                {isHighlighted && isIdentifyPiecesExercise && (
                    <div className="absolute inset-0 border-4 border-yellow-400 rounded pointer-events-none animate-pulse" />
                )}
            </motion.div>
        );
    };

    return (
        <div className="flex flex-col items-center space-y-6">
            {/* Question above board for identify pieces */}
            {isIdentifyPiecesExercise && (
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center"
                >
                    <h2 className="text-3xl font-bold  mb-2">
                        {exercise.instructions.split('|')[0] || "What is this piece called?"}
                    </h2>
                    <p className="">Look at the highlighted piece and choose the correct answer</p>
                </motion.div>
            )}

            {/* Identify Pieces Options - MOVED ABOVE BOARD */}
            {isIdentifyPiecesExercise && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="w-full max-w-lg"
                >
                    <div className="grid grid-cols-2 gap-4">
                        {getIdentifyPiecesOptions().map((option, index) => {
                            const isSelected = selectedAnswer === option;
                            const isCorrect = exercise.is_correct && isSelected;
                            const isWrong = !exercise.is_correct && isSelected;
                            
                            return (
                                <motion.button
                                    key={option}
                                    onClick={() => handleAnswerSelect(option)}
                                    disabled={showFeedback || exercise.module_completed || (exercise.exercise_completed && exercise.progress_current === exercise.progress_total)}
                                    className={`p-4 rounded-lg font-semibold text-lg transition-all duration-300 ${
                                        showFeedback
                                            ? isCorrect
                                                ? 'bg-green-500 text-white border-2 border-green-600'
                                                : isWrong
                                                    ? 'bg-red-500 text-white border-2 border-red-600'
                                                    : 'bg-gray-200 text-gray-500 border-2 border-gray-300'
                                            : exercise.module_completed || (exercise.exercise_completed && exercise.progress_current === exercise.progress_total)
                                                ? 'bg-gray-300 text-gray-600 border-2 border-gray-400 cursor-not-allowed'
                                                : 'bg-blue-500 text-white border-2 border-blue-600 hover:bg-blue-600 hover:border-blue-700 shadow-lg hover:shadow-xl'
                                    }`}
                                    whileHover={!showFeedback && !exercise.module_completed && !(exercise.exercise_completed && exercise.progress_current === exercise.progress_total) ? { scale: 1.05 } : {}}
                                >
                                    {option}
                                    {showFeedback && isCorrect && (
                                        <span className="ml-2">✓</span>
                                    )}
                                    {showFeedback && isWrong && (
                                        <span className="ml-2">✗</span>
                                    )}
                                </motion.button>
                            );
                        })}
                    </div>
                </motion.div>
            )}

            {/* Board Setup UI */}
            {isBoardSetupExercise && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="w-full max-w-4xl"
                >
                    <div className="bg-white/10 backdrop-blur-md rounded-2xl shadow-xl border border-white/20 p-6 mb-4">
                        <h3 className="text-xl font-bold mb-4 text-center text-white">Select a Piece to Place</h3>
                        <div className="flex flex-col items-center space-y-4">
                            <select 
                                value={exercise.current_piece_type || ''}
                                onChange={(e) => handlePieceSelection(e.target.value)}
                                className="w-full max-w-md px-4 py-3 bg-white/20 backdrop-blur-sm border-2 border-white/30 rounded-lg focus:border-blue-400 focus:outline-none text-white placeholder-white/70 text-lg"
                            >
                                <option value="" className="bg-gray-800">Select a piece...</option>
                                {getBoardSetupPieces().map((piece) => {
                                    const placedCount = getPlacedPiecesCount(piece.type);
                                    const remaining = piece.count - placedCount;
                                    
                                    return (
                                        <option 
                                            key={piece.type} 
                                            value={piece.type}
                                            disabled={remaining === 0}
                                            className="bg-gray-800"
                                        >
                                            {piece.name} ({placedCount}/{piece.count})
                                        </option>
                                    );
                                })}
                            </select>
                            
                            {exercise.current_piece_type && (
                                <div className="text-center">
                                    <p className="text-sm text-white/90">
                                        Selected: {getBoardSetupPieces().find(p => p.type === exercise.current_piece_type)?.name}
                                    </p>
                                    <p className="text-xs text-blue-300 mt-1">
                                        Click on the board to place this piece
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </motion.div>
            )}

            {/* Board title and instructions for other exercises */}
            {!isIdentifyPiecesExercise && !isBoardSetupExercise && (
                <div className="text-center space-y-2">
                    <h3 className="text-2xl font-bold">
                        {exercise.instructions}
                    </h3>
                    {exercise.board_position.turn && (
                        <p className="text-sm text-gray-600">
                            Current Turn: {
                                exercise.board_position.turn === 'white' 
                                    ? '⚪ White' 
                                    : '⚫ Black'
                            }
                        </p>
                    )}
                    {exercise.board_position.is_check && (
                        <p className="text-sm font-bold text-red-600 mt-1">
                            ⚠️ CHECK!
                        </p>
                    )}
                </div>
            )}

            {/* Chess board */}
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: "spring", stiffness: 200 }}
                className="relative"
            >
                {/* Board shadow */}
                <div className="absolute inset-0 bg-black opacity-20 rounded-lg blur-md" />
                
                {/* Main board */}
                <div className="relative bg-white border-4 border-gray-800 rounded-lg overflow-hidden">
                    <div className="grid grid-cols-8 gap-0">
                        {exercise.board_layout.squares.map((square, index) => 
                            renderSquare(square, index)
                        )}
                    </div>
                </div>

                {/* Coordinate labels */}
                <div className="absolute -left-8 top-0 flex flex-col justify-around h-full text-sm font-bold text-gray-700">
                    {['8', '7', '6', '5', '4', '3', '2', '1'].map(rank => (
                        <div key={rank} className="h-[60px] flex items-center justify-center">
                            {rank}
                        </div>
                    ))}
                </div>
                <div className="absolute -bottom-8 left-0 flex justify-around w-full text-sm font-bold text-gray-700">
                    {['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'].map(file => (
                        <div key={file} className="w-[60px] flex items-center justify-center">
                            {file}
                        </div>
                    ))}
                </div>
            </motion.div>

            {/* Action buttons - Hide for gameplay module */}
            {exercise.module_id !== 'gameplay' && (
                <div className="flex space-x-4 mt-6">
                    <motion.button
                        className="px-6 py-3 bg-blue-500 text-white rounded-lg font-semibold hover:bg-blue-600 transition-colors"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => onAction('hint')}
                        disabled={!exercise.hint_available}
                    >
                        💡 Hint
                    </motion.button>
                    
                    <motion.button
                        className="px-6 py-3 bg-yellow-500 text-white rounded-lg font-semibold hover:bg-yellow-600 transition-colors"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => onAction('skip')}
                    >
                        ⏭️ Skip
                    </motion.button>
                    
                    {exercise.exercise_completed && (
                        <motion.button
                            className="px-6 py-3 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-600 transition-colors"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => onAction('next')}
                        >
                            ➡️ Next Exercise
                        </motion.button>
                    )}
                </div>
            )}

            {/* Game controls for gameplay module */}
            {exercise.module_id === 'gameplay' && (
                <div className="flex space-x-4 mt-6">
                    {exercise.exercise_completed ? (
                        <motion.button
                            className="px-6 py-3 bg-purple-500 text-white rounded-lg font-semibold hover:bg-purple-600 transition-colors"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => onAction('new_game')}
                        >
                            🎮 New Game
                        </motion.button>
                    ) : (
                        <motion.button
                            className="px-6 py-3 bg-gray-500 text-white rounded-lg font-semibold hover:bg-gray-600 transition-colors"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => onAction('resign')}
                        >
                            🏳️ Resign
                        </motion.button>
                    )}
                </div>
            )}

            {/* Progress bar - Hide for gameplay module */}
            {exercise.module_id !== 'gameplay' && (
                <div className="w-full max-w-md">
                    {(() => {
                        console.log('🔍 DEBUG: Progress bar rendering for', exercise.module_id, {
                            progress_current: exercise.progress_current,
                            progress_total: exercise.progress_total,
                            percentage: Math.round((exercise.progress_current / exercise.progress_total) * 100),
                            boardSetupProgress: boardSetupProgress
                        });
                        return null;
                    })()}
                    <div className="flex justify-between text-sm text-gray-600 mb-2">
                        <span>Progress</span>
                        <span>{exercise.progress_current} / {exercise.progress_total}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                        <motion.div
                            className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full"
                            initial={{ width: 0 }}
                            animate={{ 
                                width: `${(exercise.progress_current / exercise.progress_total) * 100}%` 
                            }}
                            transition={{ type: "spring", stiffness: 100 }}
                            key={`progress-${exercise.progress_current}`} // Force re-render on progress change
                        />
                    </div>
                </div>
            )}

            {/* Feedback message */}
            <AnimatePresence>
                {exercise.feedback_message && (
                    <motion.div
                        className={`px-6 py-3 rounded-lg font-semibold text-center ${
                            exercise.is_correct === true 
                                ? 'bg-green-100 text-green-800 border-2 border-green-300' 
                                : exercise.is_correct === false 
                                ? 'bg-red-100 text-red-800 border-2 border-red-300'
                                : 'bg-blue-100 text-blue-800 border-2 border-blue-300'
                        }`}
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        transition={{ type: "spring", stiffness: 300 }}
                    >
                        {exercise.feedback_message}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
