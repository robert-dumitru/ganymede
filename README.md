# IPYNB Converter Bot

This repository contains the code for the ipynb Converter Bot, a telegram bot that converts Jupyter Notebooks to PDF. 
The bot is currently available at this link: [https://t.me/ipynb_converter_bot](https://t.me/ipynb_converter_bot)

Compared to other methods of converting Jupyter notebooks online, this bot can render latex formulas in Markdown cells 
even when nbconvert's latex renderer fails via pyppeteer.

## Usage

Just send the bot a Jupyter notebook file and it will convert it to PDF and send it back to you. For the full list of 
commands, see the `\help` command in the bot. 

## Installation

If you want to deploy your own instance of the bot, there are 2 choices of infrastructure you can use:

### Dedicated Server (Recommended):

This method was tested on a t2.micro instance on AWS with an Ubuntu AMI. The bot should work on any linux server with at
least 1GB of RAM and 1 CPU core. While all render modes work in this setup, it is possible to choke the server if enough
traffic is sent to it.

1. ssh into your server and clone the repository:

    ```bash
    git clone https://github.com/robert-dumitru/ipynbconverterbot
    cd ipynbconverterbot

2. Install ubuntu dependencies:

    ```bash
   sudo apt-get update
   xargs sudo apt-get install -y < package.txt

3. Set the `TELEGRAM_TOKEN` environment variable to your telegram token.
4. Install python dependencies:

    ```bash
    pip install pipenv
    pipenv install

5.  Set the `ROOT_PATH` variable in `app/process_messages.py` to the absolute path of the repository.
6. Run the bot:

    ```bash
    pipenv run python app/process_messages.py
7. Done! Your bot should now respond to messages.

### AWS Lambda:

This method has been tested on an x86_64 machine running Ubuntu 22.04. Note that the fallback chromium render mode does 
**not** work on Lambda due to a [long-standing bug](https://github.com/pyppeteer/pyppeteer/issues/108) in pyppeteer. 
I've tried many workarounds, but there seems that there is no way as of now to run pyppeteer reliably within docker on 
AWS Lambda. The latex renderer works fine however, and this method carries the advantage of near-instantaneous scaling.


1. Install [Docker](https://www.docker.com/), [Serverless](https://www.serverless.com/framework/docs/getting-started), 
and the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) on your machine, and 
set up your AWS credentials if you haven't already.
2. Clone this repository and install dependencies:

    ```bash
    git clone https://github.com/robert-dumitru/ipynbconverterbot
    cd ipynbconverterbot
    pip install -r requirements.txt

3. Set the `ROOT_PATH` variable in `app/process_messages.py` to `\tmp\\` (as this is the only writable path in the 
Lambda environment).
4. Set the `TELEGRAM_TOKEN` environment variable to your telegram token.
5. Run the following command to build the docker image and deploy the Lambda function:

    ```bash
    serverless deploy
6. Find the URL of the Lambda function in the output of the previous command, and set it as the webhook for your bot 
with this command:
    
    ```bash
    chmod +x set_webhook.sh
   ./set_webhook.sh <URL>

7. Done! Your bot should now be up and running.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
        
