# coding:utf-8
import xml.sax
import sys
from langconv import *
import jieba.posseg as pseg
import jieba
import gensim
import numpy

reload(sys)
sys.setdefaultencoding('utf-8')


class MovieHandler(xml.sax.ContentHandler):
	def __init__(self, of, model):
		self.CurrentData = ""
		self.title = ""
		self.text = ""
		self.counter = 0
		self.file = open(of, 'w')
		self.model = model

	def __del__(self):
		self.file.close()

	def startDocument(self):
		self.file.write('<doc>\n')

	def endDocument(self):
		self.file.write('</doc>')

	def startElement(self, tag, attributes):
		self.CurrentData = tag

	def endElement(self, tag):
		if self.CurrentData == "text":
			if self.title.startswith('Wikipedia:'):
				print "Skip", self.title
				#print self.text
				self.title = ""
				return
			print "Parsing page", self.title
			line = Converter('zh-hans').convert(self.text.decode('utf-8'))
			self.text = line.encode('utf-8')
			words = jieba.posseg.cut(self.text)
			sentenceStart = False
			sentenceVecList = []
			for w in words:
				if w.word == '。' or w.word == '？' or w.word == '！':
					sentenceStart = False
					self.file.write('</text>\n\t<vec>')
					if len(sentenceVecList) == 0:
						sentenceVecList = [numpy.zeros((600,))]
					mean = numpy.mean(sentenceVecList, axis=0)
					vmax = numpy.mean(sentenceVecList, axis=0)
					vmin = numpy.mean(sentenceVecList, axis=0)
					for d in mean:
						self.file.write('%f\t'%d)
					for d in vmax:
						self.file.write('%f\t'%d)
					for d in vmin:
						self.file.write('%f\t'%d)
					self.file.write('</vec>\n</sentence>\n')
					self.sentenceVecList = []
				elif w.flag not in ['x']:
					if sentenceStart == False:
						sentenceStart = True
						self.file.write('<sentence>\n\t<text>')
					self.file.write(w.word + '\t')
					try:
						sentenceVecList.append(self.model[w.word])
					except:
						print "bang"


			if sentenceStart == True:
				sentenceStart = False
				self.file.write('</text>\n\t<vec>')
				
				if len(sentenceVecList) == 0:
					sentenceVecList = [numpy.zeros((600,))]
				mean = numpy.mean(sentenceVecList, axis=0)
				vmax = numpy.mean(sentenceVecList, axis=0)
				vmin = numpy.mean(sentenceVecList, axis=0)
				for d in mean:
					self.file.write('%f\t'%d)
				for d in vmax:
					self.file.write('%f\t'%d)
				for d in vmin:
					self.file.write('%f\t'%d)
				self.file.write('</vec>\n</sentence>\n')
				self.sentenceVecList = []

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
	print "Reading word2vec model..."
	model = gensim.models.Word2Vec.load_word2vec_format('data/word2vec/vector.bin', binary=1)
	
	parser = xml.sax.make_parser()
	# turn off namepsaces
	parser.setFeature(xml.sax.handler.feature_namespaces, 0)

	Handler = MovieHandler('data/word2vec/sentences-vec-mini.txt', model)
	parser.setContentHandler(Handler)

	print "Parsing sentences..."
	parser.parse('data/wiki-zh/wiki-mini.xml')
	
	parser = xml.sax.make_parser()
	# turn off namepsaces
	parser.setFeature(xml.sax.handler.feature_namespaces, 0)

	Handler = MovieHandler('data/word2vec/question-vec.txt', model)
	parser.setContentHandler(Handler)

	print "Parsing sentences..."
	parser.parse('data/wiki-zh/testset.xml')
