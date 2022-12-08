# first stage: build all dependencies and install them inside venv
FROM 3.12.0a3-alpine3.17 as wheel-build

RUN adduser -D app && apk update && apk upgrade && apk add gcc musl-dev libffi-dev

USER app
WORKDIR /home/app

COPY ./requirements.txt ./requirements.txt

ENV VIRTUAL_ENV=/home/app/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install -r requirements.txt

# second stage: install ansible-deployment
FROM 3.12.0a3-alpine3.17


RUN adduser -D app && apk update && apk upgrade && apk add py3-passlib ansible git vault libcap openssh-client openssh-keygen && \
    setcap cap_ipc_lock= /usr/sbin/vault

USER app
WORKDIR /home/app

COPY dist/*.tar.gz .
COPY --from=wheel-build /home/app/venv /home/app/venv

ENV VIRTUAL_ENV=/home/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-deps ansible-deployment-0.8.0.tar.gz --use-feature=in-tree-build

ENTRYPOINT ["ansible-deployment"]
