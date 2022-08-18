FROM amazonlinux:2018.03.0.20190514 as builder
RUN mkdir /var/task/
### Chrome headless
RUN yum install -y gcc openssl-devel bzip2-devel libffi-devel wget unzip libuuid expat
RUN wget https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-55/stable-headless-chromium-amazonlinux-2017-03.zip
RUN unzip stable-headless-chromium-amazonlinux-2017-03.zip && mv /headless-chromium /var/task/
### Python https://dev.to/fferegrino/creating-an-aws-lambda-using-pipenv-2h4a
RUN wget https://www.python.org/ftp/python/3.8.2/Python-3.8.2.tgz
RUN tar xzf Python-3.8.2.tgz
RUN cd Python-3.8.2 && ./configure --enable-optimizations
RUN cd Python-3.8.2 && make altinstall
WORKDIR /var/task/
#COPY pipenv-locked-requirements.txt /var/task/
#RUN python3.8 -m pip install -r pipenv-locked-requirements.txt -t /var/task/
### Libs
RUN mkdir /var/task/data && mkdir /var/task/lib
RUN cp \
        /usr/lib64/libnss3.so \
        /lib64/libuuid.so.1 \
        /lib64/libexpat.so.1 \
        /usr/lib64/libsoftokn3.so \
        /usr/lib64/libsqlite3.so.0 \
        /usr/lib64/libnssutil3.so \
    /var/task/lib

FROM pandoc/core:latest-ubuntu

ARG DEBIAN_FRONTEND=noninteractive

# set secrets
ARG TELEGRAM_TOKEN
ENV TELEGRAM_TOKEN=${TELEGRAM_TOKEN}

# install python and pip
RUN apt-get update \
    && apt-get install -y python3 \
    python3-pip

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

# pyppeteer config from previous build step
ENV PYPPETEER_HOME=/tmp/
ENV FONTCONFIG_PATH=/var/task/fonts
ENV CHROME_PROFILE_PATH=/tmp/
ENV LD_LIBRARY_PATH=/var/task/lib
ENV CHROME_EXECUTABLE_PATH=/var/task/headless-chromium
COPY --from=builder /var/task/ /var/task/

# copy app files
ARG FUNCTION_DIR="/function/"
RUN mkdir -p ${FUNCTION_DIR}
COPY ./app/ ${FUNCTION_DIR}

# set entrypoint and cmd
WORKDIR ${FUNCTION_DIR}
ENTRYPOINT [ "/usr/bin/python3", "-m", "awslambdaric" ]
CMD [ "process_messages.handler" ]