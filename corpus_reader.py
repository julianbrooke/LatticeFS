# -*- coding: UTF-8 -*-
import codecs

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
