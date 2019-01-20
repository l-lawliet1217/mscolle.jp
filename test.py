import tweepy
import urllib.request
import re
import time
import datetime
import sys
import pymysql

# 今の時間を定義
now = datetime.datetime.now()

# get_favorittersを定義
def get_favoritters(post_id):
    try:
        json_data = urllib.request.urlopen('https://twitter.com/i/activity/favorited_popup?id=' + str(post_id)).read()
        json_data=json_data.decode("utf8")
        found_ids = re.findall(r'data-user-id=\\"+\d+', json_data)
        unique_ids = list(set([re.findall(r'\d+', match)[0] for match in found_ids]))
        return unique_ids
    except urllib.request.HTTPError:
        return False

# 各種キーをセット
SCREEN_NAME = 'MsContest_'
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

# TwitterのIDをデータベースから取得し、twitter_idsに保存
twitter_ids = []
with connector.cursor() as cursor:
    sql = "select twitter_url from mom_user_info2018 where twitter_url != 'NULL'"
    cursor.execute(sql)
    results = cursor.fetchall()

for result in results:
    for res in result:
        twitter_id = res.replace("https://twitter.com/", "")
        twitter_ids.append(twitter_id)

# データベースにフォローをしたというログを保存する。
def twitter_follow_log(screen_name):
    #idをデータベースから出す。
    with connector.cursor() as cursor:
        try:
            id_select_sql = """select id from twitter_follow_log where screen_name = %s"""
            cursor.execute(id_select_sql, screen_name)
            ids = cursor.fetchall()
            for ids in idss:
                for id in ids:
                    twitter_follow_log['id'] = id

        except:
            max_id_select_sql = """select max(id) from twitter_follow_log"""
            cursor.execute(max_id_select_sql)
            idss = cursor.fetchall()
            for ids in idss:
                for id in ids:
                    twitter_follow_log['id'] = id

    #follow_countをデータベースから出す。
    with connector.cursor() as cursor:
        try:
            follow_count_select_sql = "select follow_count from twitter_follow_log where screen_name = %s"
            cursor.execute(follow_count_select_sql, screen_name)
            follow_countss = cursor.fetchall()
            for follow_counts in follow_countss:
                for follow_count in follow_counts:
                    twitter_follow_log['follow_count'] = follow_count
        except:
            follow_count = 1
            twitter_follow_log['follow_count'] = follow_count

# id,follow_count,screen_name,follow_atをDBにinsert
twitter_follow_log_list = []
twitter_follow_log_list.append(twitter_follow_log['id'])
twitter_follow_log_list.append(twitter_follow_log['follow_count'])
twitter_follow_log['screen_name'] = screen_name
twitter_follow_log_list.append(twitter_follow_log['screen_name'])
twitter_follow_log['follow_at'] = now
twitter_follow_log_list.append(twitter_follow_log['follow_at'])
twitter_follow_log['follow_type'] = follow_type
twitter_follow_log_list.append(twitter_follow_log['follow_type'])
twitter_follow_log['follow_keyword'] = keyword
twitter_follow_log_list.append(twitter_follow_log['follow_keyword'])
sql = """
insert into mscolle.twitter_follow_log (id, follow_count, screen_name, follow_at, follow_type, follow_keyword)
values(%s,%s,%s,%s,%s,%s)
"""
cursor.execute(sql, twitter_follow_log_list)
connector.commit()

screen_name = 'Miss_owu_no5'
twitter_follow_log(screen_name)

#follow_countが、borderに達していたら、フォローの処理を飛ばす
def follow_border_skip(screen_name):
    #borderを定義
    border = 1
    #idをデータベースから出す。
    follow_count_select_sql = "select follow_count from twitter_follow_log where screen_name = %s"
    cursor.execute(follow_count_select_sql, screen_name)
    follow_count = fetchall()
    if border => follow_count:
        print("処理を飛ばします")
    else:
        continue

# # followerとfollowを定義
# followers = api.followers_ids(SCREEN_NAME)
# friends = api.friends_ids(SCREEN_NAME)

# # ****************************検索キーワードでフォロー&Fav***********************
# # 検索ワードと検索数をセット
# def search_follow():
#     follow_type = 1
# 	print("検索キーワードでフォローを開始します。")
# 	keywords = ["ミスオブミス","ミスコレ","ミスコン","@Mscolle_"]
# 	for keyword in keywords:
# 		count = 50
# 		# 検索実行。search_resultsにpost_idを保存
# 		search_results = api.search(q=keyword, count=count)
# 		# 結果をフォロー
# 		for result in search_results:
# 			screen_id = result.user._json["screen_name"]
# 			try:
# 				print(screen_id + 'をフォローしました')
# 				api.create_friendship(screen_id)
# 				time.sleep(2)
# 			# 結果をfav
# 				tweet_id = result.id #ツイートのstatusオブジェクトから、ツイートidを取得			
# 				try:
# 					api.create_favorite(tweet_id) #favする
# 				except Exception as e:
# 					print(e)
# 			except Exception as e:
# 				print(e)
# 	print("検索キーワードでフォローが終了しました。")


# ## ****************似たようなアカウントをフォローしている人をフォロー***************
# # 自分に似たようなアカウントを指定
# def similar_acount_followers_follow():
#     follow_type = 2
# 	print("指定アカウントのフォロワーのフォローを開始します。")
# 	accounts = ["MISSMRCOLLE","_sute2013081503","misscon_bot","UTsweetheart",]
# 	for account in accounts:
# 		count = 50
# 		account_followers = api.followers(id=account, count=count)

# 		# 自分に似たようなアカウントのフォロワーをフォロー
# 		for account_follower in account_followers:
# 			screen_id = account_follower._json["screen_name"]
# 			try:
# 				print(screen_id + 'をフォローしました')
# 				api.create_friendship(screen_id)
# 				time.sleep(2)

# 				#フォローした人の一番上の投稿をfav
# 				result = api.user_timeline(id=screen_id, count=1, exclude_replies=True, exclude_retweets=True)
# 				tweet_id = result[0].id
# 				try:
# 					api.create_favorite(tweet_id) #favする
# 				except Exception as e:
# 					print(e)	
# 			except Exception as e:
# 				print(e)
# 	print("指定アカウントのフォロワーのフォローが終了しました。")


# # *******************自分のツイートにfavしてくれている人をフォロー******************
# # 自分のツイートをfavしてくれている人のUSER_IDを取得
# def my_favoritters_follow():
#     follow_type = 3
# 	print("自分にfavしてくれている人のフォローを開始します。")
# 	count = 10
# 	my_tweets = api.user_timeline(count=count, id='MsContest_')
# 	for my_tweet in my_tweets:
# 		screen_id = my_tweet._json["id"]
# 		favoritters_id = get_favoritters(screen_id)

# 	#自分の投稿にfavしている人をfollow
# 		for favoritter_id in favoritters_id:
# 			try:
# 				api.create_friendship(favoritter_id)
# 				print(favoritter_id + 'をフォローしました')
# 				time.sleep(2)

# 				#フォローした人の一番上の投稿をfav
# 				result = api.user_timeline(id=favoritter_id, count=1, exclude_replies=True, exclude_retweets=True)
# 				tweet_id = result[0].id
# 				try:
# 					api.create_favorite(tweet_id) #favする
# 				except Exception as e:
# 					print(e)	
# 			except Exception as e:
# 				print(e)
# 	print("自分にfavしてくれている人のフォローが終了しました。")


# # *******************自分のツイートにRTしてくれている人をフォロー******************
# # 自分のツイートをRTしてくれている人のUSER_IDを取得
# def my_retweeters_follow():
#     follow_type = 4
# 	print("自分にRTしてくれている人のフォローを開始します。")
# 	count = 10
# 	my_tweets = api.user_timeline(count=count, id='MsContest_')

# 	for my_tweet in my_tweets:
# 		retweeters = api.retweets(id=my_tweet.id_str)
# 		for retweeter in retweeters:
# 			retweeter_id = retweeter.user.id
# 			#自分の投稿にRTしている人をfollow
# 			try:
# 				api.create_friendship(retweeter_id)
# 				print(retweeter.user.screen_name + 'をフォローしました')
# 				time.sleep(2)

# 				#RTした人の一番上の投稿をfav
# 				result = api.user_timeline(id=retweeter_id, count=1, exclude_replies=True, exclude_retweets=True)
# 				tweet_id = result[0].id
# 				try:
# 					api.create_favorite(tweet_id) #favする
# 				except Exception as e:
# 					print(e)	
# 			except Exception as e:
# 				print(e)
# 	print("自分にRTしてくれている人のフォローが終了しました。")


# ## *********************ミスコレの人にfavしている人をフォロー********************
# def mscolle_favoritters_follow():
#     follow_type = 5
# 	print("ミスコレ出場者にfavしてくれている人のフォローを開始します。")
# 	for twitter_id in twitter_ids:
# 		count = 10
# 		ms_tweets = api.user_timeline(count=count, screen_name=twitter_id)
# 		for ms_tweet in ms_tweets:
# 			screen_id = ms_tweet._json["id"]
# 			favoritters_id = get_favoritters(screen_id)

# 		#ミスコレの投稿にfavしている人をfollow
# 			for favoritter_id in favoritters_id:
# 				try:
# 					api.create_friendship(favoritter_id)
# 					print(favoritter_id + 'をフォローしました')
# 					time.sleep(2)

# 					#フォローした人の一番上の投稿をfav
# 					result = api.user_timeline(id=favoritter_id, count=1, exclude_replies=True, exclude_retweets=True)
# 					tweet_id = result[0].id
# 					try:
# 						api.create_favorite(tweet_id) #favする
# 					except Exception as e:
# 						print(e)	
# 				except Exception as e:
# 					print(e)
# 	print("ミスコレ出場者にfavしてくれている人のフォローが終了しました。")
    

# ## *********************ミスコレの人にRTしている人をフォロー*********************
# def mscolle_retweeters_follow():
#     follow_type = 6
# 	print("ミスコレ出場者にRTしてくれている人のフォローを開始します。")
# 	for twitter_id in twitter_ids:
# 		count = 10
# 		ms_tweets = api.user_timeline(count=count, screen_name=twitter_id)
# 		for ms_tweet in ms_tweets:
# 			retweeters = api.retweets(id=ms_tweet.id_str)
# 			for retweeter in retweeters:
# 				retweeter_id = retweeter.user.id
# 				#自分の投稿にRTしている人をfollow
# 				try:
# 					api.create_friendship(retweeter_id)
# 					print(retweeter.user.screen_name + 'をフォローしました')
# 					time.sleep(2)

# 					#RTした人の一番上の投稿をfav
# 					result = api.user_timeline(id=retweeter_id, count=1, exclude_replies=True, exclude_retweets=True)
# 					tweet_id = result[0].id
# 					try:
# 						api.create_favorite(tweet_id) #favする
# 					except Exception as e:
# 						print(e)	
# 				except Exception as e:
# 					print(e)
# 	print("ミスコレ出場者にRTしてくれている人のフォローが終了しました。")

# ## *********************自分の投稿の一番上のUserの投稿にfavしている人をフォロー********************

# ## *********************自分の投稿の一番上のUserの投稿にRTしている人をフォロー********************

# search_follow()
# similar_acount_followers_follow()
# my_favoritters_follow()
# my_retweeters_follow()
# mscolle_favoritters_follow()
# mscolle_retweeters_follow()
