# Python 3.10-slim 버전을 기반 이미지로 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 파일을 먼저 복사하여 의존성 설치 (Docker 빌드 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 애플리케이션 코드 복사
COPY . .

# 애플리케이션 실행 명령어
CMD ["python", "main.py"]
