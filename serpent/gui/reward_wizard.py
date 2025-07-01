import streamlit as st
import numpy as np
import pytesseract
from serpent.grpc.frame_client import FrameConsumerSync
from streamlit_drawable_canvas import st_canvas
import io, time
from pathlib import Path

st.header("Reward Wizard 🏆")

plugin_name = st.sidebar.text_input("Plugin name", st.session_state.get("plugin_name","Generic_QUICKSTART"))
st.session_state["plugin_name"] = plugin_name

if 'consumer' not in st.session_state:
    st.session_state.consumer = FrameConsumerSync()

frame_msg = st.session_state.consumer.get_frame()
frame = np.frombuffer(frame_msg.data, dtype=np.uint8).reshape((frame_msg.height, frame_msg.width, 3))

st.subheader("1️⃣  Select Region of Interest (ROI)")
canvas_result = st_canvas(
    fill_color="rgba(255, 255, 255, 0.3)",
    stroke_width=3,
    stroke_color="#1bcc6f",
    background_image=frame,
    update_streamlit=True,
    height=frame_msg.height,
    width=frame_msg.width,
    drawing_mode="rect",
    key="canvas",
)

if canvas_result.json_data and len(canvas_result.json_data["objects"]):
    obj = canvas_result.json_data["objects"][0]
    left, top = int(obj["left"]), int(obj["top"])
    width, height = int(obj["width"]), int(obj["height"])
    roi = frame[top:top+height, left:left+width]
    st.image(roi, caption="Selected ROI")

    st.subheader("2️⃣  OCR Preview")
    text = pytesseract.image_to_string(roi)
    st.code(text or "<no text detected>")

    expr = st.text_input("Python expression to compute reward from OCR text",
                          value="int(text.strip()) if text.strip().isdigit() else 0")

    if st.button("Save reward function to plugin"):
        plugin_dir = Path("plugins/games") / f"{plugin_name}Plugin"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        file_path = plugin_dir / "reward.py"
        with open(file_path, "w") as f:
            f.write(f"""# Auto-generated reward function\nfrom typing import List\nfrom serpent.game_frame import GameFrame\n\n\n
def reward(frames: List[GameFrame], **kwargs):\n    # 'frames' is a buffer (latest last)\n    import pytesseract, numpy as np\n    frame = frames[-1].frame\n    roi = frame[{top}:{top+height}, {left}:{left+width}]\n    text = pytesseract.image_to_string(roi)\n    return {expr}\n""")
        st.success(f"Reward function saved to {file_path}. Relaunch game to take effect.")