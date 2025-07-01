# Lightweight optional dependency stubs to keep unit-tests importable without
# requiring the full scientific Python stack. Only the minimal surface area
# needed by the current source/tests is implemented.

import sys
import types
import numpy as np


def _create_stub_module(name: str, attrs: dict | None = None):
    """Create and register a very small stub module under *name*.

    Parameters
    ----------
    name: str
        The fully-qualified module name, e.g. "skimage.io".
    attrs: dict | None
        Attribute mapping to set on the stub module. Every value can be a
        no-op lambda or simple placeholder object.
    """
    module = types.ModuleType(name)
    attrs = attrs or {}
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


# ---------------------------------------------------------------------------
# Optional heavy dependencies that are *not* required by the unit tests.
# ---------------------------------------------------------------------------

# ------- scikit-image stubs -------------------------------------------------
try:
    import skimage  # noqa: F401
except ModuleNotFoundError:
    # Create sub-modules first so that `import skimage.io` etc. succeed.
    _create_stub_module("skimage")
    _create_stub_module("skimage.io", {
        "imread": lambda *args, **kwargs: None,
        "imsave": lambda *args, **kwargs: None,
    })
    _create_stub_module("skimage.util")
    _create_stub_module("skimage.color")
    _create_stub_module("skimage.transform")
    _create_stub_module("skimage.measure")
    _create_stub_module("skimage.filters")
    _create_stub_module("skimage.morphology")
    _create_stub_module("skimage.metrics", {"structural_similarity": lambda *args, **kwargs: 0.0})

# ------- comet-ml stub ------------------------------------------------------
try:
    import comet_ml  # noqa: F401
except ModuleNotFoundError:
    class _CometExperimentStub:  # Minimal stub matching the interface used.
        def __init__(self, *args, **kwargs):
            pass

        # Methods used in code base
        def set_code(self, *args, **kwargs):
            pass

        def log_multiple_params(self, *args, **kwargs):
            pass

        def log_metric(self, *args, **kwargs):
            pass

    _create_stub_module("comet_ml", {"Experiment": _CometExperimentStub})

# ------- torch stubs (not needed by tests but cheap to mock) ---------------
try:
    import torch  # noqa: F401
except ModuleNotFoundError:
    _create_stub_module("torch")
    _create_stub_module("torchvision")

# ------- mss stub -----------------------------------------------------------
try:
    import mss  # noqa: F401
except ModuleNotFoundError:
    _create_stub_module("mss", {"mss": lambda *args, **kwargs: None})

# ------- PIL stub -----------------------------------------------------------
try:
    import PIL  # noqa: F401
except ModuleNotFoundError:
    image_stub = types.ModuleType("PIL.Image")
    # Provide dummy new and fromarray functions commonly used.
    def _no_op(*args, **kwargs):
        return None

    image_stub.new = _no_op
    image_stub.fromarray = _no_op
    _create_stub_module("PIL")
    sys.modules["PIL.Image"] = image_stub

# ------- gymnasium stub ------------------------------------------------------
try:
    import gymnasium  # noqa: F401
except ModuleNotFoundError:
    _create_stub_module("gymnasium")
    _create_stub_module("gymnasium.spaces", {
        "Box": object,
        "Discrete": object,
    })

# ------- ultralytics & onnxruntime stubs ------------------------------------
for _opt in ("ultralytics", "onnxruntime"):
    try:
        __import__(_opt)
    except ModuleNotFoundError:
        _create_stub_module(_opt)
        if _opt == "ultralytics":
            class _YOLOStub:  # noqa: D401
                def __init__(self, *args, **kwargs):
                    self.names = {}

                def predict(self, *args, **kwargs):
                    # Return object with minimal interface
                    class _BoxStub:
                        xyxy = np.empty((0, 4))  # type: ignore
                        conf = np.empty(0)
                        cls = np.empty(0)

                    class _ResultStub:
                        boxes = _BoxStub()

                    return [_ResultStub()]

            _create_stub_module("ultralytics", {"YOLO": _YOLOStub})

# Expose package version
__version__ = "0.1.dev0"

# ------- gRPC stubs ----------------------------------------------------------
try:
    import grpc  # noqa: F401
except ModuleNotFoundError:
    # Minimal stub to satisfy imports
    _create_stub_module("grpc")
    _create_stub_module("grpc.aio")

# ------- streamlit stub -----------------------------------------------------
try:
    import streamlit  # noqa: F401
except ModuleNotFoundError:
    _create_stub_module("streamlit", {"run": lambda *args, **kwargs: None})
    _create_stub_module("streamlit_drawable_canvas")

# requests & tqdm stubs
for _m in ("requests", "tqdm"):
    try:
        __import__(_m)
    except ModuleNotFoundError:
        _create_stub_module(_m, {"get": lambda *a, **k: None} if _m=="requests" else {"tqdm": lambda x, **k: x})