import requests
import lxml.html
import csv


STRINGS_TO_SEARCH = ["רקטות", "רקטה", "הרקטות", "הרקטה", "מטח", "מטחים", "טיל", "טילים", "המטח", "המטחים", 'הטילים',
                     "ירי מעזר", "ירי רקטי", "שיגור", "שיגורים", "הסלמה"]
YNET_PREFIX = "https://www.ynet.co.il"
N12_PREFIX = "https://www.mako.co.il"
RESHET13_PREFIX = "https://13tv.co.il"


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
    res = set()
    for article in articles:
        doc = lxml.html.fromstring(requests.get(article).content)
        title = doc.xpath("//h1/text()")[0]
        try:
            summary = doc.xpath("//h2[@class = 'art_header_sub_title']/text()")[0]
        except IndexError:
            summary = doc.xpath("//h2[@class = 'art_header_sub_title']/text()")
        for word in STRINGS_TO_SEARCH:
            if word in title or word in summary:
                res.add(article)
    return res


def get_articles_from_ynet():
    articles_clean = set()
    for i in range(2018, 2022):
        for j in range(1, 13):
            print("Getting Ynet articles for: ", j,  ", ",  i)
            articles_clean = articles_clean.union(screen_ynet_articles(get_ynet_by_month(j, i)))
    return articles_clean


def screen_n12_articles(articles):
    res = set()
    for article in articles:
        date = article.xpath(".//span[2]/text()")[0]
        year = int(date[-2:])
        if 18 < year < 22:
            url = N12_PREFIX + article.xpath("./figure/a/@href")[0]
            doc = lxml.html.fromstring(requests.get(url).content)
            try:
                title = doc.xpath("//h1/text()")[0]
            except:
                print("Breakpoint")
            summary = doc.xpath("//h2/text()")[0]
            for word in STRINGS_TO_SEARCH:
                if word in title + summary:
                    res.add(url)
    return res


def get_articles_from_n12():
    articles_clean = set()
    for i in range(50, 601):
        print("Page " + str(i) + " of 601 in N12")
        page = lxml.html.fromstring(
            requests.get("https://www.mako.co.il/news-military?page=" + str(i)).
            content)
        articles_clean = articles_clean.union(screen_n12_articles(page.xpath("//main/section[1]//section/ul//li")))
    return articles_clean


def screen_reshet13_articles(urls):
    res = set()
    for url in urls:
        doc = lxml.html.fromstring(requests.get(RESHET13_PREFIX + url).content)
        date = doc.xpath("//span[@class='ArticleCreditsstyles__DateContainer-sc-11mp18e-1 jkeEdw']/text()")[0]
        year = date.split(',')[0]
        year = year[-4:] if len(year) > 5 else None
        if year and 18 < year < 22:
            title = doc.xpath("//h1/text()")[0]
            summary = doc.xpath("//h2/text()")[0]
            for word in STRINGS_TO_SEARCH:
                if word in title + summary:
                    res.add(url)
    return res


def get_articles_from_reshet13():
    articles_clean = set()
    for i in range(25, 120):
        print("Page " + str(i) + " of 120 in Reshet13")
        page = lxml.html.fromstring(
            requests.get("https://13tv.co.il/news/politics/security/page/25/" + str(i)).
            content)
        articles_clean = articles_clean.union(screen_reshet13_articles(set(page.xpath("//*[@id='__next']/div/div[5]/div[3]//div/a/@href"))))
    return articles_clean


def get_articles():
    with open('articles.csv', 'w', newline='') as f:
        # create the csv writer
        writer = csv.writer(f)
        # write a row to the csv file
        for url in get_articles_from_reshet13().union(get_articles_from_n12()).union(get_articles_from_ynet()):
            writer.writerow([url])


get_articles_from_n12()
