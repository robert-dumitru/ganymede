import os
import subprocess
import telebot

directory = "tmp"
bot = telebot.TeleBot("2146290119:AAEnOmNToSbKolSrc_BapNT7Q5__t7FTyvI", )

def handler(event, context):
    # TODO: load file into tmp directory
    # initialize directory variables
    filename = os.listdir(directory)[0]
    extension = os.path.splitext(filename)[1]
    if extension is ".ipnyb":
        # if there are no extra files, compile directly without modifications
        subprocess.run(["jupyter", "nbconvert", "--to", "pdf", filename])
        # TODO: return pdf
    elif extension is ".zip":
        # if folder is a zip file, unzip into directory and delete zip
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
                    return "more than one jupyter notebook provided"
            elif extension is "png" or "jpg":
                pictures.append(filename)
            else:
                return "invalid file"
        file = open(notebook_path, '+')
        file_string = file.read()
        # TODO: add image code in
        file.write(file_string)
        subprocess.run(["jupyter", "nbconvert", "--to", "pdf", notebook_path])
        # TODO: return pdf
    else:
        # tell the user that their file is invalid
        return "invalid file"
