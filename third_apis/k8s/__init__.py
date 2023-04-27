import os

from loguru import logger
from pydantic import BaseModel
from kubernetes import client, config

try:
    config.load_incluster_config()
except Exception:
    logger.warning("Kubernets load_incluster_config failed")

batch_v1_api = client.BatchV1Api()
core_v1_api = client.CoreV1Api()

NAMESPACE = os.environ.get("K8S_NAMESPACE", "default")
BASE_IMAGE = os.environ.get("K8S_IMAGE", os.environ.get("base_image"))


class JobConfig(BaseModel):
    namespace: str = NAMESPACE
    image: str = BASE_IMAGE
    name: str
    command: str


class CronJobConfig(JobConfig):
    cron: str
