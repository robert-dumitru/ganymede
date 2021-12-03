import os
import subprocess
import re
import requests
import json
import telebot

token = '2146290119:AAEnOmNToSbKolSrc_BapNT7Q5__t7FTyvI'
directory = 'tmp'
bot = telebot.TeleBot(token)

"""
def convert(message):
    # initialize directory variables
    bot.send_message(message.get('chat').get('id'), 'Converting...')
    content_type = message.content_type
    document = getattr(message, content_type)
    file_id = document.file_id
    file_info = bot.get_file(file_id)
    # print(file_info)
    filename = f"converter.{os.path.splitext(file_info.file_path)}"
    file_url = f"https://api.telegram.org/file/bot{token}/{file_info.file_path}"
    with open(f"{directory}/{filename}", "wb") as f:
        f.write(requests.get(file_url).content)
    filestring, extension = os.path.splitext(filename)
    if extension == ".ipnyb":
        # if there are no extra files, compile directly without modifications
        subprocess.run(["jupyter", "nbconvert", "--to", "pdf", f"{directory}/{filename}"])
        bot.send_document(message.get('chat').get('id'), open(f"{directory}/{filestring}.pdf", 'rb'))
        return
    elif extension == ".zip":
        # if folder is a zip file, unzip into directory and delete zip
        bot.send_message(message.get('chat').get('id'), 'Converting...')
        subprocess.run(["unzip", filename])
        subprocess.run(["rm", filename])
        filenames = os.listdir(directory)
        # initialize path variables
        notebook_path = None
        pictures = []
        for filename in filenames:
            extension = os.path.splitext(filename)[1]
            if extension == ".ipnyb":
                if notebook_path is not None:
                    notebook_path = filename
                else:
                    bot.send_message(message.get('chat').get('id'), 'More than one ipnyb provided, please try again!')
                    return
            elif extension in ["png", "jpg"]:
                pictures.append(filename)
        file = open(f"{directory}/{notebook_path}", '+')
        file_string = file.read()
        for picture in pictures:
            re.sub(f"<img src=.*{picture}>", f"![{picture}]({directory}/{picture})", file_string)
        file.write(file_string)
        subprocess.run(["jupyter", "nbconvert", "--to", "pdf", f"{directory}/{notebook_path}"])
        bot.send_document(message.get('chat').get('id'), open(f"{directory}/{os.path.splitext(notebook_path)[0]}.pdf", 'rb'))
        return
    else:
        # tell the user that their file is invalid
        bot.send_message(message.get('chat').get('id'), 'Wrong file type, must be ipnyb or zip!')
        return
"""


def handler(event, context):
    print(event)
    message = json.loads(event.get('body')).get('message')
    if not message:
        return "no message attached!"
    chat = message.get('chat')
    text = message.get('text')
    if text == "/start":
        bot.send_message(
            chat.get('id'),
            'Welcome! Please upload your files to convert.'
        )
        return
    elif text == "/help":
        bot.send_message(
            chat.get('id'),
            'Welcome! This bot takes the zip/ipnyb file that you submit for CS assignments and renders it into a nice '
            'pdf that you can submit. Please include any images that are referenced in your ipnyb file in the zip '
            'file that you submit (as specified in assignment instructions). The bot should do the rest - though '
            'please note that image references within code cells are not supported currently. Do check the pdf before '
            'you submit, and if there are any errors, feel free to forward the file and pdf to me (@robertdumitru). '
            'Happy coding!'
        )
        return
    else:
        print("somehow this triggered")
        return
