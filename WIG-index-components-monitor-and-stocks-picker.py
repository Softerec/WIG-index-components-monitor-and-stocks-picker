# -*- coding: utf-8 -*-
"""
WIG monitor and picker - recommends best valuated components of index on Warsaw Stock Exchange (WSE).

WSE is a (emerging/maturing) stock exchange in Poland (developed market by World Bank).
WSE is the largest Stock Exchange in the Central-Eastern European zone (CEE).

Application scraps information about components of WIG index.
After that, analyse individual stock, present it and provide recommendation.

For gradual presentaiton: actual code, scraps only 1st page from stooq.pl.
(When needed increase page number -> see main function.)

When internet connection not available, reads locally stored json file from previous time.

"""

import requests
from bs4 import BeautifulSoup
import io
import jsonpickle
import copy

save_url_request_to_local_file = True
read_from_local_json_when_url_not_available = True
equities = dict()


class equity():
    data = {}
    def __init__(self, symbol = 'symbol_missing'):
        self.symbol = symbol


def url_content_to_json(content):
    # json-serialization of the numpy array
    content_to_json = jsonpickle.encode(content)

    # putting json-serialized numpy array into json file
    json_file_name = 'LastAvailableUrlSavedInLocal.json'
    opened_json = io.open(json_file_name, 'w')
    opened_json.write(content_to_json)
    opened_json.close()
    print('Json saved with webpage dump.')


def url_content_from_json(json_file_name):
    opened_json = io.open(json_file_name, 'r')
    content_from_opened_json = opened_json.read()
    content_from_json = jsonpickle.decode(content_from_opened_json)
    opened_json.close()
    print('Json file read.')
    return content_from_json


def remove_commas(text):
    if ',' in text:
        temp = text.split(',')
        commaless = ''.join(temp)
        return commaless
    else:
        return text


# 1st to execute
def get_page(max_pages):
    page_nr = 1

    page_type_unique_middle_chars = 'l='
    page_type_unique_end_chars = '&i=1'
    begining_part_of_url = 'https://stooq.pl/q/i/?s=wig&' + page_type_unique_middle_chars
    ending_part_of_url = page_type_unique_end_chars

    while page_nr <= max_pages:

        url = begining_part_of_url + str(page_nr) + ending_part_of_url
        print('Connecting to the url: ', url)

        try:
            page = requests.get(url, timeout = 3)
            if page.status_code >= 200 and page.status_code <= 399:
                # Actualize data in locally stored json for next time when url not available
                if save_url_request_to_local_file is True:
                    url_content_to_json(page)

                parse_the_page(page)

        except:
            print('Url not available (', url, ').')
            if True:
                if read_from_local_json_when_url_not_available is True:
                    page_from_json = url_content_from_json('LastAvailableUrlSavedInLocal.json')
                    parse_the_page(page_from_json)

        page_nr = page_nr + 1


# 2nd to execute
def parse_the_page(page):

    # beautifulsoup object needs to be created
    soup = BeautifulSoup(page.content, 'html.parser')

    soupchildren = list(soup.children)
    html = soupchildren[0]  # refers to this class 'bs4.element.Tag' as there is only one

    # Gets names and symbols of equitites. Names and symbols are taken from columns 'Nazwa','Symbol'.

    for td in html.find_all('td', id='l'):
        if 'a href' in str(td):
            equity_SYMBOL = td.find('a').contents[0]
            equity1 = equity(equity_SYMBOL)
            equity1.data['symbol'] = equity_SYMBOL
        else:
            equity_NAME = td.find('font').contents[0]
            equity1.data['name'] = equity_NAME
            equities[equity_SYMBOL] = copy.copy(equity1.data)

    # To extract parameters of specific equity based on symbol
    for symbol in equities.keys():

        # Extract of the equity parameters 
        equity_keyword_prefix = 'span id="aq_' + str(symbol.lower())
        price_keyword = equity_keyword_prefix + '_c'
        capitalization_keyword = equity_keyword_prefix + '_mv_c'
        pe_keyword = equity_keyword_prefix + '_pe_c'
        pb_keyword = equity_keyword_prefix + '_pb_c'

        for td in html.find_all('td', id='f13'):

            td_string = str(td)
            if price_keyword in td_string:
                # Get value from, an example: <span id="aq_11b_c1|2">396.0</span> 
                equity_price = float(td_string[39:].split('</span>')[0])
                equities[symbol]['price'] = equity_price
            elif capitalization_keyword in td_string:
                # Get value from, an example: <span id="aq_11b_mv_c2">905.73</span>
                # print(td_string[59:].split('</span>'))
                equity_capitalization = str(td_string[59:].split('</span>')[0])
                if ',' in equity_capitalization:
                    equity_capitalization = remove_commas(equity_capitalization)
                equities[symbol]['cap'] = equity_capitalization
            elif pe_keyword in td_string:
                # Get value from, an example: <span id="aq_11b_pe_c2">47.5</span>
                # print(td_string[59:].split('</span>'))
                equity_pe = str(td_string[59:].split('</span>')[0])
                if '<span>' in equity_pe:
                    equity_pe = equity_pe.split('<span>')[0]
                equities[symbol]['pe'] = equity_pe
            elif pb_keyword in td_string:
                # Get value from, an example: <span id="aq_11b_pb_c2">8.54</span>
                # print(td_string[59:].split('</span>'))
                equity_pb = str(td_string[59:].split('</span>')[0])
                equities[symbol]['pb'] = equity_pb

                # collect dividend data if available
                check_dividend = td.find_next('td', id='f13')
                dividend = -1.0
                if 'id="f13"></td' not in str(check_dividend) and symbol != 'WIG':
                    dividend = str(check_dividend).split('</td>')[0].split('"f13">')[1]
                elif symbol == 'WIG':
                    dividend = check_dividend.string
                if dividend != -1.0:
                    equities[symbol]['div'] = dividend
            else:
                pass

    # recommendation of buy opportunity and presentation of scrapped data
    for record in equities:
        separator_lenght = 35
        print('-'*separator_lenght)
        for key in equities[record]:

            # set proper unit for displayed later parameters
            if key == 'cap':
                unit = '(mln PLN)'
            elif key == 'price':
                unit = '(PLN)'
            elif key == 'div':
                unit = '(%/year)'
            else:
                unit = ''

            # adjustment for display of infromation and analysis results
            adjust_spaces = 12 - len(key) - len(unit)
            adjust_end_spaces = (15-len(str(equities[record][key]))) * ' '
            print('|', key.upper(), unit, ' '*adjust_spaces, equities[record][key], adjust_end_spaces, '|')
        print('| Buy opportunity for', equities[record]['symbol'], 'is {:01.1f}'.format(calculate_buy_opportunity(equities[record])[0]), ' |')

        any_zero = False
        for weight in calculate_buy_opportunity(equities[record])[1:]:
            if float(weight) == 0.0:
                any_zero = True

        if any_zero:
            if float(calculate_buy_opportunity(equities[record])[1]) == 0.0:
                print('| PB information missing.         |')
            if float(calculate_buy_opportunity(equities[record])[2]) == 0.0:
                print('| PE information missing.         |')
            if float(calculate_buy_opportunity(equities[record])[3]) == 0.0:
                print('| Dividend information missing.   |')

            print('| WARNING! : missing parameter    |')
            print('| information for better judgment.|')
        else:
            if calculate_buy_opportunity(equities[record])[0] >= 0.7:
                print('| Analyse', equities[record]['symbol'], 'to buy strong!      |')
            elif 0.5 <= calculate_buy_opportunity(equities[record])[0] < 0.7:
                print('| Analyse', equities[record]['symbol'], 'to buy some.        |')
            elif 0.3 <= calculate_buy_opportunity(equities[record])[0] < 0.5:
                print('| Analyse', equities[record]['symbol'], 'to buy one share :) |')

    print('-'*separator_lenght)
    print('\n\tPLEASE READ BELOW LEGEND CAREFULLY !')
    print('\tAnalyse company before making any decision\n\
    \teven when a good buy opportunity > 0.7, \n\
    \tanalyse in every detail when between 0.5 and 0.7, \n\
    \tgamble when between 0.3 and 0.5,\n\tjoke when below 0.3.')
    print('\tKeep in mind that stocks with lowest capitalization\n\
    \tare inliquid so can lead to price shifts.\n\
    \tRecommendation: especially avoid New Connect index.')


def calculate_buy_opportunity(equity_data):
    '''
    Assumptions about pe:
    +++ when: pe < 5
    ++ when: 5 < pe < 7
    + when: 7 < pe < 14
    # PEP8 comment: E501 line too long (87 > 79 characters)
    # PEP8 comment: E501 line too long (87 > 79 characters)
    pe disavdantages: oversensitive; cape much betten than pe (cape data not available)

    Assumptions about pb:
    +++ when: pb < 1
    ++ when: 1 < pb < 1.3
    + when: 1.3 < pb < 1.6
    # PEP8 comment: E501 line too long (95 > 79 characters)
    # PEP8 comment: E501 line too long (95 > 79 characters)
    general pb disadvantages: can be manipulated; shall be compared among one sector companies;

    Assumptions about dividend:
    +++ when: dividend > 5
    ++ when: 2.5 < dividend < 5
    + when: 0.5 < dividend < 2.5
    # PEP8 comment: E501 line too long (100 > 79 characters)
    # PEP8 comment: E501 line too long (100 > 79 characters)
    dividend disadvantages: need to be compared to historical payments; may depend on one time event

    '''
    weight_pe = 0.0
    weight_pb = 0.0
    weight_dividend = 0.0
    pe = 0.0
    pb = 0.0
    dividend = 0.0

    try:
        if equity_data['pb'] is not None:
            pb = equity_data['pb']
            pb_value = float(pb)
            if pb_value <= 1.00:
                weight_pb = 0.3
            elif 1.00 > pb_value <= 1.30:
                weight_pb = 0.2
            elif 1.30 > pb_value <= 1.60:
                weight_pb = 0.1
            else:
                weight_pb = 0.000001

    except:
        # PB data missing
        weight_pb = 0.0

    try:
        if equity_data['pe'] is not None:
            pe = equity_data['pe']
            pe_value = float(pe)
            if pe_value <= 5.0:
                weight_pe = 0.3
            elif 5 < pe_value <= 7:
                weight_pe = 0.2
            elif 7 < pe_value < 14:
                weight_pe = 0.1
            else:
                weight_pe = 0.000001
    except:
        # PE data missing.
        weight_pe = 0.0

    try:
        if equity_data['div'] is not None:
            dividend = equity_data['div']
            dividend_value = float(dividend)
            if dividend_value >= 5.0:
                weight_dividend = 0.3
            elif 2.5 <= dividend_value < 5:
                weight_dividend = 0.2
            elif 0.5 <= dividend_value < 2.5:
                weight_dividend = 0.1
            elif 0.2 < dividend_value < 0.5:
                weight_dividend = 0.01
            else:
                weight_dividend = 0.001
    except:
        # Dividend data missing.
        weight_dividend = 0.0

    total_score = weight_pe + weight_pb + weight_dividend

    return total_score, weight_pb, weight_pe, weight_dividend


def elevate_rights():
    print('Consider to elevate rights to admin to run this app:' 
          'if you like this app to save url page response to local file(.json)' 
          'or read data from locally stored (json stored previously).')


# THE MAIN
def main():
    elevate_rights()
    get_page(1) # for gradual analysis checks 1st page only (to check next pages increase the number)


if __name__ == "__main__":
    main()
