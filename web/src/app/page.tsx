"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Chess } from 'chess.js';
import ChessBoard from '@/components/ChessBoard';
import { Trophy, History, User, Play, LogOut, Settings } from 'lucide-react';

const API_BASE = "http://18.196.205.59:8000";

export default function GamePage() {
  const [game, setGame] = useState(new Chess());
  const [history, setHistory] = useState<string[]>([]);
  const [isAiThinking, setIsAiThinking] = useState(false);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [status, setStatus] = useState("Welcome to Infiniware Chess");
  const [difficulty, setDifficulty] = useState("Medium");

  // Load leaderboard on mount
  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const res = await fetch(`${API_BASE}/leaderboard`);
      const data = await res.json();
      setLeaderboard(data);
    } catch (e) {
      console.error("Leaderboard error", e);
    }
  };

  const handleMove = async (move: any) => {
    updateGameUI();
    
    if (!game.game_over()) {
      // Trigger AI Move via AWS
      setIsAiThinking(true);
      setStatus("AI is calculating...");
      
      try {
        const res = await fetch(`${API_BASE}/ai/move`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            board: game.board(),
            difficulty: difficulty,
            white_turn: game.turn() === 'w',
            // Passing simplified rights for now
            castling_rights: { 'w': 'KQ', 'b': 'kq' } 
          })
        });
        
        const data = await res.json();
        if (data.from && data.to) {
          game.move({
            from: data.from_algebraic || convertToAlgebraic(data.from),
            to: data.to_algebraic || convertToAlgebraic(data.to),
            promotion: 'q'
          });
          updateGameUI();
        }
      } catch (e) {
        console.error("AI Move failed", e);
        setStatus("AI Connection Error");
      } finally {
        setIsAiThinking(false);
        setStatus(game.turn() === 'w' ? "Your Turn" : "AI Thinking...");
      }
    }
    checkGameOver();
  };

  const convertToAlgebraic = (pos: number[]) => {
      // Convert (col, row) to algebraic
      return String.fromCharCode(97 + pos[0]) + (8 - pos[1]);
  }

  const updateGameUI = () => {
    setGame(new Chess(game.fen()));
    setHistory(game.history());
  };

  const checkGameOver = () => {
    if (game.game_over()) {
      if (game.in_checkmate()) setStatus("CHECKMATE! Game Over.");
      else if (game.in_draw()) setStatus("DRAW! Good game.");
      else setStatus("GAME OVER.");
    }
  };

  const resetGame = () => {
    const newGame = new Chess();
    setGame(newGame);
    setHistory([]);
    setStatus("New Game Started");
  };

  return (
    <main className="flex h-screen w-screen bg-bg-dark text-text-primary overflow-hidden">
      {/* Sidebar - Rank & History */}
      <aside className="w-80 h-full flex flex-col gap-4 p-4 glass border-r border-border z-10">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-gold flex items-center justify-center text-bg-dark font-black text-xl">I</div>
          <div>
            <h1 className="text-xl font-bold tracking-tighter">INFINIWARE <span className="text-gold">CHESS</span></h1>
            <p className="text-[10px] text-text-secondary uppercase tracking-[3px]">Web Edition</p>
          </div>
        </div>

        {/* Leaderboard */}
        <section className="flex-1 overflow-hidden flex flex-col">
          <div className="flex items-center gap-2 text-gold mb-3 px-1">
            <Trophy size={16} />
            <h2 className="text-xs font-bold uppercase tracking-wider">Global Leaderboard</h2>
          </div>
          <div className="flex-1 overflow-y-auto pr-1 space-y-1">
            {leaderboard.map((user, i) => (
              <div key={user.username} className="flex items-center gap-3 p-2 rounded hover:bg-white/5 transition-colors group">
                <div className={cn(
                  "w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold",
                  i === 0 ? "bg-gold text-black" : i === 1 ? "bg-slate-300 text-black" : i === 2 ? "bg-amber-700 text-white" : "bg-bg-medium text-text-secondary"
                )}>{i + 1}</div>
                <div className="flex-1 truncate text-sm font-medium">{user.username}</div>
                <div className="text-gold font-bold text-xs">{user.elo}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Move History */}
        <section className="h-48 overflow-hidden flex flex-col border-t border-border/50 pt-4">
          <div className="flex items-center gap-2 text-gold mb-3 px-1">
            <History size={16} />
            <h2 className="text-xs font-bold uppercase tracking-wider">Move History</h2>
          </div>
          <div className="flex-1 overflow-y-auto bg-black/20 p-2 text-xs font-mono grid grid-cols-2 gap-x-4 gap-y-1">
            {history.map((move, i) => (
              <div key={i} className="text-text-secondary">
                <span className="text-gold/50 mr-2">{Math.floor(i/2) + 1}.</span>
                {move}
              </div>
            ))}
          </div>
        </section>
      </aside>

      {/* Main Game Area */}
      <div className="flex-1 relative flex flex-col items-center justify-center p-8">
        {/* Background Image */}
        <div className="absolute inset-0 opacity-10 pointer-events-none bg-[url('/assets/background.jpg')] bg-cover bg-center" />
        
        {/* Board */}
        <div className="relative z-10 w-full max-w-[640px]">
          <div className="flex justify-between items-end mb-4 px-1">
            <div className="flex flex-col">
              <span className="text-[10px] text-gold uppercase tracking-[2px] font-bold mb-1">Status</span>
              <p className="text-lg font-medium text-text-primary h-7">{status}</p>
            </div>
            <div className="flex gap-2">
                <button onClick={resetGame} className="flex items-center gap-2 px-4 py-2 bg-gold/10 border border-gold/30 text-gold hover:bg-gold hover:text-bg-dark transition-all font-bold text-sm">
                    <Play size={14} fill="currentColor" /> NEW GAME
                </button>
            </div>
          </div>

          <ChessBoard game={game} onMove={handleMove} isAiThinking={isAiThinking} />
        </div>

        {/* Footnote */}
        <div className="absolute bottom-6 text-[10px] text-text-secondary flex gap-6">
            <span>PLATFORM: AWS FRANKFURT</span>
            <span>ENGINE: INFINI-V1</span>
            <span>CONNECTED: {leaderboard.length > 0 ? "YES" : "NO"}</span>
        </div>
      </div>
    </main>
  );
}

function cn(...inputs: any[]) {
    return inputs.filter(Boolean).join(' ');
}
