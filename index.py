import blist, xml.sax, timeit, re, sys, bz2
from collections import defaultdict
from nltk.stem.porter import PorterStemmer

pageNumber = 0
compression_factor = 4

file_size_limit = 10000000

titlePageMapper = blist.sorteddict({})
indexTitle = blist.sorteddict({})
title_size = 0

#Initialise title to page mapper
title_page_map_fp=open("OutputFiles/titlePageMapper.txt","w")
pattern=re.compile('[\d+\.]*[\d]+|[\w]+')
stemmer = PorterStemmer()

def stemWords(words):
	return blist.blist([stemmer.stem(word) for word in words])

def removeStopWords(words):
	global stop_words
	return blist.blist([word for word in words if word not in stop_words])

def writeOutput(ordered_text, output_text):
	to_write=[]

	for key in ordered_text:
		to_write.extend(key.encode('utf-8') + ":")
		for item in ordered_text[key]:
			to_write.extend(" d" + str(item) + "-" + str(ordered_text[key][item]) + "|")
		to_write.extend("\n")

	name = 'OutputFiles/title.txt.bz2'

	with bz2.BZ2File(name, 'wb', compresslevel=compression_factor) as f:
		f.write("".join(to_write))
	f.close()


def indexText(words, pageNumber):
	word_length = len(words)
	if word_length:
		term = round((1/float(word_length)), 4)
		global title_size, indexTitle
		for word in words:
			if word not in indexTitle:
				indexTitle[word]={}
				indexTitle[word][pageNumber]=term
			elif pageNumber in indexTitle[word]:
				indexTitle[word][pageNumber]+=term
			else:
				indexTitle[word][pageNumber]=term
				title_size = title_size + sys.getsizeof(pageNumber) + sys.getsizeof(indexTitle[word][pageNumber])

		if title_size>=file_size_limit:
			writeOutput(indexTitle, 'title')
			indexTitle = blist.sorteddict({})
			title_size=0
	
def tokenizeTitle(title, pageNumber):
	titlePageMapper[int(pageNumber)]=title
	title_page_map_fp.write(pageNumber + ' ' + title.strip().encode('utf-8') + '\n')
	title=title.lower().replace('_',' ')
	titleWords=re.findall(pattern, title)
	words=removeStopWords(titleWords)
	words=stemWords(words)
	indexText(words, pageNumber)

def tokenizeText(text, pageNumber): 
	text=text.lower()
	lines = text.split('\n')
	infobox, category, body, links = blist.blist([]), blist.blist([]), blist.blist([]), blist.blist([]) 
	
class wikipediaHandler(xml.sax.ContentHandler):
	def __init__(self):
		xml.sax.ContentHandler.__init__(self)
		self.bufferObject = ""

	#Function to handle starting element of page
	def startElement(self, name, attrs):
		global pageNumber
		if name=="page":
		   pageNumber+=1	
	
	#Function to handle ending element of page	
	def endElement(self, name):
		global titlePageMapper
		global pageNumber

		if name=="title":
			wikipediaHandler.title=self.bufferObject
			wikipediaHandler.titleWords=tokenizeTitle(wikipediaHandler.title, str(pageNumber))

		if name=="text":
			wikipediaHandler.text=self.bufferObject
			#wikipediaHandler.textWords=tokenizeText(wikipediaHandler.text,str(pageNumber))
		if name=="page":
			if pageNumber%7000==0:
				for key in titlePageMapper:
					title_page_map_fp.write(str(key) + " " + titlePageMapper[key].strip().encode('utf-8') + "\n")
				titlePageMapper = blist.sorteddict({})

		self.bufferObject=""

	#Function to handle content from parser
	def characters(self, content):
		#Ignore the content of the tags before <page>
		global pageNumber
		if pageNumber:
			self.bufferObject+=content

if __name__=="__main__":
	if len(sys.argv)>2:
		file_name = str(sys.argv[1])
		stop_word_file = str(sys.argv[2])
	elif len(sys.argv) > 1:
		file_name = str(sys.argv[1])
		stop_word_file = "stopwords.txt"
	else:
		file_name = "wiki-search-small.xml"
		stop_word_file = "stopwords.txt" 
	
	wiki_fp = open(file_name, 'r')
	stop_word_fp = open(stop_word_file, 'r')
	stop_words = blist.blist([line.strip() for line in stop_word_fp])

	start = timeit.default_timer()
	xml.sax.parse(wiki_fp, wikipediaHandler())
	stop = timeit.default_timer()

	writeOutput(indexTitle, 'title')

	print stop - start
	print pageNumber

	title_page_map_fp.close()
	wiki_fp.close()
	stop_word_fp.close()
