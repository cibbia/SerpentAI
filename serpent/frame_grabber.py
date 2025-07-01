import numpy as np

import mss
import os, shutil

from redis import StrictRedis

from serpent.config import config

import time

from serpent.game_frame import GameFrame
from serpent.game_frame_buffer import GameFrameBuffer

from serpent.frame_transformation_pipeline import FrameTransformationPipeline

try:
    from serpent.grpc.frame_client import FrameProducer  # type: ignore
except Exception:
    FrameProducer = None  # type: ignore

try:
    from serpent.capture.pipewire_ffmpeg import FFmpegPipeWireCapture  # type: ignore
except Exception:
    FFmpegPipeWireCapture = None  # type: ignore

redis_client = StrictRedis(**config["redis"])


class FrameGrabber:

    def __init__(self, width=640, height=480, x_offset=0, y_offset=0, fps=30, pipeline_string=None, buffer_seconds=5, use_grpc: bool = False, grpc_address: str = "localhost:50051"):
        self.width = width
        self.height = height

        self.x_offset = x_offset
        self.y_offset = y_offset

        self.frame_time = 1 / fps
        self.frame_buffer_size = buffer_seconds * fps

        self.redis_client = redis_client
        self.backend = "x11"
        if (
            os.getenv("SERPENT_WAYLAND_EXPERIMENT") == "1"
            or config["frame_grabber"].get("backend") == "pipewire"
        ) and os.getenv("XDG_SESSION_TYPE") == "wayland" and FFmpegPipeWireCapture is not None:
            try:
                self.pipewire = FFmpegPipeWireCapture(self.width, self.height)
                self.backend = "pipewire"
            except Exception:
                self.pipewire = None
        else:
            self.pipewire = None

        self.screen_grabber = None if self.backend == "pipewire" else mss.mss()

        self.frame_transformation_pipeline = None

        # Optional gRPC producer
        self._grpc_producer = None
        if use_grpc and FrameProducer is not None:
            import asyncio

            self._loop = asyncio.get_event_loop()
            self._grpc_producer = FrameProducer(address=grpc_address)
            self._loop.run_until_complete(self._grpc_producer.start())

        self._use_grpc = self._grpc_producer is not None

        if pipeline_string is not None and isinstance(pipeline_string, str):
            self.frame_transformation_pipeline = FrameTransformationPipeline(pipeline_string=pipeline_string)

        # Clear any previously stored frames
        self.redis_client.delete(config["frame_grabber"]["redis_key"])
        self.redis_client.delete(config["frame_grabber"]["redis_key"] + "_PIPELINE")

    def start(self):
        while True:
            cycle_start = time.time()

            frame = self.grab_frame()

            if self.frame_transformation_pipeline is not None:
                frame_pipeline = self.frame_transformation_pipeline.transform(frame)
            else:
                frame_pipeline = frame

            frame_shape = str(frame.shape).replace("(", "").replace(")", "")
            frame_dtype = str(frame.dtype)

            frame_bytes = f"{cycle_start}~{frame_shape}~{frame_dtype}~".encode("utf-8") + frame.tobytes()

            if self._use_grpc:
                # Push PNG bytes for efficiency
                try:
                    self._loop.run_until_complete(
                        self._grpc_producer.push_frame(cycle_start, frame_pipeline if self._has_png_transformation_pipeline() else frame.tobytes(), self.width, self.height, fmt="PNG" if self._has_png_transformation_pipeline() else "RAW")
                    )
                except Exception:
                    pass
            else:
                self.redis_client.lpush(config["frame_grabber"]["redis_key"], frame_bytes)
                self.redis_client.ltrim(config["frame_grabber"]["redis_key"], 0, self.frame_buffer_size)

            if self._has_png_transformation_pipeline():
                frame_pipeline_shape = "PNG"
                frame_pipeline_dtype = "PNG"

                frame_pipeline_bytes = f"{cycle_start}~{frame_pipeline_shape}~{frame_pipeline_dtype}~".encode("utf-8") + frame_pipeline
            else:
                frame_pipeline_shape = str(frame_pipeline.shape).replace("(", "").replace(")", "")
                frame_pipeline_dtype = str(frame_pipeline.dtype)

                frame_pipeline_bytes = f"{cycle_start}~{frame_pipeline_shape}~{frame_pipeline_dtype}~".encode("utf-8") + frame_pipeline.tobytes()

            if not self._use_grpc:
                self.redis_client.lpush(config["frame_grabber"]["redis_key"] + "_PIPELINE", frame_pipeline_bytes)
                self.redis_client.ltrim(config["frame_grabber"]["redis_key"] + "_PIPELINE", 0, self.frame_buffer_size)

            cycle_end = time.time()

            cycle_duration = (cycle_end - cycle_start)
            cycle_duration -= int(cycle_duration)

            frame_time_left = self.frame_time - cycle_duration

            if frame_time_left > 0:
                time.sleep(frame_time_left)

    def grab_frame(self):
        if self.backend == "pipewire" and self.pipewire is not None:
            return self.pipewire.grab()

        frame = np.array(
            self.screen_grabber.grab({
                "top": self.y_offset,
                "left": self.x_offset,
                "width": self.width,
                "height": self.height
            }),
            dtype="uint8"
        )

        frame = frame[..., [2, 1, 0, 3]]

        return frame[..., :3]

    def _has_png_transformation_pipeline(self):
        return self.frame_transformation_pipeline and self.frame_transformation_pipeline.pipeline_string and self.frame_transformation_pipeline.pipeline_string.endswith("|PNG")

    @classmethod
    def get_frames(cls, frame_buffer_indices, frame_type="FULL", **kwargs):
        while True:
            if redis_client.llen(config["frame_grabber"]["redis_key"]) > 149:
                break
            
            time.sleep(0.1)

        game_frame_buffer = GameFrameBuffer(size=len(frame_buffer_indices))

        for i in frame_buffer_indices:
            redis_key = config["frame_grabber"]["redis_key"]
            redis_key = redis_key + "_PIPELINE" if frame_type == "PIPELINE" else redis_key

            frame_data = redis_client.lindex(redis_key, i)

            timestamp, shape, dtype, frame_bytes = frame_data.split("~".encode("utf-8"), maxsplit=3)

            if dtype == "PNG".encode("utf-8"):
                frame_array = frame_bytes
            else:
                frame_shape = [int(i) for i in shape.decode("utf-8").split(", ")]
                frame_array = np.fromstring(frame_bytes, dtype=dtype.decode("utf-8")).reshape(frame_shape)

            game_frame = GameFrame(frame_array, timestamp=float(timestamp))

            game_frame_buffer.add_game_frame(game_frame)

        return game_frame_buffer

    @classmethod
    def get_frames_with_pipeline(cls, frame_buffer_indices, **kwargs):
        while True:
            if redis_client.llen(config["frame_grabber"]["redis_key"]) > 149:
                break

            time.sleep(0.1)

        game_frame_buffers = [
            GameFrameBuffer(size=len(frame_buffer_indices)),
            GameFrameBuffer(size=len(frame_buffer_indices))
        ]

        for i in frame_buffer_indices:
            redis_keys = [config["frame_grabber"]["redis_key"], config["frame_grabber"]["redis_key"] + "_PIPELINE"]

            for index, redis_key in enumerate(redis_keys):
                frame_data = redis_client.lindex(redis_key, i)

                timestamp, shape, dtype, frame_bytes = frame_data.split("~".encode("utf-8"), maxsplit=3)

                if dtype == "PNG".encode("utf-8"):
                    frame_array = frame_bytes
                else:
                    frame_shape = [int(i) for i in shape.decode("utf-8").split(", ")]
                    frame_array = np.fromstring(frame_bytes, dtype=dtype.decode("utf-8")).reshape(frame_shape)

                game_frame = GameFrame(frame_array, timestamp=float(timestamp))

                game_frame_buffers[index].add_game_frame(game_frame)

        return game_frame_buffers
