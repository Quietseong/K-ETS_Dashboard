FROM python:3.10-slim

# 시스템 의존성 + 한글 폰트
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-nanum \
    fontconfig \
    curl \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# matplotlib 백엔드 (headless)
ENV MPLBACKEND=Agg
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 의존성 먼저 설치 (캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY agent/ agent/
COPY pages/ pages/
COPY prompts/ prompts/
COPY data/ data/
COPY docs/ docs/
COPY main.py app_api.py data_loader.py utils.py pyproject.toml ./

EXPOSE 8501 8000

# 기본: Streamlit (docker-compose에서 override)
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
