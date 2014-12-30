# coding:utf-8
import time
import jieba
import numpy
import gensim


def get_vec_list(model, s):
    m = []
    for w in s:
        try:
            m.append(model[unicode(w, 'utf8')])
        except:
            pass
    return m
    
def get_s2s_dist(model, s1, s2):
    m1 = get_vec_list(model, s1)
    m2 = get_vec_list(model, s2)
    dist = numpy.zeros((len(m1), len(m2)))
    for i in range(len(m1)):
        for j in range(len(m2)):
            w1 = m1[i]
            w2 = m2[j]
            l1 = numpy.sqrt(numpy.dot(w1, w1))
            l2 = numpy.sqrt(numpy.dot(w2, w2))
            dist[i,j] = numpy.dot(w1, w2)/numpy.sqrt(l1*l2)
    return numpy.mean(dist)

def read_sentences(filename):
    file = open(filename)
    s = file.readlines()
    for i in range(len(s)):
        s[i] = s[i].split('\t')
    return s

def get_corpus_sentence_dist(model, filename1, filename2):
    s1 = read_sentences(filename1)
    s2 = read_sentences(filename2)
    dist = numpy.zeros((len(s1), len(s2)))
    for i in range(len(s1)):
        time0 = time.time()
	print i, len(s1[i])
        for j in range(len(s2)):
            dist[i,j] = get_s2s_dist(model, s1[i], s2[j])
        print time.time() - time0
    return dist

if __name__ == '__main__':
    model = gensim.models.Word2Vec.load_word2vec_format('data/word2vec/vector.bin', binary=1)
    file = open('data/word2vec/sentences.txt')
    print get_s2s_dist(model, [u'li', u'zhihu'], [u'ul'])
    print get_corpus_sentence_dist(model, 'data/word2vec/sentences.txt',
		'data/word2vec/sentences.txt')
