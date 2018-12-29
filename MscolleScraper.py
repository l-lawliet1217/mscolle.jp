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
top_url = "https://misscolle.com"
top_url_response = requests.get(top_url)

# TOPページの中のHTMLをrootに格納。
top_html = top_url_response.text
top_root = lxml.html.fromstring(top_html)
contests_url = []
profiles_url = []
contest_images = []
profile_images = []

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

# ****** TOPページのFooterから、URL一覧を取得する。 ******
# フッター内のxpath内のデータを取得。
for a in top_root.xpath("body/footer/div/div/ul/li/a"):
    # contests_urlの配列にURLを追加
    contests_url.append(top_url + a.get("href"))

# ****** https://misscolle.com/versionsから過去のミスコン一覧ページを取得する。 ******
# 過去のミスコン一覧をroot2に格納
versions_url = "https://misscolle.com/versions"
versions_url_response = requests.get(versions_url)
versions_html = versions_url_response.text
versions_root = lxml.html.fromstring(versions_html)

# root2の中からurlを取得。
for item in versions_root.xpath(".//ul[@class='columns']"):
    for a in item.xpath(".//a"):
        aa = a.get("href")
        if aa.startswith("http://"):
            contests_url.append(aa)
        else:
            contests_url.append(top_url + aa)

# contests_urlの配列にURLを追加
for contest_url in contests_url:
    contest_info = {}

    # contest URL *
    print(contest_url)
    contest_info['contest_url'] = contest_url

    # 開催年度の取得 *
    print("開催年度", right(contest_url, 4))
    contest_info['contest_year'] = right(contest_url, 4)

    # ****** Contestのページのスクレピング******
    # TOPページの中のHTMLをrootに格納。
    contest_response = requests.get(contest_url)
    contest_html = contest_response.text
    contest_root = lxml.html.fromstring(contest_html)

    # contest_idの取得
    contest_id = contest_url[contest_url.rfind("/") + 1:]
    print("contest_id", contest_id)
    contest_info['contest_id'] = contest_id

    # contest_imageの取得 *
    for contest_img in contest_root.xpath("//*[@id='contest-header-image']/img"):
        print(top_url + contest_img.get("src"))
        contest_images.append(top_url + contest_img.get("src"))
        contest_info['contest_img'] = top_url + contest_img.get("src")
    for target in contest_images:
        re = requests.get(target)
        with open('/Users/YUSUKE/Desktop/Mscolle.com/contest_imgs/'
                  + str(uuid.uuid1()) + target.replace("?v=121001", "").split("/")[-1], 'wb') as f: # imgフォルダに格納
            # .contentで画像データとして書き込む
            f.write(re.content)

    # Contestの中身を取得
    for item in contest_root.xpath("//*[@id='summary']"):
        for entry in item.xpath(".//table/*"):
            th = entry.xpath(".//th")[0].text
            td = entry.xpath(".//td")[0].text
            if th == 'コンテスト名':
                print(th, td.replace(" ", "").replace("\n", ""))
                contest_info['contest_name'] = td.replace(" ", "").replace("\n", "")
            elif th == '大学名':
                print(th, td)
                contest_info['universe_name'] = td
            elif th == '主催団体名':
                print(th, td)
                contest_info['host_name'] = td
            elif th == '実施日':
                print(th, td)
                contest_info['contest_date'] = td
            elif th == '場所':
                print(th, td)
                contest_info['contest_place'] = td
            elif th == '団体Twitter':
                print(th, td)
                contest_info['host_twitter'] = td
            elif th == 'WEB投票開始日':
                print(th, td)
                contest_info['vote_start_date'] = td
            elif th == 'WEB投票終了日':
                print(th, td)
                contest_info['vote_end_date'] = td

    contest_list = []
    contest_list.append(contest_info['id'])
    contest_list.append(contest_info['contest_url'])
    contest_list.append(contest_info['contest_year'])
    contest_list.append(contest_info['contest_img'])
    contest_list.append(contest_info['contest_name'])
    contest_list.append(contest_info['universe_name'])
    contest_list.append(contest_info['host_name'])
    contest_list.append(contest_info['contest_date'])
    contest_list.append(contest_info['contest_place'])
    contest_list.append(contest_info['host_twitter'])
    contest_list.append(contest_info['vote_start_date'])
    contest_list.append(contest_info['vote_end_date'])
    print(contest_list)
    sql = """
    insert into mscolle.contest_info (id, contest_url, contest_year, contest_img,
    contest_name, universe_name, host_name, contest_date, contest_place, host_twitter, vote_start_date, vote_end_date)
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    cursor.execute(sql, contest_list)
    connector.commit()
    # ****** プロフィールのスクレピング******
    # プロフィールの部分を取得
    for profile in contest_root.xpath("//div[@class='entry']"):
        profile_href = profile.xpath(".//li[@class='profile']//a")[0].get("href")
        user_info = {}

        # profile_idの取得
        profile_id = profile_href[profile_href.rfind("/") + 1:]
        print("profile_id", profile_id)
        user_info['id'] = profile_id

        # contest_idの取得
        contest_id = profile_href[1:profile_href.find("/", 1)]
        print("contest_id", contest_id)
        user_info['contest_id'] = contest_id

        # エントリーNoの取得
        for entry_no in profile.xpath(".//span[1]"):
            print("エントリーNo", entry_no.text.replace("ENTRY 0", ""))
            user_info['entry_no'] = entry_no.text.replace("ENTRY 0", "")

        # 名前の取得
        for name in profile.xpath(".//h3"):
            print("名前", name.text)
            user_info['name'] = name.text

        # TwitterのURLを取得
        for icon_box in profile.xpath(".//div[@class='icon-box']"):
            for twitter_url in icon_box.xpath(".//a[contains(@class, 'twitter')]"):
                print("Twitter", twitter_url.get("href"))
                user_info['twitter_url'] = twitter_url.get("href")

        # InstagramのURLを取得
        for icon_box in profile.xpath(".//div[@class='icon-box']"):
            for instagram_url in icon_box.xpath(".//a[contains(@class, 'instagram')]"):
                print("Instagram", instagram_url.get("href"))
                user_info['instagram_url'] = instagram_url.get("href")

        # グランプリflgの取得
        for grandprix_flg in profile.xpath(".//span[2]"):
            if grandprix_flg.text == "グランプリ":
                grandprix_flg = 1
            elif grandprix_flg.text == "準グランプリ":
                grandprix_flg = 2
            else:
                grandprix_flg = 0
            print("グランプリFlg", grandprix_flg)
            user_info['grandprix_flg'] = grandprix_flg

        # ProfileのURLの取得
        for profile_directory in profile.xpath(".//div/ul/li[1]/a"):
            print("Profile URL", top_url + profile_directory.get("href"))
            profile_url = top_url + profile_directory.get("href")
            user_info['url'] = profile_url

            # Profile URLの中から、ユーザー情報を取得。
            profile_response = requests.get(profile_url)
            profile_html = profile_response.text
            profile_root = lxml.html.fromstring(profile_html)

            # profileの写真を取得
            for profile_img in profile_root.xpath("//*[@id='main-photo']/img"):
                print("Profile Photo", top_url + profile_img.get("src"))
                profile_images.append(top_url + profile_img.get("src"))
                user_info['icon_image'] = top_url + profile_img.get("src")

            for target in profile_images:
                re = requests.get(target)

                with open('/Users/YUSUKE/Desktop/Mscolle.com/profile_imgs/'
                          + str(uuid.uuid1()) + target.replace("?v=121001", "").split("/")[-1], 'wb') as f: # imgフォルダに格納
                    # .contentで画像データとして書き込む
                    f.write(re.content)

            # 学部を取得
            for faculty in profile_root.xpath("//*[@id='info']/span[2]"):
                print("学部", faculty.text.replace(" ", "").replace("\n", ""))
                user_info['faculty'] = faculty.text.replace(" ", "").replace("\n", "")

            # 誕生日を取得
            for birthday in profile_root.xpath("//*[@id='info']/dl[1]/dd"):
                print("誕生日", birthday.text)
                user_info['birthday'] = birthday.text

            # 出身地を取得
            for birthplace in profile_root.xpath("//*[@id='info']/dl[2]/dd"):
                print("出身地", birthplace.text)
                user_info['birthplace'] = birthplace.text

            # 身長を取得
            for height in profile_root.xpath("//*[@id='info']/dl[3]/dd"):
                print("身長", height.text)
                user_info['height'] = height.text

            # 血液型を取得
            for blood in profile_root.xpath("//*[@id='info']/dl[4]/dd"):
                print("血液型", blood.text)
                user_info['blood'] = blood.text

        user_list = []
        user_list.append(user_info['id'])
        user_list.append(user_info['contest_id'])
        user_list.append(user_info['entry_no'])
        user_list.append(user_info['name'])
        user_list.append(user_info['twitter_url'])
        user_list.append(user_info['instagram_url'])
        user_list.append(user_info['icon_image'])
        user_list.append(user_info['url'])
        user_list.append(user_info['grandprix_flg'])
        user_list.append(user_info['faculty'])
        user_list.append(user_info['birthday'])
        user_list.append(user_info['birthplace'])
        user_list.append(user_info['height'])
        user_list.append(user_info['blood'])
        print(user_list)
        sql = """
        insert into mscolle.user_info (id, contest_id, entry_no, name,
        twitter_url, instagram_url, icon_image, url, grandprix_flg, faculty, birthday, birthplace, height, blood)
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(sql, user_list)
        connector.commit()
