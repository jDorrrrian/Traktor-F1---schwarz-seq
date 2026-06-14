# Traktor Kontrol F1 Drum Sequencer

Python **MIDI Remote Script** for Ableton Live — no Max for Live required.

The F1 becomes a 4-channel, 16-step drum sequencer that writes patterns into Live clip slots. The **active row is whatever scene is selected in Ableton** — change the scene in Live and you get a fresh row of four clips to sequence. The F1 feels like a standalone sequencer sitting on top of the set.

## Features

| Control | Function |
|---------|----------|
| **4×4 pad grid** | Toggle the 16 steps of the selected channel's clip in the selected scene |
| **Pad LEDs** | Active steps lit in the channel color; the playing step lights brightest as the sequencer sweeps across |
| **Bottom row (CC 60–63)** | Channel select — **controller-internal only**, never moves Ableton's selection |
| **Encoder turn** | Sound select — changes the drum pitch of the current channel (the pattern moves to the new sound) |
| **Encoder push** | Reset sound to the starting position (sound 1) |
| **Selecting a scene in Ableton** | Copies the playing row's patterns into the new scene, switches to it, and launches it |
| **4 filter pots (top)** | Move the loop window for each channel's clip — pot k always controls channel k |
| **4 faders** | Track volume (tracks 1–4) |
| **Reverse (CC 56, ch 11)** | Clear the current channel's entire clip |
| **Type (CC 57) + pad** | Hold Type and tap a step to toggle an accent (higher velocity) |
| **Browse (CC 59) + encoder** | Hold Browse and turn encoder to cycle device mode |
| **Size (CC 58)** | Reserved |

### Channel colors

Each channel has its own pad color (configurable via `CHANNEL_HUES` in `F1Config.py`):

| Channel | Color |
|---------|-------|
| 1 | Orange |
| 2 | Blue |
| 3 | Yellow |
| 4 | Purple |

## Requirements

- Ableton Live 11+ (uses `add_new_notes` / `remove_notes_extended`)
- Traktor Kontrol F1 in **MIDI mode** (SHIFT + BROWSE)
- NI **Controller Editor** template matching the MIDI map below

## Installation

### 1. Install the remote script

From this project folder, run:

```bash
./install.sh
```

This copies `F1DrumSequencer/` to:

- Live's built-in **MIDI Remote Scripts** folder (inside the Ableton app)
- **`~/Music/Ableton/User Library/Remote Scripts/`** (survives Live updates)

Or copy manually:

**macOS (inside app bundle)**

```
/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts/
```

**macOS (User Library — recommended)**

```
~/Music/Ableton/User Library/Remote Scripts/
```

Your folder must contain:

```
F1DrumSequencer/
  __init__.py
  F1DrumSequencer.py
  F1Config.py
  SequencerState.py
  ClipWriter.py
```

> **Important:** Live 12 loads scripts as Python packages. Do not rename `F1Config.py` back to `Config.py` — that name conflicts with Ableton's internal modules and prevents the script from appearing in Preferences.

### 2. Restart Ableton Live

Remote scripts are only loaded at startup.

### 3. Select the control surface

1. **Settings → Link / Tempo / MIDI**
2. **Control Surface** dropdown → **F1DrumSequencer**
3. **Input** → Traktor Kontrol F1
4. **Output** → Traktor Kontrol F1
5. Enable **Track** on both input and output

### 4. F1 MIDI template (required)

The script expects the **AbletonKontrolF1Up2** MIDI template (modified from trash80's AbletonKontrolF1Up). Without it, pads/encoder use different CCs and nothing will respond.

1. Open **NI Controller Editor**
2. **Templates → Edit → Append → Open**
3. Load `templates/AbletonKontrolF1Up2.nckf1` from this project
4. **File → Send to Device**
5. On the F1: hold **SHIFT + BROWSE** to enter MIDI mode
6. Make sure the **Basic** page is active

**Pad LED feedback (critical):** For each pad in the grid, open the pad in Controller Editor and confirm:

- **Pad behavior:** **Trigger** (not gate/toggle variants that ignore remote feedback)
- **Color mode:** **HSB** (required for orange/blue/yellow/purple per channel)
- **LED / illumination:** driven by **MIDI in** (incoming MIDI from Live), not local-only lighting

If pads respond to presses but never change color from the script, this is almost always the cause — Live was sending HSB correctly, but the template wasn't applying incoming MIDI to the pad LEDs. Re-import `AbletonKontrolF1Up2.nckf1` if a pad's color mode gets stuck after editing.

| Control | Channel (0-indexed) | CC | Behavior |
|---------|---------------------|-----|----------|
| Pad grid | 2 | 0–15 | increment (any value = press) |
| Channel select | 0 | 60–63 | increment (any value = press) |
| Encoder turn | 0 | 105 | comp mode: 1 = CW, 127 = CCW |
| Encoder push | 0 | 106 | gate 0/127 |
| Clear (Reverse) | 11 | 56 | gate 0/127 |
| Type (accent mod) | 11 | 57 | hold + pad |
| Size / Browse | 11 | 58 / 59 | reserved |
| Pattern pots (filters) | 12 | 2–5 | absolute 0–127 |
| Volume faders | 11 / 7 / 8 / 7 | 0 / 7 / 7 / 8 | absolute 0–127 |

### 5. Avoid MIDI port conflicts

Only **one** control surface should use the F1 input. In **Settings → MIDI**:

- **F1DrumSequencer** → Input: Traktor Kontrol F1, Output: Traktor Kontrol F1
- Set **Input = None** on any other control surface that was using the F1 (e.g. Komplete Kontrol)
- F1 **Input**: **Remote = ON** (required)
- F1 **Output**: **Remote = ON** (required for pad LEDs)

Adjust `F1Config.py` if your template differs.

## Ableton session setup

1. Create **4 MIDI tracks** with Drum Racks (or instruments)
2. Tracks map to channels starting at `FIRST_TRACK_INDEX` in `F1Config.py` (default: tracks 1–4 = indices 0–3)
3. Create one or more **scenes** — each scene is a "row" of four clips, one per channel

### The scene-row model

The sequencer always works in the **scene currently selected in Ableton**. For the four sequencer tracks, that scene's row of clip slots is the row the F1 edits:

```
                track 1    track 2    track 3    track 4
                (ch 1)     (ch 2)     (ch 3)     (ch 4)
scene 1   ->    clip       clip       clip       clip     <- selected = active row
scene 2         clip       clip       clip       clip
scene 3         clip       clip       clip       clip
```

- **Selecting a different scene in Ableton** copies the previous row's patterns into the new scene, switches to it, and launches it
- Each clip can hold up to **16 one-bar loop windows** (`MAX_WINDOWS`); the **filter pots** scrub which window is playing/editing per channel
- The 16 pads edit the **current loop window** of the selected channel
- **Channel select on the F1 is controller-internal** — it never moves Ableton's track or scene selection
- If a slot is empty, the script creates a multi-bar MIDI clip the first time you edit
- **Hold Type + tap a pad** to accent that step (velocity 127 vs 100)
- **Reverse** clears the entire clip for the selected channel

This is built for livesets: duplicate a groove into a new scene, scrub pots to find variations, accent hits live.

## Configuration

Edit `F1DrumSequencer/F1Config.py`:

```python
FIRST_TRACK_INDEX = 0
MAX_WINDOWS = 16                 # variations per clip (16 bars)
COPY_PATTERN_ON_SCENE_SELECT = True
SOUND_PITCHES = [ ... ]
CHANNEL_HUES = (12, 85, 24, 100)
ACCENT_VELOCITY = 127
```

After editing, restart Live.

## How the step sequencer works

1. **Select a scene** in Ableton — the previous row's patterns are copied in and launched
2. Press a **bottom row button** (CC 60–63) to select channel 1–4
3. **Turn the encoder** to change the drum sound; **push** to reset to sound 1
4. **Turn a filter pot** to move that channel's loop window (variations within the clip)
5. Tap **pads** to toggle steps in the current loop window
6. **Hold Type + tap a pad** to accent that step
7. Press **Reverse** to clear the current channel's clip
8. **Hold Browse + turn encoder** to switch mode (Drum 1 → Drum 2 → MIDI map)

### Device modes

| Mode | Function |
|------|----------|
| **Drum 1** | 4-channel sequencer on tracks 1–4 |
| **Drum 2** | 4-channel sequencer on tracks 5–8 |
| **MIDI map** | Passthrough — F1 MIDI is forwarded to Live so you can map controls in Ableton's MIDI mapping mode. Pad LEDs turn off. Hold Browse + encoder to return to a drum mode. |

In **MIDI map** mode, enable **Remote** on the F1 input in Live's MIDI settings and use Live's MIDI mapping (or session Remote assignments) as usual.

The **7-segment display** next to the encoder shows the mode number (**1**, **2**, or **3**). Tune `MODE_DISPLAY_VALUES` in `F1Config.py` if the glyphs read wrong on your unit.

## Debugging

Remote script logs appear in Live's Log.txt:

**macOS:** `~/Library/Preferences/Ableton/Live */Log.txt`

Look for lines starting with `F1DrumSequencer` or `RemoteScriptError` mentioning `F1DrumSequencer`.

After restarting Live, press a few pads and look for `F1 raw` lines (shows what the F1 actually sends) and `F1 step` lines (confirms the sequencer received the press).

If the script still does not appear after install, run `./install.sh` again, **fully quit and restart Live**, and check Log.txt for `RemoteScriptError`.

### Debugging the LEDs

**Most common fix:** In Controller Editor, set each pad to **Trigger**, **HSB** color mode, and **MIDI in** for LED feedback.

Set `DEBUG_LEDS = True` in `F1Config.py` to log LED messages to Log.txt.

## Project layout

```
F1DrumSequencer/           ← install this folder in Live
  __init__.py
  F1DrumSequencer.py       ← main control surface
  F1Config.py                ← MIDI map + track settings
  SequencerState.py        ← pattern/step memory
  ClipWriter.py            ← Live clip read/write

js/                        ← optional legacy Max for Live version
  f1_drum_sequencer.js
  lib/
```

## Max for Live version

The `js/` folder contains an earlier Max for Live implementation. The **remote script is the recommended approach** if you don't have Max for Live.

## Next steps

**Size / Browse** (CC 58–59) are forwarded but unassigned — wire them up in `F1DrumSequencer.py` → `_handle_cc()`.
