import tweepy
import urllib.request
import re
import time
import datetime
import sys
import pymysql
import schedule

# 初期変数設定
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


# TwitterのIDをデータベースから取得し、twitter_idsに保存
def get_twitter_ids():
    twitter_ids = []
    with connector.cursor() as cursor:
        sql = "select twitter_url from mom_user_info2018 where twitter_url != 'NULL'"
        cursor.execute(sql)
        results = cursor.fetchall()

    for result in results:
        for res in result:
            twitter_id = res.replace("https://twitter.com/", "")
            twitter_ids.append(twitter_id)
    return twitter_ids
twitter_ids = get_twitter_ids()

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
            log_data.append(log_id[0][0])  # id保持
            update_sql = """
            update mscolle.twitter_follow_log set follow_count = %s, follow_flg = %s where log_id = %s 
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
            insert_sql = """
            insert into mscolle.twitter_follow_log (log_id, follow_count, twitter_id, follow_at, follow_type, follow_keyword, follow_flg)
            values(%s,%s,%s,%s,%s,%s,%s)
            """
            cursor.execute(insert_sql, log_data)
            connector.commit()
            print("ログ登録が完了しました。")


# follow_countが、borderに達していたら、フォローの処理を飛ばす
def follow_border_skip(twitter_id):
        # borderを定義
        border = 1
        # idをデータベースから出す。
        with connector.cursor() as cursor:
            follow_count_select_sql = "select follow_flg, follow_count from twitter_follow_log where twitter_id = %s"
            cursor.execute(follow_count_select_sql, twitter_id)
            follow_log = cursor.fetchall()
            if len(follow_log) == 0:
                print("follow_border_skip", "初回フォロー：続行")
                return False
            elif follow_log[0][0] == 1:
                print("follow_border_skip", "フォロー中です：スキップ")
                return True
            elif border <= follow_log[0][1]:
                print("follow_border_skip", "ボーダー以上：スキップ")
                return True
            else:
                print("follow_border_skip", "ボーター未満：続行")
                return False

# # followerとfollowを定義
# followers = api.followers_ids(twitter_id)
# friends = api.friends_ids(twitter_id)


# ****************************検索キーワードでフォロー&Fav***********************
# 検索ワードと検索数をセット
def search_follow():
    follow_type = 1
    print("検索キーワードでフォローを開始します。")
    keywords = ["ミスオブミス", "ミスコレ", "ミスコン", "@Mscontest_"]
    for keyword in keywords:
        count = 50
        # 検索実行。search_resultsにpost_idを保存
        search_results = api.search(q=keyword, count=count)
        # 結果をフォロー
        for result in search_results:
            twitter_id = result.user._json["id"]
            if follow_border_skip(twitter_id):
                continue
            else:
                try:
                    api.create_friendship(twitter_id)
                    print(str(twitter_id) + 'をフォローしました')
                    time.sleep(2)
                    twitter_follow_log(twitter_id, follow_type, keyword)
                    # 結果をfav
                    tweet_id = result.id  # ツイートのstatusオブジェクトから、ツイートidを取得
                    try:
                        api.create_favorite(tweet_id)  # favする
                    except Exception as e:
                        print(e)
                except Exception as e:
                    print(e)
    print("検索キーワードでフォローが終了しました。")


# ****************似たようなアカウントをフォローしている人をフォロー***************
# 自分に似たようなアカウントを指定
def similar_acount_followers_follow():
    follow_type = 2
    print("指定アカウントのフォロワーのフォローを開始します。")
    accounts = ["MISSMRCOLLE", "_sute2013081503", "misscon_bot", "UTsweetheart"]
    for account in accounts:
        count = 50
        account_followers = api.followers(id=account, count=count)

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


# *********************ミスコレの人にfavしている人をフォロー********************
def mscolle_favoritters_follow(twitter_ids):
    follow_type = 5
    print("ミスコレ出場者にfavしてくれている人のフォローを開始します。")
    for twitter_id in twitter_ids:
        count = 10
        ms_tweets = api.user_timeline(count=count, twitter_id=twitter_id)
        for ms_tweet in ms_tweets:
            post_id = ms_tweet._json["id"]
            favoritters_id = get_favoritters(post_id)
                # ミスコレの投稿にfavしている人をfollow
            for favoritter_id in favoritters_id:
                if follow_border_skip(str(favoritter_id)):
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
    print("ミスコレ出場者にfavしてくれている人のフォローが終了しました。")


# *********************ミスコレの人にRTしている人をフォロー*********************
def mscolle_retweeters_follow(twitter_ids):
    follow_type = 6
    print("ミスコレ出場者にRTしてくれている人のフォローを開始します。")
    for twitter_id in twitter_ids:
        count = 10
        ms_tweets = api.user_timeline(count=count, twitter_id=twitter_id)
        for ms_tweet in ms_tweets:
            retweeters = api.retweets(id=ms_tweet.id_str)
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
    print("ミスコレ出場者にRTしてくれている人のフォローが終了しました。")

# *********************自分の投稿の一番上のUserの投稿にfavしている人をフォロー********************

# *********************自分の投稿の一番上のUserの投稿にRTしている人をフォロー********************

#メインの処理
def job():
    search_follow()
    similar_acount_followers_follow()
    my_favoritters_follow()
    my_retweeters_follow()
    mscolle_favoritters_follow()
    mscolle_retweeters_follow()

# 1時間おきに処理を実行
schedule.every().hour.do(job)
while True:
  schedule.run_pending()
  time.sleep(1)
