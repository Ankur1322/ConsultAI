FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml .
COPY consultai ./consultai
COPY prompts ./prompts
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "consultai.main:app", "--host", "0.0.0.0", "--port", "8000"]
