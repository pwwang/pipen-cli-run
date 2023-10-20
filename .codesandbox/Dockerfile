FROM python:3.10.12

RUN apt-get remove -y curl && \
    apt-get update && apt-get install -y curl fish && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    chsh -s /usr/bin/fish
