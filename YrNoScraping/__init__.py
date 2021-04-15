"""
Scraping yr.no's hourly forcast for the day and converting it into json

Created on Sun Apr 11 19:21:26 2021

@author: Wernich
"""


import azure.functions as func
import json
import logging
import re
import requests

from bs4 import BeautifulSoup
from os import path
from pathlib import Path


def get_web_page_soup(url):
    site = requests.get(url)    
    
    return BeautifulSoup(site.content, 'html.parser')

    
def get_forecast_table_rows(soup):
    return soup.select('.hourly-weather-dialog .hourly-weather-table .fluid-table__row')


def get_row_time(row):
    time_elem = row.select('.hourly-weather-table__time time')

    return time_elem[0].attrs['datetime']


def get_row_weather_img_path(row):
    img = row.select('.hourly-weather-table__weather img')[0]
    
    return Path(path.basename(img.attrs['src'])).stem


def get_row_temperature(row):
    temp_elem = row.select('.temperature')[0]
    
    return temp_elem.text.replace('Temperature', '')


def get_row_precipitation(row):
    rain_elem = row.select('.precipitation .precipitation__value')[0]
    
    return rain_elem.text


def get_row_wind_details(row):
    wind_value = row.select('.wind .wind__container .wind__value')[0].text

    try:
        wind_arrow = row.select('.wind .wind__container .wind__arrow .wind-arrow__arrow')[0]
        wind_direction = re.findall(r"rotate\((\d+)deg\)", wind_arrow.attrs['style'])[0]
    except Exception:
        wind_direction = None
    
    wind_description = row.select('.hourly-weather-table__wind-description .wind-description')[0].text
    
    wind = dict();
    wind['speed'] = '{}m/s'.format(wind_value)
    wind['desc'] = wind_description
    
    if wind_direction is not None:
        wind['dir'] = '{}°'.format(wind_direction)
    else:
        wind['dir'] = None
    
    return wind


def get_sunrise_sunset(soup):
    celestial_elems = soup.select('.celestial-events .celestial-events__item time.celestial-events__text')
    
    celestial_events = dict()
    celestial_events['sunrise'] = celestial_elems[0].attrs['datetime']
    celestial_events['sunset'] = celestial_elems[1].attrs['datetime']
    
    return celestial_events
    

def process_row(row):
    row_dict = dict()
    row_dict['time'] = get_row_time(row)
    row_dict['icon'] = get_row_weather_img_path(row)
    row_dict['temp'] = get_row_temperature(row)
    row_dict['rain'] = get_row_precipitation(row)
    row_dict['wind'] = get_row_wind_details(row)
    
    return row_dict
    

def get_location_name(soup):
    return soup.select('.page-header__location-name')[0].text.strip(' ')

    
def get_forecast_for_location(locationId):
    url = "https://www.yr.no/en/forecast/hourly-table/{}".format(locationId)
    soup = get_web_page_soup(url)
    
    rows = get_forecast_table_rows(soup)
    
    forecast_today = dict();
    
    forecast_today['location'] = get_location_name(soup)
    forecast_today['forecast'] = [process_row(row) for row in rows]
    forecast_today['celestial'] = get_sunrise_sunset(soup)
    
    return forecast_today


def json_encode(weather):
    return json.dumps(weather)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Incoming request')

    location_id = req.params.get('location')
    if not location_id:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            location_id = req_body.get('location')

    if not location_id:
        location_id = '2-1003820'    #fourways

    logging.info('Requesting info for location {}'.format(location_id))

    forecast = get_forecast_for_location(location_id)

    logging.info('Retrieved weather for location {} ({})'.format(forecast['location'], location_id))
    
    return func.HttpResponse(json_encode(forecast), mimetype='application/json')
