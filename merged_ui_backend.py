import streamlit as st
import io
import textwrap
from dataclasses import dataclass, asdict
from typing import List, Optional
from PIL import Image
from diffusers import StableDiffusionPipeline
import torch
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
import base64

# ================= Backend Logic =================

@dataclass
class Scene:
    index: int
    title: str
    text: str
    image_prompt: str
    image_bytes: Optional[bytes] = None

    def to_dict(self):
        d = asdict(self)
        if self.image_bytes is not None:
            d["image_bytes"] = f"<{len(self.image_bytes)} bytes>"
        return d

def generate_scenes_locally(idea, genre, tone, audience, n_scenes, art_style) -> List[Scene]:
    base_titles = ["Opening", "Rising Trouble", "Turning Point", "The Peak", "Aftermath"]
    titles = base_titles[:n_scenes]

    scenes: List[Scene] = []
    for i, t in enumerate(titles, start=1):
        paragraph = textwrap.fill(
            f"[{genre}/{tone}/{audience}] {t}: Based on the idea — {idea} — story continues here.",
            width=100,
        )
        image_prompt = f"{genre} {tone} illustration of {idea.lower()} — scene '{t}', style: {art_style}. Wide shot, cinematic lighting"
        scenes.append(Scene(i, t, paragraph, image_prompt))
    return scenes

# Stable Diffusion pipeline
pipe: Optional[StableDiffusionPipeline] = None
def load_sd_pipeline():
    global pipe
    if pipe is None:
        model_id = "stabilityai/sd-turbo"
        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32)
        pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")
    return pipe

def generate_image_fast(image_prompt: str) -> Optional[bytes]:
    try:
        pipe = load_sd_pipeline()
        image = pipe(image_prompt, height=256, width=256).images[0]
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        print("Image generation error:", e)
        return None

def export_pdf(scenes: List[Scene]) -> Optional[bytes]:
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    margin = 2 * cm
    text_width = width - 2 * margin

    for sc in scenes:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, height - margin, f"{sc.index}. {sc.title}")
        c.setFont("Helvetica", 11)
        y = height - margin - 1.2 * cm
        wrapped = textwrap.wrap(sc.text, width=95)
        for line in wrapped:
            c.drawString(margin, y, line)
            y -= 14
            if y < margin + 8 * cm:
                break
        if sc.image_bytes:
            try:
                img = Image.open(io.BytesIO(sc.image_bytes))
                img_ratio = img.width / img.height
                max_w, max_h = text_width, 10 * cm
                if max_w / max_h > img_ratio:
                    draw_h = max_h
                    draw_w = draw_h * img_ratio
                else:
                    draw_w = max_w
                    draw_h = draw_w / img_ratio
                c.drawImage(ImageReader(img), margin, margin, width=draw_w, height=draw_h, preserveAspectRatio=True, mask="auto")
            except:
                pass
        c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

# ================= Streamlit Frontend =================

st.set_page_config(page_title="Fast Text-to-Image Story Generator", layout="wide")
st.title("📖 Fast Story Generator with AI Images")

with st.sidebar:
    st.header("Settings")
    idea = st.text_area(
        "Story idea",
        placeholder="A young girl finds a secret door in her grandmother's attic.",
        height=120
    )
    colA, colB = st.columns(2)
    with colA:
        genre = st.selectbox(
            "Genre",
            ["fantasy", "sci-fi", "mystery", "adventure", "comedy", "drama"],
            0
        )
        audience = st.selectbox("Audience", ["kids", "teens", "adults"], 0)
    with colB:
        tone = st.selectbox(
            "Tone",
            ["lighthearted", "whimsical", "epic", "dark", "hopeful", "poignant"],
            0
        )
        n_scenes = st.slider("# of scenes", 3, 5, value=3)
    art_style = st.selectbox("Art style", ["cartoon", "anime", "realistic", "3D render"], 0)
    go = st.button("✨ Generate Story")

if "scenes" not in st.session_state:
    st.session_state["scenes"] = []

if go and idea.strip():
    st.session_state["scenes"] = generate_scenes_locally(idea.strip(), genre, tone, audience, n_scenes, art_style)

scenes = st.session_state["scenes"]

if scenes:
    st.subheader("Your Illustrated Story")

    if st.button("🖼 Generate All Images"):
        progress_text = st.empty()
        progress_bar = st.progress(0)
        total = len(scenes)
        for idx, sc in enumerate(scenes):
            progress_text.text(f"Generating image {idx+1}/{total}: {sc.title}")
            sc.image_bytes = generate_image_fast(sc.image_prompt)   # ✅ FIXED
            progress_bar.progress((idx + 1) / total)
        progress_text.text("All images generated! ✅")
        st.success("All images generated!")

    for idx, sc in enumerate(scenes):
        with st.container():
            st.markdown(f"### Scene {sc.index}: {sc.title}")
            st.write(sc.text)
            cols = st.columns([3, 2])
            with cols[0]:
                st.caption("Editable image prompt")
                new_prompt = st.text_area(f"prompt_{idx}", value=sc.image_prompt, height=100, label_visibility="collapsed")
                if new_prompt != sc.image_prompt:
                    sc.image_prompt = new_prompt
                if st.button("🖼 Generate image", key=f"img_{idx}"):
                    sc.image_bytes = generate_image_fast(sc.image_prompt)   # ✅ FIXED
            with cols[1]:
                if sc.image_bytes:
                    st.image(io.BytesIO(sc.image_bytes), caption=f"Scene {sc.index} — Illustration")
                else:
                    st.info("No image yet. Click Generate Image above.")

    st.divider()

    if st.button("🧾 Export PDF"):
        pdf_bytes = export_pdf(scenes)
        if pdf_bytes:
            st.download_button(
                "📥 Download Story PDF",
                data=pdf_bytes,
                file_name="story.pdf",
                mime="application/pdf"
            )

else:
    st.info("Add a story idea and click Generate Story to begin.")
