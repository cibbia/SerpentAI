from __future__ import annotations

"""Experimental Wayland PipeWire capture using ffmpeg.

Requires:
  * ffmpeg with --enable-libpipewire (Arch, Fedora, Ubuntu 22.04+)
  * ffmpeg-python for convenient subprocess handling (optional)
Activate via env var:
  SERPENT_WAYLAND_EXPERIMENT=1
or config.yml:
  frame_grabber:
     backend: pipewire
"""

import os, shutil, subprocess, threading
from typing import Optional
import numpy as np

class FFmpegPipeWireCapture:
    def __init__(self, width: int, height: int):
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg not found")
        self.width = width
        self.height = height
        self.frame_size = width * height * 3  # RGB24
        cmd = [
            "ffmpeg",
            "-f", "pipewire",
            "-i", "0",
            "-vf", f"scale={width}:{height}",
            "-pix_fmt", "rgb24",
            "-vcodec", "rawvideo",
            "-nostats", "-loglevel", "error",
            "-an", "-sn", "-",
        ]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8)
        self.lock = threading.Lock()

    def grab(self):
        with self.lock:
            buf = self.proc.stdout.read(self.frame_size)
        if len(buf) != self.frame_size:
            raise RuntimeError("PipeWire frame read underflow")
        return np.frombuffer(buf, dtype=np.uint8).reshape((self.height, self.width, 3))

    def close(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()