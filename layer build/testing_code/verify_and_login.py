import boto3
import hmac
import base64
import hashlib
from botocore.exceptions import ClientError

def get_secret_hash(username, client_id, client_secret):
    msg = username + client_id
    dig = hmac.new(str(client_secret).encode('utf-8'),
                   msg=str(msg).encode('utf-8'),
                   digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

def verify_and_login():
    client = boto3.client('cognito-idp', region_name='us-east-1')
    
    CLIENT_ID = '4quucr17sofk8c874jlhm29g0o'
    CLIENT_SECRET = 'bim9cvkkua3443kam6vrr5jar1umu8p0rmdi6b8c520r9knm42r'
    
    # 获取用户输入
    username = input("请输入用户名: ")
    verification_code = input("请输入验证码: ")
    password = input("请输入密码: ")
    
    try:
        # 首先验证邮箱
        secret_hash = get_secret_hash(username, CLIENT_ID, CLIENT_SECRET)
        confirm_response = client.confirm_sign_up(
            ClientId=CLIENT_ID,
            SecretHash=secret_hash,
            Username=username,
            ConfirmationCode=verification_code
        )
        print("\n邮箱验证成功!")
        
        # 然后尝试登录
        try:
            auth_response = client.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                ClientId=CLIENT_ID,
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password,
                    'SECRET_HASH': secret_hash
                }
            )
            
            print("\n登录成功!")
            print("Access Token:", auth_response['AuthenticationResult']['AccessToken'][:20] + "...")
            print("ID Token:", auth_response['AuthenticationResult']['IdToken'][:20] + "...")
            print("Refresh Token:", auth_response['AuthenticationResult']['RefreshToken'][:20] + "...")
            
            # 保存令牌到文件（可选）
            with open('auth_tokens.txt', 'w') as f:
                f.write(f"Access Token: {auth_response['AuthenticationResult']['AccessToken']}\n")
                f.write(f"ID Token: {auth_response['AuthenticationResult']['IdToken']}\n")
                f.write(f"Refresh Token: {auth_response['AuthenticationResult']['RefreshToken']}\n")
            print("\n令牌已保存到 auth_tokens.txt 文件中")
            
        except ClientError as e:
            if 'NotAuthorizedException' in str(e):
                print("登录失败：用户名或密码错误")
            else:
                print(f"登录时出错: {str(e)}")
            
    except ClientError as e:
        if 'ExpiredCodeException' in str(e):
            print("验证码已过期，请重新注册获取新的验证码")
        elif 'CodeMismatchException' in str(e):
            print("验证码错误，请检查后重试")
        elif 'AliasExistsException' in str(e):
            print("该邮箱已被验证，请直接尝试登录")
            # 如果邮箱已验证，直接尝试登录
            try:
                secret_hash = get_secret_hash(username, CLIENT_ID, CLIENT_SECRET)
                auth_response = client.initiate_auth(
                    AuthFlow='USER_PASSWORD_AUTH',
                    ClientId=CLIENT_ID,
                    AuthParameters={
                        'USERNAME': username,
                        'PASSWORD': password,
                        'SECRET_HASH': secret_hash
                    }
                )
                
                print("\n登录成功!")
                print("Access Token:", auth_response['AuthenticationResult']['AccessToken'][:20] + "...")
                print("ID Token:", auth_response['AuthenticationResult']['IdToken'][:20] + "...")
                print("Refresh Token:", auth_response['AuthenticationResult']['RefreshToken'][:20] + "...")
                
                # 保存令牌到文件（可选）
                with open('auth_tokens.txt', 'w') as f:
                    f.write(f"Access Token: {auth_response['AuthenticationResult']['AccessToken']}\n")
                    f.write(f"ID Token: {auth_response['AuthenticationResult']['IdToken']}\n")
                    f.write(f"Refresh Token: {auth_response['AuthenticationResult']['RefreshToken']}\n")
                print("\n令牌已保存到 auth_tokens.txt 文件中")
                
            except ClientError as e:
                print(f"登录时出错: {str(e)}")
        else:
            print(f"验证时出错: {str(e)}")

if __name__ == "__main__":
    verify_and_login() 