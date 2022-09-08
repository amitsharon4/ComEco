import time
import pandas as pd
import requests
import lxml.html
import csv


STRINGS_TO_SEARCH = ["רקטות", "רקטה", "הרקטות", "הרקטה", "מטח", "מטחים", "טיל", "טילים", "המטח", "המטחים", 'הטילים',
                     "ירי מעזר", "ירי רקטי", "שיגור", "שיגורים", "הסלמה"]
YNET_PREFIX = "https://www.ynet.co.il"
N12_PREFIX = "https://www.mako.co.il"
RESHET13_PREFIX = "https://13tv.co.il"
CENTRAL_ISRAEL = ["תל אביב", "בת ים", "חולון", "אור יהודה" , "רמת גן","קריית אונו" ,"גבעתיים","בני ברק","רמת השרון",
                  "הרצליה","כפר שמריהו","גליל ים","ראשון לציון","נס ציונה","רחובות","באר יעקב","רמלה","לוד","בית דגן",
                  "גני תקווה","שדות דן","דרום השרון","יהוד","מונוסון","גבעת שמואל","פתח תקווה","הוד השרון","כפר סבא",
                  "רעננה","קריית עקרון","נתניה","שוהם","קדימה","צורן","מודיעין","ראש העין","מזכרת בתיה","מקווה ישראל",
                  "כפר טרומן",'כפר חב״ד',"משמר השבעה","נצר סרני",'כפר ביל״ו',"כפר נוער בן שמן"]


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
    for article in articles1+articles2+articles3+articles4+articles5:
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
        n12_articles = get_articles_from_n12()
        for entry in n12_articles:
            writer.writerow([entry, n12_articles[entry]])
    with open('articles_N12.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        n12_articles = ynet_articles()
        for entry in n12_articles:
            writer.writerow([entry, ynet_articles[entry]])
    with open('articles_N12.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        n12_articles = reshet13_articles()
        for entry in n12_articles:
            writer.writerow([entry, reshet13_articles[entry]])


#get_articles()
alarms_by_date = {}
peripheral_cities = set()
central_cities = set()
alarms_central, alarms_peripheral, articles_central, articles_peripheral = 0,0,0,0
alarms2018_2020 = pd.read_csv("RocketLaunchData1 2018-2020.csv")[['data', 'date', 'time']]
alarms2021 = pd.read_csv("RocketLaunchData 2021.csv")[['data', 'date', 'time']]
all_alarms = pd.concat([alarms2018_2020, alarms2021], axis = 0)
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
for index, row in all_alarms.iterrows():
    alarms_by_date.setdefault(row['date'], []).append(row["data"])
n12 = pd.read_csv("articles_N12.csv", header=None)
ynet = pd.read_csv("articles_reshet13.csv", header=None)
reshet13 = pd.read_csv("articles_reshet13.csv", header=None)
all_articles = pd.concat([n12, ynet, reshet13], axis=0)
articles_by_date = {}
for row in all_articles.iterrows():
    articles_by_date[row[1][1]] = 1 if row[1][1] not in articles_by_date else articles_by_date[row[1][1]] + 1
for date in alarms_by_date:
    peripheral_alarm = False
    central_alarm = False
    for city in alarms_by_date[date]:
        if city in central_cities:
            central_alarm = True
        else:
            peripheral_alarm = True
    if peripheral_alarm:
        alarms_peripheral += 1
    if central_alarm:
        alarms_central += 1
    if date in articles_by_date:
        if peripheral_alarm:
            articles_peripheral += 1
        if central_alarm:
            articles_central += 1

print("Percentage of coverage in central Israel is: " + str((articles_central/alarms_central) * 100))
print("Percentage of coverage in peripheral Israel is: " + str((articles_peripheral/alarms_peripheral) * 100))
