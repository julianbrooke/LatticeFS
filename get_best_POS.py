import gc
### this code finds the best (most common) POS tag sequence for a given set
### of n-grams (or skip/gap n-grams). The assumption is that, for the purposes
### of LPR, it is sufficient, and in fact in many ways better, to assume that
### there is exactly one correct tag sequence for any given n-gram (n >= 2)
### and to use only that sequence for calculating the conditional probability
### due the tags needed for the LPR calculation

import cPickle
import sys
from multiprocessing import Process,Queue
import lang_specific_helper
from multi_helper import *
from corpus_reader import read_sentence_from_corpus

gc.disable()


def get_pos_dict_setup(start_sent,end_sent,full_ngrams,full_skipgrams,rev_id_dict,POS_rev_id_dict,Q):
    best_pos_dict = {}
    best_pos_skip_dict = {}
    unigram_dict = {}
    count = 0
    for sentence in read_sentence_from_corpus(options.corpus,start_sent,end_sent):
        org_pos = [pair[1] for pair in sentence]
        words = []
        pos = []
        for i in range(len(sentence)):
            if sentence[i][1] in POS_rev_id_dict:
                pos.append(POS_rev_id_dict[sentence[i][1]])
            else:
                pos.append(-2)
            if sentence[i][0] in rev_id_dict:
                words.append(rev_id_dict[sentence[i][0]])
            else:
                words.append(-2)

            if words[i] != -2:
                uni_id = get_multi_id_range_both(words, pos, i, i+1)
                unigram_dict[uni_id] = unigram_dict.get(uni_id,0) + 1

        for i in range(len(words)):            
            matched = True
            j = i + 1
            while j < len(words) + 1 and matched:
                multi_id = get_multi_id_range(words,i,j)
                if multi_id in full_ngrams:
                    pos_multi_id = get_multi_id_range(pos,i,j)                          
                    if multi_id not in best_pos_dict:
                        best_pos_dict[multi_id] = {}
                    best_pos_dict[multi_id][pos_multi_id] = best_pos_dict[multi_id].get(pos_multi_id,0) + 1
                    k = 1
                    while j + k < len(words) and matches_gap(org_pos,j,j+k):
                        m = 1                    
                        while j +k +m < len(words) + 1:
                            multi_id = get_multi_id_range_skip(words,i,j,j+k,j+k+m)
                            if multi_id in full_skipgrams:
                                if multi_id not in best_pos_skip_dict:
                                    best_pos_skip_dict[multi_id] = {} 
                                pos_multi_id = get_multi_id_range_skip(pos,i,j,j+k,j+k+m)
                                best_pos_skip_dict[multi_id][pos_multi_id] = best_pos_skip_dict[multi_id].get(pos_multi_id,0) + 1

                            else:
                                break
                                

                            m +=1
                        

                        k+= 1
                else:
                    matched = False
                j+= 1
        if count % 10000 == 0:
            Q.put([unigram_dict,best_pos_dict,best_pos_skip_dict])
            best_pos_dict = {}
            best_pos_skip_dict = {}
            unigram_dict = {}
    Q.put(-1)


f = open("%s_options.dat" % sys.argv[1],"rb")
options = cPickle.load(f)
f.close()

lang_specific_helper.set_lang(options.lang, options.corpus)
matches_gap = lang_specific_helper.matches_gap


if __name__ == "__main__":

    f = open("%s_ngrams.dat"  % options.output,"rb")
    sentence_count = cPickle.load(f)
    id_dict = cPickle.load(f)
    full_ngrams = cPickle.load(f)
    full_skipgrams = cPickle.load(f)
    token_count = cPickle.load(f)
    POS_id_dict = cPickle.load(f)
    f.close()

    rev_id_dict = {}
    for ID in id_dict:
        rev_id_dict[id_dict[ID]] = ID

    POS_rev_id_dict = {}
    for ID in POS_id_dict:
        POS_rev_id_dict[POS_id_dict[ID]] = ID

    intervals = []
    for i in range(options.workers):
        intervals.append(i*(sentence_count/options.workers))
    intervals.append(sentence_count)

    Q = Queue()
    processes = []

    for i in range(options.workers):
        processes.append(Process(target=get_pos_dict_setup,args=(intervals[i],intervals[i+1],full_ngrams,full_skipgrams,rev_id_dict,POS_rev_id_dict,Q)))
        processes[-1].start()

    done_threads = 0
    best_pos_dict = {}
    best_pos_skip_dict = {}
    unigram_dict = {}
    best_instance_dict = {}
    skip_best_instance_dict = {}
    example_dict = {}


    while done_threads < options.workers:
        result = Q.get()
        if result == -1:
            done_threads += 1
        else:
            for unigram in result[0]:
                unigram_dict[unigram] = unigram_dict.get(unigram,0) + result[0][unigram]

            for ngram in result[1]:
                if ngram not in best_pos_dict:
                    best_pos_dict[ngram] = {}
                for pos in result[1][ngram]:
                    best_pos_dict[ngram][pos] = best_pos_dict[ngram].get(pos,0) + result[1][ngram][pos]

            for ngram in result[2]:
                if ngram not in best_pos_skip_dict:
                    best_pos_skip_dict[ngram] = {}
                for pos in result[2][ngram]:
                    best_pos_skip_dict[ngram][pos] = best_pos_skip_dict[ngram].get(pos,0) + result[2][ngram][pos]

    for ngram in best_pos_dict:
        best = 0
        best_pos = 0
            
        for pos in best_pos_dict[ngram]:
            if best_pos_dict[ngram][pos] > best:
                best = best_pos_dict[ngram][pos]
                best_pos = pos
        best_pos_dict[ngram] = best_pos


    for ngram in best_pos_skip_dict:
        best = 0
        best_pos = 0
        for pos in best_pos_skip_dict[ngram]:
            if best_pos_skip_dict[ngram][pos] > best:
                best = best_pos_skip_dict[ngram][pos]
                best_pos = pos
        best_pos_skip_dict[ngram] = best_pos


    f = open("%s_best_POS.dat" % options.output,"wb")
    cPickle.dump(best_pos_dict,f,-1)
    cPickle.dump(best_pos_skip_dict,f,-1)
    cPickle.dump(unigram_dict,f,-1)
    f.close()
    
