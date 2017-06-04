import lucene
from builtins import print

from math import log
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import IndexReader, DirectoryReader
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.document import Document, TextField, Field
from org.apache.lucene.index import IndexWriter, IndexWriterConfig

from org.apache.lucene.analysis.standard import StandardTokenizer
from org.apache.lucene.analysis import StopFilter
from org.apache.lucene.analysis.tokenattributes import CharTermAttribute
from org.tartarus.snowball.ext import EnglishStemmer
from java.io import StringReader

from org.apache.lucene.store import SimpleFSDirectory
from java.nio.file import Paths
import xml.etree.ElementTree as ET


class MyAnalyzer(StandardAnalyzer):
    def __init__(self):
        super().__init__()

    def createComponents(fieldName):
        print("WYWOŁANO")


def my_tokenizer(phrase):
    es = EnglishStemmer()
    stok = StandardTokenizer()
    sread = StringReader(str(phrase))
    stok.setReader(sread)
    stok.reset()
    results = ''
    sfil = StopFilter(stok, StandardAnalyzer.ENGLISH_STOP_WORDS_SET)
    while sfil.incrementToken():
        es.setCurrent(str(sfil.getAttribute(CharTermAttribute.class_)))
        es.stem()
        results = results + ' ' + es.getCurrent()
    return (results)


def search(phrase):
    vm_env = lucene.getVMEnv()
    vm_env.attachCurrentThread()

    index_path = Paths.get('var/index')
    index_dir = SimpleFSDirectory(index_path)
    # print(str(index_dir))
    ind_reader = DirectoryReader.open(index_dir)
    ind_searcher = IndexSearcher(ind_reader)
    query_parser = QueryParser('abstract', StandardAnalyzer())
    tokens = my_tokenizer(phrase)
    query = query_parser.parse(tokens)
    print(query)
    hits = ind_searcher.search(query, 100)
    print(str(hits.totalHits) + " documents found.")
    arts = []
    idf = calc_idf(ind_searcher, hits, phrase)
    for score_doc in hits.scoreDocs:
        # print(score_doc.score)
        tf_sum, tf = calc_tf(ind_searcher.doc(score_doc.doc).getField('abstract').stringValue(), phrase)
        tfidf = tf.copy()
        tfidf_sum = 0
        for token, val in tfidf.items():
            tfidf[token] = val * idf[token]
            tfidf_sum += tfidf[token]
        arts.append({ \
            'title': ind_searcher.doc(score_doc.doc).getField('title').stringValue(), \
            'id': score_doc.doc, \
            'score': score_doc.score, \
            'tf': tf_sum, \
            'tfidf': tfidf_sum})
    # for art in arts:
    #     print(str.split(my_tokenizer(art)))
    return (arts, tokens)


def calc_tf(article, phrase):
    tf = {}
    counter = 0
    tokens = str.split(my_tokenizer(phrase))
    for token in tokens:
        tf[token] = 0
    article = str.split(my_tokenizer(article))
    for word in article:
        # print(">>>" + word + "<<<")
        if word in tokens:
            counter = counter + 1
            tf[word] = tf[word] + 1
    tf_sum = counter / len(article)
    return (tf_sum, tf)


def calc_idf(ind_searcher, hits, phrase):
    art_num = len(hits.scoreDocs)
    tokens = str.split(my_tokenizer(phrase))
    idf = {}
    for token in tokens:
        idf[token] = 0
    for score_doc in hits.scoreDocs:
        article = str.split(ind_searcher.doc(score_doc.doc).getField('abstract').stringValue())
        for token in tokens:
            if token in article:
                idf[token] += 1
    for token, val in idf.items():
        idf[token] = log(art_num / val)
    return (idf)


# TODO:
#   - upload files in secure way
#   - index author field
def index_articles(data_file):
    vm_env = lucene.getVMEnv()
    vm_env.attachCurrentThread()
    tree = ET.parse(data_file)
    root = tree.getroot()
    doc = Document()
    path = Paths.get('var/index')
    ind_dir = SimpleFSDirectory(path)
    conf = IndexWriterConfig(StandardAnalyzer())
    ind_wr = IndexWriter(ind_dir, conf)
    for pmed_article in root.findall('PubmedArticle'):
        article = pmed_article.find('MedlineCitation').find('Article')
        if article is not None and article.find('Abstract') is not None:
            doc = Document()
            doc.add(TextField('title', article.find('ArticleTitle').text, Field.Store.YES))
            doc.add(TextField('abstract', article.find('Abstract').find('AbstractText').text, Field.Store.YES))
            ind_wr.addDocument(doc)
    ind_wr.close()
