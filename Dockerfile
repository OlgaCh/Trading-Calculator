FROM python:3.8

WORKDIR /src

RUN apt-get update && apt-get install -qq -y \
  build-essential libpq-dev --no-install-recommends

COPY . /src
RUN pip3 install -e .
