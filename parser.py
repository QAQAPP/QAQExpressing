import sqlite3
import os
import nltk
import string
import random
import time

def initTable():
	# c.execute("CREATE TABLE QAQGrammar(this_tag text, prev_id int, next_id int)")
	table = c.execute("SELECT * FROM sqlite_master WHERE name ='QAQGrammar' and type='table'")
	if not table.fetchone():
		c.execute("CREATE TABLE QAQGrammar(this_tag text, child_tags text)")
		c.execute("INSERT INTO QAQGrammar(this_tag) VALUES ('.')")
	table = c.execute("SELECT * FROM sqlite_master WHERE name ='QAQWords' and type='table'")
	if not table.fetchone():
		c.execute("CREATE TABLE QAQWords(this_word text, this_tag text, next_word text, next_tag text, hit int)")

def parseText(text):
	printable = set(string.printable)
	text = filter(lambda x: x in printable, text)
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
		c.execute("INSERT INTO QAQWords (this_word, this_tag, next_word, next_tag, hit) VALUES (?, ?, ?, ?, ?)",[this_word, this_tag, next_word, next_tag, 1])
	else:
		c.execute("UPDATE QAQWords SET hit=? WHERE this_word=? AND this_tag=? AND next_word=? AND next_tag=?", [(result + 1), this_word, this_tag, next_word, next_tag])

def getHit(this_word, this_tag, next_word, next_tag):
	result = c.execute("SELECT hit FROM QAQWords WHERE this_word=? AND this_tag=? AND next_word=? AND next_tag=?", (this_word, this_tag, next_word, next_tag)).fetchall()
	if len(result) == 0:
		return None
	else:
		return result[0][0]

def parseFile(file):
	with open(file, 'r') as file:
		s = file.read()
		parseText(s)





def getRandomChild(this_word, this_tag, this_tag_id):
	words_result = c.execute("SELECT next_word, hit, next_tag FROM QAQWords WHERE this_word=? AND this_tag=?", (this_word,this_tag)).fetchall()
	# print this_tag_id
	tags_result = c.execute("SELECT child_tags FROM QAQGrammar WHERE rowid=?", (this_tag_id,))
	# print tags_result.fetchall()
	s = tags_result.fetchall()[0][0]
	tags_result = s.split(chr(31))
	child_tags = tags_result[1::2]
	child_indexes = tags_result[::2]
	words_result = [item for item in words_result if item[2] in child_tags]
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
	this_word = '.'
	this_tag = '.'
	this_tag_id = 1
	sentence = ''
	while True:
		(next_word, next_tag, next_tag_id) = getRandomChild(this_word, this_tag, this_tag_id)
		if next_word == None:
			return sentence
		sentence += next_word + ' '
		if next_word == '.':
			return sentence
		(this_word, this_tag, this_tag_id) = (next_word, next_tag, next_tag_id)

conn = sqlite3.connect('QAQExpress.db')
c = conn.cursor()
time0 = time.time()
initTable()
time1 = time.time()
print 'init table takes', time1 - time0


# parseFile('philosophy.txt')
# time2 = time.time()
# print 'parse philosophy takes', time2 - time1
# parseFile('history.txt')
# time3 = time.time()
# print 'parse history takes', time3 - time2
# parseFile('sociology.txt')
# time4 = time.time()
# print 'parse sociology takes', time4 - time3
# parseFile('book.txt')
# time5 = time.time()
# print 'parse book takes', time5 - time4
# print 'total time', time5 - time0


for x in xrange(1,100):
	print str(x)+':', getRandomSentence()
conn.commit()
conn.close()
