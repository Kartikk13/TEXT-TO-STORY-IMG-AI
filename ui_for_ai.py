import streamlit as st
import requests
import io
from PIL import Image
import base64

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Fast Text-to-Image Story Generator", layout="wide")
st.title("📖 Fast Story Generator with AI Images")