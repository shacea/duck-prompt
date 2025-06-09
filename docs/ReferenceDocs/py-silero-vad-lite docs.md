# Silero VAD Lite

Silero VAD Lite is a **lightweight Python wrapper** for the high-quality [Silero Voice Activity Detection (VAD)](https://github.com/snakers4/silero-vad) model using ONNX Runtime.

- **Simple interface** to use Silero VAD in Python, supporting **streaming audio** processing
- **Binary wheels** for **Windows, Linux, and MacOS** for easy installation
- **Zero dependencies** for the installable package, because it includes internally:
  - The Silero VAD model in ONNX format, so you don't need to supply it separately
  - The C++ ONNX Runtime (CPU), so the Python package for ONNX Runtime is not required

## Installation

You can install Silero VAD Lite using pip:

```bash
python -m pip install silero-vad-lite
```

This should install the package from the provided binary wheels, which are highly recommended. Installing from source is somewhat brittle and requires a C++ compiler.

## Usage

Here's a simple example of how to use Silero VAD Lite:

```python
from silero_vad_lite import SileroVAD
vad = SileroVAD(16000)  # sample_rate = 16000 Hz
speech_probability = vad.process(audio_data)
print(f"Voice activity detection probability of speech: {speech_probability}")  # 0 <= speech_probability <= 1
```

Requirements:

- Sample rate must be either 8000 Hz or 16000 Hz.
- Audio data must be 32-bit float PCM samples, normalized to the range [-1, 1], mono channel.
- Audio data must be supplied with length of 32ms (512 samples for 16kHz, 256 samples for 8kHz).
- Audio data can be supplied as: `bytes`, `bytearray`, `memoryview`, `array.array`, or `ctypes.Array`.
