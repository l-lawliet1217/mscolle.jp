# importの設定
import requests
import lxml.html
# import cssselect
import pymysql
import uuid

# Left,Right,middleを定義
def left(text, n):
    return text[:n]

def right(text, n):
    return text[-n:]

def mid(text, n, m):
    return text[n-1:n+m-1]

# TOPページのurlをrに格納
top_url = "https://missofmiss.jp"
top_url_response = requests.get(top_url)
top_html = top_url_response.text
top_root = lxml.html.fromstring(top_html)

# 保存するデータベースを獲得
profiles_url = []
profile_url = []
profile_images = []
title = []
detail = []

# SQLのログイン情報を記載
connector = pymysql.connect(
   host='127.0.0.1',
   db='mscolle',
   user='root',
   passwd='root',
   charset='utf8',
)

# cursorでSQLにログインが可能な状態にする。
cursor = connector.cursor()

# ****** TOPページから、URL一覧を取得する。 ******
for a in top_root.xpath("//*[@id='entries']/div/ul/li"):
    for aa in a.xpath(".//a"):
        profiles_url.append(top_url + aa.get("href"))
    # profile_urlの配列にURLを追加
        print('URL', top_url + aa.get("href"))

# contests_urlの配列にURLを追加
        for profile_url in profiles_url:
            profile_response = requests.get(profile_url)
            profile_html = profile_response.text
            profile_root = lxml.html.fromstring(profile_html)

# 出場者の名前を取得する
        for name in a.xpath(".//a/div[2]/p[1]"):
            print('出場者名', name.text)

# 出場者の大学を取得する
        for university in a.xpath(".//a/div[2]/p[2]"):
            print('大学名', university.text)

# Twitter_urlを取得
        for ul in profile_root.xpath("//*[@id='history']/div/div/div/div[1]/ul"):
            for twitter_url in ul.xpath(".//a[contains(@href, 'twitter')]"):
                print("Twitter", twitter_url.get("href"))

# instagram_urlを取得
            for instagram_url in ul.xpath(".//a[contains(@href, 'instagram')]"):
                print("Instagram", instagram_url.get("href"))

# 出場者の出身大学、学部を取得
        for faculty in profile_root.xpath("//*[@id='history']/div/div/div/div[2]/h3"):
            print("大学・学部・学年", faculty.text)

# 生年月日を取得
        for birthday in profile_root.xpath("//*[@id='history']/div/div/div/div[3]/h3"):
            print("生年月日", birthday.text)

# プロフィール情報を取得
        for items in profile_root.xpath("//*[@id='history']/div/div/div"):
            for item in items.xpath(".//div/*"):
                title = item.xpath(".//p[1]")[0].text
                detail = item.xpath(".//p[2]")[0].text
# 趣味を取得
                if title == '趣味':
                    print(title, detail)
# 特技を取得
                elif title == '特技':
                    print(title, detail)
# 将来の夢を取得
                elif title == '将来の夢':
                    print(title, detail)

# 投票URLを取得
        for vote_url in profile_root.xpath("//*[@id='history']/div/div/div/a"):
            print("投票URL", vote_url.get("href"))
