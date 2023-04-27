# docker build --build-arg BASE_IMAGE="" -build-arg ENVIRONMENT=""
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ENV base_image ${BASE_IMAGE}
# optional environment: development、test、production;  From 为变量作用域
ARG ENVIRONMENT
ENV environment ${ENVIRONMENT}
ADD ./ /code
WORKDIR /code
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' >/etc/timezone
RUN pip install -v poetry
RUN poetry install --only main
EXPOSE 8000
CMD ["python", "entrypoint/main.py"]
