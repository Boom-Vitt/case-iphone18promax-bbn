"""Create an original ambient score, encode the film, and validate the output.
Requires Python 3 standard library, FFmpeg, and FFprobe.
"""
from array import array
from pathlib import Path
import hashlib
import json
import math
import struct
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parent
FPS, SECONDS, RATE = 24, 16, 48000
frames = [ROOT / 'frames' / f'{n:04d}.png' for n in range(1, FPS * SECONDS + 1)]
for path in frames:
    with path.open('rb') as f:
        header = f.read(24)
    assert header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (1920, 1080), path
assert len({hashlib.sha256(p.read_bytes()).digest() for p in frames}) == 384, 'Duplicate/still frames in film'

# Original quiet D-minor ambient progression: soft pads and four bell accents.
chords = [(50, 57, 60, 64, 69), (46, 53, 57, 60, 65), (41, 53, 57, 60, 67), (45, 52, 55, 60, 64)]
score = [0.0] * (RATE * SECONDS)
for index, chord in enumerate(chords):
    begin = index * 4
    for note in chord:
        frequency = 440 * 2 ** ((note - 69) / 12)
        for n in range(int(min(5, SECONDS - begin) * RATE)):
            t = n / RATE
            envelope = min(t / 0.8, 1) * min(max((5 - t) / 1.8, 0), 1)
            signal = math.sin(2 * math.pi * frequency * t) + 0.12 * math.sin(2 * math.pi * frequency * 2.002 * t)
            score[begin * RATE + n] += 0.025 * envelope * signal
    bell = 440 * 2 ** ((chord[-1] + 12 - 69) / 12)
    for n in range(min(2 * RATE, len(score) - begin * RATE)):
        t = n / RATE
        score[begin * RATE + n] += 0.07 * math.exp(-3 * t) * min(t / 0.015, 1) * (math.sin(2 * math.pi * bell * t) + 0.15 * math.sin(2 * math.pi * bell * 2.01 * t))

pcm = array('h')
peak = 0
for n, value in enumerate(score):
    t = n / RATE
    fade = min(t / 0.6, 1) * min((SECONDS - t) / 1.4, 1)
    left = (value + (score[n - 7901] * 0.18 if n >= 7901 else 0)) * fade
    right = (value + (score[n - 10903] * 0.18 if n >= 10903 else 0)) * fade
    peak = max(peak, abs(left), abs(right))
    assert max(abs(left), abs(right)) < 1, 'Audio clipping'
    pcm.extend([round(left * 32767), round(right * 32767)])
if sys.byteorder == 'big':
    pcm.byteswap()
with wave.open(str(ROOT / 'ambient-score.wav'), 'wb') as output:
    output.setparams((2, 2, RATE, 0, 'NONE', 'not compressed'))
    output.writeframes(pcm.tobytes())

video = ROOT / 'iphone18-pro-max-premium.mp4'
subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning', '-framerate', str(FPS), '-start_number', '1', '-i', str(ROOT / 'frames/%04d.png'), '-i', str(ROOT / 'ambient-score.wav'), '-map', '0:v:0', '-map', '1:a:0', '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,fade=t=in:st=0:d=0.45,fade=t=out:st=15.2:d=0.8', '-af', 'loudnorm=I=-20:TP=-2:LRA=7', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-c:a', 'aac', '-b:a', '192k', '-ar', str(RATE), '-t', str(SECONDS), '-movflags', '+faststart', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', str(video)], check=True)
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(video)]))
v = next(s for s in probe['streams'] if s['codec_type'] == 'video')
a = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
assert (v['width'], v['height'], v['r_frame_rate'], int(v['nb_read_frames'])) == (1920, 1080, '24/1', 384), v
assert v['codec_name'] == 'h264' and a['codec_name'] == 'aac' and a['channels'] == 2
assert abs(float(probe['format']['duration']) - 16) < 0.05
subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-f', 'null', '-'], check=True)
report = {'status': 'PASS', 'video': video.name, 'duration_seconds': 16, 'resolution': [1920, 1080], 'fps': 24, 'unique_source_frames': 384, 'decoded_frames': 384, 'audio': 'Original procedural ambient score, stereo AAC 48kHz', 'unmastered_audio_peak': peak, 'sha256': hashlib.sha256(video.read_bytes()).hexdigest(), 'bytes': video.stat().st_size, 'decode': 'FFmpeg full decode passed'}
(ROOT / 'video-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
