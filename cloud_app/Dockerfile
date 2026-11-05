FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOST=0.0.0.0 PORT=8080 TV4_DATABASE=/tmp/tv4.sqlite3
WORKDIR /app

# Cai dat dependencies
COPY cloud_app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Sao chep source code app va model AI
COPY cloud_app/ /app/cloud_app/
COPY data_features/ /app/data_features/
COPY traditional_ml/ /app/traditional_ml/
COPY deep_learning/ /app/deep_learning/

RUN mkdir -p /tmp && chmod 777 /tmp
EXPOSE 8080
HEALTHCHECK --start-period=90s --interval=30s --timeout=5s CMD python -c "import urllib.request, os; p = os.environ.get('PORT', '8080'); urllib.request.urlopen('http://127.0.0.1:' + p + '/api/health', timeout=4)"
CMD ["python", "cloud_app/app.py"]
