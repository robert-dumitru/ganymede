FROM python:3.11-bullseye as builder

SHELL ["/bin/bash", "-c"]
COPY pyproject.toml poetry.lock ./
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN ${HOME}/.local/bin/poetry export --output requirements.txt

FROM python:3.11-bullseye

SHELL ["/bin/bash", "-c"]
ARG DEBIAN_FRONTEND=noninteractive
# patch dependencies for pyppeteer
RUN apt-get update && \
    apt-get install -y  \
    gconf-service \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libc6 \
    libcairo2  \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    ca-certificates \
    fonts-liberation \
    libappindicator1 \
    libnss3 \
    lsb-release \
    xdg-utils  \
    wget  \
    libcairo-gobject2 \
    libxinerama1 \
    libgtk2.0-0 \
    libpangoft2-1.0-0 \
    libthai0 \
    libpixman-1-0 \
    libxcb-render0 \
    libharfbuzz0b \
    libdatrie1 \
    libgraphite2-3 \
    libgbm1 \
    texlive-xetex  \
    texlive-fonts-recommended  \
    texlive-plain-generic \
    pandoc

# set up python dependencies
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY --from=builder requirements.txt .
RUN pip install -r requirements.txt && pyppeteer-install

# set up run configuration
ARG IPYNB_TG_TOKEN
RUN mkdir -p /app
ADD app /app/
CMD ["python3", "-m", "app"]
