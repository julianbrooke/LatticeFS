# -*- coding: utf-8 -*-
### This script calculates an initial set of n-gram and skip (gap) n-grams
### It first does an initial pass and sets an exact n-gram frequency cutoff;
### words above that cutoff are removed, and id numbers assigned
### Then, iteratively, the n is increased and any n-gram that is still above
### the threshold is also added to the initial set of n-gram. POS tags are
### also assigned (different) ids at this step 


import cPickle
import re
from pos_helper import matches_gap_en,matches_gap_fr,matches_gap_ja,matches_gap_ja_simple, matches_gap_hr,matches_gap_en_bnc,matches_gap_universal
from multiprocessing import Process,Queue
from multi_helper import *
from corpus_reader import read_sentence_from_corpus_ICWSM_quick,read_sentence_from_corpus_BNC,read_sentence_from_corpus_ja,read_sentence_from_corpus_hr,read_sentence_from_corpus_simple
import sys

import gc
gc.disable()

good_word = re.compile("^[A-Za-z]+([A-Za-z']*|[A-Za-z\-]+[A-Za-z]+)$")

bad_ja_word = set(u"０１２３４５６７８９＞｛　｝（　）［　］【　】、，…‥。・「　」『　』　〜：！？♪.,'-?!<>[]{}|“／”；−┐▲．＿卍■Г×┘〕＊＾’→●￣☆〇ＸＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ")

#bad_ja_word = re.compile(u"記号|URL|web誤脱|空白")


def check_good_en(pair):
    return good_word.search(pair[0])    

def all_good_words_en(span,start,end): # used to exclude nonalphabetic words from gaps
    for i in range(start,end):
        if not good_word.search(span[i][0]):
            return False
    return True

def check_good_ja(pair):
    #if u"記号" in span[i][1] or span[i][1] == u"URL" or span[i][1] = "web誤脱" or span[i][1] = "空白":
    return pair[0] not in bad_ja_word

def all_good_words_ja(span,start,end):
    for i in range(start,end):
        if not check_good_word(span[i]):
            return False

    return True



def get_ngrams(n,start,end,full_ngrams,full_skipgrams,rev_id_dict,options,return_Q):
    gap = 0
    temp_ngrams = {}
    temp_skipgrams = {}
    for sentence in read_sentence_from_corpus(options.corpus,start=start,stop=end):
        words = []
        pos = []
        for i in range(len(sentence)):
            pos.append(sentence[i][1])
            if sentence[i][0] in rev_id_dict:
                words.append(rev_id_dict[sentence[i][0]])
            else:
                words.append(-2)
        last_matched = set()
        last_matched_other = False
        for i in range(len(words) - (n - 1)):
            matched_other = False
            multi_id = get_multi_id_range(words,i,i+n - 1)
            if multi_id in full_ngrams:
                matched_other = True
                if last_matched_other:
                    ngram = get_multi_id_mixed(words[i-1],multi_id)
                    temp_ngrams[ngram] = temp_ngrams.get(ngram,0) + 1
            last_matched_other = matched_other
        '''
        at_point = False
        for i in range(len(words) - 3):
            if get_multi_id(words[i:i+4]) == 3206725044157547480 and n == 2:
                print "at point"
                print pos[i:i+4]
                at_point = True
                point_start = i
        '''
        for i in range(len(words) - 2):
            if words[i] != -2:
                j = i + 2
                '''
                if at_point and i == point_start:
                    print i
                    print j
                    print j < len(words)
                    print matches_gap(pos, i + 1, j)
                    print pos[i+1:j]
                    print all_good_words(sentence,i+1,j)
                '''
                while j < len(words) and matches_gap(pos, i + 1, j) and all_good_words(sentence,i+1,j) and words[j] != -2:
                    if n == 2:
                        multi_id = get_multi_id([0,words[i],words[j]])
                        '''
                        if multi_id == 12232324808704:
                            gap += 1
                            print "added gap3"
                        '''
                        temp_skipgrams[multi_id] = temp_skipgrams.get(multi_id,0) + 1
                    else:
                        for k in range(n -2):
                            start_index = i-(n - 3) + k
                            end_index = j+k + 1
                            if start_index < 0 or end_index > len(sentence):
                                continue
                            temp_words = []
                            temp_words.append(n-k - 3)
                            temp_words.extend(words[start_index:i + 1])
                            temp_words.extend(words[j:end_index])
                            ID = get_multi_id(temp_words)
                            if ID in full_skipgrams:
                                if start_index > 0 and get_multi_id(words[start_index-1:i+1]) in full_ngrams:
                                    temp_words = []
                                    temp_words.append(n-k - 2)
                                    temp_words.extend(words[start_index - 1:i + 1])
                                    temp_words.extend(words[j:end_index])
                                    multi_id = get_multi_id(temp_words)
                                    '''
                                    if multi_id == 12232324808704:
                                        gap += 1
                                        print "added gap1"
                                    '''
                                    temp_skipgrams[multi_id] = temp_skipgrams.get(multi_id,0) + 1
                                if i == start_index and end_index < len(sentence) and get_multi_id(words[j:end_index + 1]) in full_ngrams:
                                    temp_words = []
                                    temp_words.append(n-k - 3)
                                    temp_words.extend(words[start_index:i + 1])
                                    temp_words.extend(words[j:end_index + 1])
                                    multi_id = get_multi_id(temp_words)
                                    '''
                                    if multi_id == 12232324808704:
                                        gap += 1
                                        print "added gap2"
                                    '''
                                    temp_skipgrams[multi_id] = temp_skipgrams.get(multi_id,0) + 1                                      
                    j+=1
                    '''
                    if at_point and i == point_start:
                        print i
                        print j
                        print j < len(words)
                        print matches_gap(pos, i + 1, j)
                        print all_good_words(sentence,i+1,j)
                    '''
    '''
    print "total_gap"
    print gap
    '''
    return_Q.put((temp_ngrams,temp_skipgrams))


not_wanted_en_icwsm = set(["en","enhy","www","http","im", "dont", "didnt","doesnt","cant","wont","shouldnt","aint","ive","whats","arent","couldnt", "hadnt","hasnt","havent","isnt","shes","wasnt","werent","whod","wouldnt","youre","youve","whos","thats","wheres","com"])
not_wanted_fr = set(["www","http","com"])
not_wanted_ja = set()

f = open("temp_options_%s.dat" % sys.argv[1],"rb")
options = cPickle.load(f)
f.close()
if options.lang == "uni":
    not_wanted = set([])
    read_sentence_from_corpus = read_sentence_from_corpus_BNC
    matches_gap = matches_gap_universal
    check_good_word = check_good_en
    all_good_words = all_good_words_en
elif options.lang == "fr":
    not_wanted = not_wanted_fr
    matches_gap = matches_gap_fr
    check_good_word = check_good_en
    all_good_words = all_good_words_en
    #suffix = "fr"
elif options.lang == "ja":
    read_sentence_from_corpus = read_sentence_from_corpus_ja
    not_wanted = not_wanted_ja
    #matches_gap = matches_gap_ja
    matches_gap = matches_gap_ja_simple
    check_good_word = check_good_ja
    all_good_words = all_good_words_ja
    #suffix = "ja"
elif options.lang == "en":
    if "bnc" in options.corpus:
        matches_gap = matches_gap_en_bnc
        read_sentence_from_corpus = read_sentence_from_corpus_BNC
        not_wanted = set([])
        #suffix = "BNC"
    else:
        matches_gap = matches_gap_en
        read_sentence_from_corpus = read_sentence_from_corpus_ICWSM_quick
        not_wanted = not_wanted_en_icwsm
        #suffix = "ICWSM
    check_good_word = check_good_en
    all_good_words = all_good_words_en
else:
    matches_gap = matches_gap_en
    read_sentence_from_corpus = read_sentence_from_corpus_simple
    not_wanted = not_wanted_en_icwsm
    check_good_word = check_good_en
    all_good_words = all_good_words_en    

if __name__ == "__main__":


    full_ngrams = {}
    full_skipgrams = {}
    temp_ngrams = {}
    POS_rev_id_dict = {}
    POS_id_dict = {}
    token_count = 0
    sentence_count = 0
    for sentence in read_sentence_from_corpus(options.corpus,stop=options.sentences):
        sentence_count += 1
        token_count += len(sentence)
        for pair in sentence:
            #if pair[0] == u"ケン":
            #    print "|".join([temp_pair[0] for temp_pair in sentence])
            #    print "|".join([temp_pair[1] for temp_pair in sentence])
            #    print check_good_word(pair)
            if check_good_word(pair) and not pair[0] in not_wanted:
                temp_ngrams[pair[0]] = temp_ngrams.get(pair[0],0) + 1
                if pair[1] not in POS_rev_id_dict:
                    POS_rev_id_dict[pair[1]] = len(POS_rev_id_dict) + 1
                    POS_id_dict[POS_rev_id_dict[pair[1]]] = pair[1]
        #if sentence_count == 10000000:
        #    break
        #for i in range(len(sentence)):
        #    print matches_gap([sentence[i][1]],0,1)

    cutoff = token_count/options.frequency


    for wp in temp_ngrams.keys():
        if temp_ngrams[wp] < cutoff:
            del temp_ngrams[wp]

    if not options.silent:
        print "initial unigram pass complete"
        print "sentences:%d" % sentence_count
        print "tokens:%d" % token_count
        print "types after filtering:%d" % len(temp_ngrams)
        print "frequency threshold:%d" % cutoff

    #print kfdjsldkfj

    if is_multi(len(temp_ngrams) + len(POS_id_dict)):
        print "WARNING: you have too many types in your vocabulary, increase your frequency cutoff!"
        raise Exception()

    id_dict = {}
    rev_id_dict = {}

    for wp in temp_ngrams:
        rev_id_dict[wp] = len(rev_id_dict) + 1 + len(POS_id_dict)
        id_dict[rev_id_dict[wp]] = wp
        full_ngrams[rev_id_dict[wp]] = temp_ngrams[wp]

    return_Q = Queue()

    intervals = []
    for i in range(options.workers):
        intervals.append(i*(sentence_count/options.workers))
    intervals.append(sentence_count)

    for n in range(2,options.n + 1):
        temp_ngrams = {}
        temp_skipgrams = {}
        workers = []
        for w in range(options.workers):
            workers.append(Process(target=get_ngrams,args=(n,intervals[w],intervals[w+1],full_ngrams,full_skipgrams,rev_id_dict,options,return_Q)))
            workers[-1].start()
        completed = 0
        while completed < len(workers):
            part_ngrams, part_skipgrams = return_Q.get()
            for ngram in part_ngrams:
                temp_ngrams[ngram] = temp_ngrams.get(ngram,0) + part_ngrams[ngram]
            for skipgram in part_skipgrams:
                temp_skipgrams[skipgram] = temp_skipgrams.get(skipgram,0) + part_skipgrams[skipgram]
            completed += 1

        ngram_count =0 

        for ngram in temp_ngrams:
            if ngram == 0:
                continue
            if temp_ngrams[ngram] >= cutoff:
                ngram_count += 1
                full_ngrams[ngram] = temp_ngrams[ngram]


        print len(temp_skipgrams)
        skipgram_count = 0

        for ngram in temp_skipgrams:
            if ngram == 0:
                continue
            if temp_skipgrams[ngram] >= cutoff:
                skipgram_count += 1
                full_skipgrams[ngram] = temp_skipgrams[ngram]

        if not options.silent:
            print "%d-gram pass complete" % n
            print "added %d n-grams" % ngram_count
            print "added %d gapped n-grams" % skipgram_count
    #for ngram in full_ngrams:
    #    print " ".join(id_dict[word] for word in decode_id(ngram))
    fout = open("temp_ngrams_%s.dat"  % options.lang,"wb")
    cPickle.dump(id_dict,fout,-1)
    cPickle.dump(full_ngrams,fout,-1)
    cPickle.dump(full_skipgrams,fout,-1)
    cPickle.dump(token_count,fout,-1)
    cPickle.dump(sentence_count,fout,-1)
    cPickle.dump(POS_id_dict,fout,-1)
    fout.close()



