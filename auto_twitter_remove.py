import tweepy
import urllib.request
import re
import time
import datetime
import sys
import pymysql
import schedule

# 今の時間を定義
now = datetime.datetime.now()

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
    sql = "select screen_name from users where auto_remove_flg = 1 and consumer_key is not NULL"
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

    # authを設定
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

    # APIインスタンスを作成
    api = tweepy.API(auth)

    # follow_atをfollow_idから取得する。
    def get_follow_at(f):
        with connector.cursor() as cursor:
            sql = "select follow_at from twitter_follow_log where twitter_id = %s"
            cursor.execute(sql, f)
            follow_at = cursor.fetchall()
            return follow_at[0][0]

    # refollow_flgをfollow_idから取得する。
    def get_refollow_flg(f):
        with connector.cursor() as cursor:
            sql = "select refollow_flg from twitter_follow_log where twitter_id = %s"
            cursor.execute(sql, f)
            refollow_flg = cursor.fetchall()
            return refollow_flg

    #followerとfollowを定義
    followers = api.followers_ids(my_twitter_id,count=5000)
    friends = api.friends_ids(my_twitter_id,count=5000)

    #リフォローをログに残す
    def refollow_log(f):
        try:
            log_data = []
            with connector.cursor() as cursor:
                select_sql = """select refollow_flg from twitter_follow_log where twitter_id = %s"""
                cursor.execute(select_sql, f)
                refollow_flg = cursor.fetchall()
            if refollow_flg == 1:
                print("")
            else:
                log_data.append(1)  # refollow_flg
                log_data.append(now)  # refollow_at
                log_data.append(f)  # id保持
                with connector.cursor() as cursor:
                    update_sql = """
                    update mscolle.twitter_follow_log set refollow_flg = %s, refollow_at = %s where twitter_id = %s 
                    """
                    cursor.execute(update_sql, log_data)
                    connector.commit()
        except Exception as e:
            print(e)

    #リムーブをログに残す
    def remove_log(f):
        try:
            with connector.cursor() as cursor:
                log_data = []
                log_data.append(0) # follow_flg
                log_data.append(1)  # remove_flg
                log_data.append(now)  # remove_at
                log_data.append(f)  # id保持
                update_sql = """
                update mscolle.twitter_follow_log set follow_flg = %s, remove_flg = %s, remove_at = %s where twitter_id = %s 
                """
                cursor.execute(update_sql, log_data)
                connector.commit()
        except Exception as e:
            print(e)



    # **************************1週間フォロー返してくれない人をフォロー解除**************************
    def destroy_non_follow_back():
        days = 7
        border = now - datetime.timedelta(days=days)
        print(days, "日以上フォロー返してくれない人のフォロー解除を開始します。")

        for f in friends:
            refollow_flg = get_refollow_flg(f)
            if f not in followers:
                try: 
                    follow_at = get_follow_at(f)
                    if border >= follow_at:
                        api.destroy_friendship(f)
                        remove_log(f)
                        print("ID:",str(f),"のフォローを解除しました")
                        print("リムーブをログに追加しました。")
                        # time.sleep(1)
                    else:
                        print("ID:",str(f),"フォローバック待ってるね。")
                        # time.sleep(1)
                except:
                    api.destroy_friendship(f)
                    print("データベースに見つからなかったのでID:",str(f),"のフォローを解除しました")
                    print("リムーブをログに追加しました。")
                    # time.sleep(1)
            elif refollow_flg == 1:
                print("ID:",str(f),"さんフォローバックありがとう！")
                refollow_log(f)
                print("フォローバックをログに追加しました。")
                # time.sleep(1)
            else:
                print("ID:",str(f),"さんいつもありがとう。")
                # time.sleep(1)
        print("1週間フォロー返してくれない人のフォロー解除が終了しました。")


    # **************************30日以上投稿していない人をフォロー解除**************************
    def destroy_non_active():
        # ボーダーラインを設定
        days = 30
        print(days, "日以上投稿していない人のフォロー解除を開始します。")
        border_line = datetime.timedelta(days=days)

        # トップのツイートを取得
        for f in friends:
            top_tweets = api.user_timeline(count=1, id=f, exclude_replies=True, exclude_retweets=True)
        # トップツイートの投稿時間を探して、今の時間との差分をpast_timeに保存
            for top_tweet in top_tweets:
                top_tweet_day = top_tweet.created_at + datetime.timedelta(hours=9)
                past_time = now - top_tweet_day
        # past_timeがボーダーラインより大きかったら、フォローを解除する。
                if past_time > border_line:
                    print("ID:",str(f),"のフォローを解除しました。")
                    api.destroy_friendship(f)
                    remove_log(f)
                    print("リムーブをログに追加しました。")
                    time.sleep(1)
        # past_timeがボーダーラインより小さかったら
                else:
                    print("ID:",str(f),"さんいつもありがとう。")
        print("30日以上投稿していない人のフォロー解除が終了しました。")

    #メインの実装
    def job():
        destroy_non_follow_back()
        destroy_non_active()
    job()

    # # 1時間おきに処理を実行
    # schedule.every().hour.do(job)
    # while True:
    # schedule.run_pending()
    # time.sleep(1)
