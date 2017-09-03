'''
Created on 05-Feb-2016

@author: nakul, chaitrali
'''
'''
Accept user search query
query solr for the same
read solr results, combine results from same blog, run sentiment analysis on the same
return results
'''
from nltk import sent_tokenize
import pysolr

from senti_classifier import senti_classifier

overallPosScore = 0
overallNegScore = 0
blogwiseScores = dict()
blogwiseExcerpt = dict()

def analyze_sents(content, blog_title):
#     fo = io.open('/home/chaitrali/officework/nltkCode/blogs/24-hours-in-fort-kochi.html.txt', 'r+', encoding='utf8', newline="\r")
#     content = fo.read()
    sents = sent_tokenize(content)
#   print len(sents)
    pos_score, neg_score = senti_classifier.polarity_scores(sents)
    #print (blog_title, pos_score, neg_score)
    
    global overallPosScore 
    overallPosScore += pos_score
    global overallNegScore 
    overallNegScore += neg_score
    #print (blog_title, sents, pos_score, neg_score)
   
    
    blogwiseScores[blog_title] = pos_score, neg_score
    
def read_from_solr(query):
    global blogwiseExcerpt, blogwiseScores
    blogwiseExcerpt.clear()
    blogwiseScores.clear()
    query_modified = 'ne:' + query        
    solr = pysolr.Solr('http://localhost:8983/solr/blogRelevance', timeout=10)
    results = solr.search(query_modified,**{'rows' : '1000', 'sort' : u'relevance asc'})
    
    #print(results.grouped)
    #print(len(results.grouped))
    #result = results.grouped
    #print(results)
    top_5 = 0
    for result in results:
        sentence_count = 0
        if (top_5 > 4):
            break
        #print result.get(u'blog_title')
        solrBlogs = pysolr.Solr('http://localhost:8983/solr/blogCollection', timeout=10)
        queryBlogs = 'tags:' + query
        blog_title = result.get(u'blog_title')
        resultsBlogs = solrBlogs.search(queryBlogs,**{'rows' : '1000', 'fq' : u'blog_title:' + blog_title + ' '})
        
        sentences = ''
        for blog in resultsBlogs:
            content = u''
            if(u'text' in blog):
                content = content + blog[u'text']
                sentences += content
            if(sentence_count == 0) :
                blogwiseExcerpt[blog_title] = content
            sentence_count += 1
        analyze_sents(sentences, blog_title)
        #print('=============================================================')
        top_5 +=1
        
#     for relevance in blogwiseScores.items():
#         print type(relevance) 
#     print (overallPosScore, overallNegScore)
#     for excerpt in blogwiseExcerpt.items():
#         print excerpt
        #
    return blogwiseScores, overallPosScore, overallNegScore, blogwiseExcerpt
#     for key in result.keys():
#         print (key)
#         value = result.get(key)
#         for groupKey in value.keys() :
#             print (groupKey)
#             groupValue = value.get(groupKey)
#     higherObject = result.get(u'blog_title')
#     groups = higherObject.get(u'groups')
#     #print(len(groups))    
#     #print(type(groups))   
#     #print(groups)
#     total = 0
#     for group in groups :
#         #print(group)
#         doclist = group.get(u'doclist')
#         groupDocs = doclist.get(u'docs')
#         #print(len(groupDocs))
#         total = total + len(groupDocs)
#         sentences = ''
#         i = 0
#         for groupDoc in groupDocs:
#             #print (groupDoc.keys())
#             if (i == 0) :
#                 blogwiseExcerpt[group.get(u'groupValue')] = groupDoc.get(u'text')
#             if(u'text' in groupDoc):
#                 sentences += groupDoc.get(u'text')
#             i += 1
#             print(groupDoc.get(u'text'))
#         #print(group.get(u'groupValue'))
#         #print(sentences)
#         analyze_sents(sentences, group.get(u'groupValue'))
    
#     for relevance in blogwiseScores.items():
#         print relevance 
#     print (overallPosScore, overallNegScore)
#     for excerpt in blogwiseExcerpt.items():
#         print excerpt
            
#analyze_sents(u'I was born and brought-up in Maharashtra.', u'this is sparta')
#read_from_solr('maharashtra')
