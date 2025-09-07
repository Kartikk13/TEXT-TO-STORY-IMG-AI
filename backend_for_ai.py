import os, io, textwrap
from dataclasses import dataclass, asdict
from typing import List, Optional
from PIL import Image
from transformers import pipeline
from diffusers import StableDiffusionPipeline
import torch
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
import base64
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

@dataclass      #dataclasses for defining scene generating objects
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
    

def generate_scenes_locally(idea, genre, tone, audience, n_scenes) -> List[Scene]:      #local scene generating function
    base_titles = ["Opening", "Rising Trouble", "Turning Point", "The Peak", "Aftermath"]
    titles = base_titles[:n_scenes]

    scenes: List[Scene] = []        #created scene list
    for i, t in enumerate(titles, start=1):
        paragraph = textwrap.fill(
            f"[{genre}/{tone}/{audience}] {t}: Based on the idea — {idea} — story continues here.",     #scene heading paragraph
            width=100,
        )
        image_prompt = f"{genre} {tone} illustration of {idea.lower()} — scene '{t}'. Wide shot, cinematic lighting"  #image creating prompt
        scenes.append(Scene(i, t, paragraph, image_prompt))
    return scenes



pipe = None
def load_sd_pipeline():         #pipeline for loading
    global pipe
    if pipe is None:
        model_id = "stabilityai/sd-turbo"       #sd-turbo model from stabilityai is used
        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32)
        pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")
    return pipe

def generate_image_fast(image_prompt: str) -> Optional[bytes]:      #image generation
    try:
        pipe = load_sd_pipeline()
        image = pipe(image_prompt, height=256, width=256).images[0]
        buf = io.BytesIO()
        image.save(buf, format="PNG")               #saving img in png format
        return buf.getvalue()
    except Exception as e:
        print("Image generation error:", e)         #handling img generation error
        return None
    


def export_pdf(scenes: List[Scene]) -> Optional[bytes]:     #pdf exporting
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)         #defining the canvas for each pg of pdf
    width, height = A4
    margin = 2 * cm
    text_width = width - 2 * margin

    for sc in scenes:                               #defining characterstics of text shown
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
                img = Image.open(io.BytesIO(sc.image_bytes))        #img characterstics to be use in pdf
                img_ratio = img.width / img.height
                max_w, max_h = text_width, 10 * cm
                if max_w / max_h > img_ratio:
                    draw_h = max_h
                    draw_w = draw_h * img_ratio
                else:
                    draw_w = max_w
                    draw_h = draw_w / img_ratio
                c.drawImage(ImageReader(img), margin, margin, width=draw_w, height=draw_h, preserveAspectRatio=True, mask="auto")
            except Exception:
                pass
        c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()



app = FastAPI()                                         #fast api login and call
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Backend is running successfully 🚀"}

@app.post("/generate_scenes")                   #generating scenes
def api_generate_scenes(payload: dict):
    idea = payload["idea"]
    genre = payload["genre"]
    tone = payload["tone"]
    audience = payload["audience"]
    n_scenes = payload["n_scenes"]
    art_style = payload.get("art_style", "cartoon")
    scenes = generate_scenes_locally(idea, genre, tone, audience, n_scenes)
    for sc in scenes:
        sc.image_prompt = sc.image_prompt.rstrip(".") + f", style: {art_style}, high detail, cinematic lighting"  #prompt for img generation
    return {"scenes": [sc.to_dict() for sc in scenes]}

@app.post("/generate_image")
def api_generate_image(payload: dict):
    prompt = payload["prompt"]
    image_bytes = generate_image_fast(prompt)
    if image_bytes:
        return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")
    return {"error": "Image generation failed"}

@app.post("/export_pdf")
def api_export_pdf(payload: dict):
    scenes_list = []
    for s in payload["scenes"]:
        img_bytes = None
        if s.get("image_bytes"):
            img_bytes = base64.b64decode(s["image_bytes"])
        scenes_list.append(
            Scene(
                index=s["index"],
                title=s["title"],
                text=s["text"],
                image_prompt=s["image_prompt"],
                image_bytes=img_bytes
            )
        )
    pdf_bytes = export_pdf(scenes_list)
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf")
