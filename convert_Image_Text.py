import os
import pytesseract
from PIL import Image

# Đường dẫn đến thư mục chứa ảnh
image_folder = 'saveimage'

# Đường dẫn đến thư mục chứa kết quả văn bản
text_folder = 'textimage'

# Tạo thư mục textimage nếu nó chưa tồn tại
if not os.path.exists(text_folder):
    os.makedirs(text_folder)

# Đường dẫn đến Tesseract OCR (dùng cho Windows)
pytesseract.pytesseract.tesseract_cmd = r'D:/Tesseract-OCR/tesseract.exe'

# Lặp qua tất cả các tệp ảnh trong thư mục
for filename in os.listdir(image_folder):
    if filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        # Đường dẫn đến ảnh
        image_path = os.path.join(image_folder, filename)
        
        # Đọc ảnh
        img = Image.open(image_path)
        
        # Sử dụng Tesseract OCR để chuyển đổi ảnh thành văn bản
        text = pytesseract.image_to_string(img)
        
        # Tạo tên file cho văn bản dựa trên tên file ảnh
        text_filename = os.path.splitext(filename)[0] + '.txt'
        
        # Đường dẫn đến tệp văn bản
        text_path = os.path.join(text_folder, text_filename)
        
        # Lưu văn bản vào tệp
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)

print("Chuyển đổi ảnh thành văn bản hoàn tất.")
