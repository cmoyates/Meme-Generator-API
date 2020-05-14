from flask import Flask, send_file, request
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from tempfile import NamedTemporaryFile
from shutil import copyfileobj
from os import remove
from io import BytesIO
import requests




#############################################################################
white = (255,255,255)
black = (0,0,0)

imageString = None
contrastScale = 2.5
saturationScale = 2.5
sharpenScale = 5
brightnessScale = 0.65
font = None
tx = ty = bx = by = 0
width = None
height = None

def ImportImage(imgString):
    r = requests.get(imgString)
    img = Image.open(BytesIO(r.content))
    width, height = img.size
    fontSize = min(width, height)/9
    font = ImageFont.truetype("impact.ttf", round(fontSize))
    return img, width, height, font

def DeepFry(img):
    img = ImageEnhance.Contrast(img).enhance(contrastScale)
    img = ImageEnhance.Color(img).enhance(saturationScale)
    img = ImageEnhance.Sharpness(img).enhance(sharpenScale)
    img = ImageEnhance.Brightness(img).enhance(brightnessScale)
    return img

def AddText(img, topText, bottomText):
    draw = ImageDraw.Draw(img)
    tw, th = draw.textsize(topText,font)
    bw, bh = draw.textsize(bottomText,font)
    tx = ((width-tw)/2)
    bx = ((width-bw)/2)
    ty = (height/15)
    by = height - (height/15) - bh
    for i in range(4):
        xOffset = -1 if (i%2) else 1
        yOffset = -1 if (i < 3) else 1
        draw.text((tx+xOffset, ty+yOffset), topText, font=font, fill=black)
        draw.text((bx+xOffset, by+yOffset), bottomText, font=font, fill=black)
    draw.text((tx, ty), topText, white, font=font)
    draw.text((bx, by), bottomText, white, font=font)
    return img
#############################################################################



app = Flask(__name__)

@app.route("/api", methods=["GET"])
def hello_world():

    Query = str(request.args["query"])
    data = Query.split("|")
    print(data)
    global width, height, font
    img, width, height, font = ImportImage(data[0])
    c = "car.jpg"
    newImg = DeepFry(AddText(img, data[1], data[2])) if (data[3]=="1") else AddText(img, data[1], data[2])
    newImg = newImg.convert("RGB")
    newImg.save(c)
    tempFileObj = NamedTemporaryFile(mode='w+b',suffix='jpg')
    pilImage = open(c,'rb')
    copyfileobj(pilImage,tempFileObj)
    pilImage.close()
    remove(c)
    tempFileObj.seek(0,0)
    
    response = send_file(tempFileObj, as_attachment=True, attachment_filename=c)
    return response

if __name__ == "__main__":
    app.run()