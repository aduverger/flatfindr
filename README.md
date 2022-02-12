# Flatfindr

A Telegram bot that help you find your next apartment.

As this tool has been developed for flats in Montreal - Canada, it currently supports scrapping from :
- Facebook Marketplace
- Kijiji (coming soon)
- Craigslist (coming sooner or later)
<br/><br/>

# 💻 Setup

## Install the package

Clone the project and install it:

```bash
git clone git@github.com:aduverger/flatfindr.git
cd flatfindr
make install clean
```

## Copy your Facebook login infos
<i>This part is mandatory only if you want to access the Facebook Marketplace.</i>

Copy inside `logins.py` your id and password in place of `"<ID>"` and `"<PWD>"`, or use this command instead:
```bash
make logins
```

## Create a Telegram bot
- To generate an Access Token, you have to talk to [BotFather](https://t.me/botfather) and follow a few simple steps (described [here](https://core.telegram.org/bots#6-botfather)).

- Once you have your token, paste it in `./flatfindr/logins.py` in place of `"<TOKEN>"`, or use this command instead:
```bash
make token
```

Just keep it mind that if you shut down your computer, the bot won't be accessible anymore. So you'll have to re-run the above `flatfindr-bot` command.

## Download the appropriate chromedriver
- Go to the [chromedriver website](https://chromedriver.chromium.org/downloads).
- Download the driver that is compatible with your Chrome version and system.

- Save this file as `./driver/chromedriver`
<br/><br/>

# 🔥 Scrap it like it's hot
- You can run the bot instance locally (prefered) or in the cloud (not currently supported). To run it locally:
```bash
flatfindr-bot
```
When your bot instance is running, you can access it directly from Telegram:
- First you need to answer a few questions to set your search criteria.
- Once these criteria are defined, your bot will get back to you every 30 minutes with new flats if he found some.
- You can cancel the search at any time by sending `/stop`.
- To run it again, just send `/run`. You previous search criteria will be used.
- To access you current criteria, send `/params`.
- If you want to modify some of these criteria, send `/start` again.
<br/><br/>

<img src="https://github.com/aduverger/flatfindr/blob/master/images/alfred2.png?raw=true" alt="drawing" width="200"/> &nbsp; &nbsp; &nbsp; <img src="https://github.com/aduverger/flatfindr/blob/master/images/alfred3.png?raw=true" alt="drawing" width="200"/> &nbsp; &nbsp; &nbsp; <img src="https://github.com/aduverger/flatfindr/blob/master/images/alfred4.png?raw=true" alt="drawing" width="200"/> 

<img src="https://github.com/aduverger/flatfindr/blob/master/images/alfred5.png?raw=true" alt="drawing" width="200"/> &nbsp; &nbsp; &nbsp; <img src="https://github.com/aduverger/flatfindr/blob/master/images/alfred6.png?raw=true" alt="drawing" width="200"/> &nbsp; &nbsp; &nbsp; <img
src="https://github.com/aduverger/flatfindr/blob/master/images/alfred7.png?raw=true" alt="drawing" width="200"/>

