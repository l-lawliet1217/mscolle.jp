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
    sql = "select screen_name from users where auto_follow_flg = 1 and consumer_key is not NULL"
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

    # データベースにフォローをしたというログを保存する。
    def twitter_follow_log(twitter_id, follow_type, follow_keyword=None):
        log_data = []
        # 今の時間を定義
        now = datetime.datetime.now()
        # idをデータベースから出す。
        with connector.cursor() as cursor:

            #2度目以上
            id_select_sql = """select log_id, follow_count, follow_flg from twitter_follow_log where twitter_id = %s"""
            cursor.execute(id_select_sql, twitter_id)
            log_id = cursor.fetchall()
            if log_id:
                log_data.append(log_id[0][1] + 1)  # follow_count追加
                log_data.append(1)  # follow_flg
                log_data.append(user_id) # user_id
                log_data.append(log_id[0][0])  # id保持
                update_sql = """
                update mscolle.twitter_follow_log set follow_count = %s, follow_flg = %s, user_id = %s where log_id = %s 
                """
                cursor.execute(update_sql, log_data)
                connector.commit()
                print("ログを更新しました。")

            else:
                # 新規追加
                max_id_select_sql = """select max(log_id) + 1 from twitter_follow_log"""
                cursor.execute(max_id_select_sql)
                max_id = cursor.fetchall()
                log_data.append(max_id[0][0])  # id保持
                log_data.append(1)  # follow_count
                log_data.append(twitter_id)  # twitter_id
                log_data.append(now)  # follow_at
                log_data.append(follow_type)  # follow_type
                log_data.append(follow_keyword)  # follow_keyword
                log_data.append(1)  # follow_flg
                log_data.append(user_id)  # user_id
                insert_sql = """
                insert into mscolle.twitter_follow_log (log_id, follow_count, twitter_id, follow_at, follow_type, follow_keyword, follow_flg, user_id)
                values(%s,%s,%s,%s,%s,%s,%s,%s)
                """
                cursor.execute(insert_sql, log_data)
                connector.commit()
                print("ログ登録が完了しました。")


    # follow_countが、borderに達していたら、フォローの処理を飛ばす
    def follow_border_skip(target_twitter_id):
            # borderを定義
            border = 1
            # idをデータベースから出す。
            with connector.cursor() as cursor:
                log_data = []
                log_data.append(target_twitter_id)  # my_twitter_id
                log_data.append(user_id)  # user_id
                follow_count_select_sql = "select follow_flg, follow_count from twitter_follow_log where twitter_id = %s and user_id = %s"
                cursor.execute(follow_count_select_sql, log_data)                
                follow_log = cursor.fetchall()
                if log_data[0] == my_twitter_id:
                    print("follow_border_skip", "あなた自身です：スキップ")
                    time.sleep(1)
                    return True
                elif len(follow_log) == 0:
                    print("follow_border_skip", "初回フォロー：続行")
                    return False
                    time.sleep(1)
                elif follow_log[0][0] == 1:
                    print("follow_border_skip", "フォロー中です：スキップ")
                    time.sleep(1)
                    return True
                elif border <= follow_log[0][1]:
                    print("follow_border_skip", "ボーダー以上：スキップ")
                    time.sleep(1)
                    return True
                else:
                    print("follow_border_skip", "ボーター未満：続行")
                    return False
                    time.sleep(1)


    # ****************************検索キーワードでフォロー&Fav***********************
    # 検索ワードと検索数をセット
    def search_follow():
        follow_type = 1
        print("検索キーワードでフォローを開始します。")
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
                target_twitter_id = result.user._json["id"]
                if follow_border_skip(target_twitter_id):
                    continue
                else:
                    try:
                        api.create_friendship(target_twitter_id)
                        print(str(target_twitter_id) + 'をフォローしました')
                        time.sleep(2)
                        twitter_follow_log(target_twitter_id, follow_type, keyword)
                        # 結果をfav
                        tweet_id = result.id  # ツイートのstatusオブジェクトから、ツイートidを取得
                        try:
                            api.create_favorite(tweet_id)  # favする
                        except Exception as e:
                            print(e)
                    except Exception as e:
                        print(e)
        print("検索キーワードでフォローが終了しました。")


    # ****************特定のアカウントをフォローしている人をフォロー***************
    # アカウントを指定
    def target_acount_followers_follow():
        follow_type = 2
        print("指定アカウントのフォロワーのフォローを開始します。")
        with connector.cursor() as cursor:
            sql = "SELECT follow_target_accounts.screen_name FROM follow_target_accounts INNER JOIN users ON follow_target_accounts.user_id = users.id WHERE users.screen_name = %s"
            cursor.execute(sql, screen_name)
            accounts = cursor.fetchall()
        for account in accounts:
            account = account[0]
            count = 50
            account_followers = api.followers(screen_name=account, count=count)

            # 自分に似たようなアカウントのフォロワーをフォロー
            for account_follower in account_followers:
                twitter_id = account_follower._json["id"]
                if follow_border_skip(str(twitter_id)):
                    continue
                else:
                    try:
                        print(str(twitter_id) + 'をフォローしました')
                        api.create_friendship(twitter_id)
                        time.sleep(2)
                        twitter_follow_log(twitter_id, follow_type)
                        # フォローした人の一番上の投稿をfav
                        result = api.user_timeline(id=twitter_id, count=1, exclude_replies=True, exclude_retweets=True)
                        tweet_id = result[0].id
                        try:
                            api.create_favorite(tweet_id)  # favする
                        except Exception as e:
                            print(e)
                    except Exception as e:
                        print(e)
        print("指定アカウントのフォロワーのフォローが終了しました。")


    # *******************自分のツイートにfavしてくれている人をフォロー******************
    # 自分のツイートをfavしてくれている人のUSER_IDを取得
    def my_favoritters_follow():
        follow_type = 3
        print("自分にfavしてくれている人のフォローを開始します。")
        count = 10
        my_tweets = api.user_timeline(count=count, id='MsContest_')
        for my_tweet in my_tweets:
            post_id = my_tweet._json["id"]
            favoritters_id = get_favoritters(post_id)
                # 自分の投稿にfavしている人をfollow
            for favoritter_id in favoritters_id:
                if follow_border_skip(favoritter_id):
                    continue
                else:
                    try:
                        api.create_friendship(favoritter_id)
                        print(str(favoritter_id) + 'をフォローしました')
                        time.sleep(2)
                        twitter_follow_log(favoritter_id, follow_type)
                        # フォローした人の一番上の投稿をfav
                        result = api.user_timeline(id=favoritter_id, count=1, exclude_replies=True, exclude_retweets=True)
                        tweet_id = result[0].id
                        try:
                            api.create_favorite(tweet_id)  # favする
                        except Exception as e:
                            print(e)
                    except Exception as e:
                        print(e)
        print("自分にfavしてくれている人のフォローが終了しました。")


    # *******************自分のツイートにRTしてくれている人をフォロー******************
    # 自分のツイートをRTしてくれている人のUSER_IDを取得
    def my_retweeters_follow():
        follow_type = 4
        print("自分にRTしてくれている人のフォローを開始します。")
        count = 10
        my_tweets = api.user_timeline(count=count, id='MsContest_')

        for my_tweet in my_tweets:
            retweeters = api.retweets(id=my_tweet.id_str)
            for retweeter in retweeters:
                retweeter_id = retweeter.user.id
                if follow_border_skip(retweeter_id):
                    continue
                else:
                    # 自分の投稿にRTしている人をfollow
                    try:
                        api.create_friendship(retweeter_id)
                        print(str(retweeter_id) + 'をフォローしました')
                        time.sleep(2)
                        twitter_follow_log(retweeter_id, follow_type)
                        # RTした人の一番上の投稿をfav
                        result = api.user_timeline(id=retweeter_id, count=1, exclude_replies=True, exclude_retweets=True)
                        tweet_id = result[0].id
                        try:
                            api.create_favorite(tweet_id)  # favする
                        except Exception as e:
                            print(e)
                    except Exception as e:
                        print(e)
        print("自分にRTしてくれている人のフォローが終了しました。")

    #メインの処理
    def job():
        search_follow()
        target_acount_followers_follow()
        my_favoritters_follow()
        my_retweeters_follow()
    job()

    # # 1時間おきに処理を実行
    # schedule.every().hour.do(job)
    # while True:
    # schedule.run_pending()
    # time.sleep(1)
