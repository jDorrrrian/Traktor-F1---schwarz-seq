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
        self.finger_drum_bank = 0
        self.finger_drum_lit_pad = -1

        # ---- melodic sequencer state ----
        n = Config.MELODIC_MAX_STEPS
        self.mel_active = [False] * n
        self.mel_note = [Config.MELODIC_DEFAULT_PITCH] * n
        self.mel_octave = [Config.MELODIC_DEFAULT_OCTAVE] * n
        self.mel_velocity = [Config.MELODIC_DEFAULT_VELOCITY] * n
        self.mel_length = [Config.STEP_DURATION_BEATS * 0.9] * n
        self.mel_release = [Config.MELODIC_DEFAULT_RELEASE] * n
        self.mel_length_steps = Config.MELODIC_DEFAULT_LENGTH
        self.mel_page = 0
        self.mel_held_pads = set()
        self.mel_tentative = {}
        self.mel_last_step = 0
        self.mel_play_step = -1
        self.mel_key = 0
        self.mel_scale_type = 0

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

    def cycle_finger_drum_bank(self, direction):
        self.finger_drum_bank += direction

    def reset_finger_drum_bank(self):
        self.finger_drum_bank = 0

    def finger_drum_pitch(self, pad_index):
        pitch = (
            Config.FINGER_DRUM_BASE_PITCH
            + self.finger_drum_bank * Config.FINGER_DRUM_BANK_SIZE
            + pad_index
        )
        return max(
            Config.FINGER_DRUM_MIN_PITCH,
            min(Config.FINGER_DRUM_MAX_PITCH, pitch),
        )

    def finger_drum_bank_clamped(self):
        """Return bank index so the lowest pad stays within MIDI range."""
        max_bank = (
            Config.FINGER_DRUM_MAX_PITCH
            - Config.FINGER_DRUM_BASE_PITCH
            - (Config.FINGER_DRUM_BANK_SIZE - 1)
        ) // Config.FINGER_DRUM_BANK_SIZE
        min_bank = (
            Config.FINGER_DRUM_MIN_PITCH - Config.FINGER_DRUM_BASE_PITCH
        ) // Config.FINGER_DRUM_BANK_SIZE
        return max(min_bank, min(max_bank, self.finger_drum_bank))

    def clamp_finger_drum_bank(self):
        self.finger_drum_bank = self.finger_drum_bank_clamped()

    def finger_drum_pad_led_value(self, pad_index):
        if pad_index == self.finger_drum_lit_pad:
            return Config.LED_PLAYHEAD_ACTIVE
        return Config.LED_ACTIVE

    # ------------------------------------------------------------ melodic
    def mel_page_count(self):
        steps = max(1, self.mel_length_steps)
        pages = (steps + Config.MELODIC_STEPS_PER_PAGE - 1) // Config.MELODIC_STEPS_PER_PAGE
        return max(1, min(Config.MELODIC_MAX_PAGES, pages))

    def mel_global_step(self, pad):
        return self.mel_page * Config.MELODIC_STEPS_PER_PAGE + pad

    def mel_step_in_range(self, step):
        return 0 <= step < self.mel_length_steps

    def mel_effective_pitch(self, step):
        pitch = self.mel_note[step] + 12 * self.mel_octave[step]
        return max(0, min(127, pitch))

    def mel_toggle_step(self, step):
        self.mel_active[step] = not self.mel_active[step]
        return self.mel_active[step]

    def mel_target_steps(self):
        """Steps that faders / encoder should edit: held pads, else last step."""
        if self.mel_held_pads:
            return sorted(self.mel_held_pads)
        if 0 <= self.mel_last_step < Config.MELODIC_MAX_STEPS:
            return [self.mel_last_step]
        return []

    def mel_change_pitch(self, step, direction):
        self.mel_note[step] = max(0, min(127, self.mel_note[step] + direction))

    def mel_set_octave_from_fader(self, step, value):
        span = Config.MELODIC_OCTAVE_MAX - Config.MELODIC_OCTAVE_MIN
        self.mel_octave[step] = Config.MELODIC_OCTAVE_MIN + int(round(value / 127.0 * span))

    def mel_set_velocity_from_fader(self, step, value):
        self.mel_velocity[step] = max(1, min(127, value))

    def mel_set_length_from_fader(self, step, value):
        lo = Config.MELODIC_LENGTH_MIN_BEATS
        hi = Config.MELODIC_LENGTH_MAX_BEATS
        self.mel_length[step] = lo + (value / 127.0) * (hi - lo)

    def mel_set_release_from_fader(self, step, value):
        self.mel_release[step] = max(0, min(127, value))

    def mel_change_length_steps(self, direction):
        self.mel_length_steps = max(
            Config.MELODIC_LENGTH_MIN_STEPS,
            min(Config.MELODIC_LENGTH_MAX_STEPS, self.mel_length_steps + direction),
        )
        if self.mel_page >= self.mel_page_count():
            self.mel_page = self.mel_page_count() - 1
        return self.mel_length_steps

    def mel_change_key(self, direction):
        self.mel_key = (self.mel_key + direction) % Config.MELODIC_KEY_COUNT
        return self.mel_key

    def mel_change_scale_type(self, direction):
        self.mel_scale_type = (
            self.mel_scale_type + direction
        ) % Config.MELODIC_SCALE_TYPE_COUNT
        return self.mel_scale_type

    def mel_select_page(self, page):
        if 0 <= page < Config.MELODIC_MAX_PAGES:
            self.mel_page = page
            return True
        return False

    def mel_extend_length_for(self, step):
        """Grow the sequence length (snapped to a page) to include step."""
        if step < self.mel_length_steps:
            return False
        page = step // Config.MELODIC_STEPS_PER_PAGE
        new_len = min(
            Config.MELODIC_MAX_STEPS,
            (page + 1) * Config.MELODIC_STEPS_PER_PAGE,
        )
        if new_len == self.mel_length_steps:
            return False
        self.mel_length_steps = new_len
        return True

    def mel_reset_step(self, step):
        self.mel_note[step] = Config.MELODIC_DEFAULT_PITCH
        self.mel_octave[step] = Config.MELODIC_DEFAULT_OCTAVE
        self.mel_velocity[step] = Config.MELODIC_DEFAULT_VELOCITY
        self.mel_length[step] = Config.STEP_DURATION_BEATS * 0.9
        self.mel_release[step] = Config.MELODIC_DEFAULT_RELEASE

    def mel_clear(self):
        n = Config.MELODIC_MAX_STEPS
        self.mel_active = [False] * n
        self.mel_note = [Config.MELODIC_DEFAULT_PITCH] * n
        self.mel_octave = [Config.MELODIC_DEFAULT_OCTAVE] * n
        self.mel_velocity = [Config.MELODIC_DEFAULT_VELOCITY] * n
        self.mel_length = [Config.STEP_DURATION_BEATS * 0.9] * n
        self.mel_release = [Config.MELODIC_DEFAULT_RELEASE] * n
        self.mel_tentative = {}

    def mel_load(self, notes_by_step, length_steps):
        """notes_by_step: dict step -> (pitch, velocity, duration, release)."""
        self.mel_clear()
        if length_steps:
            self.mel_length_steps = max(
                Config.MELODIC_LENGTH_MIN_STEPS,
                min(Config.MELODIC_LENGTH_MAX_STEPS, length_steps),
            )
        for step, (pitch, velocity, duration, release) in notes_by_step.items():
            if not (0 <= step < Config.MELODIC_MAX_STEPS):
                continue
            self.mel_active[step] = True
            self.mel_note[step] = max(0, min(127, int(pitch)))
            self.mel_octave[step] = 0
            self.mel_velocity[step] = max(1, min(127, int(velocity)))
            self.mel_length[step] = float(duration)
            self.mel_release[step] = max(0, min(127, int(release)))
        if self.mel_page >= self.mel_page_count():
            self.mel_page = self.mel_page_count() - 1

    def mel_pad_led_hsb(self, pad, hue):
        step = self.mel_global_step(pad)
        active = self.mel_active[step]
        is_playhead = step == self.mel_play_step
        in_range = self.mel_step_in_range(step)
        is_held = step in self.mel_held_pads

        if is_held:
            return (hue, Config.LED_SATURATION, Config.LED_PLAYHEAD_ACTIVE)
        if active:
            brightness = (
                Config.LED_PLAYHEAD_ACTIVE if is_playhead else Config.LED_ACTIVE
            )
        elif is_playhead:
            brightness = Config.LED_PLAYHEAD_EMPTY
        elif in_range:
            # Faintly mark steps that belong to the current sequence length.
            brightness = Config.LED_PLAYHEAD_EMPTY // 2
        else:
            brightness = Config.LED_OFF
        return (hue, Config.LED_SATURATION, brightness)

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
