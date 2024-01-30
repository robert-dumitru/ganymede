FROM python:3.11-buster as builder

RUN pip install poetry==1.5.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install && rm -rf $POETRY_CACHE_DIR

FROM python:3.11-buster as runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y  \
    texlive-xetex  \
    texlive-fonts-recommended  \
    texlive-plain-generic  \
    pandoc
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
RUN echo "deb http://ftp.us.debian.org/debian buster main non-free" >> /etc/apt/sources.list.d/fonts.list
RUN playwright install --with-deps chromium

ADD src/* ./

CMD ["python", "main.py"]

