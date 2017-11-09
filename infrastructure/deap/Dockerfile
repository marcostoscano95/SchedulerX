FROM python:3

ENV PYTHONUNBUFFERED 1

RUN mkdir /conf
RUN mkdir /data
RUN mkdir /app

WORKDIR /conf
ADD ./requirements.txt /conf
RUN pip install -r requirements.txt --src /usr/local/src

WORKDIR /app
