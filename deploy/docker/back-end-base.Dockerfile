FROM python:3.9-alpine
RUN apk update
RUN apk add gcc g++

ADD ./poetry.lock /code/
ADD ./pyproject.toml /code/
WORKDIR /code
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' >/etc/timezone
RUN pip install --trusted-host 192.168.3.59 --index-url http://192.168.3.59:8082/simple/ poetry
ENV POETRY_VIRTUALENVS_CREATE=false
RUN poetry install --only main
