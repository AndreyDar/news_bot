import os
from sqlalchemy import create_engine




# database
ENGINE = create_engine('postgresql://user:password@hostname/database_name')


# bot
BOT_TOKEN = 'token'

'''
if not BOT_TOKEN:
    print('You have forgot to set BOT_TOKEN')
    quit()


HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')


# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT'))
'''
