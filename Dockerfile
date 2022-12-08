# first stage: build all dependencies and install them inside venv
FROM python:3.9.6-alpine as wheel-build


RUN adduser -D app && apk update && apk upgrade && apk add git build-base \
  cairo \
  cairo-dev \
  cargo \
  freetype-dev \
  gcc \
  gdk-pixbuf-dev \
  gettext \
  jpeg-dev \
  lcms2-dev \
  libffi-dev \
  musl-dev \
  openjpeg-dev \
  openssl-dev \
  pango-dev \
  poppler-utils \
  postgresql-client \
  postgresql-dev \
  py-cffi \
  python3-dev \
  rust \
  tcl-dev \
  tiff-dev \
  tk-dev \
  zlib-dev

USER app
WORKDIR /home/app

COPY ./ansible_deployment.egg-info/requires.txt ./requires.txt

ENV VIRTUAL_ENV=/home/app/venv
RUN python -m venv $VIRTUAL_ENV && pip wheel -w wheels/ -r requires.txt --use-feature=in-tree-build 
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install -r requires.txt

# second stage: install ansible-deployment
FROM python:3.9.6-alpine as venv-build


RUN adduser -D app && apk update && apk upgrade && apk add git vault libcap && \
    setcap cap_ipc_lock= /usr/sbin/vault
WORKDIR /home/app

USER app

COPY ./ansible_deployment/ ./ansible_deployment
COPY ./setup.py ./
COPY ./README.md ./
COPY --from=wheel-build /home/app/venv /home/app/venv

ENV VIRTUAL_ENV=/home/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-index . --use-feature=in-tree-build

ENTRYPOINT ["ansible-deployment"]
