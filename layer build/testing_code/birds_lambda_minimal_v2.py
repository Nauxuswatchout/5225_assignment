import json
import boto3
import cv2
import numpy as np
import os
import tempfile
import time
import onnxruntime

# 初始化 AWS 服务客户端
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('bird_detections')

# 鸟类类别映射
CLASSES = {
    0: 'Crow',
    1: 'Kingfisher',
    2: 'Myna',
    3: 'Owl',
    4: 'Peacock',
    5: 'Pigeon',
    6: 'Sparrow'
}

def download_file_from_s3(bucket, key):
    """从S3下载文件到临时目录"""
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            s3_client.download_fileobj(bucket, key, tmp_file)
            return tmp_file.name
    except Exception as e:
        print(f"下载文件时出错: {str(e)}")
        return None

def preprocess_image(img, input_size=(640, 640)):
    """预处理图像"""
    # 调整图像大小，保持宽高比
    h, w = img.shape[:2]
    ratio = min(input_size[0] / w, input_size[1] / h)
    new_w, new_h = int(w * ratio), int(h * ratio)
    resized = cv2.resize(img, (new_w, new_h))
    
    # 创建填充图像
    padded = np.zeros((input_size[0], input_size[1], 3), dtype=np.uint8)
    dx = (input_size[1] - new_w) // 2
    dy = (input_size[0] - new_h) // 2
    padded[dy:dy+new_h, dx:dx+new_w] = resized
    
    # 转换为浮点数并归一化
    x = padded.astype(np.float32) / 255.0
    x = np.transpose(x, (2, 0, 1))  # HWC to CHW
    x = np.expand_dims(x, axis=0)  # 添加batch维度
    return x, (ratio, dx, dy)

def detect_birds(image_path, confidence_threshold=0.25):
    """使用YOLO模型检测鸟类"""
    try:
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            raise Exception("无法读取图片")

        # 预处理图像
        x, (ratio, dx, dy) = preprocess_image(img)
        
        # 读取ONNX模型
        session = onnxruntime.InferenceSession("model.onnx", providers=['CPUExecutionProvider'])
        
        # 获取输入名称
        input_name = session.get_inputs()[0].name
        
        # 运行推理
        outputs = session.run(None, {input_name: x})
        
        # 处理输出
        predictions = outputs[0][0]  # 形状为 [300, 6]
        
        # 获取有效的检测结果
        mask = predictions[:, 4] > confidence_threshold
        valid_preds = predictions[mask]
        
        # 构建检测结果列表
        detections = []
        for pred in valid_preds:
            x1, y1, x2, y2, conf, cls_id = pred
            cls_id = int(cls_id)
            
            # 转换坐标
            x1 = (x1 - dx) / ratio
            y1 = (y1 - dy) / ratio
            x2 = (x2 - dx) / ratio
            y2 = (y2 - dy) / ratio
            
            detections.append({
                'class': CLASSES[cls_id],
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

def process_s3_event(event):
    """处理S3触发事件"""
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
            'body': json.dumps(f'Error processing S3 event: {str(e)}')
        }

def process_test_event(event):
    """处理测试事件"""
    try:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Test event received successfully',
                'event': event,
                'info': '这是一个测试事件。要测试图像检测功能，请使用S3触发器或提供正确的S3事件格式。'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing test event: {str(e)}')
        }

def lambda_handler(event, context):
    """Lambda函数入口点"""
    try:
        # 检查是否是S3事件
        if 'Records' in event and len(event['Records']) > 0 and 'eventSource' in event['Records'][0] and event['Records'][0]['eventSource'] == 'aws:s3':
            return process_s3_event(event)
        else:
            return process_test_event(event)
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        } 