#!/usr/bin/python

import sys
import sqlite3
import os
import nltk
import string
import random
import time
import docx


def initTable():
	table = c.execute("SELECT * FROM sqlite_master WHERE name ='QAQGrammar' and type='table'")
	if not table.fetchone():
		c.execute("CREATE TABLE QAQGrammar(this_tag text, child_tags text)")
		c.execute("INSERT INTO QAQGrammar(this_tag) VALUES ('.')")
	table = c.execute("SELECT * FROM sqlite_master WHERE name =? and type='table'", (word_table,))
	if not table.fetchone():
		c.execute("CREATE TABLE " + word_table + " (this_word text, this_tag text, next_word text, next_tag text, hit int)")

def cleanString(text):
	printable = set(string.printable)
	text = filter(lambda x: x in printable, text)
	text = remove_bracket(text)
	remove_set = ['-', '$', '*', '+', '=', '_', '%', '#', '^', '&', '/']
	text = ''.join([char for char in text if not char in remove_set])
	replace_set = ['?', ',', ';', '!']
	text = ''.join(['.' if char in replace_set else char for char in text])
	text = text.replace('`',"'")
	arr = text.split('\n')
	text = ''
	for item in arr:
		item = item.strip()
		if item.endswith('.'):
			text += item
	arr = text.split('.')
	return arr

def parseText(text):
	arr = cleanString(text)
	i = 0
	total = len(arr)
	prev_per = 0
	for text in arr:
		i += 1
		per = i * 100 / total
		if per > prev_per:
			prev_per = per
			print str(per) + '%' + ' complete'
		if len(text) > 10:
			text = text + '.'
			tokens = nltk.word_tokenize(text.lower())
			tagged = nltk.pos_tag(tokens)
			this_word = '.'
			this_id = 1
			this_tag = '.'
			for (next_word, next_tag) in tagged:
				updateWord(this_word, this_tag, next_word, next_tag)
				rowid = updateTag(this_id, next_tag)
				this_word = next_word
				this_id = rowid
				this_tag = next_tag

def getGrammarChildren(this_id):
	result = c.execute("SELECT * FROM QAQGrammar WHERE rowid=?",[this_id]).fetchall()
	if len(result) == 0:
		return []
	elif result[0][1]:
		return result[0][1].split(chr(31))
	else:
		return []

def updateGrammarChildren(this_id, child_tag, curr_array):
	index = 1
	if not (child_tag == '.'):
		c.execute("INSERT INTO QAQGrammar (this_tag) VALUES(?)", [child_tag])
		index = c.lastrowid
	curr_array.append(str(index))
	curr_array.append(child_tag)
	s = chr(31).join(curr_array)
	c.execute("UPDATE QAQGrammar SET child_tags=? WHERE rowid=?", [s, int(this_id)])
	return index

def updateTag(this_id, child_tag):
	result = getGrammarChildren(this_id)
	if not (child_tag in result):
		return updateGrammarChildren(this_id, child_tag, result)
	else:
		index = result.index(child_tag) - 1;
		return int(result[index])

def updateWord(this_word, this_tag, next_word, next_tag):
	result = getHit(this_word, this_tag, next_word, next_tag)
	if not result:
		c.execute("INSERT INTO " + word_table + " (this_word, this_tag, next_word, next_tag, hit) VALUES (?, ?, ?, ?, ?)",[this_word, this_tag, next_word, next_tag, 1])
	else:
		c.execute("UPDATE " + word_table + " SET hit=? WHERE this_word=? AND this_tag=? AND next_word=? AND next_tag=?", [(result + 1), this_word, this_tag, next_word, next_tag])

def getHit(this_word, this_tag, next_word, next_tag):
	result = c.execute("SELECT hit FROM " + word_table + " WHERE this_word=? AND this_tag=? AND next_word=? AND next_tag=?", (this_word, this_tag, next_word, next_tag)).fetchall()
	if len(result) == 0:
		return None
	else:
		return result[0][0]

def parseTxt(file):
	with open(file, 'r') as file:
		s = file.read()
		parseText(s)
	conn.commit()

def parseDoc(filename):
	document = docx.Document(filename)
	docText = '\n\n'.join([
	    paragraph.text.encode('utf-8') for paragraph in document.paragraphs
	])
	conn.commit()
	return docText

def parseDir(path):
	arr = []
	for file in os.listdir(path):
		arr.append(file)
	for i in range(len(arr)):
		file = arr[i]
		print 'parsing', file, 'total', str(i) + '/' + str(total)
		time0 = time.time()
		filepath = path+'/'+file
		if file.endswith(".docx"):
			parseDoc(filepath)
		else:
			parseTxt(filepath)
		print 'takes', time.time() - time0





def getRandomChild(this_word, this_tag, this_tag_id, ignore_set=[]):
	words_result = c.execute("SELECT next_word, hit, next_tag FROM " + word_table + " WHERE this_word=? AND this_tag=?", (this_word,this_tag)).fetchall()
	tags_result = c.execute("SELECT child_tags FROM QAQGrammar WHERE rowid=?", (this_tag_id,))
	s = tags_result.fetchall()[0][0]
	tags_result = s.split(chr(31))
	child_tags = tags_result[1::2]
	child_indexes = tags_result[::2]
	words_result = [item for item in words_result if (item[2] in child_tags) and (item[0] not in ignore_set)]
	next_word = getRandomWord(words_result)
	if next_word == None:
		return (None, None, None)
	else:
		next_tags = [item[2] for item in words_result if item[0] == next_word]
		next_tag = next_tags[random.randrange(0, len(next_tags))]
		next_index = child_indexes[child_tags.index(next_tag)]
		return next_word, next_tag, next_index

def getRandomWord(result):
	total = sum(result[i][1] for i in range(0, len(result)))
	if total == 0:
		return
	else:
		r = random.randrange(0, total) + 1
		s = 0
		for i in range(0, len(result)):
			s += result[i][1]
			if s >= r:
				return result[i][0]

def getRandomSentence():
	while True:
		text = getRandomSentenceRecur()
		if len(text) > 30:
			return text
	# this_word = '.'
	# this_tag = '.'
	# this_tag_id = 1
	# sentence = ''
	# while True:
	# 	(next_word, next_tag, next_tag_id) = getRandomChild(this_word, this_tag, this_tag_id)
	# 	if next_word == None:
	# 		return sentence
	# 	sentence += next_word + ' '
	# 	if next_word == '.':
	# 		return sentence
	# 	(this_word, this_tag, this_tag_id) = (next_word, next_tag, next_tag_id)

def getRandomSentenceRecur(this_word='.', this_tag='.', this_tag_id=1, sentence='', depth=0):
	if len(sentence) > 1 and this_word == '.':
		return sentence
	else:
		ignore_set = [] if depth > 1 else ['.']
		while True:
			(next_word, next_tag, next_tag_id) = getRandomChild(this_word, this_tag, this_tag_id, ignore_set)
			# print next_word
			if next_word == None:
				return None
			next_sentence = getRandomSentenceRecur(next_word, next_tag, next_tag_id, sentence + ' ' + next_word, depth + 1)
			if next_sentence:
				return next_sentence
			ignore_set.append(next_word)
	return None





def remove_bracket(test_str):
    ret = ''
    skip1c = 0
    skip2c = 0
    for i in test_str:
        if i == '[':
            skip1c += 1
        elif i == '(':
            skip2c += 1
        elif i == ']' and skip1c > 0:
            skip1c -= 1
        elif i == ')'and skip2c > 0:
            skip2c -= 1
        elif skip1c == 0 and skip2c == 0:
            ret += i
    return ret



# input format python parser.py read dir (table)
#			   python parser.py write #num


def invalidInput():
	print 'In valid argument.\nUsage: python parser.py read dir (table)\n\tpython parser.py write #num'




word_table = 'material'
time0 = time.time()
conn = sqlite3.connect('QAQExpress.db')
c = conn.cursor()
initTable()
time1 = time.time()
print 'init table takes', time1 - time0, '\n'

if len(sys.argv) < 3:
	invalidInput()
else:
	if sys.argv[1] == 'read':
		if len(sys.argv) > 3:
			word_table = sys.argv[3]
		print 'start reading books in directory', sys.argv[2]
		parseDir(sys.argv[2])
		time2 = time.time()
		print 'parsing books takes', time2 - time1
	elif sys.argv[1] == 'write':
		for x in range(int(sys.argv[2])):
			print 'QAQ AI:', getRandomSentence(), '\n'
	else:
		invalidInput()
conn.close()