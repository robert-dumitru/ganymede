import os
import subprocess
import requests
import json
import telebot
import yaml

with open('parameters.yml') as f:
    parameters = yaml.safe_load(f)

token = parameters.get('secrets').get('telegram-token')
directory = '/tmp'
bot = telebot.TeleBot(token)


def handler(event, context):
    message = json.loads(event.get('body')).get('message')
    if not message:
        print("No message given!")
        return
    chat = message.get('chat')
    document = message.get('document')
    try:
        # erase cache
        subprocess.call(f"rm -rf {directory}/*", shell=True)
        file_id = document.get('file_id')
        file_info = bot.get_file(file_id)
        filename = document.get('file_name')
        file_url = f"https://api.telegram.org/file/bot{token}/{file_info.file_path}"
        f = open(f"{directory}/{filename}", "wb")
        f.write(requests.get(file_url).content)
        f.close()
        print("downloaded file")
        filestring, extension = os.path.splitext(f"{directory}/{filename}")
        if extension == ".ipynb":
            # if there are no extra files, compile directly without modifications
            subprocess.run(["jupyter", "nbconvert", "--to", "pdf", f"{filename}"], cwd=f"{directory}/")
            bot.send_document(message.get('chat').get('id'), open(f"{filestring}.pdf", 'rb'))
            return
        elif extension == ".zip":
            # if folder is a zip file, unzip into directory and delete zip
            subprocess.run(["unzip", f"{directory}/{filename}", "-d", f"{directory}"])
            filenames = os.listdir(directory)
            # initialize path variables
            print("Unzipping completed")
            notebook_path = None
            pictures = []
            for filename in filenames:
                extension = os.path.splitext(filename)[1]
                if extension == ".ipynb":
                    if notebook_path is None:
                        notebook_path = filename
                    else:
                        bot.send_message(chat.get('id'), 'More than one ipynb provided, please check your zip file!')
                        return
                elif extension in [".png", ".jpg"]:
                    pictures.append(filename)
            if notebook_path is None:
                bot.send_message(chat.get('id'), 'No ipynb provided, please check your zip file!')
                return
            print("extracted notebook path")
            subprocess.run(["jupyter", "nbconvert", "--to", "pdf", f"{notebook_path}"], cwd=f"{directory}/")
            bot.send_document(chat.get('id'), open(f"{directory}/{os.path.splitext(notebook_path)[0]}.pdf", 'rb'))
            return
        else:
            # tell the user that their file is invalid
            bot.send_message(chat.get('id'), 'Wrong file type, must be ipynb or zip!')
            return
    except:
        bot.send_message(chat.get('id'), 'Something went wrong :( Please try again or message @robertdumitru with your issue.')
        return
