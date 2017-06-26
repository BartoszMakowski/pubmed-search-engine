import lucene
from builtins import print
import math

from math import log
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import IndexReader, DirectoryReader
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.document import Document, TextField, Field, StringField
from org.apache.lucene.index import IndexWriter, IndexWriterConfig

from org.apache.lucene.analysis.standard import StandardTokenizer
from org.apache.lucene.analysis import StopFilter
from org.apache.lucene.analysis.tokenattributes import CharTermAttribute
from org.tartarus.snowball.ext import EnglishStemmer
from java.io import StringReader

from org.apache.lucene.store import SimpleFSDirectory
from java.nio.file import Paths
import xml.etree.ElementTree as ET

from wheel.test.test_basic import test_findable


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
        next_token = es.getCurrent().lower()
        try:
            int(next_token)
        except:
            results = results + ' ' + next_token
    return (results)

def weights_from_phrase(phrase):
    es = EnglishStemmer()
    stok = StandardTokenizer()
    sread = StringReader(str(phrase))
    stok.setReader(sread)
    stok.reset()
    weights = {}
    sfil = StopFilter(stok, StandardAnalyzer.ENGLISH_STOP_WORDS_SET)
    while sfil.incrementToken():
        es.setCurrent(str(sfil.getAttribute(CharTermAttribute.class_)))
        es.stem()
        next_token = es.getCurrent().lower()
        try:
            weight = int(next_token)
            weights[last_token] = int(weight)
        except:
            last_token = next_token
    return (weights)


def search(phrase):
    vm_env = lucene.getVMEnv()
    vm_env.attachCurrentThread()

    index_path = Paths.get('var/index')
    index_dir = SimpleFSDirectory(index_path)
    # print(str(index_dir))
    ind_reader = DirectoryReader.open(index_dir)
    ind_searcher = IndexSearcher(ind_reader)
    query_parser = QueryParser('abstract', StandardAnalyzer())
    query_terms = my_tokenizer(phrase)
    weights = weights_from_phrase(phrase)
    query_tf, query_tfa = calc_tf_tfa(phrase)

    query = query_parser.parse(query_terms)
    print(query)
    hits = ind_searcher.search(query, 100)
    print(str(hits.totalHits) + " documents found.")
    arts = []
    idf, idf1 = calc_idf(ind_searcher, hits, phrase)

    query_tfidf = idf.copy()
    for token, val in query_tfidf.items():
        query_tfidf[token] = val * query_tfa.get(token, 0)
        print(token + ': ' + str(query_tfidf[token]))

    sum_dl = 0
    doc_words_num = {}
    for score_doc in hits.scoreDocs:
        doc_len = len(my_tokenizer(ind_searcher.doc(score_doc.doc).getField('abstract').stringValue()).split())
        sum_dl += doc_len
        doc_words_num[str(score_doc.doc)] = doc_len
    avg_dl = sum_dl / len(hits.scoreDocs)
    print(avg_dl)

    for score_doc in hits.scoreDocs:
        # print(score_doc.score)
        doc_tf, doc_tfa = calc_tf_tfa(ind_searcher.doc(score_doc.doc).getField('abstract').stringValue())
        doc_tfidf = idf.copy()
        # tfidf_sum = 0
        for token, val in doc_tfidf.items():
            doc_tfidf[token] = val * doc_tf.get(token, 0)
        tfidf_cos_sim = round(calc_cosine_similarity(query_tfidf, doc_tfidf, weights), 3)
        tfidf1_cos_sim = round(calc_cosine_similarity(idf1, doc_tf, weights), 3)

        tf_cos_sim = round(calc_cosine_similarity(query_tf, doc_tf), 3)
        rel = tfidf_cos_sim
        doc_bm25 = calc_bm25(idf, avg_dl, doc_tf, doc_words_num[str(score_doc.doc)], weights=weights)
        arts.append({ \
            'rel': rel, \
            'title': ind_searcher.doc(score_doc.doc).getField('title').stringValue(), \
            # 'pmid': ind_searcher.doc(score_doc.doc).getField('pmid').stringValue(), \
            # 'authors': ind_searcher.doc(score_doc.doc).getField('authors').stringValue(), \
            'id': score_doc.doc, \
            'score': round(score_doc.score, 3), \
            'tf': doc_tf, \
            'tfidf': doc_tfidf, \
            'bm25': doc_bm25, \
            'tf_cos_sim': tf_cos_sim, \
            'tfidf_cos_sim': tfidf_cos_sim,
            'tfidf1_cos_sim': tfidf1_cos_sim})
    # for art in arts:
    #     print(str.split(my_tokenizer(art)))
    return (arts, query_terms)

def find_by_id(id):
    vm_env = lucene.getVMEnv()
    vm_env.attachCurrentThread()

    index_path = Paths.get('var/index')
    index_dir = SimpleFSDirectory(index_path)
    # print(str(index_dir))
    ind_reader = DirectoryReader.open(index_dir)
    doc = ind_reader.document(id)
    # print(doc.getField('authors').stringValue())
    article = { \
        'pmid': doc.getField('pmid').stringValue(), \
        'authors': doc.getField('authors').stringValue(), \
        'title': doc.getField('title').stringValue(), \
        'abstract': doc.getField('abstract').stringValue()}
    return(article)


def calc_bm25(idf, avg_dl, doc_tf, doc_words, k = 1.5, b=0.75, weights={}):
    score = 0
    for token, val in idf.items():
        score += weights.get(token, 1) * val * (doc_tf.get(token, 0) * (k + 1))/(doc_tf.get(token, 0) + (k * ((1 - b) + (b * doc_words/avg_dl))))
    return (score)



def calc_tf_tfa(article):
    tf = {}
    article = str.split(my_tokenizer(article))
    for word in article:
        tf[word] = 0
    for word in article:
        tf[word] = tf[word] + 1
    total = len(article)
    max_tf = max(tf.values())
    tf = {k: v / total for k, v in tf.items()}
    tf_a = tf.copy()
    for k, v in tf_a.items():
        tf_a[k] *= 0.5/max_tf
        tf_a[k] += 0.5
    return (tf, tf_a)


def calc_idf(ind_searcher, hits, phrase):
    art_num = len(hits.scoreDocs)
    tokens = str.split(my_tokenizer(phrase))
    idf = {}
    idf1 = {}
    for token in tokens:
        idf[token] = 0
    for score_doc in hits.scoreDocs:
        article = str.split(ind_searcher.doc(score_doc.doc).getField('abstract').stringValue())
        for token in tokens:
            if token in article:
                idf[token] += 1
    for token, val in idf.items():
        if val > 0:
            idf[token] = log(art_num / val)
            idf1[token] = log(1 + art_num / val)
        else:
            idf[token] = 0
            idf1[token] = 0
    return (idf, idf1)


def calc_cosine_similarity(query, doc, weights={}):
    dot_prod = 0
    query_vec_len = 0
    doc_vec_len = 0
    for term in query:
        dot_prod +=  weights.get(term, 1) * query[term] * doc.get(term, 0)
        query_vec_len +=  weights.get(term, 1) * query[term]**2
        doc_vec_len +=  weights.get(term, 1) * doc.get(term, 0)**2
    query_vec_len = math.sqrt(query_vec_len)
    doc_vec_len = math.sqrt(doc_vec_len)
    if doc_vec_len>0 and query_vec_len>0:
        cos_sim = dot_prod/(query_vec_len * doc_vec_len)
    else:
        cos_sim = 0
    return (cos_sim)

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
        pmid = pmed_article.find('MedlineCitation').find('PMID').text
        article = pmed_article.find('MedlineCitation').find('Article')
        if article is not None and article.find('Abstract') is not None:
            doc = Document()
            doc.add(StringField('pmid', pmid, Field.Store.YES))
            doc.add(TextField('title', article.find('ArticleTitle').text, Field.Store.YES))
            doc.add(TextField('abstract', article.find('Abstract').find('AbstractText').text, Field.Store.YES))
            author_list = article.find('AuthorList')
            authors = ''
            if author_list is not None:
                for author in author_list.findall('Author'):
                    if author.find('LastName') is not None:
                        if author.find('ForeName') is not None:
                            authors += author.find('ForeName').text + '. '
                        authors +=  author.find('LastName').text + ', '
            # print(authors)
            doc.add(TextField('authors', authors, Field.Store.YES))
            ind_wr.addDocument(doc)
    ind_wr.close()