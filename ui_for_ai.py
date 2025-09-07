import streamlit as st
import requests
import io
from PIL import Image
import base64

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Fast Text-to-Image Story Generator", layout="wide")
st.title("📖 Fast Story Generator with AI Images")


with st.sidebar:
    st.header("Settings")
    idea = st.text_area("Story idea", placeholder="A young girl finds a secret door in her grandmother's attic.", height=120)
    colA, colB = st.columns(2)
    with colA:
        genre = st.selectbox("Genre", ["fantasy", "sci-fi", "mystery", "adventure", "comedy", "drama"], 0)
        audience = st.selectbox("Audience", ["kids", "teens", "adults"], 0)
    with colB:
        tone = st.selectbox("Tone", ["lighthearted", "whimsical", "epic", "dark", "hopeful", "poignant"], 0)
        n_scenes = st.slider("# of scenes", 3, 5, value=3)
    art_style = st.selectbox("Art style", ["cartoon", "anime", "realistic", "3D render"], 0)
    go = st.button("✨ Generate Story")