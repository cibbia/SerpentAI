import os
import streamlit as st
import time
from typing import List
import sys
import subprocess, webbrowser

try:
    from serpent.grpc.frame_client import FrameConsumerSync
except Exception:
    FrameConsumerSync = None  # type: ignore

from serpent.window_controller import WindowController
from serpent.quickstart import generate_quickstart_plugin  # hypothetical helper, may not exist

st.set_page_config(page_title="Serpent.AI Dashboard", layout="wide")

st.title("🕹️  Serpent.AI Dashboard")

page = st.sidebar.selectbox("Page", ["Stream", "Reward Wizard", "Action Editor", "Model Hub"])

if page == "Reward Wizard":
    from serpent.gui import reward_wizard  # noqa: F401
    st.stop()
elif page == "Action Editor":
    from serpent.gui import action_editor  # noqa: F401
    st.stop()
elif page == "Model Hub":
    from serpent.gui import model_hub  # noqa: F401
    st.stop()

if FrameConsumerSync is None:
    st.error("gRPC dependencies not installed. Please install serpentai[full].")
    st.stop()

# Sidebar – window discovery & plugin generation
st.sidebar.header("Window Discovery")
wc = WindowController()
windows: List[str] = wc.list_windows()  # Assume method exists, else stub
selected = st.sidebar.selectbox("Choose window", windows)

if st.sidebar.button("Generate Plugin"):
    plugin_name = generate_quickstart_plugin(selected)
    st.sidebar.success(f"Plugin {plugin_name} created! Use serpent launch {plugin_name}")

st.sidebar.header("Frame Stream")
start_stream = st.sidebar.button("Start Stream")

# TensorBoard launch
st.sidebar.header("TensorBoard")
if st.sidebar.button("Open TensorBoard"):
    logdir = os.path.abspath("runs")
    subprocess.Popen([sys.executable, "-m", "tensorboard", "--logdir", logdir, "--port", "6006"])
    webbrowser.open("http://localhost:6006")

frame_area = st.empty()

if start_stream:
    consumer = FrameConsumerSync()
    st.sidebar.success("Streaming frames… Press Ctrl+C in terminal to stop.")
    while True:
        frame_msg = consumer.get_frame()
        import numpy as np
        frame = np.frombuffer(frame_msg.data, dtype=np.uint8).reshape((frame_msg.height, frame_msg.width, 3))
        frame_area.image(frame, channels="RGB")
        time.sleep(0.03)