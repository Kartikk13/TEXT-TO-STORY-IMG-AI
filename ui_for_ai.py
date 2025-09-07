import streamlit as st
import requests
import io
from PIL import Image
import base64

API_URL = "http://127.0.0.1:8000"               #url to be used locally

st.set_page_config(page_title="Fast Text-to-Image Story Generator", layout="wide")          #page configuration
st.title("📖 Fast Story Generator with AI Images")


with st.sidebar:                                #sidebar create
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



if "scenes" not in st.session_state:
    st.session_state["scenes"] = []

def fetch_scenes():
    payload = {
        "idea": idea.strip(),
        "genre": genre,
        "tone": tone,
        "audience": audience,
        "n_scenes": n_scenes,
        "art_style": art_style
    }
    res = requests.post(f"{API_URL}/generate_scenes", json=payload)         #requesting img from backend
    if res.status_code == 200:
        return res.json().get("scenes", [])
    else:
        st.error("Error connecting to backend")
        return []
    

def generate_image(scene_index):
    scene = st.session_state["scenes"][scene_index]
    res = requests.post(f"{API_URL}/generate_image", json={"prompt": scene["image_prompt"]})
    if res.status_code == 200:
        scene["image_bytes"] = res.content
    else:
        st.error("Failed to generate image")

if go and idea.strip():
    st.session_state["scenes"] = fetch_scenes()



scenes = st.session_state["scenes"]

if scenes:
    st.subheader("Your Illustrated Story")

    if st.button("🖼 Generate All Images"):             #generate img button
        progress_text = st.empty()
        progress_bar = st.progress(0)
        total = len(scenes)
        for idx, sc in enumerate(scenes):
            progress_text.text(f"Generating image {idx+1}/{total}: {sc['title']}")
            try:
                res = requests.post(f"{API_URL}/generate_image", json={"prompt": sc["image_prompt"]})
                sc["image_bytes"] = res.content
            except:
                sc["image_bytes"] = None
            progress_bar.progress((idx + 1) / total)
        progress_text.text("All images generated! ✅")
        st.success("All images generated!")

    for idx, sc in enumerate(scenes):
        with st.container():
            st.markdown(f"### Scene {sc['index']}: {sc['title']}")
            st.write(sc['text'])
            cols = st.columns([3, 2])
            with cols[0]:
                st.caption("Editable image prompt")                     #img prompt edit
                new_prompt = st.text_area(f"prompt_{idx}", value=sc["image_prompt"], height=100, label_visibility="collapsed")
                if new_prompt != sc["image_prompt"]:
                    sc["image_prompt"] = new_prompt
                if st.button("🖼 Generate image", key=f"img_{idx}"):
                    generate_image(idx)
            with cols[1]:
                if "image_bytes" in sc and sc["image_bytes"]:
                    st.image(io.BytesIO(sc["image_bytes"]), caption=f"Scene {sc['index']} — Illustration")
                else:
                    st.info("No image yet. Click Generate Image above.")

    st.divider()


    if st.button("🧾 Export PDF"):              #export pdf button
        serializable_scenes = []
        for sc in scenes:
            img_b64 = None
            if "image_bytes" in sc and sc["image_bytes"]:
                img_b64 = base64.b64encode(sc["image_bytes"]).decode("utf-8")
                serializable_scenes.append({
                "index": sc["index"],
                "title": sc["title"],
                "text": sc["text"],
                "image_prompt": sc["image_prompt"],
                "image_bytes": img_b64
            })

        pdf_response = requests.post(f"{API_URL}/export_pdf", json={"scenes": serializable_scenes})

        if pdf_response.status_code == 200:             #download pdf button
            st.download_button(
                "📥 Download Story PDF",
                data=pdf_response.content,
                file_name="story.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Failed to generate PDF")

else:
    st.info("Add a story idea and click Generate Story to begin.")