# emacs-mode: -*- python-*-

from __future__ import absolute_import, print_function, unicode_literals

from . import F1Config as Config


class SequencerState(object):
    """In-memory state for the controller."""

    def __init__(self):
        self.selected_channel = 0
        self.sound_index = [0] * Config.NUM_CHANNELS
        self.window_index = [0] * Config.NUM_CHANNELS
        self.pot_zone = [None] * Config.NUM_CHANNELS
        self.steps = [False] * Config.NUM_STEPS
        self.accents = [False] * Config.NUM_STEPS
        self.current_play_step = -1

    def load_pattern(self, steps, accents, pitch):
        self.steps = list(steps)
        self.accents = list(accents)
        if pitch is not None:
            pitches = Config.SOUND_PITCHES[self.selected_channel]
            try:
                self.sound_index[self.selected_channel] = pitches.index(pitch)
            except ValueError:
                pass

    def current_pitch(self):
        pitches = Config.SOUND_PITCHES[self.selected_channel]
        return pitches[self.sound_index[self.selected_channel] % len(pitches)]

    def toggle_step(self, step_index):
        self.steps[step_index] = not self.steps[step_index]
        if not self.steps[step_index]:
            self.accents[step_index] = False

    def toggle_accent(self, step_index):
        if not self.steps[step_index]:
            self.steps[step_index] = True
        self.accents[step_index] = not self.accents[step_index]

    def clear_pattern(self):
        self.steps = [False] * Config.NUM_STEPS
        self.accents = [False] * Config.NUM_STEPS

    def select_channel(self, channel):
        if 0 <= channel < Config.NUM_CHANNELS:
            self.selected_channel = channel

    def cycle_sound(self, direction):
        pitches = Config.SOUND_PITCHES[self.selected_channel]
        idx = self.sound_index[self.selected_channel]
        self.sound_index[self.selected_channel] = (idx + direction) % len(pitches)

    def reset_sound(self):
        self.sound_index[self.selected_channel] = 0

    def step_is_active(self, step_index):
        return self.steps[step_index]

    def step_velocity(self, step_index):
        if not self.steps[step_index]:
            return Config.NOTE_VELOCITY
        return (
            Config.ACCENT_VELOCITY
            if self.accents[step_index]
            else Config.NOTE_VELOCITY
        )

    def pad_led_hsb(self, step_index, hue):
        active = self.steps[step_index]
        is_playhead = step_index == self.current_play_step
        accented = active and self.accents[step_index]

        if active:
            if is_playhead or accented:
                brightness = Config.LED_PLAYHEAD_ACTIVE
            else:
                brightness = Config.LED_ACTIVE
        else:
            brightness = (
                Config.LED_PLAYHEAD_EMPTY if is_playhead else Config.LED_OFF
            )
        return (hue, Config.LED_SATURATION, brightness)

    def pad_led_value(self, step_index, color_value):
        active = self.steps[step_index]
        is_playhead = step_index == self.current_play_step

        if is_playhead:
            return (
                Config.LED_SINGLE_PLAYHEAD_ACTIVE
                if active
                else Config.LED_SINGLE_PLAYHEAD_EMPTY
            )
        if active:
            return (
                Config.LED_ACCENT_ACTIVE
                if self.accents[step_index]
                else color_value
            )
        return Config.LED_OFF
