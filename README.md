# Flatfindr

Telegram bot that help you find your next apartment.

As this tool has been developed for flats in Montreal - Canada, it currently supports scrapping from :
- Facebook Marketplace
- Kijiji (coming soon)
- Craigslist (coming sooner or later)
<br/><br/>
# Setup

## Install the package

Create a python3 virtualenv and activate it:

```bash
sudo apt-get install virtualenv python-pip python-dev
deactivate; virtualenv -ppython3 ~/venv ; source ~/venv/bin/activate
```

Clone the project and install it:

```bash
git clone git@github.com:aduverger/flatfindr.git
cd flatfindr
pip install -r requirements.txt
make clean install
```
## Copy your Facebook login
This part is mandatory only if you want to be able to scrap the Facebook Marketplace:
```bash
mv ./flatfindr/logins-template.py ./flatfindr/logins.py # rename logins-template into logins
```
- Copy inside this file your id and password in place of `"<ID>"` and `"<PWD>"`.
<br/><br/>

## Download the appropriate chromedriver
- Go to `https://chromedriver.chromium.org/downloads`
- Download the driver that is compatible with you Chrome version and system.

- Save this file as `./driver/chromedriver`
<br/><br/>

## Create a Telegram bot
- To generate an Access Token, you have to talk to [BotFather](https://t.me/botfather) and follow a few simple steps (described [here](https://core.telegram.org/bots#6-botfather)).

- Once you have your token, paste it in `./flatfindr/logins.py` in place of `"<TOKEN>"`

- You can then run the bot instance locally (prefered) or in the cloud (in progress).
To run it locally (on your PC or for e.g. a Raspberry Pi):
```bash
flatfindr-bot
```

Just keep it mind that if you shut down your computer, the bot won't be accessible anymore.
<br/><br/>
# 🔥 Scrap it like it's hot
Once you're bot instance is running, you can access it directly from Telegram: