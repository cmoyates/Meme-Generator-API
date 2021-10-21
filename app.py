import io
from fastapi import FastAPI, responses
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from tempfile import NamedTemporaryFile
from shutil import copyfileobj
from os import remove
from io import BytesIO
import requests


#############################################################################
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

CONTRAST_SCALE = 2.5
SATURATION_SCALE = 2.5
SHARPEN_SCALE = 5
BRIGHTNESS_SCALE = 0.65


def ImportImage(img_string: str):
    r = requests.get(img_string)
    img = Image.open(BytesIO(r.content))
    width, height = img.size
    max_dimension = max(width, height)
    if max_dimension > 1024:
        scale = max_dimension / 1024
        width = round(width / scale)
        height = round(height / scale)
        img = img.resize((width, height))
    font_size = min(width, height) / 9
    font = ImageFont.truetype("impact.ttf", round(font_size))
    return img, width, height, font


def DeepFry(img: Image):
    img = ImageEnhance.Contrast(img).enhance(CONTRAST_SCALE)
    img = ImageEnhance.Color(img).enhance(SATURATION_SCALE)
    img = ImageEnhance.Sharpness(img).enhance(SHARPEN_SCALE)
    img = ImageEnhance.Brightness(img).enhance(BRIGHTNESS_SCALE)
    return img


def AddText(img: Image, top_text: str, bottom_text: str, font: ImageFont, border_thickness: int, width: int, height: int):
    draw = ImageDraw.Draw(img)
    tw, _th = draw.textsize(top_text, font)
    bw, bh = draw.textsize(bottom_text, font)
    tx = (width - tw) / 2
    bx = (width - bw) / 2
    ty = height / 15
    by = height - (height / 15) - bh
    for i in range(4):
        x_offset = -border_thickness if (i % 2) else border_thickness
        y_offset = -border_thickness if (i < 3) else border_thickness
        draw.text((tx + x_offset, ty + y_offset), top_text, font=font, fill=BLACK)
        draw.text((bx + x_offset, by + y_offset), bottom_text, font=font, fill=BLACK)
    draw.text((tx, ty), top_text, WHITE, font=font)
    draw.text((bx, by), bottom_text, WHITE, font=font)
    return img


#############################################################################


app = FastAPI()

@app.get("/api")
def return_image(top: str, bottom: str, url: str, deep_fry: int):
    img, width, height, font = ImportImage(url)
    file_name = "car.jpg"

    new_img = AddText(
        img, top, bottom, font, 2, width, height
    )
    if deep_fry == 1:
        new_img = DeepFry(new_img)

    new_img = new_img.convert("RGB")
    new_img.save(file_name)
    temp_file_obj = NamedTemporaryFile(mode="w+b", suffix="jpg")
    pil_image = open(file_name, "rb")
    copyfileobj(pil_image, temp_file_obj)
    pil_image.close()
    remove(file_name)
    temp_file_obj.seek(0, 0)

    return responses.StreamingResponse(io.BytesIO(temp_file_obj.read()), media_type="image/jpg")


if __name__ == "__main__":
    app.run()