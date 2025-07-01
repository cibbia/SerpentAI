from __future__ import annotations

import asyncio
from typing import AsyncIterator, Optional

import logging

try:
    import grpc  # type: ignore

    from serpent.proto import frame_pb2, frame_pb2_grpc  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    grpc = None  # type: ignore

    # Provide dummies so type-checkers are happy.
    class _Dummy:  # noqa: D401
        pass

    frame_pb2 = _Dummy()  # type: ignore
    frame_pb2_grpc = _Dummy()  # type: ignore

_LOG = logging.getLogger(__name__)


class FrameProducer:
    """Connects to a FrameService and streams frames."""

    def __init__(self, address: str = "localhost:50051"):
        if grpc is None:
            raise RuntimeError("gRPC not available")
        self._channel = grpc.aio.insecure_channel(address)  # type: ignore
        self._stub = frame_pb2_grpc.FrameServiceStub(self._channel)  # type: ignore
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        async def _gen():
            while True:
                frame = await self._queue.get()
                yield frame

        self._task = asyncio.create_task(self._stub.StreamFrames(_gen()))

    async def push_frame(self, timestamp: float, data: bytes, width: int, height: int, fmt: str = "PNG"):
        frame = frame_pb2.Frame(
            timestamp=int(timestamp * 1e6),
            data=data,
            width=width,
            height=height,
            format=fmt,
        )
        if self._queue.full():
            _LOG.debug("FrameProducer queue full; dropping frame")
            return
        await self._queue.put(frame)

    async def close(self):
        if self._task is not None:
            self._task.cancel()
        await self._channel.close()


class FrameConsumer:
    """Connects to a FrameService and yields frames as they arrive."""

    def __init__(self, address: str = "localhost:50051"):
        if grpc is None:
            raise RuntimeError("gRPC not available")
        self._channel = grpc.aio.insecure_channel(address)  # type: ignore
        self._stub = frame_pb2_grpc.FrameServiceStub(self._channel)  # type: ignore

    async def frames(self) -> AsyncIterator[frame_pb2.Frame]:  # type: ignore
        async for frame in self._stub.StreamFrames(iter([])):
            yield frame

    async def close(self):
        await self._channel.close()


# ------------------------------------------------------------
# Synchronous helper for legacy Game loop (no asyncio required)
# ------------------------------------------------------------


class FrameConsumerSync:
    """Blocking consumer wrapper using the sync gRPC API."""

    def __init__(self, address: str = "localhost:50051"):
        if grpc is None:
            raise RuntimeError("gRPC not available")
        self._channel = grpc.insecure_channel(address)  # type: ignore
        self._stub = frame_pb2_grpc.FrameServiceStub(self._channel)  # type: ignore
        # Start response iterator with empty request iterator
        self._response_iterator = self._stub.StreamFrames(iter([]))

    def get_frame(self):
        """Blocking call that returns the next Frame protobuf message."""
        return next(self._response_iterator)

    def close(self):
        self._channel.close()