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
DEVICE_MODES = (
    {"label": "Drum 1 (tracks 1-4)", "first_track_index": 0},
    {"label": "Drum 2 (tracks 5-8)", "first_track_index": 4},
    {"label": "MIDI map (passthrough)", "passthrough": True},
)
NUM_DEVICE_MODES = len(DEVICE_MODES)
MODE_PASSTHROUGH_INDEX = 2

# 7-segment display (Basic page): CC 2 on wire channel 12 (Controller Editor ch 13).
SEGMENT_DISPLAY_CHANNEL = 12
SEGMENT_DISPLAY_CC = 2
# One value per device mode — sent as a single CC to update the display.
MODE_DISPLAY_VALUES = (1, 2, 3)

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

# ---------------------------------------------------------------- sounds

_CHROMATIC_FROM_C1 = list(range(36, 36 + 16))
SOUND_PITCHES = [
    list(_CHROMATIC_FROM_C1),
    list(_CHROMATIC_FROM_C1),
    list(_CHROMATIC_FROM_C1),
    list(_CHROMATIC_FROM_C1),
]

# ---------------------------------------------------------------- notes

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

LAUNCH_ON_SCENE_SELECT = True
COPY_PATTERN_ON_SCENE_SELECT = True

DEBUG_MIDI = True
DEBUG_MIDI_MAX = 60
# Always log Basic-page function-button CCs even after DEBUG_MIDI_MAX is reached.
DEBUG_FUNCTION_MIDI = True
DEBUG_LEDS = False
