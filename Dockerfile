# first stage: build all dependencies and install them inside venv
FROM python:3.10.1-alpine3.15 as wheel-build

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

COPY ./requirements.txt ./requirements.txt

ENV VIRTUAL_ENV=/home/app/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install -r requirements.txt

# second stage: install ansible-deployment
FROM python:3.10.1-alpine3.15


RUN adduser -D app && apk update && apk upgrade && apk add ansible git vault libcap openssh-client openssh-keygen && \
    setcap cap_ipc_lock= /usr/sbin/vault

USER app
WORKDIR /home/app

COPY dist/*.tar.gz .
COPY --from=wheel-build /home/app/venv /home/app/venv

ENV VIRTUAL_ENV=/home/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-deps ansible-deployment-0.8.0.tar.gz --use-feature=in-tree-build

ENTRYPOINT ["ansible-deployment"]
