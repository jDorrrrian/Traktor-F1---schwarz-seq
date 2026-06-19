# emacs-mode: -*- python-*-

from __future__ import absolute_import, print_function, unicode_literals

import Live

from . import F1Config as Config


class ClipWriter(object):
    def __init__(self, song, log_fn=None, first_track_index=None):
        self._song = song
        self._log_fn = log_fn
        self._first_track_index = (
            first_track_index if first_track_index is not None else Config.FIRST_TRACK_INDEX
        )
        # When set, sequencer read/write uses this row instead of Live's selection.
        self._working_scene_index = None

    def set_first_track_index(self, index):
        self._first_track_index = index

    def first_track_index(self):
        return self._first_track_index

    def _log(self, message):
        if self._log_fn:
            self._log_fn(message)

    # ------------------------------------------------------------ location

    def scene_index(self):
        try:
            scene = self._song.view.selected_scene
            scenes = self._song.scenes
            for i in range(len(scenes)):
                if scenes[i] == scene:
                    return i
        except (RuntimeError, AttributeError):
            pass
        return None

    def set_working_scene_index(self, scene_index):
        """Lock sequencer I/O to a scene row (standalone from Live's selection)."""
        self._working_scene_index = scene_index

    def working_scene_index(self):
        return self._working_scene_index

    def _resolve_scene_index(self, channel, scene_index=None):
        if scene_index is not None:
            return scene_index
        playing = self.playing_scene_index(channel)
        if playing is not None:
            return playing
        if self._working_scene_index is not None:
            return self._working_scene_index
        return self.scene_index()

    def active_scene_index(self, channel):
        """Scene row used for pots, pads, and display on this channel."""
        return self._resolve_scene_index(channel)

    def playing_scene_index(self, channel):
        """Scene row of the clip currently playing or triggered on this track."""
        track = self._track(channel)
        if track is None:
            return None
        try:
            for scene_i, slot in enumerate(track.clip_slots):
                if not slot.has_clip:
                    continue
                try:
                    if slot.is_playing or slot.is_triggered:
                        return scene_i
                except (RuntimeError, AttributeError):
                    try:
                        if slot.is_triggered:
                            return scene_i
                    except (RuntimeError, AttributeError):
                        pass
        except (RuntimeError, AttributeError):
            pass
        return None

    def get_playing_clip(self, channel):
        scene = self.playing_scene_index(channel)
        if scene is None:
            return None
        return self.get_clip(channel, scene)

    def _track(self, channel):
        track_index = self._first_track_index + channel
        tracks = self._song.tracks
        if track_index < 0 or track_index >= len(tracks):
            return None
        return tracks[track_index]

    def _slot(self, channel, scene_index=None):
        track = self._track(channel)
        if track is None:
            return None
        scene_index = self._resolve_scene_index(channel, scene_index)
        if scene_index is None or scene_index >= len(track.clip_slots):
            return None
        return track.clip_slots[scene_index]

    def get_clip(self, channel, scene_index=None):
        slot = self._slot(channel, scene_index)
        if slot is None or not slot.has_clip:
            return None
        clip = slot.clip
        return clip if clip.is_midi_clip else None

    def ensure_clip(self, channel, scene_index=None):
        slot = self._slot(channel, scene_index)
        if slot is None:
            self._log(
                "F1 no clip slot: ch=%d (need a selected scene and %d MIDI tracks)"
                % (channel + 1, self._first_track_index + Config.NUM_CHANNELS)
            )
            return None
        if not slot.has_clip:
            try:
                slot.create_clip(Config.MAX_WINDOWS * Config.WINDOW_BEATS)
                clip = slot.clip
                clip.looping = True
                clip.loop_start = 0.0
                clip.loop_end = Config.WINDOW_BEATS
                slot.fire()
                self._log(
                    "F1 created + fired clip ch=%d scene=%d"
                    % (channel + 1, self._resolve_scene_index(channel, scene_index) + 1)
                )
            except (RuntimeError, AttributeError) as exc:
                self._log("F1 create_clip failed ch=%d: %s" % (channel + 1, exc))
                return None
        clip = slot.clip
        return clip if clip.is_midi_clip else None

    # ------------------------------------------------------------ windows

    def window_count(self, channel, scene_index=None):
        return Config.MAX_WINDOWS

    def current_window(self, channel, scene_index=None):
        clip = self.get_clip(channel, scene_index)
        if clip is None:
            return 0
        return int(clip.loop_start / Config.WINDOW_BEATS)

    def set_loop_window(self, channel, window, scene_index=None):
        clip = self.get_clip(channel, scene_index)
        if clip is None:
            return False

        window = max(0, min(self.window_count(channel, scene_index) - 1, window))
        start = float(window * Config.WINDOW_BEATS)
        end = start + Config.WINDOW_BEATS

        try:
            clip.looping = True
        except (RuntimeError, AttributeError):
            pass

        # Move start/end markers first so the loop brace and start marker can
        # always be placed (Live rejects start_marker >= end_marker, which is
        # why this was inconsistent across clips of different lengths).
        markers_ok = self._move_clip_markers(clip, start, end)

        try:
            if start >= clip.loop_end:
                clip.loop_end = end
                clip.loop_start = start
            else:
                clip.loop_start = start
                clip.loop_end = end
        except RuntimeError:
            try:
                clip.position = start
            except (RuntimeError, AttributeError) as exc:
                self._log("F1 loop move failed ch=%d: %s" % (channel + 1, exc))
                return False

        self._log(
            "F1 loop ch=%d -> window %d (%.0f..%.0f beats)%s"
            % (
                channel + 1,
                window + 1,
                start,
                end,
                "" if markers_ok else " (markers not moved)",
            )
        )
        return True

    def _move_clip_markers(self, clip, start, end):
        """Place the clip's start/end markers around [start, end] robustly.

        Live forbids start_marker >= end_marker, so we first drop the start
        marker to 0, then extend the end marker past the window, then set the
        start marker. MIDI clips can be extended freely, so this works no
        matter how long the clip originally was. This makes launching the clip
        begin inside the looped region instead of playing everything before it.
        """
        ok = True
        try:
            clip.start_marker = 0.0
        except (RuntimeError, AttributeError):
            ok = False
        try:
            if clip.end_marker < end:
                clip.end_marker = end
        except (RuntimeError, AttributeError):
            ok = False
        try:
            clip.start_marker = start
        except (RuntimeError, AttributeError):
            ok = False
        return ok

    def _window_bounds(self, clip):
        start = float(clip.loop_start)
        return start, start + Config.WINDOW_BEATS

    # ------------------------------------------------------------ notes

    def read_pattern(self, channel, scene_index=None):
        steps = [False] * Config.NUM_STEPS
        accents = [False] * Config.NUM_STEPS
        pitch = None

        clip = self.get_clip(channel, scene_index)
        if clip is None:
            return steps, accents, pitch

        start, end = self._window_bounds(clip)
        for note in clip.get_notes_extended(0, 128, start, Config.WINDOW_BEATS):
            note_pitch = int(note.pitch)
            note_start = float(note.start_time)
            step = int(round((note_start - start) / Config.STEP_DURATION_BEATS))
            if 0 <= step < Config.NUM_STEPS:
                steps[step] = True
                if int(note.velocity) >= Config.ACCENT_VELOCITY_THRESHOLD:
                    accents[step] = True
                if pitch is None:
                    pitch = note_pitch

        return steps, accents, pitch

    def write_pattern(self, channel, steps, accents, pitch, scene_index=None):
        clip = self.ensure_clip(channel, scene_index)
        if clip is None:
            return

        start, end = self._window_bounds(clip)
        clip.remove_notes_extended(0, 128, start, Config.WINDOW_BEATS)

        specs = []
        for step, active in enumerate(steps):
            if not active:
                continue
            note_start = start + step * Config.STEP_DURATION_BEATS
            velocity = (
                Config.ACCENT_VELOCITY
                if accents[step]
                else Config.NOTE_VELOCITY
            )
            specs.append(
                Live.Clip.MidiNoteSpecification(
                    pitch=pitch,
                    start_time=note_start,
                    duration=Config.STEP_DURATION_BEATS * 0.9,
                    velocity=velocity,
                    mute=False,
                )
            )

        if specs:
            clip.add_new_notes(tuple(specs))

    def clear_loop_window(self, channel, scene_index=None):
        """Remove notes only inside the clip's current loop window."""
        clip = self.get_clip(channel, scene_index)
        if clip is None:
            return
        start, _end = self._window_bounds(clip)
        clip.remove_notes_extended(0, 128, start, Config.WINDOW_BEATS)

    def transpose_clip(self, channel, semitones, scene_index=None):
        """Shift every note in the clip by semitones (whole-clip sound change)."""
        if semitones == 0:
            return
        clip = self.get_clip(channel, scene_index)
        if clip is None:
            return

        length = Config.MAX_WINDOWS * Config.WINDOW_BEATS
        notes = list(clip.get_notes_extended(0, 128, 0.0, length))
        if not notes:
            return

        clip.remove_notes_extended(0, 128, 0.0, length)
        specs = []
        for note in notes:
            specs.append(
                Live.Clip.MidiNoteSpecification(
                    pitch=max(0, min(127, int(note.pitch) + semitones)),
                    start_time=float(note.start_time),
                    duration=float(note.duration),
                    velocity=int(note.velocity),
                    mute=bool(note.mute),
                )
            )
        clip.add_new_notes(tuple(specs))
        self._log(
            "F1 transpose ch=%d %+d semitones (%d notes)"
            % (channel + 1, semitones, len(specs))
        )

    def copy_row_from_scene(self, from_scene, to_scene):
        """Copy each channel's loop window pattern from one scene row to another."""
        if from_scene is None or to_scene is None or from_scene == to_scene:
            return

        for channel in range(Config.NUM_CHANNELS):
            steps, accents, pitch = self.read_pattern(channel, from_scene)
            src_clip = self.get_clip(channel, from_scene)
            if src_clip is None and not any(steps):
                continue

            dst_clip = self.ensure_clip(channel, to_scene)
            if dst_clip is None:
                continue

            window = self.current_window(channel, from_scene)
            self.set_loop_window(channel, window, to_scene)

            if pitch is None:
                pitch = Config.SOUND_PITCHES[channel][0]

            self.write_pattern(channel, steps, accents, pitch, to_scene)

        self._log(
            "F1 copied row scene %d -> %d" % (from_scene + 1, to_scene + 1)
        )

    # ------------------------------------------------------------ misc

    def fire_clip_if_present(self, channel, scene_index):
        """Start a clip only if the slot already has one (never create)."""
        slot = self._slot(channel, scene_index)
        if slot is None or not slot.has_clip:
            return False
        try:
            slot.fire()
            self._log(
                "F1 clip fire ch=%d scene=%d" % (channel + 1, scene_index + 1)
            )
            return True
        except (RuntimeError, AttributeError) as exc:
            self._log("F1 clip fire failed: %s" % exc)
            return False

    def adopt_scene(self, scene_index):
        """Set fallback scene row when nothing is playing (never fires clips)."""
        if scene_index is None:
            return
        self.set_working_scene_index(scene_index)
        self._log("F1 working scene %d" % (scene_index + 1))

    def clip_slot(self, channel, scene_index):
        return self._slot(channel, scene_index)

    def toggle_clip_slot(self, channel, scene_index):
        """Fire or stop a session clip slot (APC-style)."""
        slot = self._slot(channel, scene_index)
        if slot is None or not slot.has_clip:
            return False

        try:
            if slot.is_playing or slot.is_triggered:
                slot.stop()
                self._log(
                    "F1 clip stop ch=%d scene=%d" % (channel + 1, scene_index + 1)
                )
            else:
                slot.fire()
                self._log(
                    "F1 clip fire ch=%d scene=%d" % (channel + 1, scene_index + 1)
                )
            return True
        except (RuntimeError, AttributeError) as exc:
            self._log("F1 clip toggle failed: %s" % exc)
            return False

    def clip_slot_has_clip(self, channel, scene_index):
        slot = self._slot(channel, scene_index)
        return slot is not None and slot.has_clip

    def clip_slot_is_active(self, channel, scene_index):
        slot = self._slot(channel, scene_index)
        if slot is None or not slot.has_clip:
            return False
        try:
            return bool(slot.is_playing or slot.is_triggered)
        except (RuntimeError, AttributeError):
            return False

    def set_track_volume(self, channel, midi_value):
        """Map fader CC 0..127 to silence..0 dB (no +6 dB boost)."""
        track = self._track(channel)
        if track is None:
            return
        normalized = (float(midi_value) / 127.0) * Config.VOLUME_0DB_NORM
        track.mixer_device.volume.value = max(0.0, min(Config.VOLUME_0DB_NORM, normalized))

    def playing_step(self, channel):
        clip = self.get_playing_clip(channel)
        if clip is None or not clip.is_playing:
            return -1
        position = clip.playing_position - clip.loop_start
        step = int(position / Config.STEP_DURATION_BEATS)
        if 0 <= step < Config.NUM_STEPS:
            return step
        return -1
