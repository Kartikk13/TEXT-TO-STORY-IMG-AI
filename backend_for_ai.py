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
    

def generate_scenes_locally(idea, genre, tone, audience, n_scenes) -> List[Scene]:
    base_titles = ["Opening", "Rising Trouble", "Turning Point", "The Peak", "Aftermath"]
    titles = base_titles[:n_scenes]

    scenes: List[Scene] = []
    for i, t in enumerate(titles, start=1):
        paragraph = textwrap.fill(
            f"[{genre}/{tone}/{audience}] {t}: Based on the idea — {idea} — story continues here.",
            width=100,
        )
        image_prompt = f"{genre} {tone} illustration of {idea.lower()} — scene '{t}'. Wide shot, cinematic lighting"
        scenes.append(Scene(i, t, paragraph, image_prompt))
    return scenes