"""
This is a temporary workaround to get around the docker chromium limitation on lambda. If you're using this, clone
this repo, install the requirements, and start the python script. Remember to deactivate webhooks.
"""

import app.process_messages as pm
import telebot

tb: telebot.TeleBot = pm.tb
tb.infinity_polling()


