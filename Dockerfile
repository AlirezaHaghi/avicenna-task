FROM python:3.12-slim
 
WORKDIR /app
 
# Copy uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
 
# Install dependencies before copying source — keeps this layer cached on code changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
 
# Put the venv on PATH so plain `python` / `django-admin` just work
ENV PATH="/app/.venv/bin:$PATH"
 
COPY . .
 
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
 
EXPOSE 8000
 
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
 