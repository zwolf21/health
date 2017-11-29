# -*- coding: utf-8 -*-
from pprint import pprint
import json
import re, os, time, argparse, platform, getpass

try:
    from .views import *
    from .utils import isvalid_file, starts_file
except:
    from views import *
    from utils import isvalid_file, starts_file

def main():
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description="약학정보원 유틸")
    argparser.add_argument('keywords', help='검색할 키워드들 나열', nargs='*')
    argparser.add_argument('-O', '--output', help='검색 결과 엑셀파일로 저장 .html로 저장 시 약품 사진 추출',  nargs='?')
    argparser.add_argument('-J', '--json', help='검색 결과 제이슨으로 출력', action='store_true', default=False)
    argparser.add_argument('-CC', '--columns', type=int, help='html로 저장시 테이블 열수', default=5, nargs='?')
    args = argparser.parse_args()

    input_file = None
    output_file = args.output

    if len(args.keywords) == 0:
        print('검색어를 입력하거나 EDI코드가 포함된 엑셀파일을 지정하십시오 예)C:\>health 엑셀파일.xlsx')
        return

    elif len(args.keywords) == 1:
        if isvalid_file(args.keywords[0]):
            input_file = args.keywords[0]
            if not os.path.exists(input_file):
                print('존재하지 않는 경로입니다.\n\t->{}'.format(input_file))
                return

    elif len(args.keywords) == 2:
        if all(isvalid_file(f) for f in args.keywords):
            input_file, output_file = args.keywords
    

    lst = get_records(args.keywords, excel_file=input_file)

    if output_file:
        if output_file.endswith('.html'):
            get_picture_html(lst, output_html=output_file, columns=args.columns)
        else:
            lst.to_excel(output_file)
        starts_file(output_file)
    else:
        if args.json:
            print(json.dumps(lst, indent=4))
        else:
            pprint(lst, width=200)


if __name__ == '__main__':
    main()


