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

#最後のプロフィール IDを取得
id_select_sql = """select max(id) from user_info"""
cursor.execute(id_select_sql)
j = cursor.fetchall()
for jj in j:
    for jjj in jj:
        j = jjj + 1
        print(j)

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

    # contest_idの取得
    contest_id = contest_url[contest_url.rfind("/") + 1:]
    print("contest_id", contest_id)
    contest_info['id'] = contest_id

    # contest URL *
    print(contest_url)
    contest_info['contest_url'] = contest_url

    skip_sql = """select id from contest_info where id = %s"""
    row = cursor.execute(skip_sql, contest_id)
    if row > 0:
        continue
    else:

        # 開催年度の取得 *
        print("開催年度", right(contest_url, 4))
        contest_info['contest_year'] = right(contest_url, 4)

        # ****** Contestのページのスクレピング******
        # TOPページの中のHTMLをrootに格納。
        contest_response = requests.get(contest_url)
        contest_html = contest_response.text
        contest_root = lxml.html.fromstring(contest_html)

        # contest_imageの取得 *
        for contest_img in contest_root.xpath("//*[@id='contest-header-image']/img"):
            print(top_url + contest_img.get("src"))
            contest_images.append(top_url + contest_img.get("src"))
            contest_info['contest_img'] = top_url + contest_img.get("src")
        # for target in contest_images:
        #     re = requests.get(target)
        #     with open('/Users/YUSUKE/Desktop/Mscolle.com/contest_imgs/'
        #               + str(uuid.uuid1()) + target.replace("?v=121001", "").split("/")[-1], 'wb') as f: # imgフォルダに格納
        #         # .contentで画像データとして書き込む
        #         f.write(re.content)

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

    # contest_urlが既に取得済みだったらSKIP

        contest_list = []
        contest_list.append(contest_info['id'])
        contest_list.append(contest_info['contest_url'])
        contest_list.append(contest_info['contest_year'])
        try:
            contest_list.append(contest_info['contest_img'])
        except:
            contest_list.append('NULL')
        try:
            contest_list.append(contest_info['contest_name'])
        except:
            contest_list.append('NULL')
        try:
            contest_list.append(contest_info['universe_name'])
        except:
            contest_list.append('NULL')
        try:
            contest_list.append(contest_info['host_name'])
        except:
            contest_list.append('NULL')
        try:
            contest_list.append(contest_info['contest_date'])
        except:
            contest_list.append('NULL')
        try:
            contest_list.append(contest_info['contest_place'])
        except:
            contest_list.append('NULL')
        try:
            contest_list.append(contest_info['host_twitter'])
        except:
            contest_list.append('NULL')
        try:
            contest_list.append(contest_info['vote_start_date'])
        except:
            contest_list.append('NULL')
        try:
            contest_list.append(contest_info['vote_end_date'])
        except:
            contest_list.append('NULL')
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

        # 名前の取得
        for name in profile.xpath(".//h3"):
            print("名前", name.text.replace(" ", ""))
            user_info['name'] = name.text.replace(" ", "")

        # 同じ名前がデータベースにあったら SKIP
        skip_sql = """select id from user_info where name = %s"""
        row = cursor.execute(skip_sql, name.text)
        if row > 0:
            continue
        else:
            # profile_idの取得
            print("id", j)
            user_info['id'] = j
            j = j + 1

            # contest_idの取得
            contest_id = contest_url[contest_url.rfind("/") + 1:]
            print("contest_id", contest_id)
            user_info['contest_id'] = contest_id

            # エントリーNoの取得
            entry_no = profile_href[profile_href.rfind("/") + 1:]
            print("エントリーNo", entry_no)
            user_info['entry_no'] = entry_no

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

                #profileの写真をフォルダに保存
                # for target in profile_images:
                #     re = requests.get(target)
                #
                #     with open('/Users/YUSUKE/Desktop/Mscolle.com/profile_imgs/'
                #               + str(uuid.uuid1()) + target.replace("?v=121001", "").split("/")[-1], 'wb') as f: # imgフォルダに格納
                #         # .contentで画像データとして書き込む
                #         f.write(re.content)

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

                #詳細プロフィールを取得
                for profile_topics in profile_root.xpath("//*[@id='profile_topics']/ul/li"):
                    h3 = profile_topics.xpath(".//h3")[0].text
                    p = profile_topics.xpath(".//p")[0].text.replace(" ", "").replace("\n", "")
                    if h3 == '趣味':
                       print(h3, p)
                       user_info['hobby'] = p
                    elif h3 == '特技':
                       print(h3, p)
                       user_info['skill'] = p
                    elif h3 == '所属サークル':
                       print(h3, p)
                       user_info['circle'] = p
                    elif h3 == 'アルバイト':
                       print(h3, p)
                       user_info['part_time_job'] = p
                    elif h3 == 'よく行くエリア・スポット':
                       print(h3, p)
                       user_info['favorite_area'] = p
                    elif h3 == 'よく使うアプリ':
                       print(h3, p)
                       user_info['favorite_app'] = p
                    elif h3 == '自分を色で例えると?':
                       print(h3, p)
                       user_info['my_color'] = p
                    elif h3 == '休日の過ごし方':
                       print(h3, p)
                       user_info['holiday'] = p
                    elif h3 == '平均睡眠時間':
                       print(h3, p)
                       user_info['sleeping_time'] = p
                    elif h3 == 'よく読む雑誌':
                       print(h3, p)
                       user_info['favorite_magazine'] = p
                    elif h3 == '旅行で行きたい場所':
                       print(h3, p)
                       user_info['wanna_trip'] = p
                    elif h3 == '無人島に１つだけ持って行くもの':
                       print(h3, p)
                       user_info['item_to_bring_island'] = p
                    elif h3 == 'ストレス解消法':
                       print(h3, p)
                       user_info['way_to_relux'] = p
                    elif h3 == 'マイブーム':
                       print(h3, p)
                       user_info['my_into'] = p
                    elif h3 == '最近買った一番高い物':
                       print(h3, p)
                       user_info['most_variable'] = p
                    elif h3 == '好きな男性有名人':
                       print(h3, p)
                       user_info['favorite_actor'] = p
                    elif h3 == '好きな女性有名人':
                       print(h3, p)
                       user_info['favorite_actress'] = p
                    elif h3 == '好きな芸人':
                       print(h3, p)
                       user_info['favorite_comedian'] = p
                    elif h3 == '好きなテレビ番組':
                       print(h3, p)
                       user_info['favorite_tv_program'] = p
                    elif h3 == '好きな映画':
                       print(h3, p)
                       user_info['favorite_movie'] = p
                    elif h3 == '好きな歌手':
                       print(h3, p)
                       user_info['favorite_singer'] = p
                    elif h3 == '好きな食べ物':
                       print(h3, p)
                       user_info['favorite_food'] = p
                    elif h3 == '好きな場所':
                       print(h3, p)
                       user_info['favorite_spot'] = p
                    elif h3 == '掛けられて嬉しい言葉':
                       print(h3, p)
                       user_info['favorite_word_to_me'] = p
                    elif h3 == '「ドキッ」とする異性の仕草':
                       print(h3, p)
                       user_info['favorite_gesture'] = p
                    elif h3 == 'こんな異性に惹かれます':
                       print(h3, p)
                       user_info['favorite_type'] = p
                    elif h3 == '理想の告白シチュエーション':
                       print(h3, p)
                       user_info['ideal_situation'] = p
                    elif h3 == '初恋はいつ?':
                       print(h3, p)
                       user_info['first_love'] = p
                    elif h3 == '友達が異性に変わる瞬間':
                       print(h3, p)
                       user_info['fallen_love'] = p
                    elif h3 == 'もし一目惚れしたらどうアプローチする?':
                       print(h3, p)
                       user_info['how_to_approach'] = p
                    elif h3 == '理想の結婚相手':
                       print(h3, p)
                       user_info['marriage_partner'] = p
                    elif h3 == '学生生活を一言で表すと?':
                       print(h3, p)
                       user_info['my_school_life'] = p
                    elif h3 == '今まで一番嬉しかったこと':
                       print(h3, p)
                       user_info['happiest_happening'] = p
                    elif h3 == '今までで一番美味しかったもの':
                       print(h3, p)
                       user_info['most_delicious'] = p
                    elif h3 == '１００万円あったらどうする?':
                       print(h3, p)
                       user_info['what_if_million'] = p
                    elif h3 == '１つだけ願いが叶うとしたら?':
                       print(h3, p)
                       user_info['one_wish'] = p
                    elif h3 == '将来の夢':
                       print(h3, p)
                       user_info['dream'] = p
                    elif h3 == 'ミスコンテストに参加したきっかけ':
                       print(h3, p)
                       user_info['why_miss'] = p
                    elif h3 == '頑張ろうと思っていること':
                       print(h3, p)
                       user_info['hold_out'] = p
                    elif h3 == 'アピールポイント':
                       print(h3, p)
                       user_info['appeal_point'] = p
                    elif h3 == 'ミスコンテストへの意気込みを一言':
                       print(h3, p)
                       user_info['enthusiasm'] = p
                    elif h3 == '最近一番言っている言葉':
                       print(h3, p)
                       user_info['favorite_word'] = p
                    elif h3 == '尊敬する人':
                       print(h3, p)
                       user_info['respected_person'] = p
                    elif h3 == '自己流モテるテクニック':
                       print(h3, p)
                       user_info['technique_of_popular'] = p
                    elif h3 == '今までで一番笑ったこと':
                       print(h3, p)
                       user_info['best_laugh'] = p
                    elif h3 == '今までで一番泣いたこと':
                       print(h3, p)
                       user_info['best_cry'] = p
                    elif h3 == '今まで一番疲れたこと':
                       print(h3, p)
                       user_info['best_tired'] = p
                    elif h3 == '座右の銘':
                       print(h3, p)
                       user_info['favorite_motto'] = p
                    elif h3 == '得意料理':
                       print(h3, p)
                       user_info['favorite_dish'] = p
                    elif h3 == '好きな本':
                       print(h3, p)
                       user_info['favorite_book'] = p

            user_list = []
            user_list.append(user_info['id'])
            user_list.append(user_info['contest_id'])
            user_list.append(user_info['entry_no'])
            user_list.append(user_info['name'])
            try:
                user_list.append(user_info['twitter_url'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['instagram_url'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['icon_image'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['url'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['grandprix_flg'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['faculty'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['birthday'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['birthplace'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['height'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['blood'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['hobby'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['skill'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['circle'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['part_time_job'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_area'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_app'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['my_color'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['holiday'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['sleeping_time'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_magazine'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['wanna_trip'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['item_to_bring_island'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['way_to_relux'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['my_into'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['most_variable'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_actor'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_actress'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_comedian'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_tv_program'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_movie'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_singer'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_food'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_spot'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_word_to_me'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_gesture'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_type'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['ideal_situation'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['first_love'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['fallen_love'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['how_to_approach'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['marriage_partner'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['my_school_life'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['happiest_happening'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['most_delicious'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['what_if_million'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['one_wish'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['dream'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['why_miss'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['hold_out'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['appeal_point'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['enthusiasm'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_word'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['respected_person'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['technique_of_popular'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['best_laugh'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['best_cry'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['best_tired'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_motto'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_dish'])
            except:
                user_list.append('NULL')
            try:
                user_list.append(user_info['favorite_book'])
            except:
                user_list.append('NULL')


            print(user_list)
            sql = """
            insert into mscolle.user_info (id, contest_id, entry_no, name,
            twitter_url, instagram_url, icon_image, url, grandprix_flg, faculty, birthday, birthplace, height, blood, hobby, skill, circle, part_time_job, favorite_area, favorite_app, my_color, holiday, sleeping_time, favorite_magazine, wanna_trip, item_to_bring_island, way_to_relux, my_into, most_variable, favorite_actor, favorite_actress, favorite_comedian, favorite_tv_program, favorite_movie, favorite_singer, favorite_food, favorite_spot, favorite_word_to_me, favorite_gesture, favorite_type, ideal_situation, first_love, fallen_love, how_to_approach, marriage_partner, my_school_life, happiest_happening, most_delicious, what_if_million, one_wish, dream, why_miss, hold_out, appeal_point, enthusiasm, favorite_word, respected_person, technique_of_popular, best_laugh, best_cry, best_tired, favorite_motto, favorite_dish, favorite_book)
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            cursor.execute(sql, user_list)
            connector.commit()
