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

# 各種キーをセット
twitter_id = '1040912339061497856'
CONSUMER_KEY = 'uE4aWwteDqIWrjGdghu1MVQPg'
CONSUMER_SECRET = 'X2S8yWjXndq0pMbgtk4VyLbZ4AcsFum7oyFZmz9nMrDP4LJ0ii'
ACCESS_TOKEN = '1040912339061497856-ttMXdsDt7CT2WfZQiNkYPMrlN2BQEp'
ACCESS_SECRET = 'seGuv2O60qV19ue9GJMWd18PaLqOi191RP3BIbLAK3DeN'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

# APIインスタンスを作成
api = tweepy.API(auth)

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

# follow_atをfollow_idから取得する。
def get_follow_at(f):
    sql = """select follow_at from twitter_follow_log where twitter_id = %s"""
    cursor.execute(sql, f)
    follow_at = cursor.fetchall

#followerとfollowを定義
followers = api.followers_ids(twitter_id,count=5000)
friends = api.friends_ids(twitter_id,count=5000)

#リフォローをログに残す
def refollow_log(f):
    try:
        log_data = []
        select_sql = """select refollow_flg from twitter_follow_log where twitter_id = %s"""
        cursor.execute(select_sql, f)
        refollow_flg = cursor.fetchall
        if refollow_flg == 1:
            print()
        else:
            log_data.append(1)  # refollow_flg
            log_data.append(now)  # refollow_at
            log_data.append(f)  # id保持
            update_sql = """
            update mscolle.twitter_follow_log set refollow_flg = %s, refollow_at = %s where id = %s 
            """
            cursor.execute(update_sql, log_data)
            connector.commit()
    except Exception as e:
        print(e)

#リムーブをログに残す
def remove_log(f):
    try:
        log_data = []
        log_data.append(1)  # remove_flg
        log_data.append(now)  # remove_at
        log_data.append(f)  # id保持
        update_sql = """
        update mscolle.twitter_follow_log set remove_flg = %s, remove_at = %s where id = %s 
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

    try:
        for f in friends:
            if f not in followers:
                follow_at = get_follow_at(f)
                past_time = datetime.datetime.strptime(follow_at, '%Y-%m-%d %H:%M:%S') # => datetime.datetime(2017, 7, 1, 12, 6, 19)
                if border >= past_time:
                    api.destroy_friendship(f)
                    remove_log(f)
                    print("ID:",str(f),"のフォローを解除しました")
                    time.sleep(2)
                else:
                    print("ID:",str(f),"フォローバック待ってるね。")
            else:
                print("ID:",str(f),"さんいつもありがとう。")
                refollow_log(f)
    except:
        for f in friends:
            if f not in followers:
                api.destroy_friendship(f)
                print("データベースに見つからなかったのでID:",str(f),"のフォローを解除しました")
                remove_log(f)
                time.sleep(2)
            else:
                print("ID:",str(f),"さんいつもありがとう。")
                refollow_log(f)
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
                time.sleep(1)
    # past_timeがボーダーラインより小さかったら
            else:
                print("ID:",str(f),"さんいつもありがとう。")
    print("30日以上投稿していない人のフォロー解除が終了しました。")

#メインの実装
def job():
    destroy_non_follow_back()
    destroy_non_active()

job

# 1時間おきに処理を実行
schedule.every().hour.do(job)
while True:
  schedule.run_pending()
  time.sleep(1)
