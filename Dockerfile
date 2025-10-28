FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

# Install package and web dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .[web,pdf]

# Streamlit configuration: disable usage metrics
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
