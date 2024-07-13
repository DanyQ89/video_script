import numpy as np
from django.http import HttpResponse
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import datetime
import logging
import cv2
import os
from PIL import Image, ImageDraw, ImageFont
from string import ascii_letters
import sqlite3

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'videoapp/index.html')


def create_video(request):


    logger.info('Start of create_video function')

    text = request.GET.get('text')
    if not text:
        return HttpResponse("No text provided", status=400)
    timestamp = str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))


    connection = sqlite3.connect('E:/ProgramFilesX/Codes/video_site/db.sqlite')
    cursor = connection.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS Data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            datetime TEXT
        )
        """)
    a = cursor.execute(f"""INSERT INTO Data (text, datetime) VALUES (?, ?)""", (text, timestamp))
    # query = f"""INSERT INTO Data (text, datetime) VALUES {(str(text), str(timestamp))}"""
        # res = cursor.execute(query)

    connection.commit()
    cursor.close()
    connection.close()

    # except Exception as err:
    #     logger.error(f'Error connecting to database: {err}\n{text}')
    #     return HttpResponse(f"Error connecting to database\n{err}", status=500)

    width, height = 100, 100

    # Replace invalid characters in the timestamp
    name = f"video_{text}_{timestamp}.mp4"

    logger.info(f'Creating video file with name: {name}')

    out = cv2.VideoWriter(name, cv2.VideoWriter_fourcc(*'mp4v'), 24, (width, height))

    # Define font properties for PIL
    need = False
    for i in text:
        if i not in ascii_letters + ' .,/-+=_)(*&^%$#@!~':
            need = True

    font_path = "C:/Windows/Fonts/arial.ttf"  # Ensure you have a suitable font file
    if need and not os.path.exists(font_path):
        logger.error(f'Font file {font_path} not found')
        return HttpResponse("Font file not found", status=500)

    font_size = 24
    font = ImageFont.truetype(font_path, font_size)

    x, y = width, height // 2

    for t in range(72):
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Create a PIL image from the NumPy array
        pil_image = Image.fromarray(frame)
        draw = ImageDraw.Draw(pil_image)

        x -= 10

        # Draw the text on the PIL image
        draw.text((x, y - font_size // 2), text, font=font, fill=(255, 255, 255))

        # Convert the PIL image back to a NumPy array
        frame = np.array(pil_image)

        out.write(frame)

    out.release()  # Release the VideoWriter

    # Check if the file was created
    if not os.path.exists(name):
        logger.error(f'Video file {name} was not created')
        return HttpResponse("Error creating video", status=500)

    # Specify the custom folder
    custom_folder = 'C:/videos'
    if not os.path.exists(custom_folder):
        os.makedirs(custom_folder)

    # Save the video using FileSystemStorage in the custom folder
    fs = FileSystemStorage(location=custom_folder)
    video_file_path = os.path.join(custom_folder, name)

    try:
        with open(name, 'rb') as f:
            video_file = fs.save(name, f)
        logger.info(f'Video file saved as: {video_file}')
    except Exception as e:
        logger.error(f'Error saving video file: {e}')
        return HttpResponse("Error saving video", status=500)

    # Optionally delete the local video file after uploading
    try:
        os.remove(name)
        logger.info(f'Local video file {name} removed')
    except Exception as e:
        logger.error(f'Error removing local video file: {e}')

    return render(request, 'videoapp/index.html', {'video_url': fs.url(video_file)})

