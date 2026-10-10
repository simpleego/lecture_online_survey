FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py admin.py analysis.py run.py ./
COPY static ./static
RUN useradd --create-home survey
USER survey
EXPOSE 8080
CMD ["python", "run.py"]
