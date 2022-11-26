# IPYNB Converter Bot

This repository contains the code for the IPYNB Converter Bot, a telegram bot that converts jupyter notebooks to PDF. 
The bot is currently available at this link: [https://t.me/ipynb_converter_bot](https://t.me/ipynb_converter_bot)

Compared to other methods of converting jupyter notebooks online, this bot can render latex formulas in markdown cells 
even when nbconvert's latex renderer fails.

## Usage

Just send the bot a Jupyter notebook file/zip and it will send you a rendered PDF back. For the full list of 
commands, see the `\help` command in the bot. 

## Installation

If you want to deploy your own instance of this bot, it is recommended to do so via Railway:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/niu6tS?referralCode=ifVnil)

Follow the instructions on the deployment page and input the required API tokens. You may also host the bot locally or 
on your own server by building the docker container and running it with the API tokens as arguments.

## Contributing
Contributions are welcome. For major changes, please open an issue first to discuss what you would like to change.
        
