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
		self.pages =[]

		jieba.enable_parallel(20)

	def __del__(self):
		pass

	def processSentence(self, vec, pageId):
		for q in self.questionList:
			qVec = numpy.asarray(q[0][0])
			pVec = vec
			dist = numpy.dot(qVec - pVec, qVec - pVec)
			ind = 0
			while dist >= q[1][ind][1] and ind < n_nn-1:
				ind += 1
			if ind < n_nn-1:
				q[1].insert(ind, (pVec, dist, pageId))
				q[1].pop()

	def startDocument(self):
		pass
	def endDocument(self):
		cPickle.dump(self.questionList, self.file)
		cPickle.dump(self.pages, self.file)
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
			cnt = 0
			for w in words:
				if w.flag not in ['x', 'eng', 'm']:
					try:
						vec = self.model[w.word]
						pageVecList.append(vec)
					except:
						pass

			pageVecList.append(numpy.zeros((200,)))
			if len(pageVecList) == 0:
				pageVecList.append(numpy.zeros((200,)))
			mean = numpy.mean(pageVecList, axis=0)
			vmax = numpy.max(pageVecList, axis=0)
			vmin = numpy.min(pageVecList, axis=0)
			pageVec = numpy.r_[mean, vmax, vmin]

			self.pages.append([self.counter, pageVec])
			#self.processSentence(pageVec, self.counter)

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
	parser.parse('data/wiki-zh/wiki-mini.xml')
