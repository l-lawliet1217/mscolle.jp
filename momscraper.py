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

# entriesページのURLを格納
entries_url = "https://missofmiss.jp/entries"
entries_url_response = requests.get(entries_url)
entries_html = entries_url_response.text
entries_root = lxml.html.fromstring(entries_html)

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
for a in entries_root.xpath("//*[@id='entries']/div/ul/li"):
    mom_user_info = {}
    for aa in a.xpath(".//a"):
        profiles_url.append(top_url + aa.get("href"))
        mom_user_info['url'] = top_url + aa.get("href")

# contests_urlの配列にURLを追加
        for profile_url in profiles_url:
            profile_response = requests.get(profile_url)
            profile_html = profile_response.text
            profile_root = lxml.html.fromstring(profile_html)

# idを追加
            id = profile_url[profile_url.rfind("/") + 1:]
        print("id", id)
        mom_user_info['id'] = id

# idが重複するデータをスキップ
        skip_sql = """select id from mom_user_info where id = %s"""
        row = cursor.execute(skip_sql, id)
        if row > 0:
            continue
        else:
    # サムネイルを取得
            for image in entries_root.xpath("//*[@id='entries']/div/ul/li[1]/a/picture/img/@src"):
                print(image)
                mom_user_info['image'] = image

    # 出場者の名前を取得する
            for name in a.xpath(".//a/div[2]/p[1]"):
                print('出場者名', name.text)
                mom_user_info['name'] = name.text

    # 出場者の大学を取得する
            for university in a.xpath(".//a/div[2]/p[2]"):
                print('大学名', university.text)
                mom_user_info['university'] = university.text

    # Twitter_urlを取得
            for ul in profile_root.xpath("//*[@id='history']/div/div/div/div[1]/ul"):
                for twitter_url in ul.xpath(".//a[contains(@href, 'twitter')]"):
                    print("Twitter", twitter_url.get("href"))
                    mom_user_info['twitter_url'] = twitter_url.get("href")

    # instagram_urlを取得
                for instagram_url in ul.xpath(".//a[contains(@href, 'instagram')]"):
                    print("Instagram", instagram_url.get("href"))
                    mom_user_info['instagram_url'] = instagram_url.get("href")

    # 出場者の出身大学、学部を取得
            for faculty in profile_root.xpath("//*[@id='history']/div/div/div/div[2]/h3"):
                print("大学・学部・学年", faculty.text)
                mom_user_info['faculty'] = faculty.text

    # 生年月日を取得
            for birthday in profile_root.xpath("//*[@id='history']/div/div/div/div[3]/h3"):
                print("生年月日", birthday.text)
                mom_user_info['birthday'] = birthday.text

    # プロフィール情報を取得  //*[@id="history"]/div/div/div/div[5]/p[2] //*[@id="history"]/div/div/div/div[7]/p[2]
            for items in profile_root.xpath("//*[@id='history']/div/div/div"):
                for item in items.xpath(".//div"):
                    try:
                        title = item.xpath(".//p[1]")[0].text
                        detail = item.xpath(".//p[2]")[0].text
                    except:
                        continue
                    else:
    # 趣味を取得
                        if title == '趣味':
                            print(title, detail)
                            mom_user_info['hobby'] = detail
    # 特技を取得
                        elif title == '特技':
                            print(title, detail)
                            mom_user_info['skill'] = detail
    # 将来の夢を取得
                        elif title == '将来の夢':
                            print(title, detail)
                            mom_user_info['dream'] = detail
    # サークルを取得
                        if title == 'サークル':
                            print(title, detail)
                            mom_user_info['circle'] = detail

    # 画像を取得
            for images in profile_root.xpath("//*[@id='js-slick']/ul"):
                for image in images.xpath(".//li[1]"):
                    for img in image.xpath(".//img"):
                        print(img.get("src"))


    # 投票URLを取得
            for vote_url in profile_root.xpath("//*[@id='history']/div/div/div/a"):
                print("投票URL", vote_url.get("href"))
                mom_user_info['vote_url'] = vote_url.get("href")


        # データベースに保存
            mom_user_list = []
            mom_user_list.append(mom_user_info['id'])
            mom_user_list.append(mom_user_info['url'])
            mom_user_list.append(mom_user_info['name'])
            mom_user_list.append(mom_user_info['university'])
            mom_user_list.append(mom_user_info['image'])

            try:
                mom_user_list.append(mom_user_info['twitter_url'])
            except:
                mom_user_list.append('NULL')

            try:
                mom_user_list.append(mom_user_info['instagram_url'])
            except:
                mom_user_list.append('NULL')

            mom_user_list.append(mom_user_info['faculty'])
            mom_user_list.append(mom_user_info['birthday'])
            try:
                mom_user_list.append(mom_user_info['hobby'])
            except:
                mom_user_list.append('NULL')

            try:
                mom_user_list.append(mom_user_info['skill'])
            except:
                mom_user_list.append('NULL')

            try:
                mom_user_list.append(mom_user_info['dream'])
            except:
                mom_user_list.append('NULL')

            try:
                mom_user_list.append(mom_user_info['circle'])
            except:
                mom_user_list.append('NULL')
            mom_user_list.append(mom_user_info['vote_url'])
            print (mom_user_list)

        # SQLに保存
            sql = """
            insert into mscolle.mom_user_info(id, url, name, university, image,
            twitter_url, instagram_url, faculty, birthday, hobby, skill, dream, circle, vote_url)
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            cursor.execute(sql, mom_user_list)
            connector.commit()
