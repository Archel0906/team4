FROM python:3.13-slim

WORKDIR /workspace

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 코드 복사
COPY . .

# 테스트 실행
CMD ["pytest", "tests/", "-v"]