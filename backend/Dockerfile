FROM python:3.12-slim

WORKDIR /koine

RUN --mount=type=secret,id=pip.conf,mode=444 \
    PIP_CONFIG_FILE=/run/secrets/pip.conf \
    pip install --break-system-packages uv

COPY pyproject.toml uv.lock uv.toml ./
RUN --mount=type=secret,id=netrc,target=/root/.netrc,mode=444 \
    uv sync --frozen --no-dev

COPY backend/ ./backend
COPY tokenizers/ ./tokenizers
COPY .fileignore .


EXPOSE 8000
CMD ["uv", "run", "--no-sync", "-m", "backend.main"]
