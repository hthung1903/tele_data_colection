import configparser
import json
import asyncio
import os
import pytesseract
from telethon.tl.types import MessageMediaPhoto
from telethon.tl.types import MessageMediaDocument
from datetime import date, datetime
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)
from telethon.tl.types import Channel
from telethon.tl.types import Chat
from telethon.tl.types import User
from PIL import Image
import re
# some functions to parse json date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)


# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

api_hash = str(api_hash)

phone = config['Telegram']['phone']
username = config['Telegram']['username']

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)

# Đường dẫn đến Tesseract OCR (dùng cho Windows)
pytesseract.pytesseract.tesseract_cmd = r'D:/Tesseract-OCR/tesseract.exe'

async def main(phone):
    await client.start()
    print("Client Created")
    # Ensure you're authorized
    if await client.is_user_authorized() == False:
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    me = await client.get_me()

    user_input_channel = input('enter entity(telegram URL ):')

    if user_input_channel.isdigit():
        entity = PeerChannel(int(user_input_channel))
    else:
        entity = user_input_channel

    my_channel = await client.get_entity(entity)
    # Lấy tên của group
    if isinstance(my_channel, Channel) or isinstance(my_channel, Chat):
        group_name = my_channel.title        
        print("Tên đối tượng  :", group_name)
    else:
        if hasattr(my_channel, 'username'):
            print("Tên đối tượng:", my_channel.username)
        elif hasattr(my_channel, 'first_name'):
            print("Tên đối tượng:", my_channel.first_name)
        else:
            print("Không thể xác định tên của đối tượng.")
    # ID của đối tượng       
    group_id_str = str(my_channel.id)
    print("ID đối tượng:" + group_id_str)

    offset_id = 0
    limit = 100
    all_messages = []
    total_messages = 0
    total_count_limit = 0
    
    while True:
        print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
        history = await client(GetHistoryRequest(
            peer=my_channel,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))
        if not history.messages:
            break
        messages = history.messages
        for message in messages:
            
            message_dict = message.to_dict()
            # Kiểm tra xem tin nhắn có chứa ảnh không
            if message.media and isinstance(message.media, MessageMediaPhoto):
              
                # Lấy đường dẫn tệp tin ảnh
                photo_path = await client.download_media(message.media.photo, file=os.path.join('save_image', group_id_str + '_' + str(message.id) + '.jpg'))
                print("Downloaded:", photo_path)
                # Sử dụng Tesseract OCR để chuyển đổi ảnh thành văn bản
                text = pytesseract.image_to_string(Image.open(photo_path), lang='vie')
                # Kiểm tra xem có văn bản từ OCR hay không trước khi thêm vào danh sách
                if text.strip():
                    # Cập nhật nội dung của tin nhắn với văn bản nhận được từ OCR
                    message_dict['message'] = text
                    # print("Text from OCR:", text)
                    all_messages.append(message_dict)
                else:
                    print("No text found in the image")
            elif message.media and isinstance(message.media, MessageMediaDocument):
                if message.media.document.mime_type.startswith("image/"):
                    filename = message.media.document.attributes[1].file_name
                    photo_path = await client.download_media(message.media.document, file=os.path.join('save_image', group_id_str + '_' + str(message.id) + '_'+ filename))
                    print("Downloaded:", photo_path)
                    # Sử dụng Tesseract OCR để chuyển đổi ảnh thành văn bản
                    text = pytesseract.image_to_string(Image.open(photo_path), lang='vie')
                    # Kiểm tra xem có văn bản từ OCR hay không trước khi thêm vào danh sách
                    if text.strip():
                        # Cập nhật nội dung của tin nhắn với văn bản nhận được từ OCR
                        message_dict['message'] = text
                        #print("Text from OCR:", text)
                        all_messages.append(message_dict)
                    else:
                        print("No text found in the image")
                elif message.media.document.mime_type.startswith("application/"):
                    document_type = message.media.document.mime_type.split("/")[-1]
                    if "." in document_type:
                        folder_type = document_type.split(".")[-1]
                    else:
                        folder_type = document_type
                    filename = message.media.document.attributes[0].file_name
                    file_path = await client.download_media(message.media.document, file=os.path.join('save_' + str(folder_type), group_id_str + '_' + str(message.id) + '_'+ filename))
                    print("Downloaded file: ",file_path)
                elif message.media.document.mime_type.startswith("text/"):
                    filename = message.media.document.attributes[0].file_name
                    file_path = await client.download_media(message.media.document, file=os.path.join('save_text', group_id_str + '_' + str(message.id) + '_'+ filename))
                    print("Downloaded file: ",file_path)
                else:
                    print("No file to download")
            else:
                # Nếu không phải là ảnh, thêm tin nhắn vào danh sách mà không thay đổi gì
                all_messages.append(message_dict)
            
            
        offset_id = messages[len(messages) - 1].id
        total_messages = len(all_messages)
        print(message.peer_id.user_id)
        if total_count_limit != 0 and total_messages >= total_count_limit:
            break
    
    filename = f'channel_messages_peerID_{group_id_str}.json'
    with open(filename, 'w') as outfile:
        json.dump(all_messages, outfile, cls=DateTimeEncoder)

with client:
    client.loop.run_until_complete(main(phone))
