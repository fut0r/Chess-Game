"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Chess, Move } from 'chess.js';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Map piece names to our asset files
const PIECE_IMAGES: Record<string, string> = {
  'wp': '/assets/pieces/white_pawn.png',
  'wr': '/assets/pieces/white_rook.png',
  'wn': '/assets/pieces/white_knight.png',
  'wb': '/assets/pieces/white_bishop.png',
  'wq': '/assets/pieces/white_queen.png',
  'wk': '/assets/pieces/white_king.png',
  'bp': '/assets/pieces/black_pawn.png',
  'br': '/assets/pieces/black_rook.png',
  'bn': '/assets/pieces/black_knight.png',
  'bb': '/assets/pieces/black_bishop.png',
  'bq': '/assets/pieces/black_queen.png',
  'bk': '/assets/pieces/black_king.png',
};

interface ChessBoardProps {
  game: Chess;
  onMove: (move: any) => void;
  isAiThinking?: boolean;
}

export default function ChessBoard({ game, onMove, isAiThinking }: ChessBoardProps) {
  const [selectedSquare, setSelectedSquare] = useState<string | null>(null);
  const [lastMove, setLastMove] = useState<{ from: string, to: string } | null>(null);

  const onSquareClick = (square: string) => {
    if (game.game_over() || isAiThinking) return;

    if (selectedSquare === square) {
      setSelectedSquare(null);
      return;
    }

    if (selectedSquare) {
      try {
        const move = game.move({
          from: selectedSquare,
          to: square,
          promotion: 'q' // Default to queen
        });

        if (move) {
          setSelectedSquare(null);
          setLastMove({ from: move.from, to: move.to });
          onMove(move);
        } else {
          // If illegal move, try selecting the piece on the target square if it's ours
          const piece = game.get(square as any);
          if (piece && piece.color === game.turn()) {
            setSelectedSquare(square);
          } else {
            setSelectedSquare(null);
          }
        }
      } catch (e) {
        setSelectedSquare(null);
      }
    } else {
      const piece = game.get(square as any);
      if (piece && piece.color === game.turn()) {
        setSelectedSquare(square);
      }
    }
  };

  const renderSquare = (i: number) => {
    const row = Math.floor(i / 8);
    const col = i % 8;
    const isLight = (row + col) % 2 === 0;
    const coord = String.fromCharCode(97 + col) + (8 - row);
    const piece = game.get(coord as any);
    
    const isSelected = selectedSquare === coord;
    const isLastMove = lastMove && (lastMove.from === coord || lastMove.to === coord);

    return (
      <div 
        key={coord}
        onClick={() => onSquareClick(coord)}
        className={cn(
          "relative w-full h-full flex items-center justify-center cursor-pointer transition-colors duration-150",
          isLight ? "bg-[#eeeed2]" : "bg-[#769656]",
          isSelected && "bg-[#6a874d99]",
          isLastMove && "bg-[#aaa23a59]"
        )}
      >
        {piece && (
          <img 
            src={PIECE_IMAGES[`${piece.color}${piece.type}`]} 
            alt={`${piece.color} ${piece.type}`}
            className="w-[90%] h-[90%] z-10 select-none pointer-events-none transition-transform hover:scale-110"
          />
        )}
        
        {/* Coordinates */}
        {col === 0 && (
          <span className={cn(
            "absolute top-0.5 left-0.5 text-[10px] font-bold select-none",
            isLight ? "text-[#769656]" : "text-[#eeeed2]"
          )}>{8 - row}</span>
        )}
        {row === 7 && (
          <span className={cn(
            "absolute bottom-0.5 right-0.5 text-[10px] font-bold select-none",
            isLight ? "text-[#769656]" : "text-[#eeeed2]"
          )}>{String.fromCharCode(97 + col)}</span>
        )}
      </div>
    );
  };

  return (
    <div className="relative aspect-square w-full max-w-[640px] border-[4px] border-[#785a3c] shadow-2xl overflow-hidden rounded-sm">
      <div className="grid grid-cols-8 grid-rows-8 w-full h-full">
        {Array.from({ length: 64 }).map((_, i) => renderSquare(i))}
      </div>
      
      {/* AI Thinking Overlay */}
      {isAiThinking && (
        <div className="absolute inset-0 bg-black/20 backdrop-blur-[1px] flex items-center justify-center z-20 pointer-events-none">
          <div className="bg-bg-dark/80 px-4 py-2 border border-gold text-gold font-bold animate-pulse">
            AI IS THINKING...
          </div>
        </div>
      )}
    </div>
  );
}
