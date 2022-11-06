# IPYNB Converter Bot

This repository contains the code for the IPYNB Converter Bot, a telegram bot that converts jupyter notebooks to PDF. 
The bot is currently available at this link: [https://t.me/ipynb_converter_bot](https://t.me/ipynb_converter_bot)

Compared to other methods of converting jupyter notebooks online, this bot can render latex formulas in markdown cells 
even when nbconvert's latex renderer fails via pyppeteer.

## Usage

Just send the bot a Jupyter notebook file/zip and it will send you a rendered PDF back. For the full list of 
commands, see the `\help` command in the bot. 

## Installation

If you want to deploy your own instance of the bot, there are 2 choices of infrastructure you can use:

### Dedicated Server (Recommended):

This method was tested on a t2.micro instance on AWS with an Ubuntu AMI. The bot should work on any linux server with at
least 1GB of RAM and 1 CPU core. While all render modes work in this setup, it is possible to choke the server if enough
traffic is sent to it. This process assumes an SSH connection to your server.

1. Make sure that a python 3 executable is available (preferably 3.10) and 
   [poetry](https://python-poetry.org/docs/#installation) is installed.
2. clone the repository on your server and create required folders:

    ```bash
    git clone https://github.com/robert-dumitru/ipynbconverterbot
    cd ipynbconverterbot
   mkdir -p tmp

3. Install dependencies:

    ```bash
   apt-get update
   apt-get install pandoc texlive-xetex texlive-fonts-recommended texlive-plain-generic
   poetry install

4. Set the `TELEGRAM_TOKEN` environment variable to your telegram token, and the `ROOT_PATH` variable to the absolute 
   path of the `tmp` folder.
5. Run the bot:
    ```bash
    poetry run python3 app/bot.py > /dev/null 2>&1 &
    disown
6. Done! Your bot should now respond to messages. Feel free to close your ssh connection as the bot will keep running in
the background.

### AWS Lambda:

This method has been tested on an x86_64 machine running Ubuntu 22.04. Note that the fallback chromium render mode does 
**not** work on Lambda due to a [long-standing bug](https://github.com/pyppeteer/pyppeteer/issues/108) in pyppeteer. 
I've tried many workarounds, but there seems that there is no way as of now to run pyppeteer reliably within docker on 
AWS Lambda. The latex renderer works fine however, and this method carries the advantage of near-instantaneous scaling.


1. Install [Docker](https://www.docker.com/), [Serverless](https://www.serverless.com/framework/docs/getting-started), 
and the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) on your machine, and 
set up your AWS credentials if you haven't already.
2. Clone this repository on your local machine:

    ```bash
    git clone https://github.com/robert-dumitru/ipynbconverterbot
    cd ipynbconverterbot

3. Set the `TELEGRAM_TOKEN` environment variable to your telegram token.
4. Run the following command to build the docker image and deploy the Lambda function:

    ```bash
    serverless deploy
   
5. Find the URL of the Lambda function in the output of the previous command, and set it as the webhook for your bot 
with this command:
    
    ```bash
   curl https://api.telegram.org/bot"${TELEGRAM_TOKEN}"/setWebhook?url="<URL>"

6. Done! Your bot should now be up and running.

## Contributing
Contributions are welcome. For major changes, please open an issue first to discuss what you would like to change.
        
