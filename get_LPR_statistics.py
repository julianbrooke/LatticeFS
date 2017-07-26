### This script is responsible for collecting other statistics and then
### calculating an LPR (that is, a lexical predictability ratio)
### for each element of each n-gram. It requires that the set of n-grams
### has already been determined, and the most common POS tag sequence
### for each n-grams (n > 2) has been identified, since it calculates the
### conditional probability using only that sequence (this is both practical
### and seems to give a better result).
###


import gc
import copy
import math
import sys
import cPickle
from multiprocessing import Process,Queue,Manager
from pos_helper import matches_gap_en,matches_gap_fr,matches_gap_ja, matches_gap_hr,matches_gap_en_bnc, matches_gap_universal
from multi_helper import *
#from corpus_reader import read_sentence_from_corpus
from corpus_reader import read_sentence_from_corpus_ICWSM_quick,read_sentence_from_corpus_BNC,read_sentence_from_corpus_ja,read_sentence_from_corpus_hr,read_sentence_from_corpus_simple
gc.disable()
import codecs


def prepare_freq_dicts(id_dict,full_ngrams, full_skipgrams,best_pos_dict,best_pos_skip_dict):

    ### to calculate LPR, four basic types of counts are necessary: the raw n-gram
    ### count, the n-gram count with each element missing (a wild card), a
    ### the count with just POS tags for all elements except one (which is the word
    ### and its tag) and the count with just POS tags and one wild card

    #fout = codecs.open("missing_POS.txt","w",encoding ="utf-8")

    pos_counts = {}
    pos_skip_counts = {}
    for ngram in full_skipgrams:
        words = decode_id(ngram)

        for i in range(1,len(words)):
            pos_skip_counts[get_multi_id_range_wild_skip(words,1,words[0] + 2, words[0] + 2, len(words), i)] = 0
        #if best_pos_skip_dict[ngram] == 0:
        #    fout.write("|".join([id_dict[word] for word in words[1:]]) + "\n")
        #    continue

        pos = decode_id(best_pos_skip_dict[ngram])

        for i in range(1,len(words)):
            pos_skip_counts[get_multi_id_range_one_word_skip(pos,words,1,words[0] + 2, words[0] + 2, len(words),i)] = 0
            pos_skip_counts[get_multi_id_range_wild_skip(pos,1,words[0] + 2, words[0] + 2, len(words),i)] = 0
            
    pos_skip_path = set()


    ngrams = pos_skip_counts.keys()
    ngrams.sort()
    count = 0

    ### the matcher for does a greedy search, but in rare cases, related to
    ### variations in best POS, the path to a particular desired word/POS
    ### combination does not exist. This code fills in that gaps so all n-grams
    ### we want are accessible by the statistic  


    for ngram in ngrams:
        stuff = decode_id(ngram)
        skip_index = stuff[0] + 2
        wild_index = -1
        for i in range(1,len(stuff)):
            if stuff[i] in id_dict and id_dict[stuff[i]] == "*":
                wild_index = i
       
        if wild_index != -1:
            to_add = []
            candidate = None
            start_index = 1
            end_index = len(stuff)
            curr_wild = wild_index
            while candidate not in pos_skip_counts and candidate not in pos_skip_path and end_index - start_index > 1:
                if candidate:
                    to_add.append(candidate)
                if wild_index > skip_index and skip_index - start_index > 1:
                    start_index += 1

                elif wild_index <= skip_index and end_index - skip_index > 1:
                    end_index -= 1

                elif skip_index - start_index == 1:
                    end_index -= 1
                    if end_index <= wild_index:
                        curr_wild -= 1

                elif end_index - skip_index == 1:
                    start_index += 1
                    if start_index > wild_index:
                        curr_wild += 1


                candidate = get_multi_id_range_wild_skip(stuff,start_index,skip_index,skip_index,end_index,curr_wild)
                
            for item in to_add:
                pos_skip_path.add(item)


    for ngram in full_ngrams:
        if not is_multi(ngram):
            continue
        words = decode_id(ngram)
        
        for i in range(len(words)):
            pos_counts[get_multi_id_range_wild(words,0,len(words), i)] = 0
        pos = decode_id(best_pos_dict[ngram])
        if best_pos_dict[ngram] == 0:
            #fout.write("#".join([id_dict[word] for word in words]) + "\n")
            continue
        for i in range(len(words)):
            pos_counts[get_multi_id_range_one_word(pos,words,0,len(words),i)] = 0
            pos_counts[get_multi_id_range_wild(pos,0,len(words),i)] = 0
    #fout.close()
    pos_path = set()

    ngrams = pos_counts.keys()
    ngrams.sort()
    for ngram in ngrams:
        stuff = decode_id(ngram)
        wild_index = -1
        for i in range(len(stuff)):
            if stuff[i] in id_dict and id_dict[stuff[i]] == "*":
                wild_index = i
        if wild_index != -1:
            to_add = []
            candidate = None
            start_index = 0
            end_index = len(stuff)
            while candidate not in pos_counts and candidate not in pos_path and end_index - start_index > 1:
                if candidate:
                    to_add.append(candidate)
                if wild_index != start_index:
                    start_index += 1
                else:
                    end_index -= 1

                candidate = get_multi_id_range_wild(stuff,start_index,end_index,wild_index)
                
                
            for item in to_add:
                pos_path.add(item)

    return pos_counts,pos_path,pos_skip_counts,pos_skip_path


def get_pos_counts(start_sent,end_sent,pos_counts,pos_path, pos_skip_counts, pos_skip_path,rev_id_dict,POS_rev_id_dict,Q):
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
        for i in range(len(sentence)):
            find_wild_pos = True
            j = i + 2
            find_wild_word = True

            while j < len(sentence) + 1 and (find_wild_pos or find_wild_word):
            
                        
                k = i
                inner_wild_pos = False
                inner_wild_word = False
                
                while k < j:
                    if find_wild_word:
                         multi_id = get_multi_id_range_wild(words,i,j,k)                            
                         if multi_id in pos_counts:                            
                             pos_counts[multi_id] += 1
                             inner_wild_word = True
                             
                    if find_wild_pos:
                        multi_id = get_multi_id_range_wild(pos,i,j,k)
                        if multi_id in pos_counts:
                            pos_counts[multi_id] += 1
                            inner_wild_pos = True
                        elif multi_id in pos_path:
                            inner_wild_pos = True

                        multi_id = get_multi_id_range_one_word(pos,words,i,j,k)
                        if multi_id in pos_counts:                         
                            pos_counts[multi_id] += 1
                    k += 1
                find_wild_pos = inner_wild_pos
                find_wild_word = inner_wild_word

                j += 1
            if i == 0:
                continue
            j = i + 1
            while matches_gap(org_pos,i,j) and j < len(sentence):

                pos_succeed_set = set()
                pos_w_ngram_succeed_set = set()
                ngram_succeed_set = set()
                for n in (i-1,j):
                    wild_multi_pos = get_multi_id_range_wild_skip(pos,i-1,i,j,j+1,n)
                    if wild_multi_pos in pos_skip_counts or wild_multi_pos in pos_skip_path:
                        pos_succeed_set.add((i-1,j+1,n))
                        if wild_multi_pos in pos_skip_counts:
                            pos_skip_counts[wild_multi_pos] += 1
                            posword_multi = get_multi_id_range_one_word_skip(pos,words,i-1,i,j,j+1,n)
                            if posword_multi in pos_skip_counts:
                                pos_skip_counts[posword_multi] += 1
                        wild_multi = get_multi_id_range_wild_skip(words,i-1,i,j,j+1,n)
                        if wild_multi in pos_skip_counts:
                            ngram_succeed_set.add((i-1,j+1,n))
                            pos_skip_counts[wild_multi] += 1

                total_rounds = 0
                while (pos_succeed_set or ngram_succeed_set) and total_rounds < 7:
                    total_rounds += 1
                    if pos_succeed_set:
                        new_pos_succeed_set = set()
                        temp_set = set()
                        for start,end,wild in pos_succeed_set:
                            range_pairs = []
                            if start - 1 >= 0:
                                range_pairs.append((start - 1, end,start - 1))
                            if end < len(sentence):
                                range_pairs.append((start,end + 1,end))
                            for range_pair in range_pairs:
                                for my_wild in ([wild,range_pair[2]]):
                                    wild_multi_pos = get_multi_id_range_wild_skip(pos,range_pair[0],i,j,range_pair[1],my_wild)                                                
                                    if wild_multi_pos in pos_skip_counts or wild_multi_pos in pos_skip_path:
                                        new_pos_succeed_set.add((range_pair[0],range_pair[1],my_wild))
                                        if wild_multi_pos in pos_skip_counts:
                                            temp_set.add(wild_multi_pos)
                                            posword_multi = get_multi_id_range_one_word_skip(pos,words,range_pair[0],i,j,range_pair[1],my_wild)
                                    
                                            if posword_multi in pos_skip_counts:                                                    
                                                temp_set.add(posword_multi)
                        for posword_multi in temp_set:
                            pos_skip_counts[posword_multi] += 1
                        pos_succeed_set = new_pos_succeed_set

                    if ngram_succeed_set:
                        new_ngram_succeed_set = set()
                        temp_set = set()
                        for start,end,wild in ngram_succeed_set:
                            range_pairs = []
                            if start - 1 >= 0:
                                range_pairs.append((start - 1, end,start - 1))
                            if end < len(sentence):
                                range_pairs.append((start,end + 1,end))
                            for range_pair in range_pairs:
                                for my_wild in ([wild,range_pair[2]]):
                                    wild_multi = get_multi_id_range_wild_skip(words,range_pair[0],i,j,range_pair[1],my_wild)                                          
                                    if wild_multi in pos_skip_counts:
                                        new_ngram_succeed_set.add((range_pair[0],range_pair[1],my_wild))
                                        temp_set.add(wild_multi)
                        ngram_succeed_set = new_ngram_succeed_set
                        for wild_multi in temp_set:
                            pos_skip_counts[wild_multi] += 1

                j += 1
    Q.put([pos_counts,pos_skip_counts])



f = open("temp_options_%s.dat" % sys.argv[1],"rb")
options = cPickle.load(f)
f.close()
if options.lang == "uni":
    matches_gap = matches_gap_universal
    read_sentence_from_corpus = read_sentence_from_corpus_BNC
elif options.lang == "en":
    if "bnc" in options.corpus:
        matches_gap = matches_gap_en_bnc
        read_sentence_from_corpus = read_sentence_from_corpus_BNC
    else:
        matches_gap = matches_gap_en
        read_sentence_from_corpus = read_sentence_from_corpus_ICWSM_quick
elif options.lang == "ja":
    matches_gap = matches_gap_ja
    read_sentence_from_corpus = read_sentence_from_corpus_ja
elif options.lang == "hr":
    matches_gap = matches_gap_hr
    read_sentence_from_corpus = read_sentence_from_corpus_hr    
elif options.lang == "fr":
    matches_gap = matches_gap_fr
else:
    matches_gap = matches_gap_en
    read_sentence_from_corpus = read_sentence_from_corpus_simple  


if __name__ == "__main__":

    f = open("temp_ngrams_%s.dat" % sys.argv[1],"rb")
    id_dict = cPickle.load(f)
    full_ngrams = cPickle.load(f)
    full_skipgrams = cPickle.load(f)
    token_count = cPickle.load(f)
    sentence_count = cPickle.load(f)
    POS_id_dict = cPickle.load(f)
    f.close()
    id_dict[wild_card] = "*"

    f = open("temp_best_POS_%s.dat" % sys.argv[1],"rb")
    best_pos_dict = cPickle.load(f)
    best_pos_skip_dict = cPickle.load(f)
    f.close()

    pos_counts,pos_path,skip_pos_counts,skip_pos_path = prepare_freq_dicts(id_dict,full_ngrams, full_skipgrams,best_pos_dict,best_pos_skip_dict)

    rev_id_dict = {}
    for ID in id_dict:
        rev_id_dict[id_dict[ID]] = ID

    POS_rev_id_dict = {}
    for ID in POS_id_dict:
        POS_rev_id_dict[POS_id_dict[ID]] = ID

    processes = []
    Q = Queue()

    intervals = []
    for i in range(options.workers):
        intervals.append(i*(sentence_count/options.workers))
    intervals.append(sentence_count)

    for i in range(options.workers):
        processes.append(Process(target=get_pos_counts,args=(intervals[i],intervals[i+1],pos_counts,pos_path,skip_pos_counts,skip_pos_path, rev_id_dict,POS_rev_id_dict,Q)))
        processes[-1].start()

    done_threads = 0
    while done_threads < options.workers:
        result = Q.get()
        done_threads += 1
        for ngram in result[0]:
            pos_counts[ngram] += result[0][ngram]
        for ngram in result[1]:
            skip_pos_counts[ngram] += result[1][ngram]

    print "done counting"
    cond_prob_dict = {}
    skip_cond_prob_dict = {}
    for ngram in full_skipgrams:
        words = decode_id(ngram)
        pos = decode_id(best_pos_skip_dict[ngram])
        skip_cond_prob_dict[ngram] = []
        for i in range(1,len(words)):
            skip_cond_prob_dict[ngram].append(math.log(full_skipgrams[ngram],2) - math.log(skip_pos_counts[get_multi_id_range_wild_skip(words,1,words[0] + 2, words[0] + 2, len(words), i)],2) - math.log(skip_pos_counts[get_multi_id_range_one_word_skip(pos,words,1,words[0] + 2, words[0] + 2, len(words),i)],2) + math.log(skip_pos_counts[get_multi_id_range_wild_skip(pos,1,words[0] + 2, words[0] + 2, len(words),i)],2))

    for ngram in full_ngrams:
        if is_multi(ngram):
            words = decode_id(ngram)
            pos = decode_id(best_pos_dict[ngram])
            
            cond_prob_dict[ngram] = []
            for i in range(len(words)):
                cond_prob_dict[ngram].append(math.log(full_ngrams[ngram],2) - math.log(pos_counts[get_multi_id_range_wild(words,0,len(words), i)],2) - math.log(pos_counts[get_multi_id_range_one_word(pos,words,0,len(words),i)],2) + math.log(pos_counts[get_multi_id_range_wild(pos,0,len(words),i)],2))

    fout = open("temp_LPR_stats_%s.dat" % sys.argv[1], "wb")
    cPickle.dump(cond_prob_dict,fout,-1)
    cPickle.dump(skip_cond_prob_dict,fout,-1)
    cPickle.dump(pos_counts,fout,-1)
    cPickle.dump(skip_pos_counts,fout,-1)
    fout.close()
   
