# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import hmac
import base64
import hashlib
import os
from botocore.exceptions import ClientError
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 你也可以写 ["http://localhost:5500"] 更安全
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
CLIENT_ID = '4quucr17sofk8c874jlhm29g0o'
CLIENT_SECRET = 'bim9cvkkua3443kam6vrr5jar1umu8p0rmdi6b8c520r9knm42r'
REGION = 'us-east-1'

# 数据模型