# emacs-mode: -*- python-*-
#
# MIDI map for the AbletonKontrolF1Up2.nckf1 template (Basic page).
# All MIDI channels below are 0-indexed, exactly as they appear in the
# template XML and on the wire.

NUM_CHANNELS = 4
NUM_STEPS = 16
STEP_DURATION_BEATS = 0.25

# One editable/playing window = one bar of 16 steps inside a clip.
WINDOW_BEATS = NUM_STEPS * STEP_DURATION_BEATS  # 4.0 beats

# Windows (variations) per clip. New clips are created this many bars long;
# the filter pots scrub which 1-bar loop window is active per channel.
MAX_WINDOWS = 16

# Default first track for mode 1 (tracks 1-4, 0-indexed).
FIRST_TRACK_INDEX = 0

# ---------------------------------------------------------------- device modes
#
# Hold Browse + turn the encoder to cycle modes:
#   0 -> Drum sequencer on MIDI tracks 1-4
#   1 -> Drum sequencer on MIDI tracks 5-8
#   2 -> Passthrough: all F1 MIDI forwarded to Live's mapping layer
#   3 -> Clip launch grid (4 tracks x 4 scenes, APC-style)
#   4 -> Finger drumming (16 pads from C1, encoder scrolls pad banks)
DEVICE_MODES = (
    {"label": "Drum 1 (tracks 1-4)", "mode": "sequencer", "first_track_index": 0},
    {"label": "Drum 2 (tracks 5-8)", "mode": "sequencer", "first_track_index": 4},
    {"label": "MIDI map (passthrough)", "mode": "passthrough"},
    {"label": "Clip launch (APC)", "mode": "clip_launch", "first_track_index": 0},
    {"label": "Finger drum (MPC)", "mode": "finger_drum"},
)
NUM_DEVICE_MODES = len(DEVICE_MODES)
MODE_PASSTHROUGH_INDEX = 2
MODE_CLIP_LAUNCH_INDEX = 3
MODE_FINGER_DRUM_INDEX = 4

# 7-segment display (Basic page): CC 2 on wire channel 12 (Controller Editor ch 13).
SEGMENT_DISPLAY_CHANNEL = 12
SEGMENT_DISPLAY_CC = 2
MODE_DISPLAY_VALUES = (1, 2, 3, 4, 5)

# ---------------------------------------------------------------- inputs

PAD_CHANNEL = 2
PAD_CC_START = 0
PAD_CC_END = 15

CHANNEL_SELECT_CHANNEL = 0
CHANNEL_SELECT_CCS = (60, 61, 62, 63)

ENCODER_CHANNEL = 0
ENCODER_TURN_CC = 105
ENCODER_PUSH_CC = 106

# Function buttons on the Basic page (gate) — channel 11 on the wire.
# Shift-page fallbacks on channel 12 use different CC numbers (see below).
FUNCTION_CHANNELS = (11, 12)
FUNCTION_CHANNEL = 11
CLEAR_CC = 56
TYPE_CC = 57
SIZE_CC = 58
BROWSE_CC = 59
FUNCTION_CCS = (CLEAR_CC, TYPE_CC, SIZE_CC, BROWSE_CC)
FUNCTION_ROLE_BY_CC = {
    CLEAR_CC: "clear",
    TYPE_CC: "type",
    SIZE_CC: "size",
    BROWSE_CC: "browse",
}
FUNCTION_BUTTON_FALLBACKS = (
    ((12, 54), "clear"),
    ((12, 55), "type"),
    ((12, 56), "size"),
    ((12, 57), "browse"),
)

# Filter pots (absolute 0..127): pot k scrubs channel k's loop window.
POT_CHANNELS = (11, 12, 13)
POT_CCS = (2, 3, 4, 5)

FADERS = ((11, 0), (7, 7), (8, 7), (7, 8))
FADER_FALLBACKS = (((10, 0), 0), ((6, 7), 1), ((6, 8), 3))

# Live's volume parameter: 1.0 = +6 dB; ~0.85 = unity (0 dB).
VOLUME_0DB_NORM = 0.85

# ---------------------------------------------------------------- sounds

_CHROMATIC_FROM_C1 = list(range(36, 36 + 16))
SOUND_PITCHES = [
    list(_CHROMATIC_FROM_C1),
    list(_CHROMATIC_FROM_C1),
    list(_CHROMATIC_FROM_C1),
    list(_CHROMATIC_FROM_C1),
]

# Finger-drum mode: pad bank starts at C1 (MIDI 36); encoder shifts by 16 notes.
FINGER_DRUM_BASE_PITCH = 36
FINGER_DRUM_BANK_SIZE = NUM_STEPS
FINGER_DRUM_MIN_PITCH = 0
FINGER_DRUM_MAX_PITCH = 127
FINGER_DRUM_VELOCITY = 100
FINGER_DRUM_NOTE_OFF_TICKS = 2

# Clip-launch grid: 4 track columns x 4 scene rows (16 pads).
CLIP_LAUNCH_TRACKS = NUM_CHANNELS
CLIP_LAUNCH_SCENE_ROWS = 4

NOTE_VELOCITY = 100
ACCENT_VELOCITY = 127
# Steps at or above this velocity reload as accented.
ACCENT_VELOCITY_THRESHOLD = 115

# ---------------------------------------------------------------- LEDs

LED_MODE = "hsb"

PAD_LED_HSB_CHANNELS = (0, 1, 2)
PAD_LED_CCS = list(range(0, NUM_STEPS))

CHANNEL_HUES = (12, 85, 24, 100)
LED_SATURATION = 127

LED_OFF = 0
LED_PLAYHEAD_EMPTY = 20
LED_ACTIVE = 90
LED_PLAYHEAD_ACTIVE = 127
# Accented steps use full saturation + a touch more brightness when lit.
LED_ACCENT_ACTIVE = 127

LED_USE_NOTES = False
LED_CHANNEL = 2
LED_PAD_NUMBERS = list(range(0, NUM_STEPS))
CHANNEL_COLOR_VALUES = (4, 80, 20, 112)
LED_SINGLE_PLAYHEAD_EMPTY = 16
LED_SINGLE_PLAYHEAD_ACTIVE = 127

# ---------------------------------------------------------------- behavior

COPY_PATTERN_ON_SCENE_SELECT = False

DEBUG_MIDI = True
DEBUG_MIDI_MAX = 60
# Always log Basic-page function-button CCs even after DEBUG_MIDI_MAX is reached.
DEBUG_FUNCTION_MIDI = True
DEBUG_LEDS = False
