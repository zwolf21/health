# -*- coding: utf-8 -*-
from pprint import pprint
import os

from listorm import read_excel, Listorm

try:
    from health import *
    from utils import get_edi_code_from_xl
    from settings import env
except:
    from .health import *
    from .utils import get_edi_code_from_xl
    from .settings import env


def get_records(queries, excel_file=None):
    if excel_file:
        queries = get_edi_code_from_xl(excel_file)    
    detail_urls = get_search_detail_url_thread(*queries)
    return parse_detail_thread(*detail_urls)


def get_picture_html(records, columns=5, output_html=None):
    template = env.get_template('drug_picture.html')
    object_lists = []
    
    for i in range(0, len(records), columns):
        object_lists.append(records[i:i+columns])

    html = template.render(object_lists=object_lists)

    if output_html:
        with open(output_html, 'wt', encoding='utf-8') as fp:
            fp.write(html)
    else:
        return html