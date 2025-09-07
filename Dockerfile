FROM python:3.10-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir accelerate

COPY . .

# ✅ Make Streamlit dirs and ensure they’re writable
RUN mkdir -p /app/.streamlit /app/.cache /app/.config /app/.local && \
    chmod -R 777 /app/.streamlit /app/.cache /app/.config /app/.local

# ✅ Force everything into /app instead of /
ENV HOME=/app
ENV XDG_CACHE_HOME=/app/.cache
ENV XDG_CONFIG_HOME=/app/.config
ENV XDG_DATA_HOME=/app/.local/share
ENV STREAMLIT_CACHE_DIR=/app/.cache/streamlit
ENV STREAMLIT_CONFIG_DIR=/app/.config/streamlit
ENV STREAMLIT_RUNTIME_DIR=/app/.streamlit

EXPOSE 7860

CMD ["streamlit", "run", "merged_ui_backend.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.headless=true"]
