from pprint import pprint
import re, os, sys
from unicodedata import normalize
from urllib.parse import quote, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed


import requests
from tqdm import tqdm
from listorm import Listorm
from bs4 import BeautifulSoup


try:
    from settings import *
    from utils import br_to_linebreak
except:
    from .settings import *
    from .utils import br_to_linebreak


def get_search_list_soup(keyword):
    url = 'http://www.health.kr/drug_info/basedrug/list.asp'
    if re.match('[A-Z\d]\d{8}', keyword):
        data = {
            'boh_code': keyword.encode('cp949')
        }
    else:
        data = {
            'drug_name': keyword.encode('cp949'),
        }
    r = requests.post(url, data=data, headers=HEADERS)
    soup = BeautifulSoup(r.content, 'html.parser')
    return soup


def get_detail_urls(list_soup):
    host = 'http://www.health.kr/drug_info/basedrug/'
    detail_url_regex = re.compile(r'show_detail.asp\?idx=(?P<id>\d+)')
    return [urljoin(host, a['href']) for a in list_soup('a', href=detail_url_regex)]

def get_detail_soup(detail_url):
    r = requests.get(detail_url, headers=HEADERS)
    return BeautifulSoup(r.content, 'html.parser')


def _parse_product_name(td):
    if td.b:
        prd_nm_kor = td.b.text
    else:
        prd_nm_kor = td.text

    if td.span:
        prd_nm_eng = td.span.text
    else:
        prd_nm_eng = ''
    return prd_nm_kor.strip(), prd_nm_eng.strip()

def _parse_component(td):
    if td.a:
        component_exps = td.a.text.split('   ')
        if len(component_exps) == 3:
            cmpnt_eng, cmpnt_kor, cmpnt_amt = component_exps
        else:
            cmpnt_eng = td.a.text.strip()
    
    components_kor = []
    components_eng = []
    for a in td('a', href=re.compile(r'^http://www.health.kr/ingd_info/ingd_group/list.asp')):
        cmpnt_eng, cmpnt_kor, cmpnt_amt = '', '', ''
        component_exps = a.text.split('   ')
        if len(component_exps) == 3:
            cmpnt_eng, cmpnt_kor, cmpnt_amt = component_exps
        else:
            cmpnt_eng = a.text.strip()
        components_kor.append(' '.join([cmpnt_kor, cmpnt_amt]))
        components_eng.append(' '.join([cmpnt_eng, cmpnt_amt]))

    return '\n'.join(components_kor), '\n'.join(components_eng)

def _parse_edi(td):
    ret = {}
    if td.span:
        edi = td.span.text
        ret['edi'] = edi.strip()
        info = td.span.nextSibling
        price_g = re.search(r'(?P<price>\d+)원', td.text)
        delete_g = re.search(r'삭제', info) or False
        date_g = re.search(r'(?P<date>\d{4}-\d{2}-\d{2})', info)
        if price_g:
            ret['price'] = price_g.group('price')

        if date_g:
            ret['apply_date'] = date_g.group(('date'))

        ret['deleted'] = bool(delete_g)
    return ret

def _parse_general_category(td):
    pclass = normalize('NFKC', td.text).strip()
    narcotic_class = '일반'
    pro_class  = '일반'

    for pro in ['전문', '일반', '희귀']:
        if pro in pclass:
            pro_class = pro
            break

    for nar in ['향정', '마약']:
        if nar in pclass:
            narcotic_class = nar
            pclass = pclass.replace(narcotic_class, '').strip()
            break

    return pro_class, narcotic_class

def get_image_src(detail_soup):
    small_regex = re.compile(r'http://www\.pharm\.or\.kr/images/sb_photo/small/(?P<img_id>.+)')
    pack_regex = re.compile(r'http://www.health.kr/images/ext_images/pack_img/(?P<img_id>.+)')
    for img in detail_soup('img', src=small_regex):
        src = img['src']
        g = small_regex.search(src)
        img_id = g.group('img_id').replace('_s', '')
        return urljoin('http://www.pharm.or.kr/images/sb_photo/big3/', img_id)
    else:
        for img in detail_soup('img', src=pack_regex):
            return img['src']
    return ''
    



def parse_detail_soup(detail_soup):
    td_list = [td for td in detail_soup('td')]

    record = {}
    record['img_src'] = get_image_src(detail_soup)
    for i, td in enumerate(td_list):
        if i == len(td_list)-1:
            break
        next_td = td_list[i+1]
        td_text = td.text.strip()

        if '제품명' == td_text:
            prd_nm_kor, prd_nm_eng = _parse_product_name(next_td)
            if prd_nm_kor or prd_nm_eng:
                record['prd_nm_kor'] = prd_nm_kor
                record['prd_nm_eng'] = prd_nm_eng
        elif '성분명' == td_text:
            component_kor, component_eng = _parse_component(next_td)
            if component_kor or component_eng:
                record['component_kor'] = component_kor
                record['component_eng'] = component_eng
        elif '전문 / 일반' == td_text:
            isprofession = next_td.text.strip()
            pclass, narclass = _parse_general_category(next_td)
            record['isprofession'] = pclass
            record['narcotic_class'] = narclass
        elif '단일 / 복합' == td_text:
            iscomplex = next_td.text.strip()
            record['iscomplex'] = iscomplex
        elif '제조 / 수입사' == td_text:
            manufactor = next_td.text.strip()
            record['manufactor'] = manufactor
        elif '판매사' == td_text:
            celler = next_td.text.strip()
            record['celler'] = celler
        elif '제형' == td_text:
            shape = next_td.text.strip()
            record['shape'] = shape
        elif '투여경로' == td_text:
            apply_root = next_td.text.strip()
            record['apply_root'] = apply_root
        elif '식약처 분류' == td_text:
            fda_category = next_td.text.strip()
            record['fda_category'] = normalize('NFKC', fda_category)
        elif '급여정보' == td_text:
            edisset = _parse_edi(next_td)
            record.update(edisset)
        elif 'ATC 코드' == td_text:
            atc_code = next_td.text.split(' : ')[0]
            record['atc_code'] = atc_code.strip()
        elif 'KPIC 약효분류' == td_text:
            kpic_category = next_td.text.strip()
            kpic_category = re.sub('\s+', ' ', kpic_category)
            record['kpic_category'] = kpic_category
        elif '포장단위' == td_text:
            pkg_unit = next_td.text.strip()
            record['pkg_unit'] = pkg_unit
        elif '저장방법' == td_text:
            store_method = next_td.text.strip()
            record['store_method'] = store_method
        elif '효능ㆍ효과' == td_text:
            efficacy = br_to_linebreak(next_td)
            record['efficacy'] = normalize('NFKC', efficacy)

    return record



def get_search_detail_url_thread(*keywords):
    keywords_count = len(keywords)
    wokers = min(MAX_WORKER, keywords_count)
    detail_urls = []
    with ThreadPoolExecutor(wokers) as executor:
        todo_list = []
        for keyword in keywords:
            future = executor.submit(get_search_list_soup, keyword)
            todo_list.append(future)

        done_iter = tqdm(as_completed(todo_list), total=keywords_count)
        for future in done_iter:
            list_soup = future.result()
            detail_url = get_detail_urls(list_soup)
            detail_urls+=detail_url
        return detail_urls


def parse_detail_thread(*detail_urls):
    records = []
    with ThreadPoolExecutor(min(MAX_WORKER, len(detail_urls))) as executor:
        todo_list = []
        for url in detail_urls:
            future = executor.submit(get_detail_soup, url)
            todo_list.append(future)
        for done in as_completed(todo_list):
            detail_soup = done.result()
            record = parse_detail_soup(detail_soup)
            records.append(record)
    lst = Listorm(records).filter(where=lambda row: row.isprofession)
    return lst.orderby('prd_nm_kor')



























