 CREATE DATABASE photoshare;
USE photoshare;

CREATE TABLE Users (
    user_id int4  NOT NULL AUTO_INCREMENT,
    fname varchar(255) NOT NULL, 
    lname varchar(255) NOT NULL, 
    email varchar(255) NOT NULL UNIQUE,
    dob DATE NOT NULL ,  
    bio text, 
    picture longblob, 
    gender ENUM('female', 'male', ''), 
    hometown varchar(255), 
    password varchar(255) NOT NULL,
    CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Albums
(
  album_id int4  AUTO_INCREMENT,
  user_id int4,
  album_name varchar(255) NOT NULL, 
  doc date NOT NULL, 
  caption varchar(255),
  CONSTRAINT albums_pk PRIMARY KEY (album_id),
  CONSTRAINT albums_fk FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  album_id int4, 
  imgdata longblob ,
  caption VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  CONSTRAINT pictures_fk FOREIGN KEY (album_id) REFERENCES Albums(album_id)
);

CREATE TABLE Profile_Pictures
(
	profile_picture_id int4 AUTO_INCREMENT,
	user_id int4 NOT NULL,
	imgdata longblob NOT NULL,
	CONSTRAINT profile_pk PRIMARY KEY (profile_picture_id),
	CONSTRAINT profile_fk FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Friends
(
	user_id int4,
	friend_id int4, 
	CONSTRAINT friends_fk1 FOREIGN KEY (user_id) REFERENCES Users(user_id),
	CONSTRAINT friends_fk2 FOREIGN KEY (friend_id) REFERENCES Users(user_id),
	CONSTRAINT friends_pk PRIMARY KEY (user_id,friend_id)
);

CREATE TABLE Tags
(
	word varchar(255) NOT NULL, 
	picture_id int NOT NULL,
	CONSTRAINT tags_fk FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);

CREATE TABLE Comment
(
	comment_id int4 NOT NULL AUTO_INCREMENT, 
	description varchar(500),
	user_id int4,
	doc DATE,
	picture_id int4,
	CONSTRAINT comment_pk PRIMARY KEY (comment_id),
	CONSTRAINT comments_fk1 FOREIGN KEY (user_id) REFERENCES Users(user_id),
	CONSTRAINT comments_fk2 FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);

CREATE TABLE Comments_on_pictures
(
	comment_id int4,
	picture_id int4,
	CONSTRAINT comments_on_pictures_pk PRIMARY KEY (comment_id,picture_id),
	CONSTRAINT comments_on_pictures_fk1 FOREIGN KEY (comment_id) REFERENCES Comment(comment_id),
	CONSTRAINT comments_on_pictures_fk2 FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);

CREATE TABLE Likes 
(
	picture_id int, 
	user_id int, 
	CONSTRAINT likes_pk PRIMARY KEY (picture_id),
	CONSTRAINT likes_fk1 FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id),
	CONSTRAINT likes_fk2 FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
