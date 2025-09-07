# Text-to-Image Generator (Stable Diffusion + Streamlit)

This project provides a simple **Streamlit-based UI** for generating images from text prompts using the [Stable Diffusion](https://huggingface.co/CompVis/stable-diffusion) model.  
It runs on [Hugging Face Spaces](https://huggingface.co/spaces) with Docker as the runtime.

---

## 🚀 Features
- Generate images from text prompts.
- Powered by Hugging Face [🤗 Diffusers](https://github.com/huggingface/diffusers).
- Streamlit frontend with integrated backend logic.
- Dockerized for reproducibility.
- Configurable to run locally or on Hugging Face Spaces.

---

## 📦 Installation (Local Development)

1. **Clone the repository**
   ```bash
   git clone https://huggingface.co/spaces/<your-username>/<your-space-name>
   cd <your-space-name>


2. Create a virtual environment

python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows

3. Install dependencies

pip install -r requirements.txt

4. Run the app

streamlit run merged_ui_backend.py --server.port 7860 --server.address 0.0.0.0


**Running with Docker**
1. Build the image

docker build -t text-to-image .
2. Run the container

docker run -p 7860:7860 text-to-image

3. Then open http://localhost:7860
   
