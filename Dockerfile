FROM public.ecr.aws/lambda/python:3.9
COPY converter.py ${LAMBDA_TASK_ROOT}
COPY requirements.txt  .
RUN  yum update -y
RUN  yum install -y \
     texlive-xetex  \
     texlive-fonts-recommended  \
     texlive-plain-generic \
     pandoc
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
CMD [ "converter.handler" ]
