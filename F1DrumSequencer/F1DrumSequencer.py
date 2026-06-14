# emacs-mode: -*- python-*-
#
# Traktor Kontrol F1 drum sequencer for Ableton Live 12.

from __future__ import absolute_import, print_function, unicode_literals

from _Framework.ButtonElement import ButtonElement
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE
from _Framework.SliderElement import SliderElement

from . import F1Config as Config
from .ClipWriter import ClipWriter
from .SequencerState import SequencerState


class F1DrumSequencer(ControlSurface):
    """Traktor Kontrol F1 — 4-channel, 16-step, scene-following drum sequencer."""

    __module__ = __name__
    __doc__ = "F1 Drum Sequencer Remote Script"

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self._sequencer = SequencerState()
        self._clip_writer = ClipWriter(self.song(), log_fn=self.log_message)
        self._suppress_send_midi = False
        self._led_cache = {}
        self._elements = []
        self._debug_midi_count = 0
        self._led_debug_count = 0
        self._fader_map = {}
        self._type_held = False
        self._browse_held = False
        self._device_mode = 0
        self._last_scene_index = None

        self._suggested_input_port = "Traktor Kontrol F1"
        self._suggested_output_port = "Traktor Kontrol F1"

        self.log_message("F1DrumSequencer initializing")

        with self.component_guard():
            self._create_forwarding_elements()
            self.request_rebuild_midi_map()

        song = self.song()
        song.add_current_song_time_listener(self._on_song_time)
        song.add_is_playing_listener(self._on_is_playing)
        song.view.add_selected_scene_listener(self._on_selected_scene)

        self._last_scene_index = self._clip_writer.scene_index()
        self._reload_grid()
        self._refresh_all_leds(force=True)
        self._update_mode_display(force=True)
        self.log_message(
            "F1DrumSequencer ready (%d forwarded elements)" % len(self._elements)
        )

    def disconnect(self):
        song = self.song()
        if song.current_song_time_has_listener(self._on_song_time):
            song.remove_current_song_time_listener(self._on_song_time)
        if song.is_playing_has_listener(self._on_is_playing):
            song.remove_is_playing_listener(self._on_is_playing)
        if song.view.selected_scene_has_listener(self._on_selected_scene):
            song.view.remove_selected_scene_listener(self._on_selected_scene)

        self._all_leds_off()
        self._suppress_send_midi = True
        ControlSurface.disconnect(self)
        self._suppress_send_midi = False

    def refresh_state(self):
        ControlSurface.refresh_state(self)
        self._led_cache = {}
        if self._is_passthrough_mode():
            self._all_leds_off()
        else:
            self._refresh_all_leds(force=True)
        self._update_mode_display(force=True)

    # ------------------------------------------------------------ modes

    def _is_passthrough_mode(self):
        return self._device_mode == Config.MODE_PASSTHROUGH_INDEX

    def _is_drum_mode(self):
        return not self._is_passthrough_mode()

    def _cycle_device_mode(self, direction):
        self._set_device_mode(
            (self._device_mode + direction) % Config.NUM_DEVICE_MODES
        )

    def _set_device_mode(self, mode_index):
        if mode_index == self._device_mode:
            return

        self._device_mode = mode_index
        mode = Config.DEVICE_MODES[mode_index]

        if mode.get("passthrough"):
            self._sequencer.current_play_step = -1
            self._all_leds_off()
        else:
            self._clip_writer.set_first_track_index(mode["first_track_index"])
            self._reload_grid()
            self._refresh_all_leds(force=True)

        label = mode["label"]
        try:
            self.show_message("F1: %s" % label)
        except (AttributeError, RuntimeError):
            pass
        self.log_message("F1 mode -> %s" % label)
        self._update_mode_display(force=True)

    def _update_mode_display(self, force=False):
        """Show the current device mode on the F1 7-segment display."""
        if self._device_mode < len(Config.MODE_DISPLAY_VALUES):
            value = Config.MODE_DISPLAY_VALUES[self._device_mode]
        else:
            value = self._device_mode + 1
        self._send_segment(value, force=force)

    def _send_segment(self, value, force=False):
        self._send_cc(
            Config.SEGMENT_DISPLAY_CHANNEL,
            Config.SEGMENT_DISPLAY_CC,
            max(0, min(127, int(value))),
            force=force,
        )

    def _forward_to_live(self, midi_bytes):
        """Forward raw MIDI into Live (MIDI map / Remote assignments)."""
        try:
            import Live
            if hasattr(Live, "MidiMap") and hasattr(Live.MidiMap, "forward_midi"):
                Live.MidiMap.forward_midi(midi_bytes)
                return
        except (ImportError, AttributeError, RuntimeError):
            pass
        try:
            self._c_instance.send_midi(midi_bytes, False)
        except TypeError:
            self._c_instance.send_midi(midi_bytes)

    def _function_button_role(self, channel, cc):
        """Return 'clear', 'type', 'size', 'browse', or None."""
        if channel in Config.FUNCTION_CHANNELS and cc in Config.FUNCTION_ROLE_BY_CC:
            return Config.FUNCTION_ROLE_BY_CC[cc]
        for (fb_ch, fb_cc), role in Config.FUNCTION_BUTTON_FALLBACKS:
            if channel == fb_ch and cc == fb_cc:
                return role
        return None

    def _is_function_button_cc(self, channel, cc):
        if channel in Config.FUNCTION_CHANNELS and cc in Config.FUNCTION_CCS:
            return True
        for (fb_ch, fb_cc), _role in Config.FUNCTION_BUTTON_FALLBACKS:
            if channel == fb_ch and cc == fb_cc:
                return True
        return False

    @staticmethod
    def _is_button_pressed(value):
        """Gate (127) or increment (1) press on the F1."""
        return value > 0

    @staticmethod
    def _is_button_released(value):
        return value == 0

    def _update_modifier_hold_states(self, channel, cc, value):
        """Track Type / Browse hold before any other handler runs."""
        role = self._function_button_role(channel, cc)
        if role in ("type", "browse"):
            self._apply_function_button_modifier(role, value)

    def _handle_mode_switch_action(self, channel, cc, value):
        """Browse held + encoder turn cycles device mode (all modes)."""
        if channel != Config.ENCODER_CHANNEL or cc != Config.ENCODER_TURN_CC:
            return False
        if not self._browse_held:
            return False
        if 1 <= value <= 63:
            self._cycle_device_mode(1)
        elif 65 <= value <= 127:
            self._cycle_device_mode(-1)
        return True

    # ------------------------------------------------------------ wiring

    @staticmethod
    def _noop(_value):
        pass

    def _add_button(self, channel, cc, name):
        element = ButtonElement(True, MIDI_CC_TYPE, channel, cc, name=name)
        element.add_value_listener(self._noop)
        self._elements.append(element)

    def _add_function_button(self, channel, cc, role, name):
        """Function buttons use real listeners (Live routes them to elements)."""
        element = ButtonElement(True, MIDI_CC_TYPE, channel, cc, name=name)
        element.add_value_listener(
            lambda value, button_role=role: self._on_function_button_listener(
                button_role, value
            )
        )
        self._elements.append(element)

    def _on_function_button_listener(self, role, value):
        if Config.DEBUG_FUNCTION_MIDI:
            self.log_message("F1 fn %s val=%d" % (role, value))
        self._apply_function_button_modifier(role, value)
        if self._is_passthrough_mode():
            return
        self._on_function_button(role, value)

    def _apply_function_button_modifier(self, role, value):
        if role == "type":
            if self._is_button_released(value):
                self._type_held = False
            elif self._is_button_pressed(value):
                self._type_held = True
        elif role == "browse":
            if self._is_button_released(value):
                self._browse_held = False
            elif self._is_button_pressed(value):
                self._browse_held = True

    def _add_slider(self, channel, cc, name):
        element = SliderElement(MIDI_CC_TYPE, channel, cc, name=name)
        element.add_value_listener(self._noop)
        self._elements.append(element)

    def _create_forwarding_elements(self):
        for step in range(Config.NUM_STEPS):
            self._add_button(
                Config.PAD_CHANNEL, Config.PAD_CC_START + step, "Pad_%d" % step
            )

        for index, cc in enumerate(Config.CHANNEL_SELECT_CCS):
            self._add_button(
                Config.CHANNEL_SELECT_CHANNEL, cc, "ChannelSelect_%d" % index
            )

        self._add_slider(Config.ENCODER_CHANNEL, Config.ENCODER_TURN_CC, "EncoderTurn")
        self._add_button(Config.ENCODER_CHANNEL, Config.ENCODER_PUSH_CC, "EncoderPush")

        for cc, name in (
            (Config.CLEAR_CC, "Clear"),
            (Config.TYPE_CC, "Type"),
            (Config.SIZE_CC, "Size"),
            (Config.BROWSE_CC, "Browse"),
        ):
            role = Config.FUNCTION_ROLE_BY_CC[cc]
            self._add_function_button(Config.FUNCTION_CHANNEL, cc, role, name)

        for (ch, cc), role in Config.FUNCTION_BUTTON_FALLBACKS:
            self._add_function_button(ch, cc, role, "%s_shift" % role)

        for pot_channel in Config.POT_CHANNELS:
            for index, cc in enumerate(Config.POT_CCS):
                self._add_slider(
                    pot_channel, cc, "WindowPot_%d_ch%d" % (index, pot_channel)
                )

        for index, (channel, cc) in enumerate(Config.FADERS):
            self._add_slider(channel, cc, "Volume_%d" % index)
            self._fader_map[(channel, cc)] = index
        for (channel, cc), index in Config.FADER_FALLBACKS:
            self._add_slider(channel, cc, "VolumeAlt_%d" % index)
            self._fader_map[(channel, cc)] = index

    # ------------------------------------------------------------ input

    def receive_midi(self, midi_bytes):
        if len(midi_bytes) == 3:
            status = midi_bytes[0]
            kind = status & 0xF0
            channel = status & 0x0F
            data1 = midi_bytes[1]
            value = midi_bytes[2]
            self._debug_log(kind, channel, data1, value)

            if kind == 0xB0:
                self._update_modifier_hold_states(channel, data1, value)

                if self._handle_mode_switch_action(channel, data1, value):
                    return

                if self._is_passthrough_mode():
                    self._forward_to_live(midi_bytes)
                    return

                if self._handle_cc(channel, data1, value):
                    return
        elif self._is_passthrough_mode():
            self._forward_to_live(midi_bytes)
            return

        ControlSurface.receive_midi(self, midi_bytes)

    def _debug_log(self, kind, channel, data1, value):
        if Config.DEBUG_FUNCTION_MIDI and kind == 0xB0 and self._is_function_button_cc(
            channel, data1
        ):
            self.log_message(
                "F1 fn raw ch=%d cc=%d val=%d" % (channel, data1, value)
            )
        if Config.DEBUG_MIDI and self._debug_midi_count < Config.DEBUG_MIDI_MAX:
            self._debug_midi_count += 1
            self.log_message(
                "F1 raw #%d: type=%s ch=%d num=%d val=%d"
                % (
                    self._debug_midi_count,
                    "CC" if kind == 0xB0 else hex(kind),
                    channel,
                    data1,
                    value,
                )
            )

    def _handle_cc(self, channel, cc, value):
        if channel == Config.PAD_CHANNEL and Config.PAD_CC_START <= cc <= Config.PAD_CC_END:
            self._on_pad_press(cc - Config.PAD_CC_START)
            return True

        if channel == Config.CHANNEL_SELECT_CHANNEL and cc in Config.CHANNEL_SELECT_CCS:
            self._on_channel_select(Config.CHANNEL_SELECT_CCS.index(cc))
            return True

        if channel == Config.ENCODER_CHANNEL and cc == Config.ENCODER_TURN_CC:
            if self._browse_held:
                return True
            if 1 <= value <= 63:
                self._on_encoder_turn(1)
            elif 65 <= value <= 127:
                self._on_encoder_turn(-1)
            return True

        if channel == Config.ENCODER_CHANNEL and cc == Config.ENCODER_PUSH_CC:
            if self._is_button_pressed(value):
                self._on_encoder_push()
            return True

        if self._is_function_button_cc(channel, cc):
            return False

        if channel in Config.POT_CHANNELS and cc in Config.POT_CCS:
            self._on_window_pot(Config.POT_CCS.index(cc), value)
            return True

        fader_index = self._fader_map.get((channel, cc))
        if fader_index is not None:
            self._clip_writer.set_track_volume(fader_index, value / 127.0)
            return True

        return False

    # ------------------------------------------------------------ actions

    def _write_selected_channel(self):
        channel = self._sequencer.selected_channel
        self._clip_writer.write_pattern(
            channel,
            self._sequencer.steps,
            self._sequencer.accents,
            self._sequencer.current_pitch(),
        )

    def _on_pad_press(self, step):
        if self._type_held:
            self._sequencer.toggle_accent(step)
            self._write_selected_channel()
            self._set_pad_led(step)
            self.log_message(
                "F1 accent step %d %s ch=%d"
                % (
                    step + 1,
                    "on" if self._sequencer.accents[step] else "off",
                    self._sequencer.selected_channel + 1,
                )
            )
            return

        self._sequencer.toggle_step(step)
        self._write_selected_channel()
        self._set_pad_led(step)
        self.log_message(
            "F1 step %d %s ch=%d win=%d scene=%d"
            % (
                step + 1,
                "on" if self._sequencer.step_is_active(step) else "off",
                self._sequencer.selected_channel + 1,
                self._sequencer.window_index[self._sequencer.selected_channel] + 1,
                self._scene_number(),
            )
        )

    def _on_channel_select(self, channel):
        if channel == self._sequencer.selected_channel:
            return
        self._sequencer.select_channel(channel)
        self._reload_grid()
        self._refresh_all_leds(force=True)
        self.log_message(
            "F1 channel %d (sound %d, window %d)"
            % (
                channel + 1,
                self._sequencer.sound_index[channel] + 1,
                self._sequencer.window_index[channel] + 1,
            )
        )

    def _on_encoder_turn(self, direction):
        self._sequencer.cycle_sound(direction)
        self._write_selected_channel()
        self.log_message(
            "F1 sound %d pitch %d (ch %d)"
            % (
                self._sequencer.sound_index[self._sequencer.selected_channel] + 1,
                self._sequencer.current_pitch(),
                self._sequencer.selected_channel + 1,
            )
        )

    def _on_function_button(self, role, value):
        """Reverse / Type / Size / Browse — Basic page + Shift fallbacks."""
        if role == "clear":
            if self._is_button_pressed(value):
                self._on_clear()
            return

        if role == "type":
            if self._is_button_pressed(value):
                self.log_message("F1 Type held — tap pad for accent")
            return

        if role == "browse":
            if self._is_button_pressed(value):
                self.log_message("F1 Browse held — turn encoder to change mode")
            return

        if role == "size" and self._is_button_pressed(value):
            self.log_message("F1 Size (no action assigned)")

    def _on_encoder_push(self):
        self._sequencer.reset_sound()
        self._write_selected_channel()
        self.log_message(
            "F1 sound reset to 1 (ch %d)" % (self._sequencer.selected_channel + 1)
        )

    def _on_clear(self):
        channel = self._sequencer.selected_channel
        self._sequencer.clear_pattern()
        self._clip_writer.clear_clip(channel)
        self._sequencer.window_index[channel] = 0
        self._sequencer.pot_zone[channel] = None
        self._refresh_all_leds(force=True)
        self.log_message(
            "F1 cleared clip ch=%d scene=%d"
            % (channel + 1, self._scene_number())
        )

    def _on_window_pot(self, channel, value):
        window_count = self._clip_writer.window_count(channel)
        zone = min(window_count - 1, value * window_count // 128)
        if zone == self._sequencer.pot_zone[channel]:
            return
        self._sequencer.pot_zone[channel] = zone

        moved = self._clip_writer.set_loop_window(channel, zone)
        self._sequencer.window_index[channel] = zone

        if channel == self._sequencer.selected_channel:
            self._reload_grid()
            self._refresh_all_leds(force=True)

        self.log_message(
            "F1 pot ch=%d -> window %d/%d%s"
            % (
                channel + 1,
                zone + 1,
                window_count,
                "" if moved else " (no clip yet)",
            )
        )

    def _on_selected_scene(self):
        if self._is_passthrough_mode():
            return

        new_scene = self._clip_writer.scene_index()
        old_scene = self._last_scene_index

        if (
            Config.COPY_PATTERN_ON_SCENE_SELECT
            and old_scene is not None
            and new_scene is not None
            and old_scene != new_scene
        ):
            self._clip_writer.copy_row_from_scene(old_scene, new_scene)

        self._last_scene_index = new_scene
        self._reload_grid()
        self._refresh_all_leds(force=True)

        if Config.LAUNCH_ON_SCENE_SELECT:
            self._clip_writer.launch_row(new_scene)

        self.log_message("F1 scene -> %d" % self._scene_number())

    # ------------------------------------------------------------ playhead

    def _on_song_time(self):
        if self._is_passthrough_mode():
            return

        step = self._clip_writer.playing_step(self._sequencer.selected_channel)
        if step == self._sequencer.current_play_step:
            return
        previous = self._sequencer.current_play_step
        self._sequencer.current_play_step = step
        if 0 <= previous < Config.NUM_STEPS:
            self._set_pad_led(previous)
        if 0 <= step < Config.NUM_STEPS:
            self._set_pad_led(step)

    def _on_is_playing(self):
        if self._is_passthrough_mode():
            return

        if not self.song().is_playing:
            previous = self._sequencer.current_play_step
            self._sequencer.current_play_step = -1
            if 0 <= previous < Config.NUM_STEPS:
                self._set_pad_led(previous)

    # ------------------------------------------------------------ state

    def _scene_number(self):
        index = self._clip_writer.scene_index()
        return (index + 1) if index is not None else 0

    def _reload_grid(self):
        channel = self._sequencer.selected_channel
        self._sequencer.window_index[channel] = self._clip_writer.current_window(
            channel
        )
        steps, accents, pitch = self._clip_writer.read_pattern(channel)
        self._sequencer.load_pattern(steps, accents, pitch)

    # ------------------------------------------------------------ LEDs

    def _refresh_all_leds(self, force=False):
        for step in range(Config.NUM_STEPS):
            self._set_pad_led(step, force=force)
        for index, cc in enumerate(Config.CHANNEL_SELECT_CCS):
            value = 127 if index == self._sequencer.selected_channel else 0
            self._send_cc(Config.CHANNEL_SELECT_CHANNEL, cc, value, force=force)

    def _set_pad_led(self, step, force=False):
        if Config.LED_MODE == "hsb":
            cc = Config.PAD_LED_CCS[step]
            hue = Config.CHANNEL_HUES[self._sequencer.selected_channel]
            hsb = self._sequencer.pad_led_hsb(step, hue)
            for led_channel, value in zip(Config.PAD_LED_HSB_CHANNELS, hsb):
                self._send_cc(led_channel, cc, value, force=force)
        else:
            number = Config.LED_PAD_NUMBERS[step]
            color = Config.CHANNEL_COLOR_VALUES[self._sequencer.selected_channel]
            value = self._sequencer.pad_led_value(step, color)
            self._send_led(Config.LED_CHANNEL, number, value, force=force)

    def _all_leds_off(self):
        if Config.LED_MODE == "hsb":
            for cc in Config.PAD_LED_CCS:
                for led_channel in Config.PAD_LED_HSB_CHANNELS:
                    self._send_cc(led_channel, cc, 0, force=True)
        else:
            for number in Config.LED_PAD_NUMBERS:
                self._send_led(Config.LED_CHANNEL, number, Config.LED_OFF, force=True)
        for cc in Config.CHANNEL_SELECT_CCS:
            self._send_cc(Config.CHANNEL_SELECT_CHANNEL, cc, 0, force=True)
        self._send_segment(0, force=True)

    def _send_led(self, channel, number, value, force=False):
        status = (0x90 if Config.LED_USE_NOTES else 0xB0) | (channel & 0x0F)
        self._emit_led(status, number, value, force=force)

    def _send_cc(self, channel, cc, value, force=False):
        self._emit_led(0xB0 | (channel & 0x0F), cc, value, force=force)

    def _emit_led(self, status, number, value, force=False):
        if self._suppress_send_midi:
            return
        key = (status, number)
        if not force and self._led_cache.get(key) == value:
            return
        self._led_cache[key] = value
        if Config.DEBUG_LEDS and self._led_debug_count < Config.DEBUG_MIDI_MAX:
            self._led_debug_count += 1
            self.log_message(
                "F1 LED #%d -> status=0x%02X num=%d val=%d"
                % (self._led_debug_count, status, number, value)
            )
        self._send_midi((status, number, value))

    def _send_midi(self, midi_bytes, optimized=False):
        if not self._suppress_send_midi:
            ControlSurface._send_midi(self, midi_bytes, optimized=optimized)
