#!/bin/bash
curl --request POST --url https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook --header 'content-type: application/json' --data '{"url": "<INSERT API ENDPOINT HERE>"}'