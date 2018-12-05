######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
#import flask.ext.login as flask_login
import flask_login
#for image uploading
from werkzeug import secure_filename
import os, base64
import time

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'winter12' #CHANGE THIS TO YOUR MYSQL PASSWORD
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register/", methods=['GET'])
def register():
	return render_template('improved_register.html', supress='True')  

@app.route("/register/", methods=['POST'])
def register_user():
	try:
		fname= request.form.get('fname')
		lname=request.form.get('lname')
		email=request.form.get('email')
		if request.form.get("dob"):
			print "HERE"
			dob=request.form.get("dob")
			print dob
		else: 
			dob = None
		if request.form.get("picture"):
			picture = request.form.get("picture")
		else: 
			picture = None
		if request.form.get("bio"):
			bio = request.form.get("bio")
		else: 
			bio = None
		if request.form.get("gender"):
			gender = request.form.get("gender")
		else:
			gender = None
		if request.form.get("hometown"):
			hometown = request.form.get("hometown")
		else:
			hometown = None
		password=request.form.get('password')
	except Exception as E:
		print E
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		gender = 'female'
		print cursor.execute("INSERT INTO Users (fname, lname, email, dob, picture, bio, gender, hometown, password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}','{7}','{8}')".format(fname, lname, email, dob, picture, bio, gender, hometown, password))
		conn.commit()
		cursor = conn.cursor
		cursor.execute("INSERT INTO Profile_Pictures (imgdata) VALUES ('{0})".format(picture))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption, album_id FROM Pictures WHERE user_id = '{0}'".format(user_id))
	return cursor.fetchall() 

def get_prof(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata FROM Pictures WHERE user_id = '{0}'".format(user_id))
	return cursor.fetchall() 

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('profile.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		tags = str(request.form.get('tags')).split(' ')
		##get Albums name from user and then get the Albums id from the Albums name 
		album_name= request.form.get('album_name')
		album_id = getAlbumIdFromName(album_name)
		print caption
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption,album_id) VALUES ('{0}', '{1}', '{2}' ,'{3}')".format(photo_data,user_id, caption,album_id))
		conn.commit()
		photo_id = cursor.lastrowid
		addPhotoTags(tags, photo_id)
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(user_id) )
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')

@app.route('/upload_prof', methods=['GET', 'POST'])
@flask_login.login_required
def upload_prof_file():
	if request.method == 'POST':
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Profile_Pictures (imgdata, user_id) VALUES ('{0}', '{1}')".format(photo_data,user_id))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!' )
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload_prof.html')
#end photo uploading code 

def printInfo ():
	cursor = conn.cursor()
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	cursor.execute("SELECT * from Users where user_id='{0}'".format(user_id))
	cursor.commit

def addPhotoTags(tags, picture_id):
	cursor = conn.cursor()
	for i in tags:
		cursor.execute("INSERT INTO Tags (word, picture_id) VALUES ('{0}', '{1}')".format(i, picture_id))
	conn.commit()

##Code for album/picture interactions 
@app.route('/create_album', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		##get user_id 
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		if request.form.get('album_name'):
			album_name = request.form.get('album_name')
		else: 
			album_name = "Unnamed Album"
		print(album_name)
		##check to to see if Albums name is unique 
		if isAlbumNameUnique(album_name):
			cursor = conn.cursor()
			date = time.strftime("%Y-%m-%d")
			cursor.execute("INSERT INTO Albums (album_name, user_id, doc) VALUES('{0}', '{1}', '{2}')".format(album_name,user_id,date))
			conn.commit()
			return render_template('profile.html', name=getFirstName(user_id), message='Albums Created!!', albums=get_users_albums(user_id))
		else:
			return render_template('create_album.html', message="Already Chosen! Pick a new Albums name!")
	else:
		return render_template('create_album.html')

def getFirstName(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT fname FROM Users WHERE user_id ='{0}'".format(user_id))
	return cursor.fetchall()[0][0]

def isAlbumNameUnique(album_name):
	cursor = conn.cursor()
	if cursor.execute("SELECT album_name FROM Albums WHERE album_name = '{0}'".format(album_name)): 
		return False
	else:
		return True

def get_users_albums(user_id): 
	cursor = conn.cursor()
	cursor.execute("SELECT album_name, doc FROM Albums WHERE user_id='{0}'".format(user_id))
	return cursor.fetchall()

#page to view albums 
@app.route('/albums', methods=['GET', 'POST'])
def albums():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	##set up empty array to put the photos in the Albums 
	pictures_tag_comment = []
	if request.method == 'POST':
		album_id = request.form.get('album_id')
		album_name = request.form["album_name"]
		## get all the photos adn then for each photo, get the tags and comments 
		for i in get_photos_from_album(album_id, user_id):
			pictures_tag_comment += [getTagsAndComments(i)]
		return render_template("all_photos.html", photos=pictures_tag_comment, album_name=album_name)
	else:
		return render_template("albums.html", albums=show_albums(user_id))

def show_albums(user_id): 
	cursor = conn.cursor()
	cursor.execute("SELECT album_name, album_id, doc FROM Albums WHERE user_id = '{0}'".format(user_id))
	return cursor.fetchall()

def get_photos_from_album(album_id, user_id): 
	cursor = conn.cursor()
	##used P and A so i didnt have to write pictures and albums multiple times 
	query = "SELECT P.imgdata, P.picture_id, P.caption, A.album_name FROM Pictures P, Albums A WHERE A.album_id = P.album_id AND A.album_id = '{0}' AND A.user_id = '{1}'"
	cursor.execute(query.format(album_id, user_id)) ##format it in the form Albums id then user id 
	return cursor.fetchall()

def getTagsAndComments(photo):
	return [photo] + [getTags(photo[1])] + [getComments(photo[1])] + [getLikes(photo[1])] + [getUsersLiked(photo[1])]

def getComments(picture_id): 
	cursor = conn.cursor()
	cursor.execute("SELECT description FROM Comment WHERE picture_id = '{0}'".format(picture_id))
	return cursor.fetchall()

def getTags(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT word FROM Tags WHERE picture_id = '{0}'".format(picture_id))
	return cursor.fetchall()

def getLikes(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(picture_id) FROM Likes WHERE picture_id ='{0}'".format(picture_id))
	return cursor.fetchall()

def getUsersLiked(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT U.fname, U.lname FROM Likes L, Users U WHERE U.user_id = L.user_id AND L.picture_id = '{0}'".format(picture_id))
	return cursor.fetchall()

## albums are created and can be viewed -- with all helper functions 

def delete_album(): 
	cursor = conn.cursor()
	pictures_in_Albums = get_photos_from_album() 
	for pic in pictures_in_album():
		deletePhoto(pic[1])
	cursor.execute("DELETE FROM Albums WHERE album_id='{0}'".format(album_id))
	cursor.commit()

def deletePhoto(picture_id):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Comment WHERE picture_id='{0}'".format(picture_id))
	conn.commit()
	cursor.execute("DELETE FROM Tags WHERE picture_id='{0}'".format(picture_id))
	conn.commit()
	cursor.execute("DELETE FROM Pictures WHERE picture_id='{0}'".format(picture_id))
	conn.commit()

## can also delete albums and photos 

def getAlbumIdFromName(album_name):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id FROM Albums WHERE album_name = '{0}'".format(album_name))
	return cursor.fetchone()[0]


##Friends and stuff 

@app.route('/friends', methods=['GET', 'POST'])
@flask_login.login_required
def friends():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	friends = getFriends(user_id)
	friends_names = []
	for i in friends:
		friends_names += [getUserName(i)]
	if request.method == 'POST':
		fname = request.form.get('fname')
		lname = request.form.get('lname')
		print friends_names
		if searchUsers(fname, lname):
			return render_template('friends.html', friends=friends_names, users_search=searchUsers(fname,lname))
		else:
 			return render_template('friends.html', friends=friends_names, message="No users with that name! Try again!")
 	else:
 		return render_template('friends.html', friends=friends_names)

def getFriends(user_id):
 	cursor = conn.cursor()
 	cursor.execute("SELECT friend_id FROM Friends WHERE user_id = '{0}'".format(user_id))
 	return cursor.fetchall()

def getUserName(user_id):
	user_id = user_id[0]
	cursor = conn.cursor()
	cursor.execute("SELECT fname, lname FROM Users where user_id = '{0}'".format(user_id))
	return cursor.fetchall()

def searchUsers(fname='', lname=''):
	cursor = conn.cursor()
	fname=str(fname)
	lname=str(lname)
	##3 different cases that can happen 
	if fname != '' and (lname == ''):
		cursor.execute("SELECT fname, lname, dob, email, user_id FROM Users WHERE fname ='{0}'".format(fname))
	elif lname != '' and (fname == ''):
		cursor.execute("SELECT fname, lname, dob, email, user_id FROM Users WHERE lname ='{0}'".format(lname))
	else:
		cursor.execute("SELECT fname, lname, dob, email, user_id FROM Users WHERE fname = '{0}' AND lname ='{1}'".format(fname, lname))
	return cursor.fetchall()

@app.route('/add_friends', methods=['GET','POST'])
@flask_login.login_required
def friendsAdd():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	friends_names = []
	if request.method == 'POST':
		email = request.form.get('search_email')
		print email 
		friend_id = getUserIdFromEmail(email)
		if addFriend(friend_id) == True:
			friends = getFriends(user_id)
			for i in friends:
				friends_names += [getUserName(i)]
			return render_template('friends.html', friends=friends_names, message="Friend Added!")
		else:
			friends = getFriends(user_id)
			for i in friends:
				friends_names += [getUserName(i)]
			return render_template('friends.html', friends=friends_names, message="Please pick a valid email. Not found.")
	else:
		return render_template('add_friends.html')

def addFriend(friend_id):
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	if cursor.execute("SELECT user_id FROM Users WHERE user_id='{0}'".format(friend_id)):
		cursor.execute("INSERT INTO Friends (user_id, friend_id) VALUES ('{0}', '{1}')".format(user_id, friend_id))
		conn.commit()
		print("Friend added!")
		return True
	else:
		return False

def findTopUsers():
	cursor = conn.cursor()
	## count the pictures
	pictures_query = "SELECT user_id, count(picture_id) AS count FROM Pictures GROUP BY user_id"
	## count the comments 
	comments_query = "SELECT user_id, count(comment_id) AS count FROM Comment WHERE user_id != -1 GROUP BY user_id"
	## sum and put in order 
	sum_query = "SELECT U.fname, U.lname FROM Users U, (SELECT user_id, SUM(count) as count FROM (" + pictures_query + " UNION " + comments_query + " ) AS Temp WHERE user_id != -1 GROUP BY user_id) AS user_id_counts WHERE U.user_id = user_id_counts.user_id ORDER BY user_id_counts.count DESC LIMIT 10"
	cursor.execute(sum_query)
	print(sum_query)
	return cursor.fetchall()

##code that follows is for creating/uploading/dealing with photos 

@app.route("/all_photos", methods=["POST", "GET"])
@flask_login.login_required
def myPictures():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	pics = []
	for i in getUsersPhotos(user_id):
		pics += [getTagsAndComments(i)]
	return render_template("all_photos.html", photos=pics)

def showPix():
	if flask_login.current_user.is_authenticated():
		user_id = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		if request.form.get("comment"):
			comment = request.form.get("comment")
			picture_id = request.form.get("picture_id")
			if flask_login.current_user.is_authenticated():
				if (isCommentValid(picture_id, user_id)):
					comment_id = addComment(comment, user_id)
				else:
					return render_template("all_photos.html", photos=displayAllPicturesWithCommentsAndTags(), message="All photos. You cannot comment on your own photo.")
			else:
				comment_id = addComment(comment, -1)
				addCommentToPhoto(comment_id, picture_id)
			return render_template("all_photos.html", photos=displayAllPicturesWithCommentsAndTags(), message="All photos. Comment added!")
		elif request.form["photo_delete"]:
			picture_id = request.form.get("picture_id")
			if flask_login.current_user.is_authenticated():
				if currentUserOwnsPhoto(user_id, picture_id):
					deletePhoto(picture_id)
					return render_template("all_photos.html", photos=displayAllPicturesWithCommentsAndTags(), message="Photo Deleted!")
				else:
					return render_template("all_photos.html", photos = displayAllPicturesWithCommentsAndTags(), message="You do not have permission to delete this photo.")
			else:
				return render_template("all_photos.html", photos = displayAllPicturesWithCommentsAndTags(), message="You do not have permission to delete this photo.")
		else:
			return render_template("all_photos.html", photos=displayAllPicturesWithCommentsAndTags(), message="All photos")
	else:
		return render_template("all_photos.html", photos=displayAllPicturesWithCommentsAndTags(), message="All photos")


def addComment(comment, user_id):
	date = time.strftime("%Y-%m-%d")
	print(date)
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Comment(description, user_id, doc) VALUES ('{0}', '{1}', '{2}')".format(comment, user_id, date))
	conn.commit()
	comment_id = cursor.lastrowid
	return comment_id

def addCommentToPhoto(comment_id, picture_id):
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Comments_on_pictures (comment_id, picture_id) VALUES('{0}', '{1}')".format(comment_id, picture_id))
	conn.commit()

def isCommentValid(picture_id, user_id):
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM Pictures WHERE picture_id = '{0}' AND user_id='{1}'".format(picture_id, user_id)):
		return False
	else:
		return True

def displayAllPicturesWithCommentsAndTags():
	pix_with_tags_and_comments = []
	for i in getAllPhotos():
		pix_with_tags_and_comments += [getTagsAndComments(i)]
	return pix_with_tags_and_comments

def addTags(tags, picture_id):
	cursor = conn.cursor()
	for i in tags:
		cursor.execute("INSERT INTO Tags (word, picture_id) VALUES ('{0}', '{1}')".format(i, picture_id))
	conn.commit()


@app.route('/my_tag_search', methods=["POST", "GET"])
@flask_login.login_required
def searchMyTags():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	pix_with_tags_and_comments = []
	pix = []
	for i in getUsersPhotos(user_id):
		pix += [getTagsAndComments(i)]
	if request.method == "POST":
		tag = request.form.get('tag_name')
		for i in getUserTaggedPhotos(tag, user_id):
			pix_with_tags_and_comments += [getTagsAndComments(i)]
		if pix_with_tags_and_comments:
			return render_template("all_photos.html", photos=pix_with_tags_and_comments)
		else:
			return render_template("all_photos.html", message="Sorry, there is no tag with that name. Try again!")
	else:
		return render_template("all_photos.html", photos=pix)


def getUserTaggedPhotos(tag, user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption, A.album_name FROM Pictures P, Albums A, Tags T WHERE T.picture_id = P.picture_id AND P.album_id = A.album_id AND T.word = '{0}' AND P.user_id ='{1}'".format(tag, user_id))
	return cursor.fetchall()

@app.route('/tag_search', methods=["POST", "GET"])
def searchAllTags():
	pix_with_tags_and_comments = []
	if request.method == "POST":
		if(request.form.get('tag_search')):
			tags = request.form.get('tag_search').split(" ")
			for i in getAllTaggedPhotos(tags):
				pix_with_tags_and_comments += [getTagsAndComments(i)]
		else:
			tag = request.form['common_tag']
			for i in getTaggedPhotos(tag):
				pix_with_tags_and_comments += [getTagsAndComments(i)]
		if pix_with_tags_and_comments:
			return render_template("all_photos.html", photos=pix_with_tags_and_comments)
		else:
			return render_template("tags.html", common=getMostCommonTags(), message="Sorry, none, try again!")
	else:
		return render_template("tags.html", common=getMostCommonTags())

def getMostCommonTags():
	cursor = conn.cursor()
	cursor.execute("SELECT word, COUNT(word) FROM Tags GROUP BY word ORDER BY COUNT(word) DESC LIMIT 5")
	return cursor.fetchall()


def getAllTaggedPhotos(tags):
	cursor = conn.cursor()
	if len(tags) == 1:
		return getTaggedPhotos(tags[0])
	else:
		pics = getTaggedPhotos(tags[0])
		for i in pics:
			cursor.execute(getTagQuery(tags))
		return cursor.fetchall()

def getTaggedPhotos(tag):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption, A.album_name FROM Pictures P, Albums A, Tags T WHERE T.picture_id = P.picture_id AND P.album_id = A.album_id AND T.word = '{0}'".format(tag))
	return cursor.fetchall()

def getTagQuery(tags):
	query = "SELECT P.imgdata, P.picture_id, P.caption, A.album_name FROM Pictures P, Albums A, Tags T WHERE T.picture_id = P.picture_id AND P.album_id = A.album_id AND T.word = '{0}'".format(tags[0])
	for i in range(1, len(tags)):
		query += " AND P.picture_id IN (SELECT P.picture_id  FROM Pictures P, Albums A, Tags T WHERE T.picture_id = P.picture_id AND P.album_id = A.album_id AND T.word = '{0}')".format(tags[i])
	print(query)
	return query

@app.route("/recommend_tags", methods=["GET", "POST"])
@flask_login.login_required
def recommend():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == "POST":
		tags = request.form.get("recommend_tags").split(" ")
		recommended_tags = getRecommendedTags(tags, user_id)
		return render_template("profile.html", tags=recommended_tags)
	else:
		return render_template("profile.html", message="Sorry, try again")

def getRecommendedTags(tags, user_id):
	cursor = conn.cursor()
	query = "SELECT T.word, Count(T.word) as tcount FROM Tags T, ("
	for i in tags:
			query += "SELECT P.picture_id, T.word FROM Pictures P, Albums A, Tags T WHERE T.picture_id = P.picture_id AND P.album_id = A.album_id AND T.word = '{0}'".format(i)
			query += " UNION "
	query = query[:-7] +  ") as Tags WHERE Tags.picture_id = T.picture_id"
	for i in tags:
		query += " AND T.word != '{0}'".format(i)
		query += "GROUP BY T.word ORDER BY tcount DESC"
	cursor.execute(query)
	return cursor.fetchall()

def commonTagsPhotoSearch(tags, user_id):
	cursor = conn.cursor()
	query = "SELECT Tags.picture_id, Count(Tags.picture_id) as Pcount FROM ("
		for i in tags:
			query += "SELECT P.picture_id, T.word, P.user_id FROM Pictures P, Tags T WHERE T.picture_id = P.picture_id AND T.word = '{0}'".format(i)
			query += " UNION "
		query = query[:-7] +  ") as Tags WHERE Tags.user_id != '{0}' GROUP BY Tags.picture_id ORDER BY Pcount DESC".format(user_id)
	cursor.execute(query)
	suggested_photos_id = cursor.fetchall()
	suggested_photos = []
	for i in suggested_photos_id:
		suggested_photos += getPhotoFromPhotoId(i[0])
	return suggested_photos
def getYouMayAlsoLike(user_id):
	cursor = conn.cursor()
	common_tags = getCommonTags(user_id)
	lst = []
	for i in common_tags:
		lst += [i[0]]
	pics = commonTagsPhotoSearch(lst, user_id)
	return pics

def getPhotoFromPhotoId(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption, A.album_name FROM Pictures P, Albums A WHERE P.album_id = A.album_id and P.picture_id = '{0}'".format(picture_id))
	return cursor.fetchall()

def getCommonTags(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT T.word, Count(T.picture_id) FROM Tags T, Pictures P WHERE P.picture_id = T.picture_id AND P.user_id = '{0}' GROUP BY word ORDER BY Count(T.picture_id) DESC LIMIT 5".format(user_id))
	return cursor.fetchall()

@app.route("/you_may_also_like")
@flask_login.login_required
def youMayLike():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	pix_with_tags_and_comments = []
	pics = getYouMayAlsoLike(user_id)
	for i in pics: 
		pix_with_tags_and_comments += [getTagsAndComments(i)]
	return render_template("all_photos.html", message="You may also like", photos=pix_with_tags_and_comments)

def getYouMayAlsoLike(uid):
	cursor = conn.cursor()
	common_tags = getCommonTags(uid)
	lst = []
	for i in common_tags:
		lst += [i[0]]
	pics = commonTagsPhotoSearch(lst, uid)
	return pics

#default page  
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
