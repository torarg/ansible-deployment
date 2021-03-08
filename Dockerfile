FROM python:3.9.2-slim


WORKDIR /app

COPY ./ansible_deployment/ ./ansible_deployment
COPY ./setup.py ./
COPY ./README.md ./

RUN apt-get update && apt-get -y install git && pip3 install .


CMD [ "ansible-deployment" ]
