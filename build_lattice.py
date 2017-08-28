# -*- coding: utf-8 -*-
### This code defines a node in the lattice, and builds a lattice of these nodes based on n-gram subsumption relationships. When the process is complete,
### the above nodes for each node contain a list of nodes whose n-grams contain the present n-gram plus one more word, and below_nodes are n-grams which
### have one word missing (possibly an internal one). Syntactic_predictability is the minLPR metric defined in the paper, and is calculated here from the
### individual lexical predictability ratios from get_LPR_statistics.py. The nodes from the lattice are contained in the nodes list, which is sorted by
### frequency (from most to least frequent)

import cPickle
import gc
import sys
from multi_helper import *
import lang_specific_helper
from corpus_reader import read_sentence_from_corpus
import math
from multiprocessing import Process,Queue,Manager
from collections import Counter
gc.disable()


min_overlaps = 5 # don't include any overlaps with less than this count
cover_cutoff = 2.0/3.0 # ratio used for deciding if one n-gram (hard) covers another
min_syn_pred_log = 1.0 # if the log of the syntactic predictabilty (minLPR) less
                       # than this, node is turned off (like hard cover)


class Node:
    def __init__(self,ngram, id_num, pos_num, count, syntactic_predictability,length,is_skip):
        self.ngram = ngram
        self.id_num = id_num
        self.pos_num = pos_num
        self.count = count
        self.log_count = math.log(count,2)
        self.syntactic_predictability = syntactic_predictability
        self.length = length
        self.above_nodes = []
        self.below_nodes = []
        self.overlaps = {}
        self.has_pronoun = False
        self.is_skip = is_skip
        self.is_covered = False

    def __hash__(self):
        return self.id_num


    def __cmp__(self,other):
        this_num = self.count
        that_num = other.count
        if this_num > that_num:
            return -1
        elif this_num == that_num:
            if self.syntactic_predictability > other.syntactic_predictability:
                return -1
            elif self.syntactic_predictability < other.syntactic_predictability:
                return 1
            else:
                return 0
        else:
            return 1
             


def get_syntactic_predictability_reg(words,cond_prob_dict):
    final_set = []
    for i in range(len(words)):
        temp_set = []
        for j in range(0,i + 1):
            for k in range(i +1, len(words) + 1):
                if k - j == 1:
                    continue
                temp_set.append(cond_prob_dict[get_multi_id_range(words,j, k)][i-j])
        final_set.append(max(temp_set))
    if len(final_set) == 2:
        return max(min(final_set),0)
    else:
        return final_set

def get_syntactic_predictability_skip(words,loc,cond_prob_dict,cond_prob_dict_skip):
    final_set = []
    for i in range(len(words)):
        temp_set = []
        for j in range(0,i + 1):
            for k in range(i +1, len(words) + 1):
                if k - j == 1:
                    continue
                if j <= loc and k > loc + 1:
                    temp_set.append(cond_prob_dict_skip[get_multi_id_range_skip(words,j, loc + 1, loc + 1, k)][i-j])
                else:
                    temp_set.append(cond_prob_dict[get_multi_id_range(words,j, k)][i-j])
        final_set.append(max(temp_set))

    if len(final_set) == 2:
        return max(min(final_set),0)
    else:
        return final_set


def check_covered(node):
    org_count = node.count
    node.is_covered = False

    if node.has_pronoun:
        found = False
        for bnode in node.below_nodes: # once above
            if not node_lookup[bnode].has_pronoun and (org_count > node_lookup[bnode].count * cover_cutoff):
                found = True
        if not found:
            node.is_covered = True
    ref_count = org_count * cover_cutoff                

    for anode in node.above_nodes:
        if node_lookup[anode].count > ref_count:
            node.is_covered = True
    
def get_all_nodes_down_covered(ref_node):
    ref_count = ref_node.count * (1/cover_cutoff)
    new_nodes = ref_node.below_nodes
    good_nodes = set()
    while new_nodes:
        next_nodes = set()
        for node_id in new_nodes:
            if node_lookup[node_id].count < ref_count:
                good_nodes.add(node_lookup[node_id])
                next_nodes.update(node_lookup[node_id].below_nodes)
        new_nodes = next_nodes
    return good_nodes


def set_shared_syntactic_predictability(ref_node):
    local_nodes = get_all_nodes_down_covered(ref_node)
    local_nodes.add(ref_node)
    ref_node.syntactic_predictability = max([node.syntactic_predictability for node in local_nodes])
    if ref_node.syntactic_predictability < min_syn_pred_log:
        ref_node.is_covered = True


def properly_overlaps(range1,range2,sentence):
    nums1 = set(range(range1[0],range1[1]))
    if len(range1) == 5:
        nums1.update(range(range1[2], range1[3]))
        
    nums2 = set(range(range2[0],range2[1]))
    if len(range2) == 5:
        nums2.update(range(range2[2], range2[3]))
    intersected = nums1.intersection(nums2)

    return not nums1.issubset(nums2) and not nums2.issubset(nums1) and len(nums1.intersection(nums2)) > 0


def get_paired_counts(start_sent,end_sent,all_ngrams,rev_id_dict,inQ,Q):
    while True:
        wanted= inQ.get()
        if wanted == None:
            break
        overlaps = {}
        sentence_count = 0
        for sentence in read_sentence_from_corpus(options.corpus,start_sent,end_sent):
            sentence_count += 1
            if sentence_count % 10000 == 0:
                #print sentence_count
                sys.stdout.flush()
            org_pos = [pair[1] for pair in sentence]
            temp_words = []
            words = []
            for i in range(len(sentence)):
                if sentence[i][0] in rev_id_dict:
                    temp_words.append(sentence[i][0])
                    words.append(rev_id_dict[sentence[i][0]])
                else:
                    words.append(-2)
            temp_set = set()
            ranges = []
            for i in range(len(words)):            
                matched = True
                j = i + 1
                while j < len(words) + 1 and matched:
                    multi_id = get_multi_id_range(words,i,j)
                    if multi_id in all_ngrams:
                        if multi_id in wanted:
                            ranges.append([i, j,multi_id])
                        k = 1
                        while j + k < len(words) and matches_gap(org_pos,j,j+k):
                            m = 1                    
                            while j +k +m < len(words) + 1:
                                multi_id = get_multi_id_range_skip(words,i,j,j+k,j+k+m)
                                if multi_id in all_ngrams:
                                    if multi_id in wanted:
                                        ranges.append([i,j,j+k,j+k+m,multi_id])
                                else:
                                    break
                                m +=1                            
                            k+= 1
                    else:
                        matched = False
                    j+= 1

            for i in range(len(ranges)):
                j = i + 1
                while j < len(ranges) and ranges[j][0] + 1 <= ranges[i][-2]:
                    if properly_overlaps(ranges[i],ranges[j],sentence):
                        to_sort = [ranges[i][-1],ranges[j][-1]]
                        to_sort.sort()
                        pair = tuple(to_sort)
                        overlaps[pair] = overlaps.get(pair,0) + 1
                    j += 1

            if sentence_count % 1000 == 0:
                Q.put(overlaps)
                overlaps = {}
        Q.put(overlaps)
        Q.put(-1)


if __name__ == "__main__":

    f = open("%s_options.dat" % sys.argv[1],"rb")
    options = cPickle.load(f)
    f.close()

    lang_specific_helper.set_lang(options.lang, options.corpus)
    has_pronoun = lang_specific_helper.has_pronoun
    matches_gap = lang_specific_helper.matches_gap




    f = open("%s_ngrams.dat" % options.output,"rb")
    sentence_count = cPickle.load(f)
    id_dict = cPickle.load(f)
    word_counts = cPickle.load(f)
    skip_word_counts = cPickle.load(f)   
    f.close()

    rev_id_dict = {}
    for ID in id_dict:
        rev_id_dict[id_dict[ID]] = ID

    all_ngrams = set(word_counts)
    all_ngrams.update(skip_word_counts)
    word_counts = None
    skip_word_counts = None



    intervals = []
    for i in range(options.workers):
        intervals.append(i*(sentence_count/options.workers))
    intervals.append(sentence_count)


    processes = []
    Q = Queue()
    inQs = []

                          
            
    for i in range(options.workers):
        inQ = Queue()
        inQs.append(inQ)
        processes.append(Process(target=get_paired_counts,args=(intervals[i],intervals[i+1],all_ngrams,rev_id_dict,inQ,Q)))
        processes[-1].daemon = True
        processes[-1].start()

    all_ngrams = None
    f = open("%s_ngrams.dat" % options.output,"rb")
    sentence_count = cPickle.load(f)
    id_dict = cPickle.load(f)
    word_counts = cPickle.load(f)
    skip_word_counts = cPickle.load(f)
    token_count = cPickle.load(f)
    POS_id_dict = cPickle.load(f)
    f.close()


    f = open("%s_best_POS.dat" % options.output,"rb")
    best_pos_dict = cPickle.load(f)
    skip_best_pos_dict = cPickle.load(f)
    unigrams = cPickle.load(f)
    f.close()

    f = open("%s_LPR_stats.dat" % options.output,"rb")
    cond_prob_dict = cPickle.load(f)
    skip_cond_prob_dict = cPickle.load(f)
    f.close()

    id_dict[wild_card] = "*"


    total_count = None
    paired_counts = None

    nodes_dict = {}
    pos_dict = {}
    type_dict = {}
    id_num = 0
    pos_id = 0

    if not options.silent:
        print "adding regular n-gram nodes"

    ngram_list = word_counts.keys() # regular n-grams
    ngram_list.sort(reverse=True)
    for ngram in ngram_list:
        if not is_multi(ngram):
            continue
        words = decode_id(ngram)
        if ngram not in nodes_dict:
            real_pos = best_pos_dict[ngram]
            if real_pos not in pos_dict:
                pos_dict[real_pos] = pos_id
                pos_id += 1
            syntactic_predictability = get_syntactic_predictability_reg(words,cond_prob_dict)          
            nodes_dict[ngram] = Node(ngram,id_num,pos_dict[real_pos],word_counts[ngram], syntactic_predictability,len(words),False)
            id_num += 1                    
        if len(words) > 2:
            for i in range(len(words)):
                syntactic_predictability = None
                length = None
                count = None
                temp_words = words[:i] + words[i+1:]
                if i > 0 and i < len(words) - 1:
                    skip = True
                    below_ngram = get_multi_id_range_skip(words,0,i,i+1,len(words))
                    if below_ngram in skip_cond_prob_dict:
                        length = len(words) - 1
                        if below_ngram not in nodes_dict:
                            loc = i -1
                            syntactic_predictability = get_syntactic_predictability_skip(temp_words,loc, cond_prob_dict,skip_cond_prob_dict)
                            count = skip_word_counts[below_ngram]
                    else:
                        nodes_dict[ngram].syntactic_predictability[i] = 999999
                else:
                    skip = False
                    below_ngram = get_multi_id(temp_words)
                    if below_ngram in cond_prob_dict:
                        length = len(words) - 1
                        if below_ngram not in nodes_dict:
                            syntactic_predictability = get_syntactic_predictability_reg(temp_words, cond_prob_dict)
                            count = word_counts[below_ngram] 
                    else:
                        nodes_dict[ngram].syntactic_predictability[i] = 999999  
                        
                if length != None:
                    if below_ngram not in nodes_dict:
                        if skip:
                            real_pos = skip_best_pos_dict[below_ngram]
                        else:
                            real_pos = best_pos_dict[below_ngram]
                        if real_pos not in pos_dict:
                            pos_dict[real_pos] = pos_id
                            pos_id += 1
                        nodes_dict[below_ngram] = Node(below_ngram, id_num,pos_dict[real_pos],count, syntactic_predictability,length,skip)
                        id_num += 1
                    nodes_dict[below_ngram].above_nodes.append(nodes_dict[ngram].id_num)
                    nodes_dict[ngram].below_nodes.append(nodes_dict[below_ngram].id_num)                
            nodes_dict[ngram].syntactic_predictability = max(0, min(nodes_dict[ngram].syntactic_predictability))

    if not options.silent:
        print "adding skip n-gram nodes"

    ngram_list = skip_word_counts.keys() # skip n-grams
    ngram_list.sort(reverse=True)
    for ngram in ngram_list:
        if not is_multi(ngram):
            continue

        words = decode_id(ngram)
        loc = words[0]
        words = words[1:]
        if ngram not in nodes_dict:
            real_pos = skip_best_pos_dict[ngram]
            if real_pos not in pos_dict:
                pos_dict[real_pos] = pos_id
                pos_id += 1
            syntactic_predictability = get_syntactic_predictability_skip(words,loc, cond_prob_dict,skip_cond_prob_dict)          
            nodes_dict[ngram] = Node(ngram,id_num,pos_dict[real_pos],skip_word_counts[ngram], syntactic_predictability,len(words),True)
            id_num += 1

            
        if len(words) > 2:
            for i in set([0,loc,loc+1,len(words) - 1]):
                syntactic_predictability = None
                length = None
                count = None
                temp_words = words[:i] + words[i+1:]
                if not ((i== 0 and loc ==0) or (i== len(temp_words) and loc == i - 1)):
                    if i <= loc:
                        temp_loc = loc - 1
                    else:
                        temp_loc = loc
                    skip = True
                    below_ngram = get_multi_id_range_skip(temp_words,0,temp_loc + 1,temp_loc + 1,len(temp_words))
                    if below_ngram in skip_cond_prob_dict:
                        length = len(words) - 1
                        if below_ngram not in nodes_dict:
                            syntactic_predictability = get_syntactic_predictability_skip(temp_words,temp_loc, cond_prob_dict,skip_cond_prob_dict)
                            count = skip_word_counts[below_ngram]
                    else:
                        nodes_dict[ngram].syntactic_predictability[i] = 999999                                                              
                                                                
                else:
                    skip = False
                    if i == 0:
                        below_ngram = get_multi_id(temp_words)
                        if below_ngram in cond_prob_dict:
                            length = len(temp_words)
                            if below_ngram not in nodes_dict:
                                syntactic_predictability = get_syntactic_predictability_reg(temp_words, cond_prob_dict)
                                count = word_counts[below_ngram]
                        else:
                            nodes_dict[ngram].syntactic_predictability[i] = 999999 
                    else:
                        below_ngram = get_multi_id(temp_words)
                        if below_ngram in cond_prob_dict:
                            length = len(temp_words)
                            if below_ngram not in nodes_dict:
                                syntactic_predictability = get_syntactic_predictability_reg(temp_words, cond_prob_dict)
                                count = word_counts[below_ngram]
                        else:
                            nodes_dict[ngram].syntactic_predictability[i] = 999999 

                        
                if length != None:   
                    if below_ngram not in nodes_dict:
                        if skip:
                            real_pos = skip_best_pos_dict[below_ngram]
                        else:
                            real_pos = best_pos_dict[below_ngram]
                        if real_pos not in pos_dict:
                            pos_dict[real_pos] = pos_id
                            pos_id += 1

                        nodes_dict[below_ngram] = Node(below_ngram,id_num,pos_dict[real_pos],count, syntactic_predictability,length,skip)
                        id_num += 1
                    nodes_dict[below_ngram].above_nodes.append(nodes_dict[ngram].id_num)
                    nodes_dict[ngram].below_nodes.append(nodes_dict[below_ngram].id_num)                
            nodes_dict[ngram].syntactic_predictability = max(0, min(nodes_dict[ngram].syntactic_predictability))

    nodes = nodes_dict.values()

    ngram_lookup = {}
    node_lookup = {}
    reg_count = 0
    skip_count = 0
    
    for ngram in nodes_dict:
        ngram_lookup[nodes_dict[ngram].id_num] = ngram
        node_lookup[nodes_dict[ngram].id_num] = nodes_dict[ngram]
        if ngram in cond_prob_dict:
            words = [id_dict[word] for word in decode_id(ngram)]
            pos = [POS_id_dict[pos_id] for pos_id in decode_id(best_pos_dict[ngram])]
        else:
            words = [id_dict[word] for word in decode_id(ngram)[1:]]
            pos = [POS_id_dict[pos_id] for pos_id in decode_id(skip_best_pos_dict[ngram])[1:]]

        nodes_dict[ngram].has_pronoun = lang_specific_helper.has_pronoun(words,pos)

    if not options.silent:
        print "finding overlaps in corpus"


    find_overlap_list = set()
    not_wanted_list = set()
    
    id_lookup = {}

    for ID in ngram_lookup:
        id_lookup[ngram_lookup[ID]] = ID

    
    for node in nodes:
        check_covered(node)
        if not node.is_covered:
            set_shared_syntactic_predictability(node)
            if not node.is_covered:
                find_overlap_list.add(ngram_lookup[node.id_num])




    for inQ in inQs:
        inQ.put(find_overlap_list)


    done_threads = 0
    overlaps = Counter()
    while done_threads < options.workers:
        result = Q.get()
        if result == -1:
            done_threads += 1
        else:
            overlaps.update(result)
            
    for inQ in inQs:
        inQ.put(None)

    if not options.silent:
        print "adding overlaps to lattice"

    to_delete = set()
    temp_count = 0
    overlap_count = 0

    for pair in overlaps:
        node1 = id_lookup[pair[0]]
        node2 = id_lookup[pair[1]]
        if overlaps[pair] >= min_overlaps and node1 != node2:
            overlap_count += 1
            node_lookup[node1].overlaps[node2] = overlaps[pair]
            node_lookup[node2].overlaps[node1] = overlaps[pair]
  

    nodes.sort()

    if not options.silent:
        print "total overlaps added: %d" % overlap_count


    fout = open("%s_lattice.dat" % options.output,"wb")
    cPickle.dump(nodes,fout,-1)
    fout.close()

    
        
    
