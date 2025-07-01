from serpent.loggers.noop_logger import NoopLogger

try:
    from serpent.loggers.comet_ml_logger import CometMLLogger  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    # If the optional comet_ml dependency is not installed, gracefully fall back
    # to a stub implementation that behaves like a No-op logger so that the
    # rest of the codebase (and unit-tests) can still import serpent.loggers
    # without requiring the heavy comet_ml package.
    class CometMLLogger(NoopLogger):  # type: ignore
        """Fallback logger used when comet_ml is not available."""
        def __init__(self, logger_kwargs=None):
            super().__init__(logger_kwargs=logger_kwargs)