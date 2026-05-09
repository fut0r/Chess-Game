"""
clock_manager.py - Chess Clock System
Supports various time controls including Fischer increment and endless mode.
"""

import time
from config import TIME_CONTROLS, DEFAULT_TIME_CONTROL
from utils import format_time, format_time_precise


class ChessClock:
    """Manages chess clocks for both players."""

    def __init__(self, time_control_name=None):
        self.set_time_control(time_control_name or DEFAULT_TIME_CONTROL)
        self.reset()

    def set_time_control(self, name):
        """Set the time control preset."""
        self.time_control_name = name
        tc = TIME_CONTROLS.get(name, TIME_CONTROLS[DEFAULT_TIME_CONTROL])
        self.initial_time = tc["time"]
        self.increment = tc["increment"]
        self.is_endless = (self.initial_time == 0)

    def reset(self):
        """Reset both clocks."""
        self.white_time = float(self.initial_time)
        self.black_time = float(self.initial_time)
        self.active_color = None  # None = clock not started
        self.last_tick = None
        self.running = False
        self.white_timed_out = False
        self.black_timed_out = False

    def start(self, is_white_turn=True):
        """Start the clock for the given color."""
        if self.is_endless:
            return
        self.active_color = 'white' if is_white_turn else 'black'
        self.last_tick = time.time()
        self.running = True

    def stop(self):
        """Stop the clock."""
        if self.running and self.last_tick:
            self._update_time()
        self.running = False
        self.last_tick = None

    def switch(self):
        """Switch the active clock (after a move). Adds increment."""
        if self.is_endless:
            return

        if self.running and self.last_tick:
            self._update_time()

        # Add increment to the player who just moved
        if self.active_color == 'white':
            self.white_time += self.increment
            self.active_color = 'black'
        elif self.active_color == 'black':
            self.black_time += self.increment
            self.active_color = 'white'

        self.last_tick = time.time()

    def update(self):
        """Called every frame to update the active clock. Returns True if timeout."""
        if not self.running or self.is_endless:
            return False

        self._update_time()

        if self.white_time <= 0:
            self.white_time = 0
            self.white_timed_out = True
            self.running = False
            return True

        if self.black_time <= 0:
            self.black_time = 0
            self.black_timed_out = True
            self.running = False
            return True

        return False

    def _update_time(self):
        """Deduct elapsed time from active clock."""
        if not self.last_tick:
            return

        now = time.time()
        elapsed = now - self.last_tick
        self.last_tick = now

        if self.active_color == 'white':
            self.white_time -= elapsed
        elif self.active_color == 'black':
            self.black_time -= elapsed

    def get_white_display(self):
        """Get formatted white time string."""
        if self.is_endless:
            return "&#8734;"
        return format_time_precise(self.white_time) if self.white_time < 30 else format_time(self.white_time)

    def get_black_display(self):
        """Get formatted black time string."""
        if self.is_endless:
            return "&#8734;"
        return format_time_precise(self.black_time) if self.black_time < 30 else format_time(self.black_time)

    def get_white_state(self):
        """Get timer state for visual warnings: 'normal', 'warning', 'critical'."""
        if self.is_endless:
            return 'normal'
        if self.white_time < 30:
            return 'critical'
        if self.white_time < 60:
            return 'warning'
        return 'normal'

    def get_black_state(self):
        """Get timer state for visual warnings."""
        if self.is_endless:
            return 'normal'
        if self.black_time < 30:
            return 'critical'
        if self.black_time < 60:
            return 'warning'
        return 'normal'

    def is_white_active(self):
        return self.active_color == 'white'

    def is_black_active(self):
        return self.active_color == 'black'
