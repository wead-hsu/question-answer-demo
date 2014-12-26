#!/usr/bin/python
#encoding=utf-8

import codecs
import sys
import json
import xml.etree.ElementTree as etree
from trie import *
from seg_query import *
from read_template import *

def process(ifn, tfn, ofn):
	sf = open(ifn)
	xml_root = etree.fromstring(sf.read())
	root = build_extractor(tfn)
	print_trie(root)
	of = codecs.open(ofn, 'w', 'utf-8')

	line = sf.readline()
	for xml_element in xml_root.getchildren():
		query = extract_query(xml_element[0].text)
		print query
		seg_res, pos_res = seg_query(query)
		keywords = get_keywords(query)
		lats = extract_lat(root, seg_res, pos_res)
		
		query_info = {}
		query_info['seg'] = seg_res
		query_info['pos'] = pos_res
		query_info['key'] = keywords
		query_info['lat'] = []
		for lat in lats:
			if not lat[1] and len(lats) == 1 or lat[1]:
				query_info['lat'].append([lat[0], lat[1]])




		of.write('SEGMENT: ')
		for idx in range(len(seg_res)):
			of.write(seg_res[idx] + '/' + pos_res[idx] + ' ')
		of.write('\n')
		of.write('KEYWORDS: ')
		for w in keywords:
			of.write(w + ' ')
		of.write('\n')
		of.write('LAT: ')
		for i in lats:
			of.write(i[0] + ' [')
			for k in i[1]:
				of.write(k + ',')
			of.write(']')
		of.write('\n\n')
		#of.write(json.dumps(query_info) + '\n')
		line = sf.readline()
	
def extract_query(line):
	return '^' + line.split(u'？')[0] + '$'

def build_extractor(ifn):
	lat_templates = read_template(ifn)
	return build_lat_trie(lat_templates)

def extract_lat(root, seg_res, pos_res):
	ret = []
	for i in range(len(seg_res)):
		tmp_res = find_trie(root, i, seg_res, pos_res)
		if tmp_res:
			ret.append(tmp_res)
	
	for i in ret:
		for j in i:
			print j,
		print 
	return ret


if __name__ == '__main__':
	process('../data/raw-data/Sample.xml', 'lat-data/lat-template.txt','../data/query-info/example-query.txt')
