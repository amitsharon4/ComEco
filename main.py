import math
import re
import time
import pandas as pd
import requests
import lxml.html
import csv
from urllib.request import urlopen
from bs4 import BeautifulSoup

STRINGS_TO_SEARCH = ["רקטות", "רקטה", "הרקטות", "הרקטה", "מטח", "מטחים", "טיל", "טילים", "המטח", "המטחים", 'הטילים',
                     "ירי מעזר", "ירי רקטי", "שיגור", "שיגורים", "הסלמה"]
YNET_PREFIX = "https://www.ynet.co.il"
N12_PREFIX = "https://www.mako.co.il"
RESHET13_PREFIX = "https://13tv.co.il"
CENTRAL_ISRAEL = ["תל אביב", "בת ים", "חולון", "אור יהודה", "רמת גן", "קריית אונו", "גבעתיים", "בני ברק", "רמת השרון",
                  "הרצליה", "כפר שמריהו", "גליל ים", "ראשון לציון", "נס ציונה", "רחובות", "באר יעקב", "רמלה", "לוד",
                  "בית דגן",
                  "גני תקווה", "שדות דן", "דרום השרון", "יהוד", "מונוסון", "גבעת שמואל", "פתח תקווה", "הוד השרון",
                  "כפר סבא",
                  "רעננה", "קריית עקרון", "נתניה", "שוהם", "קדימה", "צורן", "מודיעין", "ראש העין", "מזכרת בתיה",
                  "מקווה ישראל",
                  "כפר טרומן", 'כפר חב״ד', "משמר השבעה", "נצר סרני", 'כפר ביל״ו', "כפר נוער בן שמן"]


def get_ynet_by_month(month, year):
    res = []
    if month < 10:
        month = "0" + str(month)
    else:
        month = str(month)
    year = str(year)
    s = "" + year + month
    page1 = lxml.html.fromstring(requests.get("https://www.ynet.co.il/home/0,7340,L-4269-141-344-" + s + "-1,00.html").
                                 content)
    page2 = lxml.html.fromstring(requests.get("https://www.ynet.co.il/home/0,7340,L-4269-141-344-" + s + "-2,00.html").
                                 content)
    page3 = lxml.html.fromstring(requests.get("https://www.ynet.co.il/home/0,7340,L-4269-141-344-" + s + "-3,00.html").
                                 content)
    page4 = lxml.html.fromstring(requests.get("https://www.ynet.co.il/home/0,7340,L-4269-141-344-" + s + "-4,00.html").
                                 content)
    page5 = lxml.html.fromstring(requests.get("https://www.ynet.co.il/home/0,7340,L-4269-141-344-" + s + "-5,00.html").
                                 content)
    articles1 = page1.xpath("//*[@id='tbl_mt']//a[contains(@href, 'article')]/@href")
    articles2 = page2.xpath("//*[@id='tbl_mt']//a[contains(@href, 'article')]/@href")
    articles3 = page3.xpath("//*[@id='tbl_mt']//a[contains(@href, 'article')]/@href")
    articles4 = page4.xpath("//*[@id='tbl_mt']//a[contains(@href, 'article')]/@href")
    articles5 = page5.xpath("//*[@id='tbl_mt']//a[contains(@href, 'article')]/@href")
    for article in articles1 + articles2 + articles3 + articles4 + articles5:
        res.append(YNET_PREFIX + article)
    return res


def screen_ynet_articles(articles):
    res = {}
    exceptions = []
    for article in articles:
        try:
            doc = lxml.html.fromstring(requests.get(article).content)
            title = doc.xpath("//h1/text()")[0]
            date = doc.xpath("//span[text()[contains(.,'פורסם')]]/text()")[0].split(' ')[1]
            date = date[:6] + '20' + date[6:]
            try:
                summary = doc.xpath("//h2[@class = 'art_header_sub_title']/text()")[0]
            except IndexError:
                summary = doc.xpath("//h2[@class = 'art_header_sub_title']/text()")
            for word in STRINGS_TO_SEARCH:
                if word in title or word in summary:
                    res[article] = date
        except:
            exceptions.append(article)
    return res, exceptions


def get_articles_from_ynet():
    articles_clean = {}
    failed_urls = []
    for i in range(2018, 2022):
        for j in range(1, 13):
            print("Getting Ynet articles for: " + str(j) + ", " + str(i))
            screened_articles, exceptions = screen_ynet_articles(get_ynet_by_month(j, i))
            failed_urls += exceptions
            articles_clean = articles_clean | screened_articles
    with open('failures_Ynet.txt', 'w') as file:
        file.write('\n'.join(failed_urls))
    return articles_clean


def screen_n12_articles(articles):
    exceptions = []
    res = {}
    for article in articles:
        time.sleep(2)
        url = N12_PREFIX + article.xpath("./figure/a/@href")[0]
        try:
            date = article.xpath(".//span[2]/text()")[0]
            year = int(date[-2:])
            if 18 < year < 22:
                doc = lxml.html.fromstring(requests.get(url).content)
                title = doc.xpath("//h1/text()")[0]
                summary = doc.xpath("//h2/text()")[0]
                for word in STRINGS_TO_SEARCH:
                    if word in title + summary:
                        res[url] = date
        except:
            exceptions.append(url)
    return res, exceptions


def get_articles_from_n12():
    articles_clean = {}
    failed_urls = []
    for i in range(50, 601):
        print("Page " + str(i) + " of 601 in N12")
        page = lxml.html.fromstring(
            requests.get("https://www.mako.co.il/news-military?page=" + str(i)).
            content)
        screened_articles, exceptions = screen_n12_articles(page.xpath("//main/section[1]//section/ul//li"))
        articles_clean = articles_clean | screened_articles
        failed_urls += exceptions
    with open('failures_N12.txt', 'w', newline='\n') as file:
        file.writelines('\n'.join(failed_urls))
    return articles_clean


def screen_reshet13_articles(urls):
    res = {}
    exceptions = []
    for url in urls:
        try:
            doc = lxml.html.fromstring(requests.get(RESHET13_PREFIX + url).content)
            date = doc.xpath("//span[@class='ArticleCreditsstyles__DateContainer-sc-11mp18e-1 jkeEdw']/text()")[0]
            date = date.split(',')[0]
            year = int(date[-4:]) if len(date) > 5 else None
            if year and 2018 < year < 2022:
                title = doc.xpath("//h1/text()")[0]
                summary = doc.xpath("//h2/text()")[0]
                for word in STRINGS_TO_SEARCH:
                    if word in title + summary:
                        res[RESHET13_PREFIX + url] = date
        except:
            exceptions.append(RESHET13_PREFIX + url)
    return res, exceptions


def get_articles_from_reshet13():
    articles_clean = {}
    failed_urls = []
    for i in range(25, 120):
        print("Page " + str(i) + " of 120 in Reshet13")
        page = lxml.html.fromstring(
            requests.get("https://13tv.co.il/news/politics/security/page/" + str(i) + "/").
            content)
        screened_articles, exceptions = screen_reshet13_articles(set(page.xpath("//*[@id='__next']/div/div["
                                                                                "5]/div[3]//div/a/@href")))
        failed_urls += exceptions
        articles_clean = articles_clean | screened_articles
    with open('failures_reshet13.txt', 'w') as file:
        file.write('\n'.join(failed_urls))
    return articles_clean


def get_articles():
    n12_articles = get_articles_from_n12()
    ynet_articles = get_articles_from_ynet()
    reshet13_articles = get_articles_from_reshet13()
    with open('articles_N12.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        for entry in n12_articles:
            writer.writerow([entry, n12_articles[entry]])
    with open('articles_Ynet.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        for entry in ynet_articles:
            writer.writerow([entry, ynet_articles[entry]])
    with open('articles_reshet13.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        for entry in reshet13_articles:
            writer.writerow([entry, reshet13_articles[entry]])
    n12_articles.update(ynet_articles)
    n12_articles.update(reshet13_articles)
    return n12_articles


def get_all_alarms():
    alarms2018_2020 = pd.read_csv("RocketLaunchData1 2018-2020.csv")[['data', 'date', 'time']]
    alarms2021 = pd.read_csv("RocketLaunchData 2021.csv")[['data', 'date', 'time']]
    return pd.concat([alarms2018_2020, alarms2021], axis=0)


def get_peripheral_and_central_cities(all_alarms):
    peripheral_cities = set()
    central_cities = set()
    for alarm_city in all_alarms.data:
        is_peripheral = True
        for central_city in CENTRAL_ISRAEL:
            if alarm_city in central_city or central_city in alarm_city:
                is_peripheral = False
        if is_peripheral:
            peripheral_cities.add(alarm_city)
        else:
            central_cities.add(alarm_city)
    with open('peripheral_cities.txt', 'w') as f:
        f.write('\n'.join(peripheral_cities))
    with open('central_cities.txt', 'w') as f:
        f.write('\n'.join(central_cities))
    return peripheral_cities, central_cities


def get_text_from_url(url):
    html = urlopen(url).read()
    soup = BeautifulSoup(html, features="html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    # get text
    text = soup.get_text()
    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    return '\n'.join(chunk for chunk in chunks if chunk)


def get_articles_per_city(all_articles, alarms_by_date, articles_per_city):
    for row in all_articles.iterrows():
        if row[1][1] in alarms_by_date:
            text = get_text_from_url(row[1][0])
            for city in articles_per_city:
                if city in text or 'ל' + city in text:
                    articles_per_city[city].add(row[1][0])
    with open('articles_per_city.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for entry in articles_per_city:
            if articles_per_city[entry] == set():
                articles_per_city[entry] = ""
            writer.writerow([entry, articles_per_city[entry], len(articles_per_city[entry])])
    return articles_per_city


def get_alarms_per_city(alarms_by_date, all_alarms, articles_per_city):
    alarms_per_city = {re.sub(r'[0-9]', '', city).strip(): set() for city in all_alarms.data}
    for date in alarms_by_date:
        for city in alarms_by_date[date]:
            alarms_per_city[re.sub(r'[0-9]', '', city).strip()].add(date)
    with open('alarms_per_city.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for entry in alarms_per_city:
            if articles_per_city[entry] == set():
                articles_per_city[entry] = ""
            writer.writerow([entry, alarms_per_city[entry], len(alarms_per_city[entry])])
    return alarms_per_city


def get_cities_info(code_by_city, religion_by_city, population_by_city, city_names):
    general_data_2017 = pd.read_excel("נתונים כלליים 2017.xls")
    general_data_cities = general_data_2017[['שם יישוב']]
    city_failures = set()
    for city in alarms_per_city:
        index = -1
        for general_data_city in general_data_cities.values:
            if city in general_data_city[0] or general_data_city[0] in city:
                index = general_data_2017[general_data_2017['שם יישוב'] == general_data_city[0]].index[0]
        try:
            if index > -1:
                code_by_city[city] = general_data_2017.iloc[index][6]
                religion_by_city[city] = general_data_2017.iloc[index][9]
                population_by_city[city] = general_data_2017.iloc[index][10]
                city_names[city] = general_data_2017.iloc[index][22]
            else:
                raise KeyError
        except KeyError:
            city_failures.add(city)
    return code_by_city, religion_by_city, population_by_city, city_failures, city_names


def get_natural_area_by_code():
    index2017 = pd.read_excel("index2017.xlsx", sheet_name=3)
    natural_area_by_code = {}
    for row_num in range(2, len(index2017.iloc[:, 5])):
        natural_area_by_code[index2017.iloc[row_num][5]] = index2017.iloc[row_num][2] if not None else ""
    return natural_area_by_code


def get_eshkols_dict():
    eshkols1 = pd.read_excel("אשכולות רשויות מקומיות.xlsx").iloc[5:, [2, 6]]
    eshkols1.rename(columns={'Unnamed: 2': 'Name', 'Unnamed: 6': 'Eshkol'}, inplace=True)
    eshkols2 = pd.read_excel("אשכולות מועצות אזוריות.xlsx").iloc[10:, [6, 12]]
    eshkols2.rename(columns={'Unnamed: 6': 'Name', 'Unnamed: 12': 'Eshkol'}, inplace=True)
    all_eshkols = pd.concat([eshkols1, eshkols2], axis=0)
    return dict(zip(all_eshkols.Name, all_eshkols.Eshkol))


# all_articles = get_articles()

# remove these
n12 = pd.read_csv("articles_N12.csv", header=None)
ynet = pd.read_csv("articles_reshet13.csv", header=None)
reshet13 = pd.read_csv("articles_reshet13.csv", header=None)
all_articles = pd.concat([n12, ynet, reshet13], axis=0)
#####

all_alarms = get_all_alarms()
articles_per_city = {re.sub(r'[0-9]', '', city).strip(): set() for city in all_alarms.data}

alarms_by_date = {}
for index, row in all_alarms.iterrows():
    alarms_by_date.setdefault(row['date'], []).append(row["data"])

articles_per_city = get_articles_per_city(all_articles, alarms_by_date, articles_per_city)
alarms_per_city = get_alarms_per_city(alarms_by_date, all_alarms, articles_per_city)

natural_area_by_code = get_natural_area_by_code()
code_by_city = {city: "" for city in alarms_per_city}
code_by_city[''] = ""
religion_by_city = {city: "" for city in alarms_per_city}
population_by_city = {city: "" for city in alarms_per_city}
city_names = {city: "" for city in alarms_per_city}
code_by_city, religion_by_city, population_by_city, city_failures, city_names = get_cities_info(code_by_city,
                                                                                                religion_by_city,
                                                                                                population_by_city,
                                                                                                city_names)
eshkols_dict = get_eshkols_dict()
with open("results.csv", 'w', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["City", "Alarms", "Articles", "Natural Zone", "Population", "Religion", "Eshkol"])
    for city in alarms_per_city:
        name = city_names[city] if city in city_names else city
        alarms = len(alarms_per_city[city])
        articles = len(articles_per_city[city])
        code = int(code_by_city[city]) if code_by_city[city] != '' and not math.isnan(code_by_city[city]) else None
        area = natural_area_by_code[code] if code and not math.isnan(code) else -1
        population = population_by_city[city] if city in population_by_city else -1
        religion = religion_by_city[city] if city in religion_by_city else -1
        eshkol = eshkols_dict[city] if city in eshkols_dict else -1
        writer.writerow([name, alarms, articles, area, population, religion, eshkol])


with open('city_failures.txt', 'w') as f:
    f.write('\n'.join(city_failures))
