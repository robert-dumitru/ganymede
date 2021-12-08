FROM pandoc/latex:latest
#init alpine environment
RUN apk update
RUN apk add \
    g++ \
    make \
    cmake \
    unzip \
    curl-dev \
    autoconf \
    automake \
    libtool \
    libexecinfo-dev \
    libffi-dev \
    bash \
    unzip \
    python3 \
    python3-dev \
    py3-pip \
    py3-wheel \
    py3-cffi

#install extra latex dependencies
RUN tlmgr update --all --self
RUN tlmgr install tcolorbox
RUN tlmgr install pgf
RUN tlmgr install xcolor
RUN tlmgr install environ
RUN tlmgr install trimspaces
RUN tlmgr install mathpazo
RUN tlmgr install parskip
RUN tlmgr install adjustbox
RUN tlmgr install collectbox
RUN tlmgr install eurosym
RUN tlmgr install ucs
RUN tlmgr install enumitem
RUN tlmgr install ulem
RUN tlmgr install jknapltx rsfs
RUN tlmgr install titling

#init lambda environment
ARG LAMBDA_TASK_ROOT="/var/task"
RUN mkdir -p ${LAMBDA_TASK_ROOT}
RUN pip install \
        --target ${LAMBDA_TASK_ROOT} \
        awslambdaric
WORKDIR ${LAMBDA_TASK_ROOT}
COPY converter.py ${LAMBDA_TASK_ROOT}
COPY requirements.txt .
RUN  pip3 install jupyter
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

ENTRYPOINT [ "/usr/bin/python3", "-m", "awslambdaric" ]
CMD [ "converter.handler" ]
