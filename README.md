# Flatfindr

Telegram bot that help you find your next apartment.

As this tool has been developed for flats in Montreal - Canada, it currently supports scrapping from :
- Facebook Marketplace
- Kijiji (coming soon)
- Craigslist (coming sooner or later)

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

