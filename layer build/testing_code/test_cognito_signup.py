import boto3
import json
import random
import string
import hmac
import base64
import hashlib
from botocore.exceptions import ClientError

def generate_random_username():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def generate_random_password():
    lowercase = ''.join(random.choices(string.ascii_lowercase, k=3))
    uppercase = ''.join(random.choices(string.ascii_uppercase, k=3))
    digits = ''.join(random.choices(string.digits, k=2))
    special = ''.join(random.choices('!@#$%^&*', k=2))
    password = lowercase + uppercase + digits + special
    password_list = list(password)
    random.shuffle(password_list)
    return ''.join(password_list)

def generate_random_name():
    first_names = ['Alex', 'Sam', 'Chris', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Jamie']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
    return random.choice(first_names), random.choice(last_names)

def get_secret_hash(username, client_id, client_secret):
    msg = username + client_id
    dig = hmac.new(str(client_secret).encode('utf-8'),
                   msg=str(msg).encode('utf-8'),
                   digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

def test_signup():
    client = boto3.client('cognito-idp', region_name='us-east-1')
    
    USER_POOL_ID = 'us-east-1_g4SvG2N1E'
    CLIENT_ID = '4quucr17sofk8c874jlhm29g0o'
    CLIENT_SECRET = 'bim9cvkkua3443kam6vrr5jar1umu8p0rmdi6b8c520r9knm42r'
    
    test_username = generate_random_username()
    test_email = "nauxuswatchout@gmail.com"  # 使用您的真实邮箱
    test_password = generate_random_password()
    first_name, last_name = generate_random_name()
    
    print(f"\n开始测试注册功能...")
    print(f"测试用户名: {test_username}")
    print(f"测试邮箱: {test_email}")
    print(f"测试密码: {test_password}")
    print(f"名字: {first_name}")
    print(f"姓氏: {last_name}")
    print("\n请保存这些信息！您需要使用它们来完成邮箱验证和登录。")
    
    try:
        secret_hash = get_secret_hash(test_username, CLIENT_ID, CLIENT_SECRET)
        
        response = client.sign_up(
            ClientId=CLIENT_ID,
            SecretHash=secret_hash,
            Username=test_username,
            Password=test_password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': test_email
                },
                {
                    'Name': 'given_name',
                    'Value': first_name
                },
                {
                    'Name': 'family_name',
                    'Value': last_name
                }
            ]
        )
        
        print("\n注册成功!")
        print(f"用户 UUID: {response['UserSub']}")
        print("请查看您的邮箱 nauxuswatchout@gmail.com，您将收到一个验证码")
        print("收到验证码后，您可以使用以下信息登录：")
        print(f"用户名: {test_username}")
        print(f"密码: {test_password}")
        
    except ClientError as e:
        print(f"\n注册失败: {str(e)}")
        if 'UsernameExistsException' in str(e):
            print("该用户名已被注册")
        elif 'InvalidPasswordException' in str(e):
            print("密码不符合要求")
        else:
            print("发生其他错误，请检查配置和权限")

if __name__ == "__main__":
    test_signup() 