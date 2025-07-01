import streamlit as st
import numpy as np
import pytesseract
from serpent.grpc.frame_client import FrameConsumerSync
from streamlit_drawable_canvas import st_canvas
import io, time

st.header("Reward Wizard 🏆")

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
        st.success("Reward function saved (stub). Reload Serpent to take effect.")
        # TODO: locate current plugin and write function