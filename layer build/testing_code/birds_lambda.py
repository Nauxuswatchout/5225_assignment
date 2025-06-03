import json
import boto3
import cv2
import numpy as np
from ultralytics import YOLO
import os
import tempfile
import time
import torch

# 初始化 AWS 服务客户端
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('bird_detections')  # 需要在AWS中创建此表

def download_file_from_s3(bucket, key):
    """从S3下载文件到临时目录"""
    try:
        print(f"尝试从 S3 下载文件: bucket={bucket}, key={key}")
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            s3_client.download_fileobj(bucket, key, tmp_file)
            return tmp_file.name
    except Exception as e:
        print(f"下载文件时出错: {str(e)}")
        return None

def read_image_from_temp(temp_path):
    """从临时文件读取图片"""
    try:
        print(f"尝试读取图片: {temp_path}")
        img = cv2.imread(temp_path)
        if img is None:
            raise Exception("无法读取图片文件")
        return img
    except Exception as e:
        print(f"读取图片时出错: {str(e)}")
        return None

def detect_birds(image, confidence_threshold=0.6):
    """使用YOLO模型检测鸟类"""
    try:
        print("开始加载模型...")
        # 添加安全全局变量
        torch.serialization.add_safe_globals(['ultralytics.nn.tasks.DetectionModel'])
        
        # 加载模型
        model = YOLO("model.pt")
        
        print("开始执行检测...")
        # 运行检测
        results = model(image)[0]
        
        # 处理结果
        detections = []
        for result in results.boxes.data:
            x1, y1, x2, y2, conf, cls = result
            if conf > confidence_threshold:
                class_name = model.names[int(cls)]
                detections.append({
                    'class': class_name,
                    'confidence': float(conf),
                    'bbox': [float(x) for x in [x1, y1, x2, y2]]
                })
        
        print(f"检测完成，找到 {len(detections)} 个目标")
        return detections
    except Exception as e:
        print(f"检测过程中出错: {str(e)}")
        return []

def save_to_dynamodb(image_url, thumbnail_url, detections):
    """保存检测结果到DynamoDB"""
    try:
        print(f"尝试保存结果到 DynamoDB: {image_url}")
        # 准备要保存的数据
        item = {
            'image_url': image_url,
            'thumbnail_url': thumbnail_url,
            'detections': detections,
            'timestamp': int(time.time())
        }
        
        # 保存到DynamoDB
        table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"保存到数据库时出错: {str(e)}")
        return False

def lambda_handler(event, context):
    """Lambda函数入口点"""
    try:
        print("Lambda 函数开始执行...")
        # 从事件中获取S3信息
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        print(f"处理图片: bucket={bucket}, key={key}")
        
        # 构建S3 URL
        image_url = f"s3://{bucket}/{key}"
        
        # 下载图片
        temp_path = download_file_from_s3(bucket, key)
        if not temp_path:
            return {
                'statusCode': 500,
                'body': json.dumps('Error downloading file from S3')
            }
        
        # 读取图片
        image = read_image_from_temp(temp_path)
        if image is None:
            return {
                'statusCode': 500,
                'body': json.dumps('Error reading image')
            }
        
        # 进行检测
        detections = detect_birds(image)
        
        # 保存结果到数据库
        save_success = save_to_dynamodb(image_url, "", detections)
        
        # 清理临时文件
        try:
            os.remove(temp_path)
        except Exception as e:
            print(f"清理临时文件时出错: {str(e)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Processing completed successfully',
                'detections': detections
            })
        }
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        } 