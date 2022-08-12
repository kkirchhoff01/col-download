import sys
import requests
from bs4 import BeautifulSoup
import os
import datetime
import calendar
import logging
import traceback
import shutil
from dateutil import parser
import argparse

# URL = "https://www.radio.com/alt965kc/podcasts/church-of-lazlo-podcasts-20110"
# URL = "https://www.audacy.com/alt965kc/podcasts/church-of-lazlo-podcasts-20110?page={page}"
URL = "https://www.audacy.com/alt965kc/podcasts/church-of-lazlo-podcasts-20110"
NAME = '{date}-{weeekday}-the-church-of-lazlo-podcast.mp3'
BASE_PATH = os.path.abspath('.')
LOG_PATH = os.path.join(BASE_PATH, 'log')
if not os.path.exists(LOG_PATH):
    LOG_PATH = BASE_PATH[:]
LOG_NAME = 'col-download.{}.log'.format(datetime.date.today())
USER = None

logname = os.path.join(LOG_PATH, LOG_NAME)
logging.basicConfig(filename=logname,
        filemode='a',
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG)

logger = logging.getLogger('downloader')

def log_message(message, error=False):
    print(message)
    if error:
        print(traceback.format_exc())
        logger.error(message)
    else:
        logger.info(message)

log_message("Running...")
        
def parse_date(name):
    # Date parsing can be somewhat
    # unpredictable when it comes to random
    # years/weekdays in titles, so we'll
    # validate that these values actually exist
    day_found, month_found, year_found = \
        False, False, False
    for n in name.split(' '):
        try:
            has_weekday = any(
                calendar.day_name[i].lower() in n.lower()
                for i in range(7))
            if has_weekday:
                continue
            new_date = parser.parse(n).date()
            if str(new_date.month) not in name and \
                    calendar.month_name[new_date.month].lower() \
                    not in name.lower():
                continue
            if str(new_date.day) not in name:
                continue
            return new_date
        except:
            pass
    return None

def save_podcast(date, url):
    log_message('Checking podcast')
    formatted_dt = str(date).replace('-', '')
    
    # Add weekday to title for readability
    weekday = calendar.day_name[date.weekday()].lower()
    name = NAME.format(date=formatted_dt, weeekday=weekday)
    path = os.path.join(BASE_PATH, name)
    if os.path.exists(path):
        log_message(f'File {path} already exists')
        return
    
    log_message(f'Downloading {name}')
    
    podcast = requests.get(url, verify=False)
    log_message('Saving file')
    
    with open(path, 'wb') as fh:
        fh.write(podcast.content)
    
    log_message('Podcast saved to destination')
    
    # I prefer this over running
    # w/ su -u in cron jobs
    if USER is not None:
        log_message(f'Changing user permissions')
        try:
            shutil.chown(path, USER, USER)
        except Exception as e:
            log_message(e, error=True)
    
    log_message('Done saving podcast')

def run():
    page = requests.get(URL)
    soup = BeautifulSoup(page.text, 'html.parser')
    
    # List item containing podcast info
    li_list = soup.findAll("li", {"class": "podcast-episode-list__item"})
    log_message(f'Found {len(li_list)} list entries')
    for li in li_list:
        try:
            log_message('Getting podcast info')
            # Podcast link in list item
            temp = li.find('a', attrs={'class':'podcast-episode-list__download-link'})
            url = temp.attrs['href']
            log_message(f'Found url: {url}')
            # Podcast title for determining if the
            # podcast is the full episode
            name = li.find('a', attrs={'class':'podcast-episode-list__title spa-link'})\
                .text.strip('\n')\
                .strip(' ')\
                .strip('\n')
            log_message(f'Found name: {name}')
            
            # Since the full-show podcasts have a 
            # consistent pattern, the date parsing
            # can also be used to determine
            # which podcast to download
            date = parse_date(name)
            if date is None:
                log_message(f'Could not find date in "{name}"')
                continue
            log_message(f'Found date: {date}')
            save_podcast(date, url)
        except Exception as e:
            log_message(e, error=True)
    
    log_message('Done...')
            
if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--path', '-p',
        default=os.path.abspath('.'),
        type=str,
    )
    argparser.add_argument(
        '--user', '-u',
        default=None,
        type=str,
    )
    args = argparser.parse_args()

    USER = args.user
    BASE_PATH = args.path

    log_message('Starting run')
    sys.exit(run())

