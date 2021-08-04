FROM python:3.9.6-alpine


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

COPY ./ansible_deployment/ ./ansible_deployment
COPY ./setup.py ./
COPY ./README.md ./

RUN pip3 install pip --upgrade && pip3 install . --use-feature=in-tree-build --prefer-binary

ENV PATH=/home/app/.local/bin:$PATH



CMD [ "ansible-deployment" ]
