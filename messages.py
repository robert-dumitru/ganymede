import json
import telebot
import boto3
import yaml
import boto3

with open('parameters.yml') as f:
    parameters = yaml.safe_load(f)

token = parameters.get('secrets').get('telegram-token')
bot = telebot.TeleBot(token)
http_200 = {'statusCode': 200}


def handler(event, context):
    update = telebot.types.Update.de_json(json.loads(event.get('body')))
    bot.process_new_messages([update.message])
    chat_id = update.message.chat.id
    try:
        @bot.message_handler(commands=['start'])
        def start_handler(message):
            bot.send_message(
                chat_id,
                'Welcome! Please upload your files to convert, or use the command /help for detailed instructions.'
            )
            return http_200

        @bot.message_handler(commands=['help'])
        def help_handler(message):
            bot.send_message(
                chat_id,
                'This bot takes the zip/ipnyb file that you submit for CS assignments and renders it into a nice pdf. Please include any images that are referenced in your ipnyb file in the zip file (as specified in assignment instructions). The bot should do the rest. There are 2 render modes - this bot uses chromium over latex by default. As a rule, chromium will convert everything that can be rendered in your browser, while latex is not as reliable but may get a nicer result. To switch between render modes, use the /switchmode command. Do check the pdf before you submit, and if there are any errors, feel free to forward the file and pdf to @robertdumitru. Happy coding!'
            )
            return http_200

        @bot.message_handler(commands=['switchmode'])
        def switchmode_handler(message):
            return http_200

        @bot.message_handler(content_types=['document'])
        def document_handler(message):
            bot.send_message(chat_id, 'Converting... (this may take a while)')
            # lambda invocation
            boto3.client('lambda').invoke(
                FunctionName='ipnyb-converter-dev-converter',
                InvocationType='Event',
                Payload=json.dumps(event)
            )
            return http_200

        @bot.message_handler(func=lambda message: True)
        def exception_handler(message):
            bot.send_message(
                chat_id,
                'This command or function does not exist. Please try again or check /help for valid commands.'
            )
            return http_200
    except:
        bot.send_message(chat_id, 'Something went wrong :( Please try again or message @robertdumitru with your issue.')
        return http_200
