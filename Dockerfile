FROM python: 3.10-slim
ENV PYTHONUNBUFFERED True

#Directory in the container where app will run
WORKDIR /app

# Copy local code to the container image and install dependencies
COPY . ./
RUN pip install --no-cache-dir -r requirements.txt


# Cloud Run injects the PORT environment variable (default 8080).
# We use that variable to tell uvicorn where to listen.
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}