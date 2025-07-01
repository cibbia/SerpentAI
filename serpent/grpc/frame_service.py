"""Asynchronous gRPC implementation of a bidirectional frame bus.

This replaces the legacy Crossbar/Twisted WAMP layer.  The service is
_optional_; if ``grpcio`` is not installed the module degrades to no-ops so
unit-tests remain lightweight.

Design
------
* **FrameGrabber** (producer) connects as a *client* and streams `Frame`
  messages to the server.
* **Consumers** (game agents, dashboard, recorder) open a second stream and
  receive the frames in real time.
* The server simply relays frames from the producer to every connected
  consumer (in-memory pub/sub).
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator, List

try:
    import grpc  # type: ignore
    from grpc.aio import ServicerContext  # type: ignore
    from grpc.experimental import aio as grpc_aio  # type: ignore  # older grpc alias
except ModuleNotFoundError:  # pragma: no cover – stubbed environment
    grpc = None  # type: ignore

from datetime import datetime, timezone

import importlib.resources as pkg_resources
from pathlib import Path

import sys

if grpc is not None:
    # Dynamically load the generated *_pb2.py files.  To avoid a build-time
    # code-gen step we compile the proto at import-time when grpcio-tools is
    # present; otherwise we assume pre-generated modules exist.
    try:
        from serpent.proto import frame_pb2, frame_pb2_grpc  # type: ignore
    except ModuleNotFoundError:  # Generate on the fly
        try:
            from grpc_tools import protoc  # type: ignore
        except ModuleNotFoundError:
            frame_pb2 = None  # type: ignore
            frame_pb2_grpc = None  # type: ignore
        else:
            proto_path = str(Path(__file__).parent.parent / "proto")
            proto_file = str(Path(proto_path) / "frame.proto")
            protoc.main([
                "protoc",
                f"-I{proto_path}",
                f"--python_out={proto_path}",
                f"--grpc_python_out={proto_path}",
                proto_file,
            ])
            from serpent.proto import frame_pb2, frame_pb2_grpc  # type: ignore
else:
    frame_pb2 = None  # type: ignore
    frame_pb2_grpc = None  # type: ignore

_LOG = logging.getLogger(__name__)


if grpc is not None and frame_pb2 is not None:

    class _FrameBus(frame_pb2_grpc.FrameServiceServicer):  # type: ignore
        """In-memory pub/sub for frames."""

        def __init__(self):
            self._subscribers: List[asyncio.Queue] = []

        async def StreamFrames(  # type: ignore
            self,
            request_iterator: AsyncIterator[frame_pb2.Frame],
            context: ServicerContext,  # type: ignore
        ) -> AsyncIterator[frame_pb2.Frame]:
            queue: asyncio.Queue = asyncio.Queue(maxsize=256)
            self._subscribers.append(queue)
            _LOG.info("Client connected. total=%d", len(self._subscribers))

            async def _producer():
                try:
                    async for frame in request_iterator:
                        # Broadcast to all subscribers (except maybe sender)
                        for q in self._subscribers:
                            if q is not queue:
                                if not q.full():
                                    await q.put(frame)
                except asyncio.CancelledError:
                    pass

            prod_task = asyncio.create_task(_producer())

            try:
                while True:
                    frame = await queue.get()
                    yield frame
            except asyncio.CancelledError:
                pass
            finally:
                prod_task.cancel()
                self._subscribers.remove(queue)
                _LOG.info("Client disconnected. total=%d", len(self._subscribers))


    async def serve(address: str = "[::]:50051") -> None:
        server = grpc.aio.server()  # type: ignore
        frame_service = _FrameBus()
        frame_pb2_grpc.add_FrameServiceServicer_to_server(frame_service, server)  # type: ignore
        server.add_insecure_port(address)
        _LOG.info("Starting gRPC FrameService on %s", address)
        await server.start()
        await server.wait_for_termination()

else:

    async def serve(*args, **kwargs):  # type: ignore
        _LOG.warning("gRPC not available – frame bus is disabled.")