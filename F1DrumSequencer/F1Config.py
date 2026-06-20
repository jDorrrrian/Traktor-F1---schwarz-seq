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
    {"label": "Melodic sequencer", "mode": "melodic"},
)
NUM_DEVICE_MODES = len(DEVICE_MODES)
MODE_PASSTHROUGH_INDEX = 2
MODE_CLIP_LAUNCH_INDEX = 3
MODE_FINGER_DRUM_INDEX = 4
MODE_MELODIC_INDEX = 5

# 7-segment display (Basic page): CC 2 on wire channel 12 (Controller Editor ch 13).
SEGMENT_DISPLAY_CHANNEL = 12
SEGMENT_DISPLAY_CC = 2
MODE_DISPLAY_VALUES = (1, 2, 3, 4, 5, 6)

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
#
# On the user's AbletonKontrolF1Up2 template the physical top buttons report:
#   Sync=51  Quant=52  Capture=53  Reverse=54  Type=55  Size=56  Browse=57
# Those match the channel-12 fallback set below. Quant is added so the melodic
# sequencer can use Quant+encoder to send a "key" CC. If your unit reports a
# different CC, enable DEBUG_FUNCTION_MIDI and update QUANT_CC.
FUNCTION_CHANNELS = (11, 12)
FUNCTION_CHANNEL = 11
CLEAR_CC = 56
TYPE_CC = 57
SIZE_CC = 58
BROWSE_CC = 59
QUANT_CC = 52
FUNCTION_CCS = (CLEAR_CC, TYPE_CC, SIZE_CC, BROWSE_CC, QUANT_CC)
FUNCTION_ROLE_BY_CC = {
    CLEAR_CC: "clear",
    TYPE_CC: "type",
    SIZE_CC: "size",
    BROWSE_CC: "browse",
    QUANT_CC: "quant",
}
FUNCTION_BUTTON_FALLBACKS = (
    ((12, 54), "clear"),
    ((12, 55), "type"),
    ((12, 56), "size"),
    ((12, 57), "browse"),
    ((12, 52), "quant"),
)

# Filter pots (absolute 0..127): pot k scrubs channel k's loop window.
POT_CHANNELS = (11, 12, 13)
POT_CCS = (2, 3, 4, 5)

FADERS = ((11, 0), (7, 7), (8, 7), (7, 8))
FADER_FALLBACKS = (((10, 0), 0), ((6, 7), 1), ((6, 8), 3))

# Channel/page buttons (CC 60-63): while held, the encoder remaps the track that
# button controls (+/- one track per tick). Best with the buttons in Gate mode so
# the hold ends on release. In Increment mode (press only) the button latches the
# hold on; press it again to release.

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

# ---------------------------------------------------------------- melodic sequencer
#
# A single-track melodic step sequencer. The 16 pads edit one "page" of steps;
# the four bottom buttons (CC 60-63) select page 1-4 for up to MELODIC_MAX_STEPS.
# Notes are written chromatically into the clip — put an Ableton Scale device on
# the track and the F1 only ever has to move notes by semitone.
MELODIC_STEPS_PER_PAGE = NUM_STEPS  # 16
MELODIC_MAX_PAGES = 4
MELODIC_MAX_STEPS = MELODIC_STEPS_PER_PAGE * MELODIC_MAX_PAGES  # 64

# Dedicated track for the melodic sequencer (0-indexed). This is fully separate
# from the drum channels — set it to whichever track holds your scale instrument.
# You can also retarget it live: hold a bottom button and turn the encoder.
MELODIC_FIRST_TRACK_INDEX = 8

# Per-step defaults.
MELODIC_DEFAULT_LENGTH = MELODIC_STEPS_PER_PAGE  # active step count of a fresh seq
MELODIC_DEFAULT_PITCH = 60                        # C3 before the Scale device snaps
MELODIC_DEFAULT_VELOCITY = 100
MELODIC_DEFAULT_OCTAVE = 0
MELODIC_DEFAULT_RELEASE = 64

# Fader -> per-step ranges (fader value is 0..127).
MELODIC_OCTAVE_MIN = -2
MELODIC_OCTAVE_MAX = 2
MELODIC_LENGTH_MIN_BEATS = 0.05
MELODIC_LENGTH_MAX_BEATS = STEP_DURATION_BEATS * MELODIC_STEPS_PER_PAGE  # up to 1 bar

# Sequence-length editing (Size + encoder), in steps.
MELODIC_LENGTH_MIN_STEPS = 1
MELODIC_LENGTH_MAX_STEPS = MELODIC_MAX_STEPS

# Key (Quant + encoder) and scale type (Type + encoder) are emitted as CCs that
# you MIDI-map in Live (e.g. to a Scale device's Root / Scale). Values are spread
# across 0..127 so a mapped discrete parameter steps through every option.
MELODIC_OUT_CHANNEL = 5
MELODIC_KEY_CC = 20
MELODIC_SCALE_TYPE_CC = 21
MELODIC_KEY_COUNT = 12
MELODIC_SCALE_TYPE_COUNT = 16

# In melodic mode the four filter pots emit these CCs (one per pot) into Live so
# you can MIDI-map them (e.g. to a filter cutoff). In the drum modes the pots keep
# scrubbing the loop window as before.
MELODIC_POT_OUT_CHANNEL = 5
MELODIC_POT_CCS = (22, 23, 24, 25)

# Melodic pad color (HSB hue) and the page-button hue for the selected page.
MELODIC_HUE = 60

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
