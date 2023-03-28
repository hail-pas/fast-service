"""
测试
"""
from fastapi.testclient import TestClient

from core.factory import app

client = TestClient(app)
