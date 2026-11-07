import wave
from pathlib import Path

from showcase.engines import Engine


class FakeEngine(Engine):
    name = "fake"
    version = "1"

    def __init__(self, fail_on=None, needs_voice=False, skip=False):
        self.fail_on = fail_on
        self.needs_voice = needs_voice
        self.skip = skip
        self.calls = 0
        self.texts = []

    def check(self):
        pass

    def synth_batch(self, items, voice):
        self.calls += 1
        for it in items:
            if self.fail_on and self.fail_on in it.text:
                raise RuntimeError("boom")
            self.texts.append(it.text)
            if self.skip:
                continue
            Path(it.out).parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(it.out), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(24000)
                w.writeframes(b"\x00\x00" * int(24000 * 0.1 * len(it.text)))
