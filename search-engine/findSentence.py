# coding:utf-8
import xml.sax
import xml.dom
import time
import jieba
import sys
import jieba.posseg as pseg
sys.path.insert(0, 'scripts')
from langconv import *
import cPickle
import numpy
import gensim
import multiprocessing

reload(sys)
sys.setdefaultencoding('utf-8')


class MovieHandler(xml.sax.ContentHandler):
	def __init__(self, of, data, questionList, model):
		self.CurrentData = ""
		self.title = ""
		self.text = ""
		self.counter = 0
		self.file = open(of, 'wb')

		self.data = data
		self.model = model
		self.questionList = questionList

		jieba.enable_parallel(20)

	def __del__(self):
		pass

	def processSentence(self, vec, pageId):
		for q in self.questionList:
			qVec = numpy.asarray(q[0][0])
			sVec = vec
			dist = numpy.dot(qVec - sVec, qVec - sVec)
			ind = 0
			while dist >= q[1][ind][1] and ind < n_nn-1:
				ind += 1
			if ind < n_nn-1:
				q[1].insert(ind, (sVec, dist, pageId))
				q[1].pop()

	def startDocument(self):
		pass
	def endDocument(self):
		cPickle.dump(self.questionList, self.file)
		self.file.close()

	def startElement(self, tag, attributes):
		self.CurrentData = tag

	def endElement(self, tag):
		if self.CurrentData == "text":
			if self.title.startswith('Wikipedia:'):
				print "Skip", self.title
				self.title = ""
				self.text = ""
				return
			print "Parsing page", self.title, self.counter
			pageVecList = []
			time_set=time.time()
			line = Converter('zh-hans').convert(self.text.decode('utf-8'))
			self.text = line.encode('utf-8')
			words = jieba.posseg.cut(self.text)	
			sentenceStart = True
			sentenceWords = []
			sentenceVecList = []
			pageSentencesList = []
			cnt = 0
			for w in words:
				if w.word == '。' or w.word == '？' or w.word == '！':
					sentenceStart = False
					if len(sentenceVecList) == 0:
						sentenceVecList = [numpy.zeros((200,))]
					mean = numpy.mean(sentenceVecList, axis=0)
					vmax = numpy.max(sentenceVecList, axis=0)
					vmin = numpy.min(sentenceVecList, axis=0)
					vec = numpy.r_[mean, vmax, vmin]
					s = (sentenceWords)
					#self.data.append(s)
					#self.processSentence(s)
					pageSentencesList.append(s)
					sentenceWords = []
					cnt = 0
				elif w.flag not in ['x', 'eng', 'm']:
					sentenceWords.append(w.word)
					try:
						vec = self.model[w.word]
						sentenceVecList.append(vec)
						pageVecList.append(vec)
					except:
						pass
					cnt += 1

			if sentenceStart == True:
				sentenceStart = False
				if len(sentenceVecList) == 0:
						sentenceVecList = [numpy.zeros((200,))]
				mean = numpy.mean(sentenceVecList, axis=0)
				vmax = numpy.max(sentenceVecList, axis=0)
				vmin = numpy.min(sentenceVecList, axis=0)
				vec = numpy.r_[mean, vmax, vmin]
				s = (sentenceWords, self.counter)
				#self.data.append(s)
				#self.processSentence(s)
				pageSentencesList.append(s)
				sentenceWords = []


			pageVec = numpy.mean(pageVecList)
			file = open('data/wiki-zh/pages/page_%08d.pkl'%self.counter, 'wb')
			cPickle.dump((pageVec,pageSentencesList), file)
			file.close()

			self.processSentence(pageVec, self.counter)
				
			print time.time() - time_set
			self.counter += 1
			self.title = ""
			self.text = ""

		self.CurrentData = ""


	def characters(self, content):
		if self.CurrentData == "title":
			self.title = self.title + content
		elif self.CurrentData == "text":
			self.text = self.text + content


if __name__ == "__main__":
	####################
	## Parameters ##
	####################
	n_nn = 10
	
	print "Load questions"
	file = open('data/wiki-zh/questions.pkl', 'rb')
	questionList = cPickle.load(file)
	file.close()
	for i in range(len(questionList)):
		questionList[i][1].extend([(None, numpy.inf, None)]*n_nn)

	
	print "Parsing questions"
	parser = xml.sax.make_parser()
	# turn off namepsaces
	parser.setFeature(xml.sax.handler.feature_namespaces, 0)

	model = gensim.models.Word2Vec.load_word2vec_format('data/word2vec/vector.bin', binary=1)

	sentenceList = []
	Handler = MovieHandler('data/wiki-zh/sentence.pkl', sentenceList, questionList, model)
	parser.setContentHandler(Handler)

	print "Generate sentence data."
	parser.parse('data/wiki-zh/wiki.xml')

	print "Generate question data."
	questionList = []
	Handler = MovieHandler('data/wiki-zh/questions.pkl', questionList, model)
	parser.setContentHandler(Handler)

	parser.parse('data/wiki-zh/testset.xml')
	

	print "Load data."
	file = open('data/wiki-zh/sentence-mini.pkl', 'rb')
	sentenceList = cPickle.load(file)
	file.close()
	

	"""
	sentenceList = [	
		((vec, [w1,w2,w3]), [(vec, [w1,w2], dist)])
	]
	"""
	print "Find nearest sentence."
	print len(questionList), len(sentenceList)

	def processSentence(i):
		time0 = time.time()
		q = questionList[i]
		for s in sentenceList:
			qVec = numpy.asarray(q[0][0])
			sVec = numpy.asarray(s[0][0])
			sText = s[0][1]
			dist = numpy.dot(qVec - sVec, qVec - sVec)
			ind = 0
			while dist >= q[1][ind][2] and ind < n_nn-1:
				ind += 1
			if ind < n_nn-1:
				q[1].insert(ind, (sVec, sText, dist))
				q[1].pop()
		print i, time.time() -time0

	"""
	pool = multiprocessing.Pool(processes=1)
	pool.map(processSentence, range(10))
	pool.close()
	pool.join()
	"""
	for i in range(len(questionList)):
	#for i in range(10):
		processSentence(i)
	print "multiprocessing done!"

	file = open('data/wiki-zh/question-nearest-sentence.pkl', 'wb')
	cPickle.dump(questionList, file)
	file.close()