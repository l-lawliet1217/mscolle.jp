import tweepy
import urllib.request
import re
import time
import datetime
import sys
import pymysql
import schedule

# SQLのログイン情報を記載
connector = pymysql.connect(
    host='127.0.0.1',
    db='mscolle',
    user='root',
    passwd='root',
    charset='utf8',
)

#データベースから、ユーザー情報を出力
with connector.cursor() as cursor:
    sql = "select screen_name from users where auto_fav_flg = 1 and consumer_key is not NULL"
    cursor.execute(sql)
    screen_names = cursor.fetchall()

for screen_name in screen_names:
    with connector.cursor() as cursor:
        sql = "select id, twitter_id, consumer_key, consumer_secret, access_token, access_secret from users where screen_name = %s"
        cursor.execute(sql, screen_name)
        results = cursor.fetchall()

    # 初期変数設定
    user_id = results[0][0]
    my_twitter_id = results[0][1]
    CONSUMER_KEY = results[0][2]
    CONSUMER_SECRET = results[0][3]
    ACCESS_TOKEN = results[0][4]
    ACCESS_SECRET = results[0][5]

    # 各種キーをセット
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

    # APIインスタンスを作成
    api = tweepy.API(auth)

    # get_favorittersを定義
    def get_favoritters(post_id):
        try:
            json_data = urllib.request.urlopen('https://twitter.com/i/activity/favorited_popup?id=' + str(post_id)).read()
            json_data = json_data.decode("utf8")
            found_ids = re.findall(r'data-user-id=\\"+\d+', json_data)
            unique_ids = list(set([re.findall(r'\d+', match)[0] for match in found_ids]))
            return unique_ids
        except urllib.request.HTTPError:
            return False

    # ****************************検索キーワードでフォロー&Fav***********************
    # 検索ワードと検索数をセット
    def search_fav():
        print("検索キーワードでfavを開始します。")
        with connector.cursor() as cursor:
            sql = "SELECT follow_target_keywords.keyword FROM follow_target_keywords INNER JOIN users ON follow_target_keywords.user_id = users.id WHERE users.screen_name = %s"
            cursor.execute(sql, screen_name)
            keywords = cursor.fetchall()
        for keyword in keywords:
            count = 100
            # 検索実行。search_resultsにpost_idを保存
            search_results = api.search(q=keyword, count=count)
            # 結果をフォロー
            for result in search_results:
                tweet_id = result.id  # ツイートのstatusオブジェクトから、ツイートidを取得
                try:
                    api.create_favorite(tweet_id)  # favする
                    print("favに成功！")
                except Exception as e:
                    print(e)
        print("検索キーワードでフォローが終了しました。")


    # ****************似たようなアカウントをフォローしている人をフォロー***************
    # 自分に似たようなアカウントを指定
    def target_acount_followers_fav():
        print("指定アカウントのフォロワーのfavを開始します。")
        with connector.cursor() as cursor:
            sql = "SELECT follow_target_accounts.screen_name FROM follow_target_accounts INNER JOIN users ON follow_target_accounts.user_id = users.id WHERE users.screen_name = %s"
            cursor.execute(sql, screen_name)
            keywords = cursor.fetchall()        
        for account in accounts:
            count = 50
            account_followers = api.followers(id=account, count=count)
        # 自分に似たようなアカウントのフォロワーをフォロー
        for account_follower in account_followers:
            result = api.user_timeline(id=my_twitter_id, count=1, exclude_replies=True, exclude_retweets=True)
            tweet_id = result[0].id
            try:
                api.create_favorite(tweet_id)  # favする
                print("favに成功！")
            except Exception as e:
                print(e)
        print("指定アカウントのフォロワーのフォローが終了しました。")


    # *******************自分のツイートにfavしてくれている人をフォロー******************
    # 自分のツイートをfavしてくれている人のUSER_IDを取得
    def my_favoritters_fav():
        print("自分にfavしてくれている人のfavを開始します。")
        count = 10
        my_tweets = api.user_timeline(count=count, id='MsContest_')
        for my_tweet in my_tweets:
            post_id = my_tweet._json["id"]
            favoritters_id = get_favoritters(post_id)
                # 自分の投稿にfavしている人をfollow
            for favoritter_id in favoritters_id:
                result = api.user_timeline(id=favoritter_id, count=1, exclude_replies=True, exclude_retweets=True)
                tweet_id = result[0].id
                try:
                    api.create_favorite(tweet_id)  # favする
                    print("favに成功！")
                except Exception as e:
                    print(e)
        print("自分にfavしてくれている人のfavが終了しました。")


    # *******************自分のツイートにRTしてくれている人をフォロー******************
    # 自分のツイートをRTしてくれている人のUSER_IDを取得
    def my_retweeters_fav():
        print("自分にRTしてくれている人のfavを開始します。")
        count = 10
        my_tweets = api.user_timeline(count=count, id='MsContest_')

        for my_tweet in my_tweets:
            retweeters = api.retweets(id=my_tweet.id_str)
            for retweeter in retweeters:
                retweeter_id = retweeter.user.id
                result = api.user_timeline(id=retweeter_id, count=1, exclude_replies=True, exclude_retweets=True)
                tweet_id = result[0].id
                try:
                    api.create_favorite(tweet_id)  # favする
                    print("favに成功！")
                except Exception as e:
                    print(e)
        print("自分にRTしてくれている人のフォローが終了しました。")


    #メインの処理
    def job():
        search_fav()
        target_acount_followers_fav()
        my_favoritters_fav()
        my_retweeters_fav()
    job()

    # # 1時間おきに処理を実行
    # schedule.every().hour.do(job)
    # while True:
    # schedule.run_pending()
    # time.sleep(1)
