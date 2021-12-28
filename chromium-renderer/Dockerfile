FROM public.ecr.aws/lambda/python:3.9
COPY chromium-converter.py ${LAMBDA_TASK_ROOT}
COPY parameters.yml ${LAMBDA_TASK_ROOT}
WORKDIR ${LAMBDA_TASK_ROOT}
COPY requirements.txt .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
RUN  pip3 install pyppeteer && pyppeteer-install
CMD  [ "chromium-converter.handler" ]