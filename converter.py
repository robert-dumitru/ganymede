import os
import subprocess
import telebot
import re
import requests

token = '2146290119:AAEnOmNToSbKolSrc_BapNT7Q5__t7FTyvI'
directory = 'tmp'
bot = telebot.TeleBot(token)


def handler(event, context):
    @bot.message_handler(commands=['start'])
    def start_message(message):
        bot.send_message(message.chat.id, 'Please send me your files')
        return

    @bot.message_handler(commands=['help'])
    def help_message(message):
        bot.send_message(message.chat.id, 'Welcome! This bot takes the zip/ipnyb file that you submit for CS '
                                          'assignments and renders it into a nice pdf that you can submit. Please '
                                          'include any images that are referenced in your ipnyb file in the zip '
                                          'folder that you submit (as specified in assignment instructions). The bot '
                                          'should do the rest - though please note that image references within code '
                                          'cells are not supported currently. Do check the pdf before you submit, '
                                          'and if there are any errors, feel free to forward the file and pdf to me ('
                                          '@robertdumitru). Happy coding!')
        return

    @bot.message_handler(content_types=['document'])
    def convert(message):
        # initialize directory variables
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
        if extension is ".ipnyb":
            # if there are no extra files, compile directly without modifications
            bot.send_message(message.chat.id, 'Converting...')
            subprocess.run(["jupyter", "nbconvert", "--to", "pdf", f"{directory}/{filename}"])
            bot.send_document(message.chat.id, open(f"{directory}/{filestring}.pdf", 'rb'))
            return
        elif extension is ".zip":
            # if folder is a zip file, unzip into directory and delete zip
            bot.send_message(message.chat.id, 'Converting...')
            subprocess.run(["unzip", filename])
            subprocess.run(["rm", filename])
            filenames = os.listdir(directory)
            # initialize path variables
            notebook_path = None
            pictures = []
            for filename in filenames:
                extension = os.path.splitext(filename)[1]
                if extension is ".ipnyb":
                    if notebook_path is not None:
                        notebook_path = filename
                    else:
                        bot.send_message(message.chat.id, 'More than one ipnyb provided, please try again!')
                        return
                elif extension is "png" or "jpg":
                    pictures.append(filename)
                else:
                    return "invalid file"
            file = open(f"{directory}/{notebook_path}", '+')
            file_string = file.read()
            for picture in pictures:
                re.sub(f"<img src=.*{picture}>", f"![{picture}]({directory}/{picture})", file_string)
            file.write(file_string)
            subprocess.run(["jupyter", "nbconvert", "--to", "pdf", f"{directory}/{notebook_path}"])
            bot.send_document(message.chat.id, open(f"{directory}/{os.path.splitext(notebook_path)[0]}.pdf", 'rb'))
            return
        else:
            # tell the user that their file is invalid
            bot.send_message(message.chat.id, 'Wrong file type, must be ipnyb or zip!')
            return

    bot.polling()
