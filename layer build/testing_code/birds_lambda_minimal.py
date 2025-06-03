import os
# 在导入任何其他包之前设置环境变量
os.environ['MPLBACKEND'] = 'Agg'  # 使用非交互式后端
os.environ['MATPLOTLIB_USE'] = 'Agg'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import json
import boto3
import cv2
import numpy as np
from ultralytics import YOLO
import tempfile
import time

# 初始化 AWS 服务客户端
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('bird_detections')

def download_file_from_s3(bucket, key):
    """从S3下载文件到临时目录"""
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            s3_client.download_fileobj(bucket, key, tmp_file)
            return tmp_file.name
    except Exception as e:
        print(f"下载文件时出错: {str(e)}")
        return None

def detect_birds(image_path, confidence_threshold=0.6):
    """使用YOLO模型检测鸟类"""
    try:
        # 加载模型
        model = YOLO("model.pt")
        
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            raise Exception("无法读取图片")
        
        # 运行检测，禁用所有可视化相关的功能
        results = model(img, verbose=False, conf=confidence_threshold, show=False, save=False)[0]
        
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
        
        return detections
    except Exception as e:
        print(f"检测过程中出错: {str(e)}")
        return []

def save_to_dynamodb(image_url, thumbnail_url, detections):
    """保存检测结果到DynamoDB"""
    try:
        item = {
            'image_id': image_url.split('/')[-1],  # 使用文件名作为主键
            'image_url': image_url,
            'thumbnail_url': thumbnail_url,
            'detections': detections,
            'timestamp': int(time.time())
        }
        table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"保存到数据库时出错: {str(e)}")
        return False

def lambda_handler(event, context):
    """Lambda函数入口点"""
    try:
        # 从事件中获取S3信息
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # 构建S3 URL
        image_url = f"s3://{bucket}/{key}"
        
        # 下载图片
        temp_path = download_file_from_s3(bucket, key)
        if not temp_path:
            return {
                'statusCode': 500,
                'body': json.dumps('Error downloading file from S3')
            }
        
        # 进行检测
        detections = detect_birds(temp_path)
        
        # 清理临时文件
        os.remove(temp_path)
        
        # 保存结果到数据库
        save_success = save_to_dynamodb(image_url, "", detections)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Processing completed successfully',
                'detections': detections
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        } 