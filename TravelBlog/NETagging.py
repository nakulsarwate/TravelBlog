'''
create ne specific files 
create one master file with whole text and most popular tags
index both

@author: nakul, chaitrali
'''
import nltk
import io   
import json
import re
import os
import warnings
from bs4 import BeautifulSoup
#from SentimentAnalyzer import read_from_solr
from nltk.tag import StanfordNERTagger
from nltk.internals import find_jars_within_path
import codecs
import sys
from string import lower
from SentimentAnalyzer import read_from_solr
from nltk.parse import stanford


from nltk.sentiment.util import demo_subjectivity



#blog_folder = "/home/chaitrali/officework/nltkCode/trial"
#blog_folder =  "/home/wikidataserver/crawler/blogs" 

#ne_folder = "/home/wikidataserver/crawler/ne"

#ne_folder = "/home/chaitrali/officework/nltkCode/trial_output"
#full_text_folder = "/home/chaitrali/officework/nltkCode/full_trial_output"
sents = []
sentJson = []
namedEntitiesCount = dict()
ne_wise_boost = dict()
textFilePath = '/home/expertadmin/'


def process_blogs():
    for blog_file in os.listdir(blog_folder):
        if blog_file.endswith(".txt"):
            print (os.path.join(blog_folder, blog_file))
            read_post(blog_folder, blog_file)
    
def build_json(sentence, tags,isFullText=False, blog_title=''):
    properties = dict()
    if(isFullText == True):
        properties['fulltext'] = sentence
    else:
        properties['text'] = sentence
    properties['blog_title'] = blog_title
    properties['tags'] = tags
    return properties

def build_full_text_json(tags, blog_title=''):
    tag_score_collection = []
    UTF8Writer = codecs.getwriter('utf8')
    sys.stdout = UTF8Writer(sys.stdout)
    for tag in tags.items():
        properties =dict()
        #print(tag[0])
        #print (tag[1])
        #tag_scores = dict()
        #tag_scores['tag_name'] = tag[0]
        #tag_scores['score'] = tag[1]
        #tag_score_collection.append(tag_scores)
        properties['blog_title'] = blog_title
        properties['ne'] = tag[0]
        properties['relevance'] = tag[1]
        tag_score_collection.append(properties)
    #properties['full-text'] = content
    return tag_score_collection

def get_continuous_chunks(tagged_sent):
    continuous_chunk = []
    current_chunk = []

    for token, tag in tagged_sent:
        if tag != "O":
            current_chunk.append((token, tag))
        else:
            if current_chunk: # if the current chunk is not empty
                continuous_chunk.append(current_chunk)
                current_chunk = []
    # Flush the final current_chunk into the continuous_chunk, if any.
    if current_chunk:
        continuous_chunk.append(current_chunk)
    return continuous_chunk

def standford_ne_tagger_sents(content):
    st = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz') 
    #stanford_dir = st._stanford_jar.rpartition('/')[0]
    #stanford_jars = find_jars_within_path(stanford_dir)
     
    #st._stanford_jar = ':'.join(stanford_jars)
    tags = st.tag(nltk.word_tokenize(content))
    result = dict()
    
    start = 0 
    sents = nltk.sent_tokenize(content)
    for sent in sents:
        words = nltk.word_tokenize(sent)
        tagged_sent = tags[start:start + len(words)]
        continuous_chunks = get_continuous_chunks(tagged_sent)
        nes = set()
        for ne in continuous_chunks :
            if(ne[0][1] == u'LOCATION'):
                #print(lower(u' '.join([token for token, tag in ne])))
                nes.add(lower(u' '.join([token for token, tag in ne])))
        result[sent] = nes
        print (sent, nes)
        start += len(words);
    return result
    

def stanford_ne_tagger(tokens):
    st = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz') 
    stanford_dir = st._stanford_jar.rpartition('/')[0]
    stanford_jars = find_jars_within_path(stanford_dir)
     
    st._stanford_jar = ':'.join(stanford_jars)
    tags = st.tag(tokens)
    continuous_chunks = get_continuous_chunks(tags)
    named_entities_str_tag = set()
    for ne in continuous_chunks :
        if(ne[0][1] == u'LOCATION'):
            named_entities_str_tag.add(lower(u' '.join([token for token, tag in ne])))

    return named_entities_str_tag

def stanford_parse(sentence):
    parser = stanford.StanfordDependencyParser(model_path="edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")
    warnings.filterwarnings('error')
    sub_obj_list = []
    try:
        parse = parser.raw_parse(sentence)        
        for sent in parse:
            #print(type(sent))
            #len(sent)
            for node in sent.triples(): 
                
                if('nsubj' in node or 'dobj' in node or 'nsubjpass' in node):
    #                 print node[2]
    #                 if('NNP' in node[2] or 'NNPS' in node[2] or 'NN' in node[2] or 'NNS' in node[2]):
                    if(('NNP' or 'NNPS' or 'NN' or 'NNS') in node[2]):
                        sub_obj_list.append(node[2])
    except Warning:
        print 'Warning was raised as an exception!'
    
    return sub_obj_list

#def subjectivity_analysis(sentence):
#     n_instances = 500
#     subj_docs = [(sent, 'subj') for sent in subjectivity.sents(categories='subj')[:n_instances]]
#     obj_docs = [(sent, 'obj') for sent in subjectivity.sents(categories='obj')[:n_instances]]

#    demo_sent_subjectivity(sentence)
    
    #print (u'' + sentence)

def analyze_sent_subjectivity(text):
    """
    Classify a single sentence as subjective or objective using a stored
    SentimentAnalyzer.

    :param text: a sentence whose subjectivity has to be classified.
    """
    from nltk.classify import NaiveBayesClassifier
    from nltk.tokenize import regexp
    word_tokenizer = regexp.WhitespaceTokenizer()
    try:
        sentim_analyzer = nltk.data.load('sa_subjectivity.pickle')
    except LookupError:
        print('Cannot find the sentiment analyzer you want to load.')
        print('Training a new one using NaiveBayesClassifier.')
        sentim_analyzer = demo_subjectivity(NaiveBayesClassifier.train, True)

    # Tokenize and convert to lower case
    tokenized_text = [word.lower() for word in word_tokenizer.tokenize(text)]
    subjectivity = sentim_analyzer.classify(tokenized_text)
    print text, subjectivity
    return subjectivity

def tag_full_content(blog_folder, blog_file):
    file_path = os.path.join(blog_folder, blog_file)
    fo = io.open(file_path, 'r+', encoding='utf8', newline="\r")
    content = fo.read()
#     sents = nltk.sent_tokenize(content)
#     tokenized_sents = list()
#     for sent in sents:
#         sent_words = nltk.word_tokenize(sent)
#         tokenized_sents.extend(sent_words)
#         tokenized_sents.append('\n')
    result = standford_ne_tagger_sents(content)
    
    
def read_post(blog_folder, blog_file):
    
    file_path = os.path.join(blog_folder, blog_file)
    filename = os.path.splitext(blog_file)
    global sents, sentJson, namedEntitiesCount, ne_wise_boost
    sents = []
    sentJson = []
    namedEntitiesCount = dict()
    ne_wise_boost = dict()
    #print file_path
    if(filename[0].endswith(".html")):
        filename = os.path.splitext(filename[0])
        #print(filename)
    nejson = filename [0] + '.json'
    #print(nejson)
    ne_path = os.path.join(ne_folder, nejson)
    full_text_path = os.path.join(full_text_folder, nejson)
#     if (os.path.isfile(ne_path) == True):
#         return
    fo = io.open(file_path, 'r+', encoding='utf8', newline="\r")
    fo_full_text = open(full_text_path, 'w')
    nefile = open(ne_path, 'w')
    content = fo.read()
    sents = nltk.sent_tokenize(content)
    i = 0
    while i < len(sents) :
        #print sents[i]
        process_sent(i, filename[0])
        i += 1
        
    #for sentence_tuples in sentence_ne_mapping.items():
        #print sentence_tuples
    
    #for js in sentJson:
        #print js
    
    popular_nes = set()
    ne_relevance_score = dict()
    i = 0
#     for w in sorted(namedEntitiesCount, key=namedEntitiesSentenceCount.get, reverse=True):
#         if(i < 10) :
#             #print ((u' ' + w), namedEntitiesCount[w])
#             popular_nes.append(w)
#             i += 1
    length = len(sents)
    for key in namedEntitiesCount.keys() :
        #namedentitywise subjectivity boost to be added
        score = namedEntitiesCount[key] / float(length)
        score = score + ne_wise_boost[key]
        ne_relevance_score[key] = score

    i = 0
    for w in sorted(ne_relevance_score, key=ne_relevance_score.get, reverse=True):
        if(i < 10) :
#           print ((u' ' + w), namedEntitiesCount[w])
            popular_nes.add(w)
            #print ((u' ' + w), ne_relevance_score[w])
        i += 1
            
    sentJson.append(build_json(content, list(popular_nes), True,filename[0]))
    full_text_json = json.dumps(build_full_text_json(ne_relevance_score, filename[0]), indent=4, sort_keys=True)
    finalJson = json.dumps(sentJson, indent=4, sort_keys=True)
    #print(finalJson)
    nefile.write(finalJson)
    
    #print(full_text_json)
    fo_full_text.write(full_text_json)
    
    
    fo.close()
    nefile.close()
    fo_full_text.close()
    return ne_path

    
def process_sent(sent_index, blog_title):
    global sents, sentJson, namedEntitiesCount, ne_wise_boost
    
    #namedEntities = set()
    
    #namedEntitiesSentenceCount = dict()
    
#     for sent in sents:
    sent = sents[sent_index]
    
    
        #neTags = set ()
    words = nltk.word_tokenize(sent)
    #print pos_tags
   
    stan_nes = stanford_ne_tagger(words)
#     subjectivity = analyze_sent_subjectivity(sent)
#     
#     
#     if(len(stan_nes) > 0):
#         for ne in stan_nes :
#             if(subjectivity == 'subj'):
#             #sentence is subjective
#                 if(ne_wise_boost.has_key(ne)):
#                     ne_wise_boost[ne] = ne_wise_boost[ne] + 0.05
#                 else :
#                     ne_wise_boost[ne] = 0.5
#             else:
#                 if(ne_wise_boost.has_key(ne)):
#                     ne_wise_boost[ne] = ne_wise_boost[ne] + 0.03
#                 else :
#                     ne_wise_boost[ne] = 0.3
#                     
#             if(ne in namedEntitiesCount) :
#                 namedEntitiesCount[ne] += 1
#             else :
#                 namedEntitiesCount[ne] = 1
#     
#     
#     window_sents = sent
#     
#     if (sent_index < len(sents) -1):  
#         next_sent = sents[sent_index + 1]
#         next_words = nltk.word_tokenize(next_sent)
#         next_stan_nes = stanford_ne_tagger(next_words)
#         next_subectivity = analyze_sent_subjectivity(next_sent) 
#         
#         if (len(next_words) == 1) and not (next_words[0].isalnum()) :
#             next_sub_obj_list = []
#         else:
#             next_sub_obj_list = stanford_parse(next_sent)
#         select = False
#         for ne in next_stan_nes :
#             if (ne in stan_nes and ne in next_sub_obj_list):
#                 if(next_subectivity == 'subj'):
#                     #the sentence is subjective and relevant - so boost
#                     ne_wise_boost[ne] = ne_wise_boost[ne] + 0.025
#                     select = True
#                 #break
#             else:
#                 select = False
#         if select:
#             window_sents = window_sents + u' ' + next_sent
#     
#         
#     sentJson.append(build_json(window_sents, list(stan_nes), blog_title=blog_title))
    
def read_post_old(blog_folder, blog_file):
    file_path = os.path.join(blog_folder, blog_file)
    filename = os.path.splitext(blog_file)
    #print file_path
    if(filename[0].endswith(".html")):
        filename = os.path.splitext(filename[0])
        #print(filename)
    nejson = filename [0] + '.json'
    #print(nejson)
    ne_path = os.path.join(ne_folder, nejson)
    full_text_path = os.path.join(full_text_folder, nejson)
#     if (os.path.isfile(ne_path) == True):
#         return
    fo = io.open(file_path, 'r+', encoding='utf8', newline="\r")
    fo_full_text = open(full_text_path, 'w')
    nefile = open(ne_path, 'w')
    content = fo.read()
    sents = nltk.sent_tokenize(content)
    
    #namedEntities = set()
    namedEntitiesCount = dict()
    #namedEntitiesSentenceCount = dict()
    sentJson = []
    for sent in sents:
        sentIndex = sents.index(sent)
        #neTags = set ()
        words = nltk.word_tokenize(sent)
        #posTags = nltk.pos_tag(words)
        
        #print(type(posTags))
        stan_nes = stanford_ne_tagger(words)
        #print stan_nes
        #nechunks = nltk.ne_chunk(posTags, binary=False)
        
        #print nechunks
        windowSents = ''
        if (not (sentIndex -1 < 0)) :
            windowSents = windowSents + u' ' + sents[sentIndex -1]
        windowSents = windowSents + u' ' + sent
        if (not ((sentIndex +1) == len(sents))):
            windowSents = windowSents + u' ' + sents[sentIndex +1]
                    
#         for subtree in nechunks.subtrees():
#             #print subtree
#             if subtree.label() == 'NE':
#                 ne = u''
#                 node_index = 1
#                 for node in subtree:
#                     if(len(subtree) > 1 and node_index < len(subtree)):
#                         ne += node[0] + u' '
#                         node_index += 1
#                     else:
#                         ne += node[0]
#                 ne = string.lower(ne)
#                 if(ne in namedEntitiesCount) :
#                     namedEntitiesCount[ne] += 1
#                 else :
#                     namedEntitiesCount[ne] = 1
#                          
#                 if not (ne in neTags) :
#                     neTags.add(ne)
#                 namedEntities.add(ne)
        for ne in stan_nes:
            if(ne in namedEntitiesCount) :
                namedEntitiesCount[ne] += 1
            else :
                namedEntitiesCount[ne] = 1
#             if(ne in namedEntitiesSentenceCount) :
#                 namedEntitiesSentenceCount[ne] += 1
#             else :l
#                 namedEntitiesSentenceCount[ne] = 1
        
        sentJson.append(build_json(windowSents, list(stan_nes), filename[0]))
            #else :
                #print(subtree)
    #finalJsonSents = {}
    #finalJsonSents ['sentences'] = sentJson
    popular_nes = []
    ne_relevance_score = dict()
    i = 0
#     for w in sorted(namedEntitiesCount, key=namedEntitiesSentenceCount.get, reverse=True):
#         if(i < 10) :
#             #print ((u' ' + w), namedEntitiesCount[w])
#             popular_nes.append(w)
#             i += 1
    length = len(sents)
    for key in namedEntitiesCount.keys() :
        score = namedEntitiesCount[key] / float(length)
        ne_relevance_score[key] = score
    
    for w in sorted(ne_relevance_score, key=ne_relevance_score.get, reverse=True):
        if(i < 10) :
#           print ((u' ' + w), namedEntitiesCount[w])
            popular_nes.append(w)
            print ((u' ' + w), ne_relevance_score[w])
            i += 1
            
    #sentJson.append(build_json(content, popular_nes, True,filename[0]))
    full_text_json = json.dumps(build_full_text_json(content, ne_relevance_score, filename[0]), indent=4, sort_keys=True)
    finalJson = json.dumps(sentJson, indent=4, sort_keys=True)
    #print(finalJson)
    nefile.write(finalJson)
    
    print(full_text_json)
    fo_full_text.write(full_text_json)
    #
    
    fo.close()
    nefile.close()
    fo_full_text.close()
    return ne_path

def re_manipulation(fileContent):
    
    fileContent = re.sub("\s\n+", "_nl_", fileContent)
    #print fileContent
    fileContent = re.sub("\._nl_", ". ", fileContent)
    fileContent = re.sub("_nl_", ". ", fileContent)
    #print fileContent
    fileContent = re.sub("\.\s+\.", ". ", fileContent)
    #print fileContent
    return fileContent

def extract_ne_from_wikitext(wiki_file_path):
    fi = io.open(wiki_file_path, 'r+', newline="\r")
    textFilePathComponents = os.path.split(wiki_file_path)
    global textFilePath
    textFileName = textFilePathComponents[1] + '.txt'
    fo = io.open(os.path.join(textFilePath, textFileName), 'w')
    content = fi.read()
    #print textFileName
    soup = BeautifulSoup(content,"lxml")
    textContent = soup.get_text(strip=False)
    fo.write(re_manipulation(textContent))
    fi.close()
    fo.close()
    ne_file_name = read_post(textFilePath, textFileName)
    return ne_file_name


def analyze_blogs_for_nes(wiki_ne_file, query):
    fi = io.open(wiki_ne_file, 'r+')
    fileJson = json.load(fi)
    tags = set()
    for doc in fileJson:
        if(doc.has_key('fulltext')):
            tags = doc['tags']
            break
    ne_wise_details = list()
    for tag in tags:
        print(' For Attraction : ' + tag)
        #query_string = u'tags:"'+ tag + u'" AND tags:"' + query + u'"'
        #query_string = u'tags:(jalna AND lonar crater)'
       
        blogwiseScores, overallPosScore, overallNegScore, blogwiseExcerpt = read_from_solr(tag)
        details = createBlogResults(blogwiseScores, blogwiseExcerpt);
            #print details.get(blogName)
        if(len(details) > 0):
            blogDetails = dict()
            blogDetails['destination'] = tag
            overallOpinion = u''
            if(overallPosScore > overallNegScore):
                overallOpinion = u'positive'
            elif(overallPosScore < overallNegScore):
                overallOpinion = u'negative'
            else:
                overallOpinion = u'neutral'
            blogDetails['overall_opinion'] = overallOpinion
            blogDetails['blog_details'] = details
            ne_wise_details.append(blogDetails)
    #for item in ne_wise_details:
        #print item
    blogJson = json.dumps(ne_wise_details, indent=4, sort_keys=True)
    #print blogJson
    return blogJson

def getBlogsForActualUserQuery(query):
    blogwiseScores, overallPosScore, overallNegScore, blogwiseExcerpt = read_from_solr(query)
    details = createBlogResults(blogwiseScores, blogwiseExcerpt);
            #print details.get(blogName)
    blogDetails = dict()
    if(len(details) > 0):
        blogDetails['destination'] = query
        overallOpinion = u''
        if(overallPosScore > overallNegScore):
            overallOpinion = u'positive'
        elif(overallPosScore < overallNegScore):
            overallOpinion = u'negative'
        else:
            overallOpinion = u'neutral'
        blogDetails['opinion'] = overallOpinion
        blogDetails['blog_details'] = details
    blogJson = json.dumps(blogDetails, indent=4, sort_keys=True)
    #print blogJson
    return blogJson

def createBlogResults(blogwiseScores, blogwiseExcerpt):
    details = dict()
    for blogName, relevance in blogwiseScores.items():
        #print blogName
        #print relevance
        opinion = u''
        if(relevance[0] > relevance[1]):
            opinion = u'positive'
        elif (relevance[0] < relevance[1]):
            opinion = u'negative'
        else :
            opinion = u'neutral'
        #print blogwiseExcerpt.get(blogName)
        details['blog_name'] = blogName
        details['opinion'] = opinion
        details['excerpt'] = blogwiseExcerpt.get(blogName) 
    
    return details
        
#analyze_blogs_for_nes('/home/chaitrali/officework/nltkCode/trial_output/love-affair-with-sahyadri-part-1.json', 'maharashtra')

tag_full_content('/home/expertadmin/Downloads/Siddhant/',blog_file='a.html.txt')


#read_post('/home/chaitrali/officework/nltkCode/trial/',blog_file='old-magazine-house-ganeshgudi.html.txt')
#import profile
#profile.run('print tag_full_content("/home/chaitrali/officework/nltkCode/trial/",blog_file="a-journey-into-snow-clad-mountains-of.html.txt"); print')
#process_blogs()

#extract_ne_from_wikitext('/home/chaitrali/eclipse/modeling-mars/eclipse/Matheran_See.html')

#if __name__ == "__main__":
    #process_blogs()
