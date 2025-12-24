# STAGE 1: Build dependencies
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# STAGE 2: Final Runtime
FROM python:3.11-slim as runner
WORKDIR /app
# Copy only the installed packages from the builder
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Run the application (production-ready; no --reload)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
