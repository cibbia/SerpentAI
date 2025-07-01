import streamlit as st
from serpent.model_hub import list_models, download_model

st.header("Model Hub 🗄️")

models = list_models()
cols = st.columns(4)
headers = ["ID", "Game", "Algo", "Action"]
for i,h in enumerate(headers):
    cols[i].markdown(f"**{h}**")

for m in models:
    cols = st.columns(4)
    cols[0].write(m['id'])
    cols[1].write(m['game'])
    cols[2].write(m['algo'])
    if cols[3].button("Download", key=m['id']):
        with st.spinner("Downloading…"):
            path = download_model(m['id'])
        st.success(f"Saved to {path}")