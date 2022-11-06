FROM pandoc/core:latest-ubuntu

ARG DEBIAN_FRONTEND=noninteractive

# set secrets
ARG TELEGRAM_TOKEN
ENV TELEGRAM_TOKEN=${TELEGRAM_TOKEN}

# set root path
ENV ROOT_PATH="/tmp/"

# install python and pip
RUN apt-get update &&  \
    apt-get install -y python3 \
    python3-pip


#install chromium dependencies
RUN apt-get update &&  \
    apt-get install -y gconf-service \
    libasound2 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
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
    libnss3 \
    lsb-release \
    xdg-utils \
    wget

# install texlive
RUN apt-get update \
    && apt-get install -y \
    texlive-xetex  \
    texlive-fonts-recommended  \
    texlive-plain-generic

# install python dependencies
RUN pip install --upgrade pip
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
RUN rm /requirements.txt

# copy app files
ARG FUNCTION_DIR="/function/"
RUN mkdir -p ${FUNCTION_DIR}
COPY ./app/ ${FUNCTION_DIR}

# set entrypoint and cmd
WORKDIR ${FUNCTION_DIR}
ENTRYPOINT [ "/usr/bin/python3", "-m", "awslambdaric" ]