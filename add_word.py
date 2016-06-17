#coding:utf-8

import requests
import time
import json
import re
import sys


class AddShanbayWord:
	def __init__(self,username,password,book_url,unit_name_list = [],unit_url,file_name):
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
				payload["word"] = i
				r = requests.post(add_url,data = payload,cookies = cookie)
				j = json.loads(r.content)
				if j["status_code"] == 0:
					print "   ",i,u"尝试添加成功"
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
		print r.status_code
		j = json.loads(r.content)
		if j["status_code"] == 0:
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
			book_id = self.book_url.split("/")[-1]
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
		j = json.load(open(file_name))
	except Exception,e:
		print "load config error",e
		exit(-1)
	username = j["username"]
	password = j["password"]
	book_url = j["bookurl"]
	auto_addunit = j["autoaddunit"]
	unit_name = j["unitname"]

	if (sys.argv) > 1:
		a = AddShanbayWord(username,password,book_url,[],sys.argv[1],"analyse_result.txt")
		a.start_add()
	elif auto_addunit:
		a = AddShanbayWord(username,password,book_url,unit_name,"","analyse_result.txt")
		a.start_add()
	else:
		print "需要指定配置文件autoaddunit参数，否则使用命令行指定单词书某一单元的链接地址"

if __name__ == "__main__":
	main()