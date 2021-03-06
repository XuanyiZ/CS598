from flask import Flask, abort, request, jsonify, render_template, redirect, url_for, session
import pymongo
import json, re

# import libraries
import urllib2
from urllib2 import urlopen
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route("/index", methods=["GET", "POST"])
@app.route('/', methods=["GET", "POST"])
def index():
	if request.method == 'GET':
		return render_template("index.html")
	else:
		if request.form['submit_btn'] == 'Register':
			newName = request.form['newUserName']
			newEmail = request.form['newUserEmail']
			newPass = request.form['newUserPass']
			addNewUserAccount(newName, newPass)

			return redirect(url_for('index'))
		else:
			userName = request.form['username']
			password = request.form['password']
			userInfo = users.find_one({"userName":userName})
			foundPassword = userInfo["password"]
		
			if str(foundPassword) == password:
				session['userName'] = userName
				return redirect(url_for('profile', userName=userName))

			return redirect(url_for('index'))


def addNewUserAccount(username,password):
	newUserAccount = {"userName":username, "password":password, "foodTags": [], "languageTags":[], "hobbyTags":[] }
	users.insert_one(newUserAccount)
	return


#a user send a new response to a post
def addNewResponseToPost(postId, responseUserName, sentMsg):
	# print(postId)
	# print(responseUserName)
	# print(sentMsg)
	responses = posts.find_one({"id": postId})["respondedPeople"]
	# print(responses)
	if responseUserName not in responses:
		responses[responseUserName] = sentMsg

	# print(responses)
	posts.find_one_and_update({"id":postId}, {'$set':{"respondedPeople": responses}})
	receiver = postId.split(" ")[0]
	# print(receiver)
	newResponse = {"respondPeople": responseUserName, "respondMessage": sentMsg, "postID":postId, "receiver":receiver}
	responds.insert_one(newResponse)

	return


def findAllRestaurantsPosts(RestaurantName):
	cursor = posts.find({"restaurant": RestaurantName})
	restaurantPosts = []
	for post in cursor:
		restaurantPosts.append(post)
	return restaurantPosts


@app.route("/getAllRestaurantsInfo", methods=["GET"])
#get all resturants Infomation
def getAllRestaurantsInfo():
	RestaurantsInfo = Restaurants.find({})
	return jsonify(list(RestaurantsInfo))


def scrape(rss_link):
	soup = BeautifulSoup(urlopen(rss_link))
	reviews = soup.find_all("item")
	ret = {}
	for each in reviews:
		tmp = each.find("title").text
		restaurant_name = re.split("\(", tmp)[0].rstrip()
		t = re.split("\(", tmp)[1].split(')')[0]
		rating = t.split('/')[0]
		ret[restaurant_name] = int(rating)


	return ret


@app.route("/inbox", methods=["GET","POST"])
def populate_inbox_msgtable():
	if request.method == 'GET':
		session_userName = session['userName'] 
		print session_userName
		InboxMsgs = responds.find({"receiver": session_userName})
		SenderList = {}
		IDList = {}
		print InboxMsgs
		for record in InboxMsgs:
			name = record["respondPeople"]
			message = record["respondMessage"]
			postid = record['postID']
			SenderList[name] = message
			IDList[name] = postid

		return render_template("inbox.html", SenderList=SenderList, IDList=IDList)
	else:
		name = request.form["sender"]
		



@app.route("/restaurants", methods=["GET","POST"])
def restaurants():
	
	RestaurantsInfo = restaurants.find({})
	if request.method == 'GET':
		return render_template("main.html", RestaurantsInfo=RestaurantsInfo)
	else:
		rss_link = request.form["rss"]
		ret = scrape(rss_link)
		print ret
		return render_template("main.html", RestaurantsInfo=RestaurantsInfo, reviews=ret)



@app.route("/restaurant_detail/<string:RestaurantName>", methods=["GET", "POST"])
def restaurant_detail(RestaurantName):
	RestaurantInfo = restaurants.find_one({"name": RestaurantName})
	# cursor = posts.find({"restaurant": RestaurantName})
	# restaurantPosts = []
	# for post in cursor:
	# 	restaurantPosts.append(post)
	
	if request.method == 'GET':
		#store current restaurant in session
		session['currRestaurant'] = RestaurantName

		# cursor = posts.find({"restaurant": RestaurantName})
		# restaurantPosts = []
		# for post in cursor:
		# 	restaurantPosts.append(post)
		# print(RestaurantInfo)
		restaurantPosts = findAllRestaurantsPosts(RestaurantName)
		return render_template("restaurant_info.html", RestaurantInfo=RestaurantInfo, posts=restaurantPosts)

	else:
		if request.form['submit_btn'] == "add new post":
			postUserName = session['userName']
			thisRestaurant = session['currRestaurant']
			time = request.form['postTime']

			newID = postUserName + " " + thisRestaurant + " " + time
			newPost = {"sender":postUserName, "restaurant": thisRestaurant, "time":time, "respondedPeople":{}, "id": newID}
			posts.insert_one(newPost)

			#search posts related to current restaurant after inserting a new post
			# cursor = posts.find({"restaurant": thisRestaurant})
			# restaurantPosts = []
			# for post in cursor:
			# 	restaurantPosts.append(post)
			restaurantPosts = findAllRestaurantsPosts(thisRestaurant)

			return render_template("restaurant_info.html", RestaurantInfo=RestaurantInfo, posts=restaurantPosts)

		elif request.form['submit_btn'] == "add new response":
				selectedPost = request.form['person']
				# print(selectedPost)
				valueOfSelectedPost = selectedPost.split(" ")
				postUser, postTime = valueOfSelectedPost[0], valueOfSelectedPost[1]

				thisRestaurant = session['currRestaurant']

				postID = postUser + " " + thisRestaurant + " " + postTime
				responseUserName = session['userName']
				sentMsg = request.form['responseMessage']
				# print(postID, responseUserName, sentMsg)

				# cursor = posts.find({"restaurant": RestaurantName})
				# restaurantPosts = []
				# for post in cursor:
				# 	restaurantPosts.append(post)
				restaurantPosts = findAllRestaurantsPosts(RestaurantName)
				addNewResponseToPost(postID, responseUserName, sentMsg)

				return render_template("restaurant_info.html", RestaurantInfo=RestaurantInfo, posts=restaurantPosts)





@app.route("/profile/<string:userName>", methods=["GET"])
def profile(userName):
	return render_template("profile.html", userName=userName)


@app.route("/preferences/<string:userName>", methods=["GET", "POST"])
def preferences(userName):
	if request.method == 'GET':
		userInfo = users.find_one({"userName":userName})
		foodPrefs = userInfo["foodTags"]
		languagePrefs = userInfo["languageTags"]
		hobbyPrefs = userInfo["hobbyTags"]

		preferenceList = {'food': foodPrefs, 'language': languagePrefs, 'hobby': hobbyPrefs}
		return render_template("preferences.html", preferenceList = preferenceList, userName = userName)
	else:
		if request.form['submit_btn'] == 'add a food' and request.form['new_food'] is not None:
			food = request.form['new_food']
			print food
			userInfo = users.find_one({"userName":userName})
			foodPrefs = userInfo["foodTags"]
			print foodPrefs
			foodPrefs.append(food)
			users.find_one_and_update({"userName":userName}, 
										 {'$set': {"foodTags":foodPrefs}})
			return redirect(url_for('preferences', userName = userName))
			
		elif request.form['submit_btn'] == 'add a language' and request.form['new_lan'] is not None:
			lan = request.form['new_lan']
			userInfo = users.find_one({"userName":userName})
			languagePrefs = userInfo["languageTags"]
			languagePrefs.append(lan)
			users.find_one_and_update({"userName":userName}, 
										 {'$set': {"languageTags":languagePrefs}})
			return redirect(url_for('preferences', userName = userName))
		
		elif request.form['submit_btn'] == 'add a hobby' and request.form['new_hobby'] is not None:
			hobby = request.form['new_hobby']
			userInfo = users.find_one({"userName":userName})
			hobbyPrefs = userInfo["hobbyTags"]

			hobbyPrefs.append(hobby)
			users.find_one_and_update({"userName":userName}, 
										 {'$set': {"hobbyTags":hobbyPrefs}})
			return redirect(url_for('preferences', userName = userName))


@app.route("/preferences_public/<string:userName>", methods=["GET"])
def preference_read_only(userName):
	
	if request.method == 'GET':
		userInfo = users.find_one({"userName":userName})
		foodPrefs = userInfo["foodTags"]
		languagePrefs = userInfo["languageTags"]
		hobbyPrefs = userInfo["hobbyTags"]

		preferenceList = {'food': foodPrefs, 'language': languagePrefs, 'hobby': hobbyPrefs}
		return render_template("public_preference.html", preferenceList = preferenceList, userName = userName)


@app.route("/messages", methods=["GET", "POST"])
def messages():
	return render_template("user_profile_msgbox.html")


# @app.route("/messages", methods=["GET", "POST"])
# #a user send a new response to a post
# def addNewResponseToPost(postId, responseUserName, sentMsg):
# 	responses = posts.find_one({"id": postId})["respondedPeople"]
# 	if responseUserName not in responses:
# 		responses[responseUserName] = sentMsg

# 	posts.find_one_and_update({"id":postId}, {'$set':{"respondedPeople": responses}})
# 	newResponse = {"respondPeople": responseUserName, "respondMessage": sentMsg, "postID":postId}
# 	responds.insert_one(newResponse)

# 	return


# @app.route("/messages", methods=["GET", "POST"])
# def addNewPost(restaurantName, postUserName, time):
# 	newID = postUserName + " " + restaurantName + " " + time
# 	newPost = {"sender":postUserName, "restaurant":restaurantName, "time":time, "respondedPeople":[], "id": newID}
# 	posts.insert_one(newPost)
# 	return 


if __name__ == '__main__':
	client = pymongo.MongoClient('mongodb://localhost:27017/')
	db = client["local"]

	restaurants = db["restaurants"]
	users = db["users"]
	posts = db["posts"]
	responds = db["responds"]

	app.run(debug = True)
  
