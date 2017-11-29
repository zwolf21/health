# -*- coding: utf-8 -*-
import os

from jinja2 import Environment, PackageLoader, select_autoescape


MAX_WORKER = 100

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_DIR = os.path.dirname(BASE_DIR)


HEADERS = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
}


env = Environment(
    loader=PackageLoader('health', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)
