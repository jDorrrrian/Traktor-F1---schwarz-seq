# WIP: Traktor Kontrol F1 Drum Sequencer

Python **MIDI Remote Script** for Ableton Live — no Max for Live required. Inspired by the Henrik Schwartz m4l sequencer as shown in his masterclasses. Stil WIP.

The F1 becomes a 4-channel, 16-step drum sequencer that writes patterns into Live clip slots. The **active row is whatever scene is selected in Ableton** — change the scene in Live and you get a fresh row of four clips to sequence. The F1 feels like a standalone sequencer sitting on top of the set.

## Features

| Control | Function |
|---------|----------|
| **4×4 pad grid** | Toggle the 16 steps of the selected channel's clip in the selected scene |
| **Pad LEDs** | Active steps lit in the channel color; the playing step lights brightest as the sequencer sweeps across |
| **Bottom row (CC 60–63)** | Channel select — **controller-internal only**, never moves Ableton's selection. **Hold a button + turn the encoder** to remap which Live track that channel controls (default 1→track 1 … 4→track 4) |
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
8. **Hold a bottom-row button + turn the encoder** to remap which Live track that channel button controls (defaults to 1–4; set channel buttons to **Gate** so the hold is detected)
9. **Hold Browse + turn encoder** to switch mode (Drum 1 → Drum 2 → MIDI map → …)

### Device modes

Hold **Browse + turn the encoder** to cycle through all modes:

| # | Mode | Function |
|---|------|----------|
| 1 | **Drum 1** | 4-channel drum sequencer on tracks 1–4 |
| 2 | **Drum 2** | 4-channel drum sequencer on tracks 5–8 |
| 3 | **MIDI map** | Passthrough — F1 MIDI is forwarded to Live so you can map controls in Ableton's MIDI mapping mode. Pad LEDs turn off. |
| 4 | **Clip launch** | 4 tracks × 4 scenes APC-style clip grid |
| 5 | **Finger drum** | 16 pads from C1; encoder scrolls pad banks |
| 6 | **Melodic sequencer** | Single-track melodic step sequencer (see below) |

In **MIDI map** mode, enable **Remote** on the F1 input in Live's MIDI settings and use Live's MIDI mapping (or session Remote assignments) as usual.

The **7-segment display** next to the encoder shows the mode number (**1**–**6**). Tune `MODE_DISPLAY_VALUES` in `F1Config.py` if the glyphs read wrong on your unit.

## Melodic sequencer mode

Mode 6 turns the F1 into a melodic step sequencer for **one** track (set by `MELODIC_FIRST_TRACK_INDEX`, default track 1). It writes one note per active step into the track's clip in the selected scene, exactly like the drum modes write patterns — but each step has its own pitch and per-note parameters.

It assumes you put an **Ableton Scale device** (or any scale-quantizing instrument) on the track. The F1 only ever moves notes **chromatically by semitone**; the Scale device keeps everything in key.

| Control | Function |
|---------|----------|
| **Tap pad** | Toggle the step on/off (writes/removes the note in the clip) |
| **Hold pad + encoder** | Raise / lower that step's note by a semitone (holding only *selects* — it does not toggle) |
| **Hold pad + Fader 1** | Octave (`MELODIC_OCTAVE_MIN..MAX`) |
| **Hold pad + Fader 2** | Velocity |
| **Hold pad + Fader 3** | Note length |
| **Hold pad + Fader 4** | Release velocity (map your instrument to react to it) |
| **Hold pad + encoder push** | Reset that step's note/params to defaults |
| **Tap bottom button (CC 60–63)** | Switch page 1–4 (16 steps each). Editing a step on a later page extends the sequence to that page (up to 64 steps) |
| **Hold bottom button + encoder** | Change which Live track the melodic sequencer targets (buttons must be **Gate** mode) |
| **Size + encoder** | Sequence length in steps (shown on the display) |
| **Quant + encoder** | Key — sends CC on `MELODIC_OUT_CHANNEL`/`MELODIC_KEY_CC` |
| **Type + encoder** | Scale type — sends CC on `MELODIC_OUT_CHANNEL`/`MELODIC_SCALE_TYPE_CC` |
| **Browse + encoder** | Switch device mode (as everywhere) |
| **Filter pots** | Forwarded to Live so you can MIDI-map them yourself |
| **Reverse (Clear)** | Clear the whole melodic sequence |

> **Pads must be set to Gate** (send 127 on press, 0 on release) for *hold-to-edit* to work. In NI Controller Editor set the 16 pads' behavior to **Gate**. If your pads only send on press, the faders/encoder will edit the **last** step you tapped instead of the one you're holding.

### Mapping key & scale type in Live

`Quant + encoder` and `Type + encoder` emit plain CCs (defaults: **channel 6** — i.e. 0-indexed 5 — CC **20** for key and CC **21** for scale type). Their values are spread across 0–127 so a mapped discrete parameter steps through every option:

1. In Live, enter MIDI map mode (Cmd-M)
2. Click the Scale device's **Root Note**, then turn the encoder while holding **Quant**
3. Click the Scale device's **Scale** selector, then turn the encoder while holding **Type**

Adjust `MELODIC_OUT_CHANNEL`, `MELODIC_KEY_CC`, `MELODIC_SCALE_TYPE_CC`, `MELODIC_KEY_COUNT`, and `MELODIC_SCALE_TYPE_COUNT` in `F1Config.py` to match.

> **Quant button:** the script expects the F1 Quant button on CC **52** (`QUANT_CC`). If yours differs, set `DEBUG_FUNCTION_MIDI = True`, press Quant, and read the CC from Live's `Log.txt`, then update `QUANT_CC`.

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

In the drum modes, **Size** is still unassigned — wire it up in `F1DrumSequencer.py` → `_on_function_button()`. (In melodic mode it already sets the sequence length.)
