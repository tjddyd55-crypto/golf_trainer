FROM python:3.12-slim

# 작업 디렉토리 고정
WORKDIR /app

# 환경변수 설정 (핵심)
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 전체 소스 복사
COPY . .

# 실행 명령 (railway Start Command 무시됨)
CMD ["gunicorn", "services.super_admin.app:app", "--bind", "0.0.0.0:8080"]
