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
class LoginRequest(BaseModel):
    username: str
    password: str

# AWS 凭证设置
def setup_aws_credentials():
    os.environ['AWS_ACCESS_KEY_ID'] = 'ASIAU4XJBVESD6765W5H'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'enZ03Eoa55kovX7Nf8w7qAD3TY7pdIoOBux5EJVi'
    os.environ['AWS_SESSION_TOKEN'] = 'IQoJb3JpZ2luX2VjEDcaCXVzLXdlc3QtMiJHMEUCICPdK7vrnkBgEde1zRVmoN+NBqnaP3JDWPP+cB6KOS4JAiEA0HcKKd+sVnegyjOomxHve7ZKD+P3epy6t3z/NlLHtgwqtQIIEBABGgwzMzY1Njk5MzYxNjQiDBP2H5pKPCQxlQlJ/iqSAvFZnrOQGJ9gTlU1cpiABM6Gs3CobAGmZDNQ/Bgq9AglgVDfSVcCE64xIBp4wqmUA16hk2zVXmfOUZJ/2eVxGok086J6+MCNOLfueihcpjV2fWHy8Uu+645u7hUfAGuqJqX0/9dqJzNc7C3uC+22G9CAuEsxTs0n3GC/D0iSCgw5rrv7qP1d/3bwNLPHSp42BahafvWRQ4b7evJrBEsU4GnsckPYp68aqoovfIWlSFrMY8YjMPp4XrgZgdWc6+dsbCRMIu/wN/NuGGAgwTY4mA+jvoTguGz0WgyjXBZXNsNjmR0Hn3bV1PmQ5AdU0Q4sbQr6wiYa+xtA0Lahutp+MdCYfH/nT/HvSYkPrIA7hSIGsYIw9K76wQY6nQFxrKYX0F3kZjUJq/RrxBUXM7kngM5z8aB4+1iD0h4zrrAAyOv3r45c92LerDbvJtrg8p2S0prZ9eS3klnDc496es0ApWz/CZFXdf7b5YrHEWaeaxt4FcpAzrfgDqiXaUByGDg5W7/jX5Yr63VvuRQSbFvFSKsmd3NQGmctWu5a3IP2HNb4KRbYokjiuMteq1mZ88xFU1wX75JxqMWW'
    os.environ['AWS_DEFAULT_REGION'] = REGION

# 生成 SECRET_HASH
def get_secret_hash(username, client_id, client_secret):
    msg = username + client_id
    dig = hmac.new(client_secret.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

# 核心复用逻辑
def login_cognito(username, password):
    setup_aws_credentials()
    client = boto3.client('cognito-idp', region_name=REGION)

    auth_response = client.initiate_auth(
        ClientId=CLIENT_ID,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': username,
            'PASSWORD': password,
            'SECRET_HASH': get_secret_hash(username, CLIENT_ID, CLIENT_SECRET)
        }
    )
    return auth_response['AuthenticationResult']

# /login 路由
@app.post("/login")
def login_api(request: LoginRequest):
    try:
        auth_result = login_cognito(request.username, request.password)
        return {
            "access_token": auth_result['AccessToken'],
            "id_token": auth_result['IdToken'],
            "refresh_token": auth_result['RefreshToken']
        }
    except ClientError as e:
        error_message = str(e)
        if 'NotAuthorizedException' in error_message:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        elif 'UserNotConfirmedException' in error_message:
            raise HTTPException(status_code=403, detail="用户邮箱未验证")
        else:
            raise HTTPException(status_code=500, detail="登录失败，请检查配置和参数")

# main 启动（可选）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
