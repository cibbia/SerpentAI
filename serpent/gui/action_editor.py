import streamlit as st
import json, os
from pathlib import Path

st.header("Action-Space Editor 🎮")

plugin_name = st.text_input("Plugin folder name", value="Generic_QUICKSTART")

plugin_dir = Path("plugins/games") / f"{plugin_name}Plugin"
inputs_file = plugin_dir / "game_inputs.json"

if not inputs_file.exists():
    st.warning(f"No game_inputs.json found at {inputs_file}.")
    st.stop()

with inputs_file.open() as f:
    data = json.load(f)

st.subheader("Toggle / rename actions")
updated = []
changed = False
for idx, entry in enumerate(data):
    col1, col2 = st.columns([1,4])
    with col1:
        enable = st.checkbox("", value=entry.get("enabled", True), key=f"cb{idx}")
    with col2:
        name = st.text_input("Action name", value=entry["name"], key=f"name{idx}")
    e = entry.copy()
    e["enabled"] = enable
    e["name"] = name
    updated.append(e)
    if enable != entry.get("enabled", True) or name != entry["name"]:
        changed = True

if st.button("Save changes") and changed:
    with inputs_file.open("w") as f:
        json.dump(updated, f, indent=2)
    st.success("Saved!")