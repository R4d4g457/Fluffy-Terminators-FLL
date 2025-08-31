
from typing import Awaitable

class _Sound:
    def play(self, sound_name: str, volume: int = 100, pitch: int = 0, pan: int = 0) -> Awaitable[None]:
        """Play a named app sound with optional volume/pitch/pan.""" ...
    def set_attributes(self, volume: int, pitch: int, pan: int) -> None:
        """Set default attributes for subsequent sounds.""" ...
    def stop(self) -> None:
        """Stop any currently playing app sound.""" ...

class _Music:
    """Simple music playback: notes, drums, tempo and instruments."""
    # Drum constants (subset)
    DRUM_SNARE: int
    DRUM_BASS: int
    DRUM_CRASH_CYMBAL: int
    DRUM_OPEN_HI_HAT: int
    DRUM_CLOSED_HI_HAT: int
    DRUM_SIDE_STICK: int
    DRUM_TAMBOURINE: int
    DRUM_HAND_CLAP: int
    DRUM_WOOD_BLOCK: int
    DRUM_COWBELL: int
    DRUM_TRIANGLE: int
    DRUM_BONGO: int
    DRUM_CONGA: int
    DRUM_GUIRO: int
    DRUM_CABASA: int
    DRUM_CUICA: int
    DRUM_VIBRASLAP: int

    # Instruments (subset)
    INSTRUMENT_PIANO: int
    INSTRUMENT_ELECTRIC_PIANO: int
    INSTRUMENT_MUSIC_BOX: int
    INSTRUMENT_ORGAN: int
    INSTRUMENT_GUITAR: int
    INSTRUMENT_ELECTRIC_GUITAR: int
    INSTRUMENT_BASS: int
    INSTRUMENT_PIZZICATO: int
    INSTRUMENT_CELLO: int
    INSTRUMENT_VIBRAPHONE: int
    INSTRUMENT_FLUTE: int
    INSTRUMENT_WOODEN_FLUTE: int
    INSTRUMENT_CLARINET: int
    INSTRUMENT_SAXOPHONE: int
    INSTRUMENT_TROMBONE: int
    INSTRUMENT_CHOIR: int
    INSTRUMENT_MARIMBA: int
    INSTRUMENT_STEEL_DRUM: int
    INSTRUMENT_SYNTH_LEAD: int
    INSTRUMENT_SYNTH_PAD: int

    def play_note(self, note: int, duration: int = 500, instrument: int = INSTRUMENT_PIANO, volume: int = 100) -> Awaitable[None]:
        """Play a single note (MIDI note number) for *duration* ms with *instrument* and *volume*.""" ...
    def play_drum(self, drum: int, duration: int = 100, volume: int = 100) -> Awaitable[None]:
        """Play a drum sound for *duration* ms at *volume*.""" ...
    def play_instrument(self, instrument: int, duration: int = 500, volume: int = 100) -> Awaitable[None]:
        """Play a held tone using *instrument* for *duration* ms at *volume*.
        Useful when you want to specify the instrument explicitly without providing a note sequence.""" ...
    def set_tempo(self, bpm: int) -> None:
        """Set the tempo in beats per minute for sequence playback.""" ...
    def get_tempo(self) -> int:
        """Return the current tempo in beats per minute.""" ...
    def stop(self) -> None:
        """Stop any ongoing music/drum playback.""" ...

sound: _Sound
music: _Music
