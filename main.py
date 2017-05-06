import os
import sys
import csv
import time
import shutil
import urllib.request
import zipfile
import cProfile
import datetime
import requests
import collections
import configparser
from selenium import webdriver
from yahoo_finance import Share
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

THIS_DIR = os.getcwd()


def get_symbol(company):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(company)
    result = requests.get(url).json()
    symbol = result['ResultSet']['Query']
    if ' ' in symbol:
        return '???'
    return symbol


def main():
    config = configparser.ConfigParser()
    try:
        config.read("config.txt")
        username = config.get("configuration", "username")
        password = config.get("configuration", "password")

    except:
        print("config.txt not found... Creating new in {}".format(THIS_DIR))
        print("PLEASE FILL THE CONFIG FILE")
        cfgfile = open(os.path.join(THIS_DIR, "config.txt"), 'w')
        config.add_section("configuration")
        config.set('configuration', 'username', 'degiro_username')
        config.set('configuration', 'password', 'degiro_password')
        config.write(cfgfile)
        cfgfile.close()
        input("Press [Enter] to end program...")
        sys.exit()

    if username == 'degiro_username' or password == 'degiro_username':
        print("WARNING: You haven't yet filled config.txt, aborting program...")
        input("Press [Enter] to end program...")
        sys.exit()

    # browser = webdriver.Chrome(executable_path="C:\\Users\\Son Goku ssj4\\Downloads\\chromedriver_win32\\chromedriver.exe")
    # browser = webdriver.PhantomJS(executable_path="C:/Users/Son Goku ssj4/Downloads/phantomjs-2.1.1-windows/bin/phantomjs.exe")

    if not os.path.isfile('phantomjs.exe'):
        print("phantomjs.exe is missing... Downloading version 2.1.1-windows now...")
        filename, _ = urllib.request.urlretrieve(
            'https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-windows.zip',
            'phantomjs-2.1.1-windows.zip'
        )
        print("Download complete...")
        print("Unzipping file and copying phantomjs.exe into root folder...")
        zp = zipfile.ZipFile(filename)
        phantomjs_file = [file for file in zp.namelist() if 'phantomjs.exe' in file][0]
        zp.extract(phantomjs_file, '.')
        zp.close()
        shutil.copy(phantomjs_file, '.')
        print("Copying is done... Removing temporary folders/files...")
        os.remove('phantomjs-2.1.1-windows.zip')
        shutil.rmtree(phantomjs_file.split('/')[0])
        print("Done... Program continues...\n")

    if os.name == 'nt':
        browser = webdriver.PhantomJS(executable_path="phantomjs.exe")
    elif os.name == 'posix':
        browser = webdriver.PhantomJS()


    # browser.set_page_load_timeout(30)
    browser.get("https://trader.degiro.nl/login/secure")
    browser.maximize_window()
    # LOGIN
    WebDriverWait(browser, 5).until(EC.presence_of_element_located(
        (By.XPATH, "//input[@name='username']"))
    )
    browser.find_element_by_xpath("//input[@name='username']").send_keys(username)
    browser.find_element_by_xpath("//input[@name='password']").send_keys(password)
    browser.find_element_by_xpath("//button[@type='submit']").click()

    # Wait for page to load
    try:
        WebDriverWait(browser, 20).until(EC.presence_of_element_located(
            (By.XPATH, "//span[@data-dg-watch-property='valueByCostsType']"))
        )
    except:
        print("Please check your config.txt for correct login informations...")
        print("Press [Enter] to end program...")
        input()
        sys.exit()

    time.sleep(3)  # wait 3 seconds to load data

    while True:

        # Save time stamp
        datestamp = datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S')

        browser.find_element_by_xpath("//*[@id='period-type']/a").click()
        browser.find_element_by_xpath("//*[@id='ui-select-choices-row-0-0']/div").click()  # sel DIFF_DAY
        diff_day = browser.find_element_by_xpath("//span[@data-dg-watch-property='valueByPeriod']").text

        # Save TotalDifference amount
        browser.find_element_by_xpath("""//*[@id="period-type"]/a/span[3]""").click()
        browser.find_element_by_xpath("""//*[@id="ui-select-choices-row-0-1"]/div""").click()  # sel DIFF_TOTAL
        diff_all = browser.find_element_by_xpath("//span[@data-dg-watch-property='valueByPeriod']").text

        # Save other informations
        portfolio = browser.find_element_by_xpath("//span[@data-dg-watch-property='portfolio']").text
        fonds = browser.find_element_by_xpath("//span[@data-dg-watch-property='cash']").text
        for_use = browser.find_element_by_xpath("//span[@data-dg-watch-property='valueByCostsType']").text
        total = browser.find_element_by_xpath("//span[@data-dg-watch-property='total']").text

        # Print results into terminal
        print("""Date: {}
        Diff all/today: ... {} / {}
        Fonds: ... {}
        For use: ... {}
        Portfolio: ... {}
        TOTAL: ... {}
        """.format(datestamp, diff_all, diff_day, fonds, for_use, portfolio, total))

        # Save results into file
        filename = os.path.join(THIS_DIR, "degiro_data.csv")
        file_exists = os.path.isfile(filename)

        with open(filename, 'a') as csvfile:
            headers = ['Date', 'DiffAll', 'DiffDay', 'Fonds', 'ForUse', 'Portfolio', 'Total']
            writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n', fieldnames=headers)

            if not file_exists:
                writer.writeheader()  # file doesn't exist yet, write a header

            writer.writerow({
                'Date': datestamp,
                'DiffAll': diff_all,
                'DiffDay': diff_day,
                'Fonds': fonds,
                'ForUse': for_use,
                'Portfolio': portfolio,
                'Total': total
            })

        browser.find_element_by_xpath("//a[@data-dg-href='home.portfolio']").click()  # click on first in list of three
        time.sleep(1)

        titles = browser.find_elements_by_xpath('//a[@class="portfolio__table-cell-product-link"]')
        sizes = browser.find_elements_by_xpath('//span[@data-dg-watch-property="size"]')
        prices = browser.find_elements_by_xpath('//span[@data-dg-watch-property="price"]')
        diff_days = browser.find_elements_by_xpath('//span[@data-dg-watch-property="todayPl"]')
        diffs_total = browser.find_elements_by_xpath('//span[@data-dg-watch-property="totalPl"]')
        changes = browser.find_elements_by_xpath('//span[@data-dg-watch-property="change"]')
        values = browser.find_elements_by_xpath('//span[@data-dg-watch-property="value"]')

        stocks = {}
        for title, size, price, diff_day, diff_total, change, value \
            in zip(titles, sizes, prices, diff_days, diffs_total, changes, values):
            values = {}
            stock_name = title.get_attribute('Title')
            values.update({'size': size.text})
            values.update({'price': price.text})
            values.update({'diff_day': diff_day.text})
            values.update({'diff_total': diff_total.text})
            values.update({'change': change.text})
            values.update({'value': value.text})

            stocks.update({stock_name: values})

        ordered_stocks = collections.OrderedDict(sorted(stocks.items()))

        max_stock_name_len = max([len(stock) for stock in stocks.keys()])
        print("{:<{_len}} {:>14} {:>12} {:>12} {:>12} {:>12} {:>12} {:>12}".format(
              'Stock Name', 'Symbol', 'Size', 'Price [$]', 'Value [Kč]', 'Change [%]', 'Diff Day', 'Diff Total',
              _len=max_stock_name_len))

        for stock_name, vals in ordered_stocks.items():
            size = vals['size']
            price = vals['price']
            value = vals['value']
            change = vals['change']
            diff_day = vals['diff_day']
            diff_total = vals['diff_total']

            symbol = get_symbol(stock_name)

            print("{:<{_len}} {:>14} {:>12} {:>12} {:>12} {:>12} {:>12} {:>12}".format(
                stock_name, symbol, size, price, value, change, diff_day, diff_total, _len=max_stock_name_len))

        print("Next auto refresh in: 10 minutes...")
        # time.sleep(600)
        sys.exit()

    input("Press [Enter] to end program...")


if __name__ == '__main__':
    cProfile.run('main()')
