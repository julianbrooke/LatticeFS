# -*- coding: UTF-8 -*-
import codecs
import cPickle
import os
import gzip

def read_sentence_from_corpus(corpus_path,start=0,stop=-1,corpus_encoding="utf-8"):
    '''
    The default corpus reader. Change if needed
    '''
    f = codecs.open(corpus_path,encoding=corpus_encoding)
    sentence = []
    sentence_count = 0
    for line in f:
        #print line
        try:
            word,pos = line.strip().split("\t")
        except:
            continue
        if pos == "SENT":
            if start <= sentence_count:
                yield sentence
            sentence = []
            sentence_count += 1
            if sentence_count == stop:
                break
        else:
            sentence.append([word,pos])

lemma_lookup_dict = {}          
#f = codecs.open("lemma_groups_fr.txt",encoding="latin-1")
#f = codecs.open("lemma_groups_MW.txt")#,encoding="utf-8")
f = codecs.open("lemma_groups_MW_fixed.txt")#,encoding="utf-8")

for line in f:
    words = line.strip().split("\t")
    for word in words[1:]:
        lemma_lookup_dict[word] = words[0]

lemma_lookup_dict_old = {}

f = codecs.open("lemma_groups_MW.txt")#,encoding="utf-8")

for line in f:
    words = line.strip().split("\t")
    for word in words[1:]:
        lemma_lookup_dict_old[word] = words[0]

del lemma_lookup_dict_old["could"]



def read_sentence_from_corpus_fr(corpus_path,start=0,stop=-1,corpus_encoding="latin-1"):#corpus_encoding="utf-8"):
    '''
    The default corpus reader. Change if needed
    '''
    f = codecs.open(corpus_path,encoding=corpus_encoding)
    sentence = []
    sentence_count = 0
    for line in f:
        #print line
        try:
            word,pos = line.strip().split("\t")
        except:
            if sentence:
                if start <= sentence_count:
                    yield sentence
                sentence = []
                sentence_count += 1
                if sentence_count == stop:
                    break
            continue
        if pos == "SENT":
            if start <= sentence_count:
                yield sentence
            sentence = []
            sentence_count += 1
            if sentence_count == stop:
                break
        else:
            word = word.lower()
            if pos == "PRP:det":
                if word == "au" or word == "aux":
                    sentence.extend([[u"à","PRP"],["le","DET:ART"]])
                elif word == "du" or word == "des":
                    sentence.extend([["de","PRP"],["le","DET:ART"]])
            else:
                if word in lemma_lookup_dict:
                    word = lemma_lookup_dict[word]                   
                if pos.startswith("VER"):
                    pos = "VER"
                sentence.append([word,pos])

def fix_pos_ja(word,pos):
    if word == u'の' and pos == u'助詞-格助詞':
        return u'助詞-POS'
    return pos

'''
def read_sentence_from_corpus_ja(corpus_path,start=0,stop=-1,corpus_encoding="utf-8"):
    for directory in ["OC","OW","PB","PN"]:
        curr_path = corpus_path + "/" + directory
        for filename in os.listdir(curr_path):
            #print filename
            f = codecs.open(curr_path +  "/" + filename,encoding=corpus_encoding)
            for line in f:
                index = line.find("<sentence")
                while index != -1:
                    sentence_string = line[index:line.find("</sentence>", index)]
                    sentence = []
                    sub_index = sentence_string.find('orthToken="')
                    while sub_index != -1:
                         token = sentence_string[sub_index + 11: sentence_string.find('"',sub_index + 11)]
                         sub_index = sentence_string.find('lemma="',sub_index)                        
                         lemma = sentence_string[sub_index + 7: sentence_string.find('"',sub_index + 7)]
                         sub_index = sentence_string.find('pos="',sub_index)
                         pos = sentence_string[sub_index + 5: sentence_string.find('"',sub_index + 5)]
                         sub_index = sentence_string.find('orthToken="',sub_index)
                         sentence.append([lemma,fix_pos_ja(token,pos),token])
                    yield sentence
                    index = line.find("<sentence", index + 1)
'''

numbers = set(u"０１２３４５６７８９")

simplified_gaps = True

def read_sentence_from_corpus_ja(corpus_path,start=0,stop=-1,corpus_encoding="utf-8"):
    sentence_count = 0
    done = False
    files = os.listdir(corpus_path)
    files.sort()
    for filename in files:
        f = gzip.open(corpus_path + "/" + filename)
        sentence = []
        for line in f:
            line = line.decode(encoding="utf-8")
            if line.startswith("EOS"):
                if sentence_count > start:
                    yield sentence
                sentence_count += 1
                sentence = []
                if sentence_count == stop:
                    done = True
                    break
            else:
                stuff = line.split("\t")
                if stuff[5] == u"助動詞-マス" or stuff[5] == u"助動詞-タ":
                    #print "removed"
                    #print stuff[5].encode("utf-8")
                    #print stuff[0].encode("utf-8")
                    continue
                if simplified_gaps:
                    if (stuff[4] == u"助動詞" and stuff[5] == u"連用形-ニ") or (stuff[4] == u"形容詞-一般" and stuff[5] == u"連用形-一般"):
                        print "adding subpos"
                        stuff[4] += stuff[5]
                if stuff[0] in numbers:
                    sentence.append((stuff[0], fix_pos_ja(stuff[3],stuff[4])))
                else:
                    sentence.append((stuff[3], fix_pos_ja(stuff[3],stuff[4])))
        if done:
            break
                    
def read_sentence_from_corpus_ja_with_lemma(corpus_path,start=0,stop=-1,corpus_encoding="utf-8"):
    sentence_count = 0
    done = False
    files = os.listdir(corpus_path)
    files.sort()
    for filename in files:
        f = gzip.open(corpus_path + "/" + filename)
        sentence = []
        for line in f:
            line = line.decode(encoding="utf-8")
            if line.startswith("EOS"):
                if sentence_count > start:
                    yield sentence
                sentence_count += 1
                sentence = []
                if sentence_count == stop:
                    done = True
                    break
            else:
                stuff = line.split("\t")
                if stuff[5] == u"助動詞-マス" or stuff[5] == u"助動詞-タ":
                    try:
                        sentence[-1][-1] += stuff[0]
                    except:
                        pass
                elif stuff[0] in numbers:
                    sentence.append([stuff[0], fix_pos_ja(stuff[3],stuff[4]),stuff[0]])
                else:
                    sentence.append([stuff[3], fix_pos_ja(stuff[3],stuff[4]),stuff[0]])
        if done:
            break


def read_sentence_from_corpus_hr(corpus_path,start=0,stop=-1,corpus_encoding="utf-8"):
    '''
    The default corpus reader. Change if needed
    '''
    f = codecs.open(corpus_path,encoding=corpus_encoding)
    sentence = []
    sentence_count = 0
    for line in f:
        #print line
        if line == "\n":
            #print "newline"
            if start <= sentence_count:
                yield sentence
            sentence = []
            sentence_count += 1
            if sentence_count == stop:
                break
        else:
            try:
                ws = line.strip().split("\t")
                word = ws[2]
                pos = ws[3]
                #print word, pos
                if (word == 'biti' or word == 'htjeti') and pos == 'V':
                    pos = "Ec"
                if (word == 'sebe') and pos == 'P':
                    pos = "Ep"
                sentence.append([word,pos])
            except:
                continue

def read_sentence_from_corpus_with_lemma_hr(corpus_path,start=0,stop=-1,corpus_encoding="utf-8"):
    '''
    The default corpus reader. Change if needed
    '''
    f = codecs.open(corpus_path,encoding=corpus_encoding)
    sentence = []
    sentence_count = 0
    for line in f:
        #print line
        if line == "\n":
            #print "newline"
            if start <= sentence_count:
                yield sentence
            sentence = []
            sentence_count += 1
            if sentence_count == stop:
                break
        else:
            try:
                ws = line.strip().split("\t")
                wordform = ws[1]
                lemma = ws[2]
                pos = ws[3]
               #print word, pos
                if (lemma == 'biti' or lemma == 'htjeti') and pos == 'V':
                    pos = "Ec"
                if (lemma == 'sebe') and pos == 'P':
                    pos = "Ep"
                sentence.append([lemma, pos, wordform])
            except:
                continue


def read_sentence_from_corpus_en(corpus_path,start=0,stop=-1,corpus_encoding="utf-8"):
    '''
    The default corpus reader. Change if needed
    '''
    f = codecs.open(corpus_path,encoding=corpus_encoding)
    sentence = []
    sentence_count = 0
    for line in f:
        #print line
        try:
            word,pos = line.strip().split("\t")
        except:
            continue
        if pos == "SENT":
            if start <= sentence_count:
                yield sentence
            sentence = []
            sentence_count += 1
            if sentence_count == stop:
                break
        else:
            sentence.append([word,pos])

preserve = set(["WDT","PDT","PP$","PNQ","DTQ"])

def fix_pos(pos,word):
    if len(pos) == 3 and pos not in preserve:
        pos = pos[:2]
    if word == "i" and pos == "NP":
        pos = "PP"
    elif pos == "RP":
        pos = "IN"
    return pos


def read_sentence_from_corpus_en_thq(corpus_path,start=0,stop=-1,corpus_encoding="utf-8"):
    f = codecs.open(corpus_path,encoding=corpus_encoding)
    sentence = []
    sentence_count = 0
    for line in f:
        #print line
        try:
            word,pos = line.strip().split("\t")
        except:
            if sentence:
                if start <= sentence_count:
                    yield sentence
                sentence = []
                sentence_count += 1
                if sentence_count == stop:
                    break
        
        if pos == "SENT":
            if start <= sentence_count:
                yield sentence
            sentence = []
            sentence_count += 1
            if sentence_count == stop:
                break
        else:
            if word in lemma_lookup_dict:
                word = lemma_lookup_dict[word]
            elif word == "'d":
                if pos.startswith("MD"):
                    word = "would"
                elif pos.startswith("VH"):
                    word = "have"
            elif word == "'s":
                if pos.startswith("VB"):
                    word = "be"
                elif pos.startswith("VH"):
                    word = "have"
                    
            sentence.append([word,fix_pos(pos)])

def read_sentence_from_corpus_ICWSM(corpus_path,start=0,stop=-1,corpus_encoding="latin-1"):
    duplicates = set()
    #f2 = open("duplicate_texts.txt")
    f2 = open("all_duplicates.txt")
    for line in f2:
        duplicates.add(int(line))
    f2.close()

    f2= open("new_bad_docs_lem.txt")
    for line in f2:
        duplicates.add(int(line.strip()))
    f2.close()

    f = codecs.open(corpus_path,encoding=corpus_encoding)
    sentence = []
    sentence_count = 0
    text = [[]]
    temp = {}
    doc_count = 0
    b_count = 0
    doc_min_word = 100
    done = False
    for line in f:
        try:
            word,pos = line.strip().split("\t")
        except:
            continue
        if word == "#":
            b_count = 1
        elif word == "@" and b_count == 1:
            b_count = 2
        elif b_count == 2 and word == "!":
            if len(temp)>= doc_min_word:
                if doc_count not in duplicates:
                    for sentence in text:
                        if sentence and start <= sentence_count:
                            yield sentence
                        sentence_count += 1
                        if sentence_count == stop:
                            done = True
                            break
                    
                doc_count +=1
                if doc_count % 10000 == 0:
                    print doc_count
                    print text
            text = [[]]
            temp = {}
            b_count = 0
        else:
            temp[word] = True
            if doc_count in duplicates:
                continue
            word = word.lower()
            if pos == "SENT":
                text[-1].append([word,fix_pos(pos,word)])
                text.append([])
            else:
                if word.endswith("ing") and pos.startswith("NN"):
                    pass
                elif word in lemma_lookup_dict:
                    word = lemma_lookup_dict[word]
                elif word == "'d":
                    if pos.startswith("MD"):
                        word = "would"
                    elif pos.startswith("VH"):
                        word = "have"
                elif word == "'s":
                    if pos.startswith("VB"):
                        word = "be"
                    elif pos.startswith("VH"):
                        word = "have"
                        
                text[-1].append([word,fix_pos(pos,word)])
        if done:
            break


def read_sentence_from_corpus_BNC(corpus_path,start=0,stop=-1,corpus_encoding="ascii"):
    f = codecs.open(corpus_path,encoding=corpus_encoding)
    sentence_count = 0
    for line in f:
        if line.startswith("<-- "):
            continue
        sentence = line.strip().split(" ")
        for i in range(len(sentence)):
            last_underscore = sentence[i].rfind("_")
            word = sentence[i][:last_underscore].lower()
            pos = sentence[i][last_underscore + 1:]

            if word.endswith("ing") and pos.startswith("NN"):
                pass
            elif word in lemma_lookup_dict:
                word = lemma_lookup_dict[word]
            elif word == "'d":
                if pos.startswith("VM"):
                    word = "would"
                elif pos.startswith("VH"):
                    word = "have"
            elif word == "'s":
                if pos.startswith("VB"):
                    word = "be"
                elif pos.startswith("VH"):
                    word = "have"
            sentence[i] = [word,fix_pos(pos,word)]

        #print sentence
    
        if sentence and start <= sentence_count:
            yield sentence
        sentence_count += 1
        if sentence_count == stop:
            break


def read_sentence_from_corpus_BNC_with_lemma(corpus_path,start=0,stop=-1,corpus_encoding="ascii"):
    f = codecs.open(corpus_path,encoding=corpus_encoding)
    sentence_count = 0
    for line in f:
        if line.startswith("<-- "):
            continue
        sentence = line.strip().split(" ")
        for i in range(len(sentence)):
            last_underscore = sentence[i].rfind("_")
            lemma = sentence[i][:last_underscore]
            word = sentence[i][:last_underscore].lower()
            pos = sentence[i][last_underscore + 1:]

            if word.endswith("ing") and pos.startswith("NN"):
                pass
            elif word in lemma_lookup_dict:
                word = lemma_lookup_dict[word]
            elif word == "'d":
                if pos.startswith("VM"):
                    word = "would"
                elif pos.startswith("VH"):
                    word = "have"
            elif word == "'s":
                if pos.startswith("VB"):
                    word = "be"
                elif pos.startswith("VH"):
                    word = "have"
            sentence[i] = [word,fix_pos(pos,word),lemma]

        #print sentence
    
        if sentence and start <= sentence_count:
            yield sentence
        sentence_count += 1
        if sentence_count == stop:
            break

def read_text_from_corpus_ICWSM(corpus_path):
    print "okay"
    duplicates = set()
    #f2 = open("duplicate_texts.txt")
    f2 = open("all_duplicates.txt")
    for line in f2:
        duplicates.add(int(line))
    f2.close()

    f2= open("new_bad_docs_lem.txt")
    for line in f2:
        duplicates.add(int(line.strip()))
    f2.close()

    f = codecs.open(corpus_path,encoding="latin-1")
    sentence = []
    sentence_count = 0
    text = [[]]
    temp = {}
    doc_count = 0
    b_count = 0
    doc_min_word = 100
    done = False
    for line in f:
        try:
            word,pos = line.strip().split("\t")
        except:
            continue
        if word == "#":
            b_count = 1
        elif word == "@" and b_count == 1:
            b_count = 2
        elif b_count == 2 and word == "!":
            if len(temp)>= doc_min_word:
                if doc_count not in duplicates:
                    yield text
                    
                doc_count +=1
            text = [[]]
            temp = {}
            b_count = 0
        else:
            temp[word] = True
            word = word.lower()
            if doc_count in duplicates:
                continue        
            if pos == "SENT":
                text[-1].append([word,fix_pos(pos,word)])
                text.append([])
            else:
                if word.endswith("ing") and pos.startswith("NN"):
                    pass
                elif word in lemma_lookup_dict:
                    word = lemma_lookup_dict[word]
                elif word == "'d":
                    if pos.startswith("MD"):
                        word = "would"
                    elif pos.startswith("VH"):
                        word = "have"
                elif word == "'s":
                    if pos.startswith("VB"):
                        word = "be"
                    elif pos.startswith("VH"):
                        word = "have"
                        
                text[-1].append([word,fix_pos(pos,word)])
        if done:
            break


def read_sentence_from_corpus_ICWSM_quick(corpus_path,start=0,stop=-1,corpus_encoding="latin-1"):
    duplicates = set()
    #f2 = open("duplicate_texts.txt")
    f2 = open("all_duplicates.txt")
    for line in f2:
        duplicates.add(int(line))
    f2.close()

    f2= open("new_bad_docs_lem.txt")
    for line in f2:
        duplicates.add(int(line.strip()))
    f2.close()

    f2 = open("ICWSM_sentence_lookup.dat")
    sentence_lookup = cPickle.load(f2)
    f2.close()


    f = codecs.open(corpus_path,encoding=corpus_encoding)

    if start > 0:
        i = start
        while i not in sentence_lookup:
            i -=1
        sentence_count = i
        f.seek(sentence_lookup[i][1])
        doc_count = sentence_lookup[i][0]
    else:
        sentence_count = 0        
        doc_count = 0        

    sentence = []

    text = [[]]
    temp = {}

    b_count = 0
    doc_min_word = 100
    done = False
    for line in f:
        try:
            word,pos = line.strip().split("\t")
        except:
            continue
        if word == "#":
            b_count = 1
        elif word == "@" and b_count == 1:
            b_count = 2
        elif b_count == 2 and word == "!":
            if len(temp)>= doc_min_word:
                if doc_count not in duplicates:
                    for sentence in text:
                        if sentence and start <= sentence_count:
                            yield sentence
                        sentence_count += 1
                        if sentence_count == stop:
                            done = True
                            break
                    
                doc_count +=1
                if doc_count % 10000 == 0:
                    print doc_count
                    #print text
            text = [[]]
            temp = {}
            b_count = 0
        else:
            temp[word] = True
            if doc_count in duplicates:
                continue
            word = word.lower()
            if pos == "SENT":
                text[-1].append([word,fix_pos(pos,word)])
                text.append([])
            else:
                if word.endswith("ing") and pos.startswith("NN"):
                    pass
                elif word in lemma_lookup_dict:
                    word = lemma_lookup_dict[word]
                elif word == "'d":
                    if pos.startswith("MD"):
                        word = "would"
                    elif pos.startswith("VH"):
                        word = "have"
                elif word == "'s":
                    if pos.startswith("VB"):
                        word = "be"
                    elif pos.startswith("VH"):
                        word = "have"
                        
                text[-1].append([word,fix_pos(pos,word)])
        if done:
            break

def read_sentence_from_corpus_ICWSM_old(corpus_path,start=0,stop=-1,corpus_encoding="latin-1"):
    f = open("all_duplicates.txt")
    duplicates = set()
    for line in f:
        duplicates.add(int(line.strip()))
    f.close()

    f= open("new_bad_docs_lem_old.txt")
    for line in f:
        duplicates.add(int(line.strip()))
    f.close()

    doc_min_word = 100
    f = open(corpus_path)
    count = 0
    b_count = 0
    doc_count = 0
    temp = {}
    text = [[]]
    done = False
    sentence_count = 0
    for line in f:
        try:
            word,pos = line.strip().split("\t")
        except:
            #print line
            continue
        if word == "#":
            b_count = 1
        elif word == "@" and b_count == 1:
            b_count = 2
        elif b_count == 2 and word == "!":
            if len(temp)>= doc_min_word:
                if doc_count not in duplicates:
                    for sentence in text:
                        if sentence_count > start:
                            yield sentence
                        sentence_count += 1
                        if sentence_count == stop:
                            done = True
                            break

                if done:
                    break
                    
                doc_count +=1
                if doc_count % 10000 == 0:
                    print doc_count
                    #break

                #if doc_count % 100 == 0:
                #    print doc_count
                    #break

            text = [[]]
            temp = {}
        
        else:
            temp[word] = True

        if doc_count not in duplicates:
            word = word.lower()
            if pos == "SENT":
                text[-1].append([word,fix_pos(pos,word)])
                text.append([])
            else:
                if word.endswith("ing") and pos.startswith("NN"):
                    pass
                elif word in lemma_lookup_dict_old:
                    word = lemma_lookup_dict_old[word]
                elif word == "'d":
                    if pos.startswith("MD"):
                        word = "would"
                    elif pos.startswith("VH"):
                        word = "have"
                elif word == "'s":
                    if pos.startswith("VB"):
                        word = "be"
                    elif pos.startswith("VH"):
                        word = "have"
                        
                text[-1].append([word,fix_pos(pos,word)])

    


def read_sentence_from_corpus_ICWSM_quick_with_lemma(corpus_path,start=0,stop=-1,corpus_encoding="latin-1"):
    duplicates = set()
    #f2 = open("duplicate_texts.txt")
    f2 = open("all_duplicates.txt")
    for line in f2:
        duplicates.add(int(line))
    f2.close()

    f2= open("new_bad_docs_lem.txt")
    for line in f2:
        duplicates.add(int(line.strip()))
    f2.close()

    f2 = open("ICWSM_sentence_lookup.dat")
    sentence_lookup = cPickle.load(f2)
    f2.close()


    f = codecs.open(corpus_path,encoding=corpus_encoding)

    if start > 0:
        i = start
        while i not in sentence_lookup:
            i -=1
        sentence_count = i
        f.seek(sentence_lookup[i][1])
        doc_count = sentence_lookup[i][0]
    else:
        sentence_count = 0        
        doc_count = 0        

    sentence = []

    text = [[]]
    temp = {}

    b_count = 0
    doc_min_word = 100
    done = False
    for line in f:
        try:
            word,pos = line.strip().split("\t")
        except:
            continue
        if word == "#":
            b_count = 1
        elif word == "@" and b_count == 1:
            b_count = 2
        elif b_count == 2 and word == "!":
            if len(temp)>= doc_min_word:
                if doc_count not in duplicates:
                    for sentence in text:
                        if sentence and start <= sentence_count:
                            yield sentence
                        sentence_count += 1
                        if sentence_count == stop:
                            done = True
                            break
                    
                doc_count +=1
                if doc_count % 10000 == 0:
                    print doc_count
                    #print text
            text = [[]]
            temp = {}
            b_count = 0
        else:
            temp[word] = True
            if doc_count in duplicates:
                continue
            org_word = word
            word = word.lower()
            if pos == "SENT":
                text[-1].append([word,fix_pos(pos,word),word])
                text.append([])
            else:
                if word.endswith("ing") and pos.startswith("NN"):
                    pass
                elif word in lemma_lookup_dict:
                    word = lemma_lookup_dict[word]
                elif word == "'d":
                    if pos.startswith("MD"):
                        word = "would"
                    elif pos.startswith("VH"):
                        word = "have"
                elif word == "'s":
                    if pos.startswith("VB"):
                        word = "be"
                    elif pos.startswith("VH"):
                        word = "have"
                        
                text[-1].append([word,fix_pos(pos,word),org_word])
        if done:
            break

def read_sentence_from_corpus_simple(corpus_path,start=0,stop=-1):
    f = open(corpus_path)
    sent_count = 0
    sentence = []
    line = True
    for line in f:
        #print line
        try:
            line = line.decode("utf-8")
        except:
            continue
        stuff = line.strip().split("\t")
        try:
            sentence.append([stuff[2], fix_pos(stuff[1],stuff[2])])
        except:
            continue
        if stuff[1] == "SENT":
            if sent_count > start:
                yield sentence
            sentence = []
            sent_count +=1
            if sent_count == stop:
                break
    if sentence:
        yield sentence
        
#read_sentence_from_corpus = read_sentence_from_corpus_ja
#read_sentence_from_corpus = read_sentence_from_corpus_ICWSM
read_sentence_from_corpus = read_sentence_from_corpus_ICWSM_quick
#read_sentence_from_corpus = read_sentence_from_corpus_BNC
#read_sentence_from_corpus_with_lemma = read_sentence_from_corpus_ICWSM_quick_with_lemma
#read_sentence_from_corpus_with_lemma = read_sentence_from_corpus_BNC_with_lemma
#read_sentence_from_corpus = read_sentence_from_corpus_fr
#read_sentence_from_corpus = read_sentence_from_corpus_en_thq
