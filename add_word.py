#coding:utf-8

import requests
import time
import json
import re
import sys


class AddShanbayWord:
	def __init__(self,username,password,book_url,unit_name_list,unit_url,file_name):
		self.username = username
		self.password = password
		self.book_url = book_url
		self.unit_name_list = unit_name_list
		self.unit_url = unit_url
		self.file_name = file_name
	def login(self):
		login_url = "https://www.shanbay.com/accounts/login/"
		cookie = {}
		cookie["csrftoken"] = "uU5l2VcTSvAfidMAc04SxJFLqGK4gf1k"
		payload = {}
		payload["csrfmiddlewaretoken"] = "uU5l2VcTSvAfidMAc04SxJFLqGK4gf1k"
		payload["username"] = self.username
		payload["password"] = self.password

		r = requests.post(login_url,data = payload,cookies = cookie,allow_redirects = False)

		if r.status_code == 302:
			print "login success"
			return r.cookies
		else:
			print "login error"
			return None
	def get_deformation(self,s):
		defor_array = []
		if s[-2:] == "ed":
			defor_array.append(s[:-2])
			defor_array.append(s[:-1])
		elif s[-3:] == "ing":
			defor_array.append(s[:-3])
			defor_array.append(s[:-3] + "e")
		elif s[-1:] == "s":
			defor_array.append(s[:-1])
		elif s[-2:] == "es":
			defor_array.append(s[:-2])
		return defor_array

	def add_word(self,cookie,uid,word):
		add_url = "https://www.shanbay.com/api/v1/wordlist/vocabulary/"
		payload = {}
		payload["id"] = uid
		payload["word"] = word

		r = requests.post(add_url,data = payload,cookies = cookie)

		j = json.loads(r.content)
		if j["status_code"] == 0:
			print word,u"添加成功"
			r.close()
		elif j["status_code"] == 1:
			print word,u"添加失败由于: " + j["msg"]
			if u"上限" in j["msg"]:
				return True
		elif j["status_code"] == 404:
			print word,u"添加失败由于: " + j["msg"]
			defor_array = self.get_deformation(word)
			for i in defor_array:
				#self.add_word(cookie,uid,i)
				payload["word"] = i
				r = requests.post(add_url,data = payload,cookies = cookie)
				j = json.loads(r.content)
				if j["status_code"] == 0:
					print "   ",i,u"尝试添加成功"
				elif u"上限" in j["msg"]:
					print "   ",i,u"尝试添加失败由于: " + j["msg"]
					return True
				else:
					print "   ",i,u"尝试添加失败由于: " + j["msg"]
				time.sleep(0.1)
			r.close()
		return False
	def add_word_unit(self,cookie,book_id,unit_name):
		unit_url = "https://www.shanbay.com/api/v1/wordbook/wordlist/"
		payload = {}
		payload["name"] = unit_name
		payload["description"] = "+"
		payload["wordbook_id"] = book_id
		r = requests.post(unit_url,data = payload,cookies = cookie)
		if r.status_code != 200:
			print u"添加单词单元%s错误" %unit_name
			print r.status_code
			exit(-1)
		j = json.loads(r.content)
		if j["status_code"] == 0:
			print u"添加单元%s成功" % unit_name
			print u"\n------------------%s---------------\n" % unit_name
			return j["data"]["wordlist"]["id"]
		else:
			return None
	def start_add(self):
		cookie = self.login()
		if cookie is None:
			exit(-1)
		word_text = open(self.file_name).read()
		r = re.compile("[a-zA-Z]+")
		word_list = r.findall(word_text)
		book_id = self.book_url.split("/")[-2]
		if self.unit_url:
			uid = self.unit_url.split("/")[-2]
			self.add_word_to_oneunit(cookie,uid,word_list,0)
		elif self.unit_name_list:
			index = 0
			for lname in self.unit_name_list:
				uid = self.add_word_unit(cookie,book_id,lname)
				index = self.add_word_to_oneunit(cookie,uid,word_list,index)
		else:
			unit_num = 1
			index = 0
			while 1:
				uid = self.add_word_unit(cookie,book_id,str(unit_num))
				index = self.add_word_to_oneunit(cookie,uid,word_list,index)
				if index == len(word_list) - 1:
					break
				unit_num += 1

	def add_word_to_oneunit(self,cookie,uid,word_list,index):
		for i in xrange(index,len(word_list)):
			print str(i) + ".",
			out_range = self.add_word(cookie,uid,word_list[i])
			if out_range:
				return i

def main():
	try:
		j = json.load(open("config.json"))
	except Exception,e:
		print "load config error:",e
		exit(-1)
	username = j["username"]
	password = j["password"]
	book_url = j["bookurl"]
	unit_name = j["unitname"]

	if len(sys.argv) == 3:
		a = AddShanbayWord(username,password,book_url,[],sys.argv[1],sys.argv[2])
		a.start_add()
	elif len(sys.argv) == 2:
		a = AddShanbayWord(username,password,book_url,unit_name,"",sys.argv[1])
		a.start_add()
	else:
		print u"命令行参数不正确。"
		print u"请按如下方法使用"
		print u"add_word.py [[unit_url]] [word.txt]"

if __name__ == "__main__":
	main()