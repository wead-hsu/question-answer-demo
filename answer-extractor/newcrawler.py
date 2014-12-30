from selenium import webdriver
import time
from bs4 import BeautifulSoup
import sys
from urllib import quote_plus
import json

reload(sys)
sys.setdefaultencoding('utf-8')
driver = webdriver.Chrome()
filenum = 0

queryf = open('test-query.json')
questionf = open('test-query.txt')

for line in queryf:
    question = ''

    for i in range(1):
        oneLine = questionf.readline().strip()
        words = oneLine.split(' ')[2:]

        for w in words:
            if '/' in w:
                wordAndPOS = w.split('/')
                POS = wordAndPOS[-1]
                word = ''.join(wordAndPOS[:-1])

                if word != '':
                    question += word

    for i in range(3):
        questionf.readline()

    url = 'https://www.baidu.com/s?wd=' + quote_plus(question) + '&rsv_spt=1&issp=1&f=8&rsv_bp=0&rsv_idx=2&ie=utf-8&tn=baiduhome_pg'

    of = open('openEvidence\\' + str(filenum) + '.txt', 'w')
    filenum += 1

    driver.get(url)

    data = driver.page_source
    soup = BeautifulSoup(data)
    descriptions = soup.find_all('div', class_='c-abstract')

    for d in descriptions:
        t = d.get_text().replace('\n', '')
        of.write(t + '\n')

    of.close()

queryf.close()




