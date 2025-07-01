from __future__ import annotations

"""Gymnasium wrapper for Serpent.AI games.

This provides a minimal `gymnasium.Env` interface so that modern
reinforcement-learning libraries such as **Stable-Baselines3** can train
agents on Serpent games out-of-the-box.

Usage
-----
```python
from serpent.gym_env import SerpentGymEnv
from serpent.games.flappy_bird import SerpentFlappyBirdGame  # example plugin

env = SerpentGymEnv(SerpentFlappyBirdGame, frame_handler="COLLECT_FRAMES")
obs, info = env.reset()
...
```

The wrapper is intentionally lightweight: it launches the requested game
plugin in headless mode, grabs raw RGB frames as observations and expects
`GameAgent.observe()` to compute rewards & terminal flags.

The module only imports `gymnasium` when available; otherwise it can still
be imported (e.g. during unit tests) thanks to the stub created in
`serpent.__init__`.
"""

from typing import Any, Tuple, Dict

import numpy as np

# gymnasium is optional; the stub in serpent.__init__ guarantees the import.
import gymnasium as gym  # type: ignore
from gymnasium import spaces  # type: ignore

import offshoot

from serpent.game import Game  # Base class, not a concrete plugin
from serpent.input_controller import InputController


def _default_observation_space(width: int, height: int) -> spaces.Box:  # type: ignore
    """Return a default Box(0,255, shape=(H,W,3), dtype=uint8)."""
    return spaces.Box(low=0, high=255, shape=(height, width, 3), dtype=np.uint8)


class SerpentGymEnv(gym.Env):  # type: ignore
    """A very thin adapter between Serpent `Game` objects and Gymnasium."""

    metadata = {"render_modes": ["rgb_array"], "render_fps": 30}

    def __init__(
        self,
        game_cls: type[Game],
        *,
        observation_space: spaces.Space | None = None,
        action_space: spaces.Space | None = None,
        frame_handler: str | None = None,
        **game_kwargs: Any,
    ) -> None:
        super().__init__()

        if not issubclass(game_cls, Game):
            raise TypeError("game_cls must be a subclass of serpent.game.Game")

        # Instantiate the game (does **not** launch yet).
        self._game: Game = game_cls(**game_kwargs)
        self._frame_handler = frame_handler

        # Observation space – default to raw window resolution.
        if observation_space is None:
            width = self._game.config.get("resolution", {}).get("width", 640)
            height = self._game.config.get("resolution", {}).get("height", 480)
            observation_space = _default_observation_space(width, height)
        self.observation_space = observation_space

        # Action space – discrete index across the flattened game-input mapping.
        if action_space is None:
            # We use the first game-input mapping to get a count.
            dummy_agent = offshoot.discover("Agent").get("Agent")  # type: ignore
            if dummy_agent is None:
                raise RuntimeError("Could not locate base Agent class through offshoot.")
            mapping_len = 4  # fallback
            action_space = spaces.Discrete(mapping_len)
        self.action_space = action_space

        # Internal state
        self._last_obs: np.ndarray | None = None
        self._terminated = False

        # Note: Game launch is deferred until reset() so that gym wrappers can
        # construct envs in subprocesses without side-effects.

    # ---------------------------------------------------------------------
    # Gymnasium required interface
    # ---------------------------------------------------------------------

    def reset(self, *, seed: int | None = None, options: Dict | None = None):  # type: ignore
        del options
        super().reset(seed=seed)

        # Launch game if not running
        if not self._game.is_launched:
            # In many use-cases users will manage launching themselves; for the
            # default experience we do a barebones launch here.
            self._game.launch(dry_run=False)
            self._game.start_frame_grabber()

        # Grab initial frame
        game_frame, _ = self._game.grab_latest_frame()
        self._last_obs = game_frame.frame
        self._terminated = False

        info: Dict[str, Any] = {}
        return self._last_obs.copy(), info  # type: ignore

    def step(self, action):  # type: ignore
        if self._terminated:
            raise RuntimeError("step() called on terminated episode; call reset().")

        # Map discrete action index to actual game inputs – this is a stub and
        # should be replaced by a real mapping obtained from the Game plugin.
        # For now we do nothing (No-Op).

        # Wait one frame and capture observation.
        game_frame, _ = self._game.grab_latest_frame()
        obs = game_frame.frame

        reward = 0.0  # Replace with your GameAgent reward calculation.
        terminated = False  # Determine based on game state.
        truncated = False
        info: Dict[str, Any] = {}

        self._last_obs = obs
        self._terminated = terminated or truncated

        return obs.copy(), reward, terminated, truncated, info  # type: ignore

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def render(self):  # type: ignore
        return self._last_obs

    def close(self):
        if self._game.is_launched:
            self._game.stop_frame_grabber()