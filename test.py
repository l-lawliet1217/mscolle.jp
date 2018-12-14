import requests
import lxml.html
import cssselect
from urllib.request import urlopen
from bs4 import BeautifulSoup

#Left,Right,middleを定義
def left(text, n):
  return text[:n]

def right(text, n):
  return text[-n:]

def mid(text, n, m):
  return text[n-1:n+m-1]

#TOPページのurlをrに格納
top_url = "https://misscolle.com"
top_url_response = requests.get(top_url)

#TOPページの中のHTMLをrootに格納。
top_html = top_url_response.text
top_root = lxml.html.fromstring(top_html)
contests_url = []

##****** TOPページのFooterから、URL一覧を取得する。 ******##
#フッター内のxpath内のデータを取得。
for a in top_root.xpath("body/footer/div/div/ul/li/a"):

#contests_urlの配列にURLを追加
  contests_url.append(top_url + a.get("href"))

##****** https://misscolle.com/versionsから過去のミスコン一覧ページを取得する。 ******##
#過去のミスコン一覧をroot2に格納
versions_url = "https://misscolle.com/versions"
versions_url_response = requests.get(versions_url)
versions_html = versions_url_response.text
versions_root = lxml.html.fromstring(versions_html)

#root2の中からurlを取得。
for item in versions_root.xpath(".//ul[@class='columns']"):
  for a in item.xpath(".//a"):
    aa = a.get("href")
    if aa.startswith("http://"):
      contests_url.append(aa)
    else:
      contests_url.append(top_url + aa)

#contests_urlの配列にURLを追加
for contest_url in contests_url:
    #contest URL *
    print(contest_url)

    #開催年度の取得 *
    print(right(contest_url,4))

#****** Contestのページのスクレピング******##
    contest_response = urlopen(contest_url)
    bs_obj = BeautifulSoup(contest_response, "html.parser")

    table = bs_obj.findAll("table")[0]
    rows = table.findAll("tr")

    for row in rows:
        print("========row========")
        print(row.th.getText())
        print(row.td.getText())
    #コンテスト名

    #大学名

    #主催団体名

    #実施学園祭

    #実施日

    #場所

    #団体Twitter

    #WEB投票開始日

    #WEB投票終了日
