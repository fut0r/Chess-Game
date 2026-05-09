"""
sound_manager.py - Sound Effects Manager
Generates and plays chess sound effects using Pygame.
Uses pure Python (math + array) &#8212; no numpy dependency required.
"""

import pygame
import math
import array
import os
from config import SOUNDS_DIR


class SoundManager:
    """Manages sound effects for the chess game."""

    def __init__(self):
        self.enabled = True
        self.sounds = {}
        self._initialized = False

    def init(self):
        """Initialize the sound system and generate sounds."""
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self._generate_sounds()
            self._initialized = True
        except Exception as e:
            print(f"Sound initialization failed: {e}")
            self.enabled = False

    def _make_sound_from_samples(self, samples):
        """Create a pygame Sound from a list of float samples [-1.0, 1.0]."""
        # Convert to 16-bit signed integers
        int_samples = array.array('h', [int(max(-32767, min(32767, s * 32767))) for s in samples])
        sound = pygame.mixer.Sound(buffer=int_samples)
        return sound

    def _generate_tone(self, frequency, duration, volume=0.3, fade_out=True):
        """Generate a simple tone."""
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            val = math.sin(2 * math.pi * frequency * t) * volume
            # Apply fade out
            if fade_out and i > n_samples * 0.7:
                fade_pos = (i - n_samples * 0.7) / (n_samples * 0.3)
                val *= (1.0 - fade_pos)
            samples.append(val)
        return self._make_sound_from_samples(samples)

    def _generate_click(self, freq1, freq2, duration=0.08, volume=0.25):
        """Generate a click-like sound with two frequencies."""
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            wave = (math.sin(2 * math.pi * freq1 * t) * 0.5 +
                    math.sin(2 * math.pi * freq2 * t) * 0.5) * volume
            # Sharp attack, quick decay
            envelope = math.exp(-t * 30)
            samples.append(wave * envelope)
        return self._make_sound_from_samples(samples)

    def _generate_sounds(self):
        """Generate all game sounds programmatically."""
        # Move sound - subtle wooden click
        self.sounds['move'] = self._generate_click(800, 1200, 0.06, 0.2)

        # Capture sound - sharper, more impactful
        self.sounds['capture'] = self._generate_click(400, 900, 0.12, 0.35)

        # Check sound - alert tone
        self.sounds['check'] = self._generate_tone(880, 0.15, 0.3)

        # Castling sound - two quick clicks
        sample_rate = 44100
        duration = 0.2
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            val = 0.0
            # First click
            if t < 0.06:
                val = math.sin(2 * math.pi * 700 * t) * 0.3 * math.exp(-t * 40)
            # Second click
            elif 0.1 <= t < 0.16:
                t2 = t - 0.1
                val = math.sin(2 * math.pi * 900 * t2) * 0.3 * math.exp(-t2 * 40)
            samples.append(val)
        self.sounds['castle'] = self._make_sound_from_samples(samples)

        # Game over sound - descending tones
        duration = 0.6
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            freq = 660 - 200 * t
            val = math.sin(2 * math.pi * freq * t) * 0.25 * math.exp(-t * 3)
            samples.append(val)
        self.sounds['game_over'] = self._make_sound_from_samples(samples)

        # Promotion sound - ascending
        duration = 0.3
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            freq = 440 + 440 * t
            val = math.sin(2 * math.pi * freq * t) * 0.2 * math.exp(-t * 5)
            samples.append(val)
        self.sounds['promote'] = self._make_sound_from_samples(samples)

        # UI click
        self.sounds['ui_click'] = self._generate_click(1000, 1500, 0.04, 0.15)

    def play(self, sound_name):
        """Play a sound by name."""
        if not self.enabled or not self._initialized:
            return
        sound = self.sounds.get(sound_name)
        if sound:
            sound.play()

    def play_move_sound(self, move):
        """Play the appropriate sound for a move."""
        if not self.enabled:
            return

        if move.is_castling:
            self.play('castle')
        elif move.captured:
            self.play('capture')
        elif move.promotion:
            self.play('promote')
        else:
            self.play('move')

    def toggle(self):
        """Toggle sound on/off."""
        self.enabled = not self.enabled
        return self.enabled
