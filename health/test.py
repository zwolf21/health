from pprint import pprint
from listorm import read_excel, Listorm

try:
    from health import *
    from utils import get_edi_code_from_xl
except:
    from .health import *
    from .utils import get_edi_code_from_xl

test_file = '약품정보.xls'

edis = get_edi_code_from_xl(test_file)[:100]

# edis = ['647802630']

print('total edi count: ', len(edis))

records = []
for i, edi in enumerate(edis):
    print('\tgetting detail urls for {}({}/{})...'.format(edi, i+1, len(edis)))
    soup = get_search_list_soup(edi)
    detail_urls = get_detail_urls(soup)
    for url in detail_urls:
        print('\t\tparsing detail: {}...'.format(url))
        detail_soup = get_detail_soup(url)
        record = parse_detail_soup(detail_soup)
        pprint(record, indent=10)
        records.append(record)


# lst = Listorm(records)
# lst.to_excel('test_result.xlsx')

