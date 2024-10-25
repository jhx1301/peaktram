import cv2
import time
import os

# 定义图片处理函数
def process_image(image_path, model, device):
    try:


        # 定义保存路径为 temp/
        folder_save_path = "temp"
        # 确保目录存在，如果不存在则创建
        if not os.path.exists(folder_save_path):
            os.makedirs(folder_save_path)

        # 使用模型处理图像
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Image at {image_path} could not be loaded.")
        print("Image successfully loaded.")
        print("done")
        # 确保图像在指定设备上处理
        print(f"[*] Running inference on device: {device}")
        try:


            results = model.predict(img, imgsz=320, conf=0.2, stream=False, device=device)
            print("Inference done")
        except Exception as e:
            raise RuntimeError(f"Error during model inference: {e}")
        annotated_frame = results[0].plot()

        # 保存处理后的图像
        processed_image_path = f'{folder_save_path}/processed_{time.time()}.jpg'
        cv2.imwrite(processed_image_path, annotated_frame)
        print("done")
        # 处理后的结果保存到文件
        cls_result = None
        if results[0].boxes.cls.nelement() > 0:
            cls_result = int(results[0].boxes.cls.item())

        # 保存检测结果
        result_file_path = f'{folder_save_path}/result_{time.time()}.txt'
        with open(result_file_path, 'w') as f:
            if cls_result is None:
                f.write("No detections found.")
            else:
                f.write(f"Detection class: {cls_result}")

        print(f"[*] Image processed and result saved: {processed_image_path}, {result_file_path}")

    except Exception as e:
        print(f"Error during processing: {e}")
