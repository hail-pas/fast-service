import os
import contextlib

from pydantic import BaseModel
from kubernetes import client, config

with contextlib.suppress(Exception):
    config.load_incluster_config()


batch_v1_api = client.BatchV1Api()
core_v1_api = client.CoreV1Api()

NAMESPACE = os.environ.get("K8S_NAMESPACE", "default")
BASE_IMAGE = os.environ.get("K8S_IMAGE", os.environ.get("base_image"))  # noqa

JOB_TEMPLATE = "third_apis/k8s/templates/job_template.yaml"
CRONJOB_TEMPLATE = "third_apis/k8s/templates/cronjob_template.yaml"


class JobConfig(BaseModel):
    namespace: str = NAMESPACE
    image: str = BASE_IMAGE
    name: str
    command: str


class CronJobConfig(JobConfig):
    cron: str
