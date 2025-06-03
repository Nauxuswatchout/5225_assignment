import boto3
import hmac
import base64
import hashlib
import os
from botocore.exceptions import ClientError

def get_secret_hash(username, client_id, client_secret):
    msg = username + client_id
    dig = hmac.new(str(client_secret).encode('utf-8'),
                   msg=str(msg).encode('utf-8'),
                   digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

def setup_aws_credentials():
    # 设置 AWS 凭证
    os.environ['AWS_ACCESS_KEY_ID'] = 'ASIAU4XJBVESD6765W5H'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'enZ03Eoa55kovX7Nf8w7qAD3TY7pdIoOBux5EJVi'
    os.environ['AWS_SESSION_TOKEN'] = 'IQoJb3JpZ2luX2VjEDcaCXVzLXdlc3QtMiJHMEUCICPdK7vrnkBgEde1zRVmoN+NBqnaP3JDWPP+cB6KOS4JAiEA0HcKKd+sVnegyjOomxHve7ZKD+P3epy6t3z/NlLHtgwqtQIIEBABGgwzMzY1Njk5MzYxNjQiDBP2H5pKPCQxlQlJ/iqSAvFZnrOQGJ9gTlU1cpiABM6Gs3CobAGmZDNQ/Bgq9AglgVDfSVcCE64xIBp4wqmUA16hk2zVXmfOUZJ/2eVxGok086J6+MCNOLfueihcpjV2fWHy8Uu+645u7hUfAGuqJqX0/9dqJzNc7C3uC+22G9CAuEsxTs0n3GC/D0iSCgw5rrv7qP1d/3bwNLPHSp42BahafvWRQ4b7evJrBEsU4GnsckPYp68aqoovfIWlSFrMY8YjMPp4XrgZgdWc6+dsbCRMIu/wN/NuGGAgwTY4mA+jvoTguGz0WgyjXBZXNsNjmR0Hn3bV1PmQ5AdU0Q4sbQr6wiYa+xtA0Lahutp+MdCYfH/nT/HvSYkPrIA7hSIGsYIw9K76wQY6nQFxrKYX0F3kZjUJq/RrxBUXM7kngM5z8aB4+1iD0h4zrrAAyOv3r45c92LerDbvJtrg8p2S0prZ9eS3klnDc496es0ApWz/CZFXdf7b5YrHEWaeaxt4FcpAzrfgDqiXaUByGDg5W7/jX5Yr63VvuRQSbFvFSKsmd3NQGmctWu5a3IP2HNb4KRbYokjiuMteq1mZ88xFU1wX75JxqMWW'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

def login():
    # 首先设置 AWS 凭证
    setup_aws_credentials()
    
    client = boto3.client('cognito-idp', region_name='us-east-1')
    
    CLIENT_ID = '4quucr17sofk8c874jlhm29g0o'
    CLIENT_SECRET = 'bim9cvkkua3443kam6vrr5jar1umu8p0rmdi6b8c520r9knm42r'
    
    # 使用已注册的用户信息
    username = "dgiu6ai9"
    password = "qTa0NY7w#^"
    
    try:
        # 使用普通用户认证流程
        auth_response = client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': get_secret_hash(username, CLIENT_ID, CLIENT_SECRET)
            }
        )
        
        print("\n登录成功!")
        print("Access Token:", auth_response['AuthenticationResult']['AccessToken'][:20] + "...")
        print("ID Token:", auth_response['AuthenticationResult']['IdToken'][:20] + "...")
        print("Refresh Token:", auth_response['AuthenticationResult']['RefreshToken'][:20] + "...")
        
        # 保存令牌到文件
        with open('auth_tokens.txt', 'w') as f:
            f.write(f"Access Token: {auth_response['AuthenticationResult']['AccessToken']}\n")
            f.write(f"ID Token: {auth_response['AuthenticationResult']['IdToken']}\n")
            f.write(f"Refresh Token: {auth_response['AuthenticationResult']['RefreshToken']}\n")
        
        print("\n令牌已保存到 auth_tokens.txt 文件中")
            
    except ClientError as e:
        print(f"\n登录失败: {str(e)}")
        if 'NotAuthorizedException' in str(e):
            print("用户名或密码错误")
        elif 'UserNotConfirmedException' in str(e):
            print("用户邮箱未验证")
        else:
            print("请检查用户名和密码是否正确")
            print("\n您可能需要在 Cognito 控制台中启用 USER_PASSWORD_AUTH:")
            print("1. 进入 Cognito 控制台")
            print("2. 选择您的用户池")
            print("3. 点击 'App integration'")
            print("4. 在 'App clients and analytics' 中找到您的客户端")
            print("5. 点击 'Edit' 按钮")
            print("6. 在 'Auth Flows Configuration' 部分")
            print("7. 确保选中 'Enable username password based authentication (ALLOW_USER_PASSWORD_AUTH)'")

if __name__ == "__main__":
    login() 