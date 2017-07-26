import cPickle
import gc
gc.disable()
import math
import copy
import time
from build_lattice_with_old import Node
#from scipy.special import beta as beta_f
#from scipy.misc import comb
#from scipy.stats import beta as beta_d
#from scipy.special import gamma
from scipy.stats import norm
from numpy import array
#from multi_helper import decode_id
import sys
from collections import Counter, defaultdict

from multiprocessing import Process,Queue,Manager
from pos_helper import matches_gap_en,matches_gap_fr, matches_gap_ja, matches_gap_en_bnc, matches_gap_hr
from multi_helper import *
from corpus_reader import read_sentence_from_corpus_ja, read_sentence_from_corpus_ICWSM_quick, read_sentence_from_corpus_BNC,read_sentence_from_corpus_ICWSM_old, read_sentence_from_corpus_hr#, read_sentence_from_corpus_simple
from scipy.stats import entropy
import random

import cProfile, pstats, StringIO
pr = cProfile.Profile()


workers = 4

hr = True
ja = False
BNC = False
new_old = False


other = ""

if hr:
   matches_gap = matches_gap_hr
elif ja:
   matches_gap = matches_gap_ja
elif BNC:
   matches_gap = matches_gap_en_bnc
else:
   matches_gap = matches_gap_en

if hr:
   corpus = "/home/snajder/unimelb/fscro/hrwac/fhrwac-parsed.conll"
   read_sentence_from_corpus = read_sentence_from_corpus_hr
   corpus_str = "hr"
elif ja:
   corpus = "/home/jbrooke/temp_japan"
   read_sentence_from_corpus = read_sentence_from_corpus_ja
   corpus_str = "ja"
elif BNC:
   corpus = "/lt/data/bnc-preprocessed/bnc.bnc"
   read_sentence_from_corpus = read_sentence_from_corpus_BNC
   corpus_str = "BNC"
elif other:
   corpus = "%s_data.dat" % other
   read_sentence_from_corpus = read_sentence_from_corpus_simple
   corpus_str = other
else:
   corpus = "../tier1_ICWSM/tier1_tagged"
   #read_sentence_from_corpus = read_sentence_from_corpus_ICWSM
   #read_sentence_from_corpus = read_sentence_from_corpus_ICWSM_quick
   read_sentence_from_corpus = read_sentence_from_corpus_ICWSM_old
   corpus_str = "ICWSM"



#output_string = "get_overlaps_2cutoff_ja_big"
#output_string = "basic_cover_nb_oldstats_4_2avg_wbr"

#output_string = "basic_cover_nb_oldstats_4_2avg_logscale4_overlap5_BNC10m_costmem"
#output_string = "basic_cover_nb_oldstats_4_2avg_logscale4_nolimitblock_debug"
#output_string = "basic_cover_nb_oldstats_4_2avg_prodweight4_nolimitblock_nastybugfixed"

#output_string = "basic_cover_nb_oldstats_4_2avg_logscale4_nolimitblock_newoverlap5rel0.1_real_ja"
#output_string = "basic_cover_nb_oldstats_4_2avg_logscale4_overlap5_hr"

liberal_hard_cut = False
switch_search = True
precalc_solo_relevant = True
load_state = False
get_overlaps = False
load_overlaps = True
old_lattice = True
use2avg = True
weight_by_logcount = False
product_weight = False
logcount_over_pos = False
weight_by_ratio_log_scaled = True
sigmoid_weight = False
#simpliest_weight = True
simple_weight = False
scale = 2
weight_by_ratio = False
weight_by_ratio_log = False
do_pos_entropy = False
do_pos_weighting = False
check_overlaps = False
boost_cost_overlaps = True
parent_cost = False
length_MWE_cost = False
use_block = False
block_relative = True
block_expo = True
block_logexpo = False
block_mixed = False
blocking_limit = 1.0
#block_nolimit = False
block_pronouns = True
hard_soft_block = False
use_fuzzy_cover = True
cover_bug = False
cover_product = False
cover_block = True
part_LPR = True
min2 = True
max2 = False
use_overlap_shifter = False
shift_value = 0.75
MWE_cost = 4
#MWE_cost = 4.6484
#MWE_cost = 4.1404
#MWE_cost = 4.01953
#MWE_cost = 4.01953
#MWE_cost = 3.1346667
#if use_shifter:
#   MWE_cost = 2 + 2*shift_value
min_overlaps = 2
overlap_absolute_filter = True
absolute_filter_cutoff = 5
relative_filter = False
relative_filter_cutoff = 0.05
#min_overlaps = 0
cover_cutoff = 2.0/3.0
#cover_cutoff = 0.5
#relevancy_cutoff = 0.1
relevancy_cutoff = 0
max_relevant_nodes = 5
block_cutoff_extra = 3
min_syn_pred_log = 1.0
if liberal_hard_cut:
   min_syn_pred_log = math.log(1.5,2)
use_cost_memory = True

if get_overlaps:
    load_state = False
    load_overlaps = False
    weight_by_logcount = False
    check_overlaps = False
    use_fuzzy_cover = False
    use_block = False
    MWE_cost = 2
    #MWE_cost /= 2
    #MWE_cost = 1.5

debug = False
new = False

MWE_cost_log = math.log(MWE_cost,2)
cover_cutoff_log =  math.log(cover_cutoff,2)
block_upper_bound = MWE_cost

output_stuff = [corpus_str]
output_stuff.append("cost" +str(MWE_cost))

lattice_stuff = ["lattice",corpus_str]

if not use_block:
   output_stuff.append("noblock")
elif block_relative:
   if block_expo:
      if block_logexpo:
         output_stuff.append("rellogexpoblock")
      else:
         output_stuff.append("relexpoblock")
   else:
      output_stuff.append("relblock")
elif block_mixed:
   output_stuff.append("mixedblock")
   output_stuff.append(str(blocking_limit))
else:
   output_stuff.append("absblock")
                       
if not check_overlaps:
   output_stuff.append("nooverlaps")

if cover_block:
   output_stuff.append("coverblock")


if weight_by_logcount:
   output_stuff.append("logscale" + str(scale))
else:
   output_stuff.append("nologcount")


if use_overlap_shifter:
   output_stuff.append("overlapshift" + str(shift_value))

if liberal_hard_cut:
   output_stuff.append("1.5hardcut")

if debug:
   output_stuff.append("debug")


if get_overlaps:
   output_stuff = ["get_overlaps_2cutoff"] + [corpus_str]
else:
   overlap_stuff = ["get_overlaps_2cutoff"] + [corpus_str]

if part_LPR:
   output_stuff.append("partLPR")
   lattice_stuff.append("partLPR")
   if not get_overlaps:
      overlap_stuff.append("partLPR")

if new:
   output_stuff.append("new")
   lattice_stuff.append("new")
   #if not get_overlaps:
   #   overlap_stuff.append("new")

if min2:
   output_stuff.append("min2")
   lattice_stuff.append("min2")
   if not get_overlaps:
      overlap_stuff.append("min2")

if max2:
   output_stuff.append("max2")
   lattice_stuff.append("max2")
   if not get_overlaps:
      overlap_stuff.append("max2")



output_string = "_".join(output_stuff) 
#output_string = "get_overlaps_2cutoff_hr"
#output_string = "get_overlaps_2cutoff_ja_big"
#output_string = "get_overlaps_2cutoff_BNC_new_2max"
#output_string = "get_overlaps_2cutoff_BNC_gaming"
#output_string = "get_overlaps_2cutoff_ICWSM_modLPR"
#output_string = "get_overlaps_2cutoff_BNC_partLPR"

print output_string


def print_ngram_multi(ngram):
    try:
        print [id_dict[word] for word in decode_id(ngram)]
    except:
        print ["skip"] + [id_dict[word] for word in decode_id(ngram)[1:]]
   


def print_ngram(pos_id):
    try:
        print [id_dict[word] for word in decode_id(ngram_lookup[pos_id])]
    except:
        print ["skip"] + [id_dict[word] for word in decode_id(ngram_lookup[pos_id])[1:]]

def ngram_string(pos_id):
    try:
        return str([id_dict[word] for word in decode_id(ngram_lookup[pos_id])])
    except:
        return str(["skip"] + [id_dict[word] for word in decode_id(ngram_lookup[pos_id])[1:]])


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
        MWEs = inQ.get()
        if MWEs == None:
            break
        #overlap_counts = {}
        overlaps = {}
        sentence_count = 0
        for sentence in read_sentence_from_corpus(corpus,start_sent,end_sent):
            sentence_count += 1
            if sentence_count % 10000 == 0:
                #print sentence_count
                sys.stdout.flush()
            start = time.time()
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
                        if multi_id in MWEs:
                            #print [item[0] for item in sentence[i:j]]
                            ranges.append([i, j,multi_id])
                        k = 1
                        while j + k < len(words) and matches_gap(org_pos,j,j+k):
                            m = 1                    
                            while j +k +m < len(words) + 1:
                                multi_id = get_multi_id_range_skip(words,i,j,j+k,j+k+m)
                                if multi_id in all_ngrams:
                                    if multi_id in MWEs:
                                        #print [item[0] for item in sentence[i:j+k+m]]
                                        ranges.append([i,j,j+k,j+k+m,multi_id])
                                else:
                                    break
                                    

                                m +=1
                            

                            k+= 1
                    else:
                        matched = False
                    j+= 1
            #print " ".join(temp_words).encode("utf-8")
            #print " ".join([str(temp_int) for temp_int in words])
            #print ranges
            #if "camel" in temp_words and "straw" in temp_words and "back" in temp_words:
            #   print "!!!!"
            #   print sentence
            #   print ranges

            for i in range(len(ranges)):
                j = i + 1
                while j < len(ranges) and ranges[j][0] + 1 <= ranges[i][-2]:
                    if properly_overlaps(ranges[i],ranges[j],sentence):
                        '''
                        if len(ranges[i]) == 3:
                            print [id_dict[word] for word in words[ranges[i][0]:ranges[i][-2]]]
                        else:
                            print [id_dict[word] for word in words[ranges[i][0]:ranges[i][1]]] + ["*"] + [id_dict[word] for word in words[ranges[i][2]:ranges[i][3]]]
                        if len(ranges[j]) == 3:                        
                            print [id_dict[word] for word in words[ranges[j][0]:ranges[j][-2]]]
                        else:
                            print [id_dict[word] for word in words[ranges[j][0]:ranges[j][1]]] + ["*"] + [id_dict[word] for word in words[ranges[j][2]:ranges[j][3]]]                       
                        '''
                        to_sort = [ranges[i][-1],ranges[j][-1]]
                        to_sort.sort()
                        pair = tuple(to_sort)
                        overlaps[pair] = overlaps.get(pair,0) + 1
                        #print "added"
                        #print_ngram_multi(pair[0])
                        #print_ngram_multi(pair[1])
                        '''
                        if ranges[i][-1] not in overlap_counts:
                            overlap_counts[ranges[i][-1]] = {}

                        overlap_counts[ranges[i][-1]][ranges[j][-1]] = overlap_counts[ranges[i][-1]].get(ranges[j][-1],0) + 1

                        if ranges[j][-1] not in overlap_counts:
                            overlap_counts[ranges[j][-1]] = {}

                        overlap_counts[ranges[j][-1]][ranges[i][-1] ] = overlap_counts[ranges[j][-1]].get(ranges[i][-1],0) + 1
                        '''
                    j += 1

            if sentence_count % 1000 == 0:
                Q.put(overlaps)
                #overlap_counts = {}
                overlaps = {}
        Q.put(overlaps)
        Q.put(-1)



class TempSet:

    def __init__(self,fixed_set):
        self.fixed_set = fixed_set
        self.added_set = set()
        self.removed_set = set()


    def add(self,item):
        if item not in self.fixed_set:
            self.added_set.add(item)
        self.removed_set.discard(item)

    def remove(self,item):
        if item in self.fixed_set:
            self.removed_set.add(item)
        self.added_set.discard(item)


    def is_changed(self,item):
        if item in self.added_set or item in self.removed_set:
            return True
        return False
            

    def __len__(self):
        return len(self.fixed_set) + len(self.added_set) - len(self.removed_set)

    def __contains__(self, item):
        return item in self.added_set or (item in self.fixed_set and item not in self.removed_set)

    def finalize_changes(self):
        self.fixed_set.update(self.added_set)
        self.fixed_set.difference_update(self.removed_set)


class TempDict:

    def __init__(self,fixed_dict):
        self.fixed_dict = fixed_dict
        self.changed_dict = {}


    def is_changed(self,item):
        return item in self.changed_dict


    def __setitem__(self,item,value):
        #print "added"
        #print value
        if item not in self.fixed_dict:
            #print "changed"
            self.changed_dict[item] = value
        else:
            if self.fixed_dict[item] == value:
                #print "fixed"
                if item in self.changed_dict:
                    del self.changed_dict[item]
            else:
                #print "changed"
                self.changed_dict[item] = value
            

    def __getitem__(self,item):
        if item in self.changed_dict:
            return self.changed_dict[item]
        else:
            return self.fixed_dict[item]

    def get(self,item,default):
        if item in self.changed_dict:
            return self.changed_dict[item]
        else:
            return self.fixed_dict.get(item,default)

    def finalize_changes(self):
        for item in self.changed_dict:
            #print "finalized"
            #print self.changed_dict[item]
            self.fixed_dict[item] = self.changed_dict[item]


    def copy(self):
        new_dict = TempDict(self.fixed_dict)
        new_dict.changed_dict = self.changed_dict.copy()
        return new_dict

'''

def get_temp_MWEs(relevant_nodes,affected_nodes,current_config):
    new_MWEs = TempSet(MWEs)
    for node in affected_nodes:
        new_MWEs.remove(node)
    for i in range(len(relevant_nodes)):
           if current_config[i]:
               new_MWEs.add(relevant_nodes[i])
    for affected_node in affected_nodes:
        if affected_node not in relevant_nodes:
            if not is_blocked(affected_node,new_MWEs):
                if not is_blocking(affected_node) :
                    new_MWEs.add(affected_node)
    return new_MWEs

'''



overlapping_nodes = defaultdict(dict)

def get_all_nodes_down(node_ids):
    new_nodes = node_ids
    all_nodes = set()
    while new_nodes:
        temp_nodes = set()
        for node in new_nodes:
            temp_nodes.update(node_lookup[node].below_nodes)
        new_nodes = temp_nodes.difference(all_nodes)
        all_nodes.update(temp_nodes)
    return all_nodes

def get_all_nodes_up(node_ids):
    new_nodes = node_ids
    all_nodes = set()
    while new_nodes:
        temp_nodes = set()
        for node in new_nodes:
            temp_nodes.update(node_lookup[node].above_nodes)
        new_nodes = temp_nodes.difference(all_nodes)
        all_nodes.update(temp_nodes)
    return all_nodes


def get_all_nodes_down_covered(ref_node):
    ref_count = node_lookup[ref_node].count * (1/cover_cutoff)
    new_nodes = node_lookup[ref_node].below_nodes
    good_nodes = set()
    while new_nodes:
        next_nodes = set()
        for node in new_nodes:
            if node_lookup[node].count < ref_count:
                good_nodes.add(node)
                next_nodes.update(node_lookup[node].below_nodes)
        new_nodes = next_nodes
    return good_nodes

covered_lookup = {}

def get_all_nodes_down_notcovered(ref_node):
    #ref_count = node_lookup[ref_node].count * (1/relative_filter_cutoff)
    new_nodes = node_lookup[ref_node].below_nodes
    good_nodes = set()
    while new_nodes:
        next_nodes = set()
        for node in new_nodes:
            #if not relative_filter or node_lookup[node].count < ref_count:
               if not is_covered(node) and not get_syntactic_predictability(node) < min_syn_pred_log:
                   good_nodes.add(node)
               next_nodes.update(node_lookup[node].below_nodes)
        new_nodes = next_nodes
    return good_nodes

def is_covered(ref_node):
    try:
        return node_lookup[ref_node].is_covered
    except:
        org_count = node_lookup[ref_node].count

        if block_pronouns and node_lookup[ref_node].has_pronoun:
            found = False
            for node in node_lookup[ref_node].below_nodes: # once above
                #if not node_lookup[node].has_pronoun and (org_count == node_lookup[node]:
                if not node_lookup[node].has_pronoun and (org_count > node_lookup[node].count * cover_cutoff):
                    found = True
            if not found:
                node_lookup[ref_node].is_covered = True
                return True
        ref_count = org_count * cover_cutoff                

        for node in node_lookup[ref_node].above_nodes:
            #if ((not block_pronouns or not node_lookup[node].has_pronoun) and node_lookup[node].count > ref_count) or (block_pronouns and node_lookup[node].has_pronoun and node_lookup[node].count == org_count):
            if node_lookup[node].count > ref_count:
                node_lookup[ref_node].is_covered = True
                return True
        node_lookup[ref_node].is_covered = False
        return False

def not_covered(ref_node):
    return not is_covered(ref_node)

def get_syntactic_predictability(node_id):
    main_node = node_lookup[node_id]
    try:
        main_node.group_syntactic_predictability
    except:
        local_nodes = get_all_nodes_down_covered(node_id)
        local_nodes.add(node_id)      
        if cover_product:
            main_node.group_syntactic_predictability = sum([node_lookup[node].syntactic_predictability for node in local_nodes])
        else:
            main_node.group_syntactic_predictability = max([node_lookup[node].syntactic_predictability for node in local_nodes])
            

    #if output:
    #    print_ngram(node_id) 
    #    print "base syntactic_predictability"
    #    print main_node.group_syntactic_predictability
    return main_node.group_syntactic_predictability

'''
def is_blocking(ref_node):
    ref_count = float(node_lookup[ref_node].count)
    ref_pred = get_syntactic_predictability(ref_node)
    new_nodes = node_lookup[ref_node].above_nodes
    while new_nodes:
        next_nodes = set()
        for node in new_nodes:
            if not is_covered(node) and MWE_cost < get_syntactic_predictability(node) < min(ref_pred*(ref_count - node_lookup[node].count)/ref_count,MWE_cost*2):
                 return True
            next_nodes.update(node_lookup[node].above_nodes)
        new_nodes = next_nodes
    return False
'''
blocked_lookup = {}

def get_all_nodes_up_blocked(ref_node):
    if ref_node in blocked_lookup:
        return blocked_lookup[ref_node]
    else:
        ref_pred = get_syntactic_predictability(ref_node)
        #ref_count = float(node_lookup[ref_node].count)
        new_nodes = node_lookup[ref_node].above_nodes
        good_nodes = set()
        while new_nodes:
            next_nodes = set()
            for node in new_nodes:
                if not is_covered(node) and min_syn_pred_log < get_syntactic_predictability(node) < ref_pred: #min(ref_pred*(ref_count - node_lookup[node].count)/ref_count,MWE_cost*2):
                     good_nodes.add(node)
                next_nodes.update(node_lookup[node].above_nodes)
            new_nodes = next_nodes
        if len(good_nodes) > 5:
            blocked_lookup[ref_node] = good_nodes
        return good_nodes
'''
def get_all_nodes_up_blocked_recusive(ref_node,MWEs):
    new_nodes = [ref_node]
    all_nodes = set(new_nodes)
    potential_blockers = set()
    while new_nodes:
        temp_set = set()
        for node in new_nodes:
            if node in MWES:
                result = get_all_nodes_up_blocked(node)
                if result:
                    temp_set.update(result)
                    potential_blockers.add(node)
        new_nodes = temp_set.difference(all_nodes)
        all_nodes.update(new_nodes)
    return all_nodes, potential_blockers            
'''            
'''
def is_blocked(ref_node,MWEs):
    ref_count = float(node_lookup[ref_node].count)
    ref_pred = get_syntactic_predictability(ref_node)
    new_nodes = node_lookup[ref_node].below_nodes
    while new_nodes:
        next_nodes = set()
        for node in new_nodes:
            if node in MWEs:
                curr_pred = get_syntactic_predictability(node)
                curr_count = node_lookup[node].count
                if MWE_cost < ref_pred < min(curr_pred*(curr_count - ref_count)/curr_count,block_upper_bound):
                    return True
            next_nodes.update(node_lookup[node].below_nodes)
        new_nodes = next_nodes
    return False  
'''


def get_blocking_factor(ref_node):
    #if get_syntactic_predictability(ref_node) < MWE_cost_log:
    #   print "lb"
    #return MWE_cost_log
    
    #if block_nolimit:
    if block_mixed or block_relative:
       return get_syntactic_predictability(ref_node)
    #elif block_mixed:
    #   return min(get_syntactic_predictability(ref_node), MWE_cost_log)       
    else:
       return MWE_cost_log

    #return min(get_syntactic_predictability(ref_node), MWE_cost_log)# + block_cutoff_extra)
    #return get_syntactic_predictability(ref_node)
'''
def get_blocked_factor(ref_node,temp_blocked_dict):
    if ref_node not in temp_blocked_dict:
        return 0
    factor = 0
    for node in temp_blocking_dict[ref_node]:
        factor += get_blocking_factor(node)
    return factor
'''

def get_ratio(anchor, compare):
    if anchor > compare:
        return compare/float(anchor)
    else:
        return anchor/float(compare)

def get_relevant_and_affected_nodes(ref_node,MWEs):
    ref_count = float(node_lookup[ref_node].count)
    ref_syntax = get_syntactic_predictability(ref_node)
    overlap_cutoff = ref_count * cover_cutoff
    if use_block:
        block_affected_nodes = get_all_nodes_up_blocked(ref_node)
        block_relevant_nodes = MWEs.intersection(get_all_nodes_up([ref_node]))
        #block_relevant_nodes = MWEs.intersection(block_affected_nodes)

        if len(block_relevant_nodes) > 0:
            blocking_factor = get_blocking_factor(ref_node)
        #block_affected_nodes.update(block_relevant_nodes)
    else:
        block_affected_nodes = []
        block_relevant_nodes = []
    if use_fuzzy_cover:
        cover_affected_nodes = get_all_nodes_down_notcovered(ref_node)
        #if relative_filter:
        #   cover_relevant_nodes = MWEs.intersection(get_all_nodes_down([ref_node]))
        #else:
        cover_relevant_nodes = MWEs.intersection(cover_affected_nodes)

        #cover_relevant_nodes = cover_relevant_nodes
    else:
        cover_affected_nodes = []
        cover_relevant_nodes = []

    if check_overlaps:
        overlap_affected_nodes = overlapping_nodes.get(ref_node,[])
        #print_ngram(ref_node)
        #print node_lookup[ref_node].count
        #print "overlapping"
        #print len(overlap_affected_nodes)
        overlap_relevant_nodes = MWEs.intersection(overlap_affected_nodes)
        #print "active overlapping"
        #print len(overlap_relevant_nodes)
        if boost_cost_overlaps:
            overlap_affected_nodes = overlap_relevant_nodes
    else:
        overlap_relevant_nodes = []
        overlap_affected_nodes = []
    

    overlapped_count = 0
    relevant_nodes = set()
    if len(overlap_relevant_nodes) + len(block_relevant_nodes) + len(cover_relevant_nodes) > max_relevant_nodes:
       to_sort = []
       for node_id in overlap_relevant_nodes:
           overlap_count = float(overlapping_nodes[ref_node][node_id])
           other_count = node_lookup[node_id].count
           if other_count > ref_count:
              affected_percent = overlap_count/ref_count
           else:
              affected_percent = overlap_count/other_count
           #affected_percent = overlap_count/ref_count

           #if affected_percent > 1:
           #    print "point 1"
           #affected_percent = 2**(max(0,MWE_cost_log*(ref_count/(ref_count-(ref_overlap_total - overlap_count)) - curr_overlap_weight) - ref_syntax))

           #affected_percent = max(overlap_total/node_lookup[node_id].count,affected_percent)


           #other_count = float(node_lookup[ref_node].count)
           #other_syntax = get_syntactic_predictability(node_id)
           #other_overlap_total = float(sum([overlapping_nodes[node_id][other_node] for other_node in [node for node in overlapping_nodes[node_id] if node in MWEs]]))

           #if ref_node in MWEs:
           #    other_overlap_total -= overlap_count
           #try:
           #    affected_percent = max(affected_percent, 2**(min(0,MWE_cost_log*(other_count/(other_count-(other_overlap_total + overlap_count)) - other_count/(other_count-other_overlap_total)) - other_syntax)))
           #except:
           #    affected_percent = 1
           #if affected_percent > 1:
           #    print "point 2"

           #print "overlap_result"
           #print_ngram(node_id)
           #print overlap_total
           #print affected_percent
           #if affected_percent > relevancy_cutoff:
               #print "overlap"
               #print affected_percent
           to_sort.append((affected_percent,node_lookup[node_id].count,node_id))
       #if overlapped_count > max_relevant_nodes:
       #    print "too many overlaps"
       #    return None, None
       
       for node_id in block_relevant_nodes:
           #if relative_filter and node_id not in block_affected_nodes:
           #   affected_percent = 
           #else:
           if node_id not in block_affected_nodes:
              affected_percent = node_lookup[node_id].count/ref_count
           else:
              affected_percent = 1 #max(node_lookup[node_id].count/ref_count,2**(min(blocking_factor - get_syntactic_predictability(node_id),0)))
           #if affected_percent > 1:
           #    print "point 4"
           to_sort.append((affected_percent, node_lookup[node_id].count,node_id))
                   
       for node_id in cover_relevant_nodes:
           #if relative_filter and node_id not in cover_affected_nodes:
           #   affected_percent = 2**(min(get_blocking_factor(node_id) - get_syntactic_predictability(ref_node),0)) 
           #else:
           affected_percent = ref_count/node_lookup[node_id].count#,2**(min(get_blocking_factor(node_id) - get_syntactic_predictability(ref_node),0)))
           if get_syntactic_predictability(node_id) > ref_syntax:
              affected_percent = 1
           #if affected_percent > 1:
           #    print "point 6"
           to_sort.append((0,affected_percent, node_lookup[node_id].count,node_id))
                   
       to_sort.sort(reverse=True)
        #print "at to sort"
        #print to_sort
       for i in range(min(len(relevant_nodes),max_relevant_nodes)):
          relevant_nodes.add(to_sort[i][-1])
    else:
       relevant_nodes.update(cover_relevant_nodes)
       relevant_nodes.update(block_relevant_nodes)
       relevant_nodes.update(overlap_relevant_nodes)
      
      

    relevant_nodes = list(relevant_nodes)

    affected_nodes = set([ref_node])
    affected_nodes.update(cover_affected_nodes)
    affected_nodes.update(block_affected_nodes)
    affected_nodes.update(overlap_affected_nodes)
    
    if precalc_solo_relevant:
        affected_nodes_by_relevant = []
        if relevant_nodes:
            affected_nodes_by_relevant.append(copy.copy(affected_nodes))
        
    for relevant_node in relevant_nodes:
        if precalc_solo_relevant:
            temp_affected = affected_nodes
            affected_nodes = set()
        if use_block:
            affected_nodes.update(get_all_nodes_up_blocked(relevant_node))
        if use_fuzzy_cover:
            affected_nodes.update(get_all_nodes_down_notcovered(relevant_node))
        if check_overlaps:
            if boost_cost_overlaps:
                affected_nodes.update(MWEs.intersection(overlapping_nodes.get(relevant_node,[])))                
            else:
                affected_nodes.update(overlapping_nodes.get(relevant_node,[]))
        affected_nodes.add(relevant_node)
        affected_nodes.add(ref_node)
        if precalc_solo_relevant:
            affected_nodes_by_relevant.append(affected_nodes)
            temp_affected.update(affected_nodes)
            affected_nodes = temp_affected
    relevant_nodes.insert(0,ref_node)
    if precalc_solo_relevant:
        return relevant_nodes,[affected_nodes,affected_nodes_by_relevant]
    else:
        return relevant_nodes,affected_nodes


count_weight_dict = {}

def calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict, affected_node_id):
    affected_node = node_lookup[affected_node_id]
    count = float(affected_node.count)
    if affected_node_id in temp_MWEs:
        result = MWE_cost_log
        if check_overlaps and boost_cost_overlaps:
            #if output:
            #    print_ngram(affected_node_id)
            #    print "is MWE"
            overlap_count = sum([overlapping_nodes[affected_node_id][other_node] for other_node in [node for node in overlapping_nodes[affected_node_id] if node in temp_MWEs]])
            if cover_block:
               overlap_count += sum(temp_covering_dict[affected_node_id])
            #if output and overlap_count > 0:
            #    print "overlaps"
            #    print overlap_count
            #    print affected_node.count
            #    for node in overlapping_nodes[affected_node_id]:
            #        if node in temp_MWEs:
            #            print_ngram(node)
            #            print overlapping_nodes[affected_node_id][node]
            if overlap_count >= affected_node.count:
                #if output:
                #    print "fully overlapped"
                result = 999999999

            elif use_overlap_shifter:
                result*=(count/(count-overlap_count))**(shift_value)
            else:
                result*=(count/(count-overlap_count))
        #if output:
        #    print "cost for node"
        #    print result
        return result

    if old_lattice:
        result = get_syntactic_predictability(affected_node_id)
        #if output:
        #    print_ngram(affected_node_id)
        #    print "starting syn"
        #    print result

        modifier = 0

        if check_overlaps and not boost_cost_overlaps and overlapping_nodes:
            modifier = sum([overlapping_nodes[affected_node_id][other_node] for other_node in [node for node in overlapping_nodes[affected_node_id] if node in temp_MWEs]])
            #if output and modifier:
            #    print "overlaps"
            #    print modifier
                       

        if use_fuzzy_cover:
            temp = sum(temp_covering_dict[affected_node_id])
            #if output and temp:
            #    print "doing fuzzy cover"
            #    print temp
            modifier += temp
            
        if modifier > 0:
            if hard_soft_block and modifier > count*cover_cutoff:
                #if output:
                #    print "covered!"
                #    print "cost for node"
                #    print 0
                return 0
            if cover_bug:
               modifier = math.log(count - modifier,2) - affected_node.log_count
            else:
               modifier = -(min(count, modifier)/count)*result

            result += modifier
   
        if use_block:
            modifier = -sum(temp_blocking_dict[affected_node_id])
            #if output and modifier:
            #    print "blocking"
            #    print modifier
            #if use_shifter:
            #   result += modifier*shift_value
            #else:
            if block_expo:
               result*= 2**modifier
            else:
               result += modifier

        if result <= 0:
            #if output:
            #    print "cost for node"
            #    print 0
            result = 0



            
        if weight_by_logcount and result:
            #if output:
            #    print "logcount weight"
            #    print node_lookup[affected_node_id].log_count
            #    print pos_avg_counts[node_lookup[affected_node_id].pos_num]
            #if simpliest_weight:
            #   result += math.log(count/min_count,2)
            try:
               weight = count_weight_dict[affected_node_id]
            except:
               if simple_weight:
                  weight = 1 + math.log(count/min_count,10)
                  
               elif sigmoid_weight:
                  weight = 1 + (1 - min_count/count)
               #elif product_weight:
               #   result += math.log(1 + (scale - 1)*math.log(node_lookup[affected_node_id].count/min_count,2)/max_log_ratio,2)
               elif weight_by_ratio:
                  weight = float(node_lookup[affected_node_id].count/min_count)
                  
               elif weight_by_ratio_log:
                  weight = math.log(float(node_lookup[affected_node_id].count/min_count),2)

               elif weight_by_ratio_log_scaled:
                  #print 1 + math.log(float(node_lookup[affected_node_id].count/min_count),2)/max_log_ratio
                  weight = 1 + (scale - 1)*math.log(float(node_lookup[affected_node_id].count/min_count),2)/max_log_ratio

               elif logcount_over_pos:
                   weight = node_lookup[affected_node_id].log_count/pos_avg_counts[node_lookup[affected_node_id].pos_num]
               else:
                   weight = node_lookup[affected_node_id].log_count/min_log_count
               count_weight_dict[affected_node_id] = weight
            result *= weight

        '''     
        if do_pos_weighting and it_count > 0:
            pos_num = node_lookup[affected_node_id].pos_num
            if output:
                print_ngram(affected_node_id)
                print pos_counts[pos_num]
                print pos_totals[pos_num]
                print len(temp_MWEs)
                print total_nodes
                average = len(temp_MWEs)/total_nodes
                print average
                print min(1,0.5*(1 + (pos_counts[pos_num]/pos_totals[pos_num])/average)**(1 - 1.0/pos_totals[pos_num]))
                #print (pos_counts[pos_num] + 1)/(pos_totals[pos_num] + 1)/(len(temp_MWEs)/total_nodes)
                #print 1 - 1.0/pos_totals[pos_num]

            #if pos_counts[pos_num] == 0:
            #    result *= 0.5**(1 - 1.0/pos_totals[pos_num])
            #else:
            average = len(temp_MWEs)/total_nodes
                #result *= (1/((math.log((pos_counts[pos_num] + 1)/(pos_totals[pos_num] + 1),2))/(math.log((len(temp_MWEs)/total_nodes),2))))**(1 - 1.0/pos_totals[pos_num])
            result *= min(2,0.5*(1 + (pos_counts[pos_num]/pos_totals[pos_num])/average)**(1 - 1.0/pos_totals[pos_num]))
        '''
        #if output:
        #    print "cost for node"
        #    print result
        return result
    else:
        return math.log(get_syntactic_predictability(affected_node_id),2)



def update_lattice(relevant_nodes,config,MWEs,blocking_dict,covering_dict,cost_memory=None,affected_nodes=None):
    temp_blocking_dict = {}
    temp_covering_dict = {}
    for i in range(len(relevant_nodes)):
        relevant_node = relevant_nodes[i]
        count = node_lookup[relevant_node].count
        changed_true = config[i] and relevant_node not in MWEs
        changed_false = not config[i] and relevant_node in MWEs
        blocking_factor = get_blocking_factor(relevant_node)
        if changed_true or changed_false:
            if use_cost_memory:
               cost_memory[relevant_node] = None
            if check_overlaps:
                if use_cost_memory:
                   for node in overlapping_nodes[relevant_node]:
                       if node in MWEs:
                           cost_memory[node] = None
            if use_fuzzy_cover:
                wanted_cover = get_all_nodes_down_notcovered(relevant_node)
                if precalc_solo_relevant and affected_nodes:
                    wanted_cover = wanted_cover.intersection(affected_nodes)
                for node in wanted_cover:
                    if node not in temp_covering_dict:
                        #print covering_dict[node]
                        temp_covering_dict[node] = copy.copy(covering_dict[node])
                        #print temp_covering_dict[node]
                    if use_cost_memory and node not in MWEs:
                        cost_memory[node] = None
                    if changed_true:

                        temp_covering_dict[node].append(count)
                        #print "Added covering"
                        #print_ngram(node)
                        #print count
                        #print temp_covering_dict[node]
                    else:
                        #print "Removing covering"
                        #print_ngram(node)
                        #print count
                        #print temp_covering_dict[node]
                        temp_covering_dict[node].remove(count)
            if use_block:
                wanted_block = get_all_nodes_up_blocked(relevant_node)
                if precalc_solo_relevant and affected_nodes:
                    wanted_block = wanted_block.intersection(affected_nodes)
                for node in wanted_block:
                    if node not in temp_blocking_dict:
                        temp_blocking_dict[node] = copy.copy(blocking_dict[node])                    
                    if use_cost_memory and node not in MWEs:
                        cost_memory[node] = None
                    if changed_true:
                        if block_relative:
                           if block_logexpo:
                              temp_blocking_dict[node].append(math.log(blocking_factor/get_syntactic_predictability(node),2))
                           else:
                              temp_blocking_dict[node].append(blocking_factor - get_syntactic_predictability(node))
                        elif block_mixed:
                           temp_blocking_dict[node].append(min(blocking_limit, blocking_factor - get_syntactic_predictability(node)))
                        else:
                           temp_blocking_dict[node].append(blocking_factor)
                        #print "Added blocking"
                        #print_ngram(node)
                        #print blocking_factor
                        #print temp_blocking_dict[node]
                    else:
                        #print "Removing blocking"
                        #print_ngram(node)
                        #print blocking_factor
                        #print temp_blocking_dict[node]
                        try:
                           if block_relative:
                              if block_logexpo:
                                 temp_blocking_dict[node].append(blocking_factor/get_syntactic_predictability(node))
                              else:
                                 temp_blocking_dict[node].append(blocking_factor - get_syntactic_predictability(node))
                           elif block_mixed:
                              temp_blocking_dict[node].remove(min(blocking_limit, blocking_factor - get_syntactic_predictability(node)))
                           else:
                              temp_blocking_dict[node].remove(blocking_factor)
                        except:
                            print_ngram(node)
                            print_ngram(relevant_node)
                            print node
                            print relevant_node
                            print relevant_nodes
                            print blocking_factor
                            print temp_blocking_dict[node]
                            print dksjlfkjds
            if changed_true:
                MWEs.add(relevant_node)
            else:
                MWEs.remove(relevant_node)
    for node in temp_blocking_dict:
        blocking_dict[node] = temp_blocking_dict[node]
    
    for node in temp_covering_dict:
        covering_dict[node] = temp_covering_dict[node]       
         

def change_pos_counts(pos_counts, relevant_nodes,config,diff):
    for i in range(len(config)):
        #print relevant_nodes
        #print config
        if config[i]:
            #print "change pos"
            #print_ngram(relevant_nodes[i])
            #print pos_counts[node_lookup[relevant_nodes[i]].pos_num]
            #print diff
            #print node_lookup[relevant_nodes[i]].id_num
            #print node_lookup[relevant_nodes[i]].pos_num
            #print len(pos_counts)
            #print node_lookup[relevant_nodes[i]].pos_num
            #print len(pos_counts)
            
            pos_counts[node_lookup[relevant_nodes[i]].pos_num] += diff


def calculate_pos_entropy_cost(pos_counts, relevant_nodes,config,temp_MWEs):
    change_pos_counts(pos_counts, relevant_nodes,config,1)
    result =  math.log(entropy(pos_counts,base=2.0)*math.log(len(temp_MWEs),2),2)
    change_pos_counts(pos_counts, relevant_nodes,config,-1)
    return result



    

def convert_to_binary(binary):
    if binary:
        return "1"
    else:
        return "0"


def get_starting_config(relevant_nodes):
    config = []
    for node in relevant_nodes:
        if node in MWEs:
            config.append(True)
        else:
            config.append(False)
    return config

'''
def is_consistent(config,relevant_nodes,i):
    ref_node = relevant_nodes[i]
    i -= 1
    while i > -1:
        if config[i]:
            if ref_node in get_all_nodes_up_blocked(relevant_nodes[i]) or relevant_nodes[i] in get_all_nodes_up_blocked(ref_node):
                return False
        i-= 1
    return True
'''

if __name__ == "__main__":

    my_count = 0
    

    if old_lattice:
        if hr:
            f = open("hr_ngrams.dat","rb")
            id_dict = cPickle.load(f)
            word_counts = cPickle.load(f)
            skip_word_counts = cPickle.load(f)
            token_count = cPickle.load(f)
            sentence_count = cPickle.load(f)
            f.close() 
        elif ja:
            f = open("temp_ngrams_ja.dat","rb")
            #f = open("ja_BNCsize_ngrams.dat","rb")
            id_dict = cPickle.load(f)
            word_counts = cPickle.load(f)
            skip_word_counts = cPickle.load(f)
            token_count = cPickle.load(f)
            sentence_count = cPickle.load(f)
            f.close()           
        elif new_old:
            f = open("new_ICWSM_ngrams.dat","rb")
            id_dict = cPickle.load(f)
            word_counts = cPickle.load(f)
            skip_word_counts = cPickle.load(f)
            token_count = cPickle.load(f)
            sentence_count = cPickle.load(f)
            f.close()
       
           
        elif BNC:
            #f = open("BNC_ngrams_10M.dat","rb")
            f = open("temp_ngrams_en.dat","rb")
            id_dict = cPickle.load(f)
            word_counts = cPickle.load(f)
            skip_word_counts = cPickle.load(f)
            token_count = cPickle.load(f)
            sentence_count = cPickle.load(f)
            f.close()

        elif other:
            f = open("temp_ngrams_%s.dat" % other,"rb")
            id_dict = cPickle.load(f)
            word_counts = cPickle.load(f)
            skip_word_counts = cPickle.load(f)
            token_count = cPickle.load(f)
            sentence_count = cPickle.load(f)
            f.close()    

        else:
            f = open("cond_prob_stats_one_pos_final.dat","rb")
            id_dict = cPickle.load(f)
            cPickle.load(f)
            cPickle.load(f)
            word_counts = cPickle.load(f)
            skip_word_counts = cPickle.load(f)
            cPickle.load(f)
            cPickle.load(f)
            cPickle.load(f)
            token_count = cPickle.load(f)
            sentence_count = 48096339
            #sentence_count = 52107934
            #sentence_count = 100000
            f.close()

        if get_overlaps or (check_overlaps and not load_overlaps):
            all_ngrams = set(word_counts.keys() + skip_word_counts.keys())
            word_counts = None
            skip_word_counts = None
        '''
        if new_old:
            sentence_count = 52107934

        elif ja:
            sentence_count = 10000000

        elif BNC:
            sentence_count = 4619194

        else:
            f = open("initial_ngrams_2.dat","rb")
            cPickle.load(f)
            cPickle.load(f)
            token_count = cPickle.load(f)
            sentence_count = cPickle.load(f)
            f.close()
        '''

        

    else:

        f = open("initial_ngrams_2.dat","rb")
        id_dict = cPickle.load(f)
        ngrams = cPickle.load(f)
        token_count = cPickle.load(f)
        sentence_count = cPickle.load(f)
        POS_id_dict = cPickle.load(f)
        f.close()
        all_ngrams = set(ngrams.keys())
        ngrams = None

    rev_id_dict = {}
    for ID in id_dict:
        #print id_dict[ID].encode("utf-8")
        rev_id_dict[id_dict[ID]] = ID

    #print rev_id_dict['do']
    #print rev_id_dict[u'do']

    if get_overlaps or (check_overlaps and not load_overlaps):

        intervals = []
        for i in range(workers):
            intervals.append(i*(sentence_count/workers))
        intervals.append(sentence_count)


        processes = []
        Q = Queue()
        inQs = []

                          
            
        for i in range(workers):
            inQ = Queue()
            inQs.append(inQ)
            processes.append(Process(target=get_paired_counts,args=(intervals[i],intervals[i+1],all_ngrams,rev_id_dict,inQ,Q)))
            processes[-1].daemon = True
            processes[-1].start()
    '''
    if old_lattice:
        if use2avg:
            if hr:
               if part_LPR:
                  f = open("lattice_hr_partLPR.dat", "rb")
               else:
                  f = open("lattice_hr.dat", "rb")
            elif ja:
               #f = open("lattice_ja_BNCsize.dat", "rb")
               if part_LPR:
                  f = open("lattice_ja_partLPR.dat", "rb")
               else:
                  f = open("lattice_ja.dat", "rb")
            elif new_old:
               f = open("lattice_new_old_2avg.dat","rb")
 
            elif BNC:
                #f = open("lattice_BNC_10M.dat","rb")
                #f = open("lattice_BNC.dat","rb")
               if part_LPR:
                  if new:
                     if min2:
                        f = open("lattice_BNC_new_2min_partLPR.dat","rb")
                     elif max2:
                        f = open("lattice_BNC_new_2max_partLPR.dat","rb")
                     else:
                        f = open("lattice_BNC_new_partLPR.dat","rb")
                  else:
                     if min2:
                        f = open("lattice_BNC_2min_partLPR.dat","rb")
                     elif max2:
                        f = open("lattice_BNC_2max_partLPR.dat","rb")
                     else:
                        f = open("lattice_BNC_partLPR.dat","rb")                     

               else:
                  f = open("lattice_BNC_new.dat","rb")
            elif other:
               f = open("lattice_%s.dat" % other,"rb")
            else:
               if new:
                  f = open("lattice_for_old_modLPr.dat")
               elif part_LPR:
                  f = open("lattice_for_old_2avg_partLPR.dat")                 
               else:
                  f = open("lattice_for_old_2avg.dat","rb")
        else:
            f = open("lattice_for_old.dat","rb")
    else:
        f = open("lattice.dat","rb")
    '''
    f = open("_".join(lattice_stuff) + ".dat","rb")
    nodes = cPickle.load(f)
    pos_id = cPickle.load(f)
    ngram_lookup = cPickle.load(f)
    #node_lookup = cPickle.load(f)
    f.close()

    node_lookup = {}
    for node in nodes:
        node_lookup[node.id_num] = node
    total_nodes = float(len(nodes))
    #nodes.reverse()
    #for node in nodes:
    #    print node.length
    #    print node.syntactic_predictability

    id_lookup = {}

    for ID in ngram_lookup:
        id_lookup[ngram_lookup[ID]] = ID






    total_ngrams= len(nodes)
    if hr:
       min_count = 123.0
    elif ja:
       #min_count = 19.0
       min_count = 90.0
    elif new_old:
       min_count = 100.0
    elif BNC:
       min_count = 9.0
    elif other:
       min_count = 5.0
    else:
       min_count = 89.0
    min_log_count = math.log(min_count,2)



    #intervals = []
    #for i in range(workers):
    #    intervals.append(i*((sentence_count/50)/workers))
    #intervals.append(sentence_count/50)



    #pos_total_count_dict = {}
    #pos_pattern_count_dict = {}
    explained_count_dict = {}
    #pos_lookup_dict = {}
    pos_totals = array([0.0]*len(pos_id))
    pos_avg_counts = array([0.0]*len(pos_id))
    if do_pos_entropy or do_pos_weighting:
        pos_counts = array([0]*len(pos_id))
    else:
        pos_counts = []
    max_count = 0
    for node in nodes:
        if node.count > max_count:
           max_count = node.count
        #if node.pos_num > 81529:
        #    print_ngram(node.id_num)
        #    print node.pos_num
        #print node.syntactic_predictability
        #pos_total_count_dict[node.pos_num] = pos_total_count_dict.get(node.pos_num,0) + 1
        #pos_pattern_count_dict[node.pos_num] = 0
        #explained_count_dict[node.id_num] = 0
        #explained_count_dict[node.id_num] = []
        pos_totals[node.pos_num] += 1
        pos_avg_counts[node.pos_num] += node.count
        #if node.pos_num not in pos_lookup_dict:
        #    pos_lookup_dict[node.pos_num] = []
        #pos_lookup_dict[node.pos_num].append(node.id_num)
        #node.log_count = math.log(node.count)
        #node.predictability = node.syntactic_predictability + node.topic_predictability
    for i in range(len(pos_totals)):
        pos_avg_counts[i] = math.log(pos_avg_counts[i]/pos_totals[i],2)
    max_log_ratio = math.log(max_count/min_count,2)
    #print len(pos_id)
    #print max(pos_id.values())
    #print len(pos_pattern_count_dict)
    changed_dict = set(iter(node_lookup))

    MWEs= set()
    blocking_dict = defaultdict(list)
    covering_dict = defaultdict(list)
    if use_cost_memory:
       cost_memory = {}
    else:
       cost_memory = None

    if load_overlaps:
        '''
        #f = open("get_overlaps_temp_MWEs_0.dat","rb")
        ####f = open("get_overlaps_partial_pronoun_cover_temp_MWEs_0.dat","rb")
        if hr:
           f = open("get_overlaps_2cutoff_hr_temp_MWEs_0.dat","rb")
        elif ja:
            #f = open("get_overlaps_ja_BNCsize_temp_MWEs_0.dat","rb")
            #f = open("get_overlaps_ja_BNCsize_5cutoff_temp_MWEs_0.dat","rb")
            #f = open("get_overlaps_2cutoff_ja_BNCsize_temp_MWEs_0.dat","rb")
           f = open("get_overlaps_2cutoff_ja_big_temp_MWEs_0.dat","rb")
        elif new_old:
            f = open("get_overlaps_new_old_temp_MWEs_0.dat","rb")

        elif BNC:
           #f = open("get_overlaps_BNC_10M_temp_MWEs_0.dat","rb")
            #f = open("get_overlaps_BNC_rev0.1_temp_MWEs_0.dat","rb")
           #f = open("get_overlaps_2cutoff_BNC_temp_MWEs_0.dat","rb")
           #f = open("get_overlaps_2cutoff_BNC_final_temp_MWEs_0.dat","rb")
           #f = open("get_overlaps_2cutoff_BNC_new_temp_MWEs_0.dat","rb")
           if new:
              if part_LPR:
                 if max2:
                     f = open("get_overlaps_2cutoff_BNC_new_2max_temp_MWEs_0.dat","rb")
                 else:
                     f = open("get_overlaps_2cutoff_BNC_new_temp_MWEs_0.dat","rb")
           else:
              if part_LPR:
                 f = open("get_overlaps_2cutoff_BNC_partLPR_temp_MWEs_0.dat")
              else:
                 f = open("get_overlaps_2cutoff_BNC_final_temp_MWEs_0.dat","rb")

           if liberal_hard_cut:
              f = open("get_overlaps_2cutoff_BNC_final1.5_temp_MWEs_0.dat","rb")

        elif other:
           f = open("get_overlaps_2cutoff_%s_temp_MWEs_0.dat" % other,"rb")
        else:
          if new:
              f = open("get_overlaps_2cutoff_ICWSM_modLPR_temp_MWEs_0.dat")             
          else:
              f = open("get_overlaps_2cutoff_oldcorpus_temp_MWEs_0.dat")
            #f = open("get_overlaps_5cutoff_oldcorpus_temp_MWEs_0.dat")
            #f = open("get_overlaps_ICWSM_rev0.1_temp_MWEs_0.dat","rb")
            #f = open("get_overlaps_partial_pronoun_cover_temp_MWEs_0.dat","rb")
        '''
        f = open("_".join(overlap_stuff) + "_temp_MWEs_0.dat","rb")
        #f = open("get_overlaps_partial_cover0.5_temp_MWEs_0.dat","rb")
        overlapping_nodes = cPickle.load(f)
        f.close()
        #for node in overlapping_nodes:
        #   try:
        #      print_ngram(node)
        #   except:
        #       print decode_id(node_lookup[node])
        #   print len(overlapping_nodes[node])

    if load_state:
        print "loading old state"
        f = open("basic_cover_nb_oldstats_4_2avg_logw_halfcut_newocut_temp_MWEs_0.dat","rb")
        saved_MWEs = cPickle.load(f)
        if not load_overlaps:
            overlapping_nodes = cPickle.load(f)
        f.close()
        MWE_list = list(saved_MWEs)
        config = [True]*len(saved_MWEs)
        update_lattice(MWE_list,config,MWEs,blocking_dict,covering_dict)
        if do_pos_entropy or do_pos_weighting:
            change_pos_counts(pos_counts, MWE_list,config,1)
        print "loaded!"
        it_count = 1
    else:
        it_count = 0        

    overlap_count = 0
    delete_absolute = 0
    delete_relative = 0
    if overlap_absolute_filter:
       for ngram1 in overlapping_nodes:
          for ngram2 in overlapping_nodes[ngram1].keys():
             overlap_count += 1
             if overlapping_nodes[ngram1][ngram2] < absolute_filter_cutoff:
                del overlapping_nodes[ngram1][ngram2]
                delete_absolute += 1
                
    if relative_filter:
       for ngram1 in overlapping_nodes:
         count1 = float(node_lookup[ngram1].count)
         for ngram2 in overlapping_nodes[ngram1].keys():
            count2 = float(node_lookup[ngram2].count)
            if overlapping_nodes[ngram1][ngram2] < relative_filter_cutoff*count1 and overlapping_nodes[ngram1][ngram2] < relative_filter_cutoff*count2:
               del overlapping_nodes[ngram1][ngram2]
               delete_relative += 1
    print "total overlaps"
    print overlap_count
    print "absolute deleted"
    print delete_absolute
    print "relative_deleted"
    print delete_relative
            
      
    #f = open("plain_cost3_temp_MWEs_3.dat","rb")
    #MWEs = cPickle.load(f)
    #f.close()

    output = False
    #ever_MWEs = set()
    pr.enable()
    the_end_of_id = None
    while len(changed_dict) > 0:
        old_changed = changed_dict
        changed_dict = set()
        print "start iteration"
        print it_count
        node_count = 0
        last_MWEs = copy.copy(MWEs)
        #random.shuffle(nodes)
        #if it_count == 1:
        #   break
        for node in nodes:

            
            if node_count == 10000:
                pr.disable()
                s = StringIO.StringIO()
                sortby = 'cumulative'
                ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
                ps.print_stats()
                print s.getvalue()
                #print dkfjslfkjdslkfj
            #if node_count == 100000:
            #    changed = 0
            #    break
            #update_lattice([node.id_num],[True],MWEs,blocking_dict,covering_dict)
            #print "node"
            #print_ngram(node.id_num)
            try:
                 ngram = [id_dict[word] for word in decode_id(ngram_lookup[node.id_num])]
            except:
                 ngram = [id_dict[word] for word in decode_id(ngram_lookup[node.id_num])[1:]]

            #print ngram
            #print is_covered(node.id_num)
            #print node.has_pronoun
            #print get_syntactic_predictability(node.id_num)
            #print node.id_num not in old_changed
            if is_covered(node.id_num) or (not get_overlaps and get_syntactic_predictability(node.id_num) < min_syn_pred_log) or node.id_num not in old_changed:
                #print "is covered"
                #print get_syntactic_predictability(node.id_num)
                continue
            #print "here"
            #continue
            #else:
            #    print "not covered"
            #    print get_syntactic_predictability(node.id_num)
            #    continue
                

            #if use_block and is_blocked(node.id_num,MWEs):
            #    print "is blocked"
            #    print_ngram(node.id_num)
            #    continue

            #if node.id_num in overlapping_nodes and MWEs.intersection(overlapping_nodes[node.id_num]):
            #    if node.id_num in MWEs:
            #        MWEs.remove(node.id_num)
            #        if do_pos_entropy or do_pos_weighting:
            #            pos_counts[node.id_num] -= 1
            #    print "overlap!"
            #    print_ngram(node.id_num)
            #    continue
            
            '''
            print "covered_nodes"
            for other_node in get_all_nodes_down_covered(node.id_num):
                print_ngram(other_node)
            print "covering_nodes"
            for other_node in get_all_nodes_up_covering(node.id_num):
                print_ngram(other_node)
            print "blocked_nodes"
            for other_node in get_all_nodes_up_blocked(node.id_num,MWEs):
                print_ngram(other_node)
            print "blocking_nodes"
            for other_node in get_all_nodes_down_blocking(node.id_num):
                print_ngram(other_node)
            continue
            '''




            
            #if "hispanic" in ngram or "shrew" in ngram:
                #continue
            #print "start"
            #print calculate_total_likelihood()
            node_time = 0
            global_time = 0
            result_time = 0
            setup_time = 0

            

            init_setup_time = time.time()

            start_time = time.time()
            node_count += 1
            #if node_count == 10000:
            #   print kfjdslkfsjdljfds
            #   break
            #affected_nodes = get_all_nodes_down([node.id_num])
            #print node_count
            #relevant_nodes = node.relevant_nodes
            #if use_block:
            relevant_nodes,affected_nodes = get_relevant_and_affected_nodes(node.id_num,MWEs)
            #if relevant_nodes == None:
            #    if node.id_num in MWEs:
            #        update_lattice([node.id_num],[False],MWEs,blocking_dict,covering_dict)
            #        if do_pos_entropy or do_pos_weighting:
            #            change_pos_counts(pos_counts, [node.id_num],[False],-1)
            #    continue

            for relevant_node in relevant_nodes:
         
                try:
                    ngram = [id_dict[word] for word in decode_id(ngram_lookup[relevant_node])]
                except:
                    ngram = [id_dict[word] for word in decode_id(ngram_lookup[relevant_node])[1:]]
                #if "make" in ngram and "most" in ngram:
                if  "consumer" in ngram and "affair" in ngram and "spokesman" in ngram: #len(ngram) == 3 and "dodajmo" in ngram and "i" in ngram and "kako" in ngram: #"entitlement" in ngram or "moment" in ngram or (len(ngram) <= 3 and "lot" in ngram) or ("science" in ngram and "technology" in ngram) or ("park" in ngram and "lot" in ngram):
                    output = True
                    if the_end_of_id == None:
                       the_end_of_id = relevant_node
                    break
                else:
                    output = False
                    #output = True


            starting_config = get_starting_config(relevant_nodes)              
            #relevant_nodes = list(relevant_nodes)
            if output:
                print "node:" + ngram_string(node.id_num)                
                for relevant_node in relevant_nodes:
                    print "relevant:" + ngram_string(relevant_node)
                print "starting config"
                print starting_config


            if precalc_solo_relevant:
                affected_nodes, affected_nodes_by_relevant = affected_nodes
                costs = []
                if len(relevant_nodes) > 1 and len(affected_nodes) > 5:
                    solo_affected_nodes = []
                    if output:
                        print "doing pre calc"
                        print len(affected_nodes)

                        handled = set()
                    for i in range(len(relevant_nodes)):
                        costs.append([0,0,[]])
                        solo_affected = copy.copy(affected_nodes_by_relevant[i])
                        relevant_node = relevant_nodes[i]
                        for j in range(0,len(relevant_nodes)):
                            if i != j:
                                solo_affected.difference_update(affected_nodes_by_relevant[j])
                        if output:
                            print_ngram(relevant_nodes[i])
                            print len(affected_nodes_by_relevant[i])
                            for temp_node in affected_nodes_by_relevant[i]:
                                print_ngram(temp_node)
                            print len(solo_affected)

                        solo_affected_nodes.append(solo_affected)
                        if solo_affected:                                
                            temp_MWEs = TempSet(MWEs)
                            if use_cost_memory:
                               temp_cost_memory = TempDict(cost_memory)
                            else:
                               temp_cost_memory = None
                            if use_block:
                                temp_blocking_dict = TempDict(blocking_dict)
                            else:
                                temp_blocking_dict = {}
                            if use_fuzzy_cover:
                                temp_covering_dict = TempDict(covering_dict)
                            else:
                                temp_covering_dict = {}  
                            update_lattice([relevant_node],[False],temp_MWEs,temp_blocking_dict,temp_covering_dict,temp_cost_memory,solo_affected)
                            for affected_node in solo_affected:
                                if use_cost_memory:
                                   if temp_cost_memory.get(affected_node, None) == None:
                                      temp_cost = calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict,affected_node)
                                      temp_cost_memory[affected_node] = temp_cost
                                      costs[-1][0] += temp_cost
                                   else:
                                      #temp_cost = calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict,affected_node)
                                      #if temp_cost != temp_cost_memory[affected_node]:
                                      #   print "oh oh!!!!"
                                      #   print_ngram(affected_node)
                                      #   print temp_cost
                                      #   print temp_cost_memory[affected_node]
                                      costs[-1][0] += temp_cost_memory[affected_node]
                                else:
                                   costs[-1][0] += calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict,affected_node) 
                            costs[-1][2].append(temp_cost_memory)
                            if use_cost_memory:
                               temp_cost_memory = TempDict(cost_memory)
                            else:
                               temp_cost_memory = None
                            temp_MWEs = TempSet(MWEs)
                            if use_block:
                                temp_blocking_dict = TempDict(blocking_dict)
                            else:
                                temp_blocking_dict = {}
                            if use_fuzzy_cover:
                                temp_covering_dict = TempDict(covering_dict)
                            else:
                                temp_covering_dict = {}                            
                            update_lattice([relevant_node],[True],temp_MWEs,temp_blocking_dict,temp_covering_dict,temp_cost_memory,solo_affected)
                            for affected_node in solo_affected:
                              if use_cost_memory:
                                 if temp_cost_memory.get(affected_node, None) == None:
                                      temp_cost = calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict,affected_node)
                                      temp_cost_memory[affected_node] = temp_cost
                                      costs[-1][1] += temp_cost
                                 else:
                                    #temp_cost = calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict,affected_node)
                                    #if temp_cost != temp_cost_memory[affected_node]:
                                    #     print "oh oh!!!!"
                                    #     print_ngram(affected_node)
                                    #     print temp_cost
                                    #     print temp_cost_memory[affected_node]
                                    costs[-1][1] += temp_cost_memory[affected_node]
                              else:
                                 costs[-1][1] += calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict,affected_node) 

                            costs[-1][2].append(temp_cost_memory)
            if output:
                print "affected"
                for temp_node in affected_nodes: 
                    print_ngram(temp_node)
                print "-----"
            ''' 
            for relevant_node in relevant_nodes:
                print_ngram(relevant_node)

            for affected_none in affected_nodes[:5]:
                print_ngram(affected_node)

            print len(affected_nodes)

            MWEs.add(node)

            continue
            '''
            #else:
            #    relevant_nodes = set([node.id_num])
           #     affected_nodes = set([node.id_num])
                
            #relevant_nodes = list(relevant_nodes)

            #if it_count > 0:
            #output = True


                
            best_cost = None
            best_configuration = None
            empty_config = [False]*len(relevant_nodes)
            if do_pos_entropy or do_pos_weighting:
                change_pos_counts(pos_counts, relevant_nodes,empty_config,-1)
            if switch_search:
                config_queue = [[None,[True]*len(relevant_nodes)]]
            else:
                config_queue = [[None,empty_config]]#, temp_pos_pattern_count_dict]]
            config_count = 0
            init_setup_time = time.time() - init_setup_time
            has_starting = False
            #config_list = []

            while config_queue:
                temp_time = time.time()
                config_count += 1
                #print config_count
                #print len(node.relevant_nodes)
                current_config = config_queue.pop()
                #if current_config[1] == starting_config:
                #    has_starting = True
                if output:
                    print "configuration"
                    print current_config[1]

                temp_MWEs = TempSet(MWEs)
                if use_block:
                    temp_blocking_dict = TempDict(blocking_dict)
                else:
                    temp_blocking_dict = {}
                if use_fuzzy_cover:
                    temp_covering_dict = TempDict(covering_dict)
                else:
                    temp_covering_dict = {}
                if use_cost_memory:
                   temp_cost_memory = TempDict(cost_memory)
                else:
                   temp_cost_memory = None

                #"start"
                #print node.id_num in MWEs
                #print node.id_num in temp_MWEs

                cost = 0

                if precalc_solo_relevant and costs:
                    temp_affected_nodes = affected_nodes
                    affected_nodes = copy.copy(affected_nodes)
                    for i in range(len(relevant_nodes)):
                        if current_config[1][i]:
                            cost += costs[i][1]
                        else:
                            cost += costs[i][0]
                            
                        affected_nodes.difference_update(solo_affected_nodes[i])
                    #if output:
                    #    print affected_nodes
                    #    print len(affected_nodes)
                    
                    update_lattice(relevant_nodes,current_config[1],temp_MWEs,temp_blocking_dict,temp_covering_dict, temp_cost_memory,affected_nodes)

                else:

                    update_lattice(relevant_nodes,current_config[1],temp_MWEs,temp_blocking_dict,temp_covering_dict, temp_cost_memory)
                if best_cost != None and cost > best_cost:
                   continue
                   
                #"after update"
                #print node.id_num in MWEs
                #print node.id_num in temp_MWEs                
                
                #temp_MWEs = get_temp_MWEs(relevant_nodes,affected_nodes,current_config[1])


                #likelihoods = []
                setup_time += time.time() - temp_time
                temp_time = time.time()
                #node_like = []
                for affected_node in affected_nodes:
                     #if output:
                     #    print_ngram(affected_node)
                     #    print_ngram(node.id_num)
                     if use_cost_memory:
                        if temp_cost_memory.get(affected_node, None) == None:
                            node_cost = calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict,affected_node)
                            temp_cost_memory[affected_node] = node_cost
                        else:
                            node_cost = cost_memory[affected_node]
                     else:
                        node_cost = calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict,affected_node)
                        
                     if output:
                         print node_cost
                     if node_cost == None:
                         #print "conflicting node"
                         cost = None
                         break
                     #node_like.append(node_likelihood)
                     cost += node_cost
                     if best_cost != None and cost > best_cost:
                        break

                #print "finished node cost"
                #print cost

                if cost == None:
                    #print "fail"
                    continue
                if output:
                    print "final cost for configuration"
                    print cost
                    print "best cost til now"
                    print best_cost
                #print cost

                #if do_pos_entropy and len(temp_MWEs) > 10:
               #     cost += calculate_pos_entropy_cost(pos_counts,relevant_nodes,current_config[1],temp_MWEs)
                
                #print "succeed"
                #likelihoods.append(likelihood)
                #node_time += time.time() - temp_time
                #temp_time = time.time()
                #likelihood += calculate_pos_likelihood(pos_total_count_dict, temp_pos_pattern_count_dict,temp_patterns, temp_MWEs,affected_pos,cache)
                #likelihoods.append(calculate_pos_likelihood(pos_total_count_dict, temp_pos_pattern_count_dict,temp_patterns, temp_MWEs,affected_pos,cache))
                #likelihood += calculate_global_likelihood(temp_MWEs,cache)
                #print calculate_global_likelihood(temp_MWEs,cache)
                #likelihoods.append(calculate_global_likelihood(temp_MWEs,cache))
                #likelihoods.append(node_like)
                #print likelihood
                #global_time += time.time() - temp_time
                #temp_time = time.time()
                #config_list.append([current_config[1],likelihood,likelihoods])
                if best_cost == None or cost < best_cost:
                    best_cost = cost
                    temp_changed = 0
                    for relevant_node in relevant_nodes:
                        if temp_MWEs.is_changed(relevant_node):
                            temp_changed += 1
                    best_configuration = [temp_changed,temp_MWEs,temp_blocking_dict,temp_covering_dict,temp_cost_memory,current_config[1]]
                #print "best"
                if current_config[0] == None or cost < current_config[0]:
                    i = len(current_config[1]) - 1
                    #print i
                    #print current_config[1]
                    while i >= 0 and ((not switch_search and not current_config[1][i]) or (switch_search and current_config[1][i])):
                        #print i
                        new_config = current_config[1][:i]
                        if switch_search:
                            new_config.append(False)
                        else:
                            new_config.append(True)
                        while len(new_config) < len(relevant_nodes):
                            if switch_search:
                                new_config.append(True)
                            else:
                                new_config.append(False)
                        #if is_consistent(new_config,relevant_nodes,i):
                        config_queue.append([cost,new_config])
                        i -= 1
                    result_time += time.time() - temp_time
                if precalc_solo_relevant and costs:
                    affected_nodes = temp_affected_nodes  
                    #"end"
                    #print node.id_num  in MWEs
                    #print node.id_num in temp_MWEs
            #print kdfjlkjsf
            if best_configuration[-1] != starting_config:
                temp_MWEs = best_configuration[1]
                temp_blocking_dict = best_configuration[2]
                temp_covering_dict = best_configuration[3]
                temp_cost_dict = best_configuration[4]
                for i in range(len(relevant_nodes)):
                   if best_configuration[-1][i] != starting_config[i]:
                      if relevant_nodes[i] in changed_dict:
                         changed_dict.remove(relevant_nodes[i])
                      else:
                         changed_dict.add(relevant_nodes[i])
                      
                        
                
                if precalc_solo_relevant:
                    for i in range(len(relevant_nodes)):
                        update_lattice(relevant_nodes,best_configuration[-1],MWEs,blocking_dict,covering_dict,cost_memory)
                        if use_cost_memory:
                           if costs:
                              for i in range(len(relevant_nodes)):
                                  if costs[i][2]:
                                      if best_configuration[-1][i]:
                                          costs[i][2][1].finalize_changes()
                                      else:
                                          costs[i][2][0].finalize_changes()
                           
                           temp_cost_dict.finalize_changes()
                else:
                    temp_MWEs.finalize_changes()
                    if use_block:
                        temp_blocking_dict.finalize_changes()
                    if use_fuzzy_cover:
                        temp_covering_dict.finalize_changes()
            #for i in range(len(relevant_nodes)):
            #   if not best_configuration[-1][i]:
            #      print_ngram(relevant_nodes[i])
            

            #if the_end_of_id != None:
            #   if cost_memory[the_end_of_id] != calculate_node_cost(MWEs,blocking_dict,covering_dict,the_end_of_id):
            #      print "problem!!!"
            #      print "relevant"
            #      for relevant_node in relevant_nodes:
            #         print_ngram(relevant_node)
            #      print "affected"
            #      for affected_node in affected_nodes:
            #         print_ngram(affected_node)
            #      print 
               
            if do_pos_entropy or do_pos_weighting:
                #print "adding pos back"
                #print best_configuration[2]
                change_pos_counts(pos_counts, relevant_nodes,best_configuration[-1],1)
                #best_configuration[3].finalize_changes()
                #ever_MWEs.update(best_configuration[3].added_set)
                #best_configuration[4].finalize_changes()
            if output:
                print "final result"
                print best_configuration[-1]

            #print "nodes with explained_count"
            #for node_id in explained_count_dict:
            #    if explained_count_dict[node_id]:
            #        print node_id
            #        print explained_count_dict[node_id]

            #if node.pos_num == 58033:
            #    print "HERE!!!"
            #    print_ngram(node.id_num)
            #    if node.id_num in MWEs:
            #        my_count += 1
            #    print my_count
            #    print pos_counts[58033]
                

            if node_count % 1000 == 0:
                #assert(sum(pos_counts) == len(MWEs))
                print node_count
                print "node"
                print node_count
                print len(relevant_nodes)
                print len(affected_nodes)
                print config_count
                print len(MWEs)
                if best_configuration[0] > 0:
                    print "changed"
                #print (changed - last_changed)/1000.0
                #last_changed = changed
                elapsed_time = time.time() - start_time
                sys.stdout.flush()
                #print elapsed_time
                #print init_setup_time
                #print setup_time
                #print node_time
                #print global_time
                #print result_time
                #if elapsed_time > 0.5:
                #    print "long time"
                #    print [id_dict[word] for word in decode_id(ngram_lookup[node.id_num])]
            #if node_count % 100000 == 0:
            #    print "total likelihood"
            #    print calculate_total_likelihood()
            #    sys.stdout.flush()

            #print calculate_total_likelihood()
            #print "end"

            #if not has_starting:
            #    print "NO STARTING!!!!!"
            #    print starting_config
            #    print config_list
        #pr.disable()
        #s = StringIO.StringIO()
        #sortby = 'cumulative'
        #ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        #ps.print_stats()
        #print s.getvalue()
        #print kjfkdlsjl
        #if check_overlaps and not load_overlaps:
        if get_overlaps or (check_overlaps and not load_overlaps):

            print "looking for overlaps"

            curr_MWEs = set()

            for MWE in MWEs:
                curr_MWEs.add(ngram_lookup[MWE])

            for inQ in inQs:
                inQ.put(curr_MWEs)


            done_threads = 0
            #overlap_counts = {}
            overlaps = Counter()
            while done_threads < workers:
                result = Q.get()
                if result == -1:
                    done_threads += 1
                else:
                    overlaps.update(result)
                    #for ngram in result:
                    #    if ngram not in overlap_counts:
                    #        overlap_counts[ngram] = {}
                    #    for ngram2 in result[ngram]:
                    #        overlap_counts[ngram][ngram2] = overlap_counts[ngram].get(ngram2,0) + result[ngram][ngram2]
                    #print "finished one"
                    #sys.stdout.flush()

            print "total num overlaps"
            print len(overlaps)

            '''

            for overlap in overlaps:
                first = id_lookup[overlap[0]]
                second = id_lookup[overlap[1]]
                if first == second:
                    continue
                if first in overlapping_nodes:
                    overlapping_nodes[first][second] = overlapping_nodes[first].get(second,0)
                else:
                    overlapping_nodes[first] = {second:1}
                    
                if second in overlapping_nodes:
                    overlapping_nodes[second][first] = overlapping_nodes[second].get(first,0) + 1
                else:
                    overlapping_nodes[second] = {first:1}
            '''

            to_delete = set()
            temp_count = 0
            overlap_count = 0

            for pair in overlaps:
                node1 = id_lookup[pair[0]]
                node2 = id_lookup[pair[1]]
                if overlaps[pair] >= min_overlaps and node1 != node2:
                #if node1 != node2 and (overlaps[pair] >= node_lookup[node1].count*relevancy_cutoff or overlaps[pair] >= node_lookup[node2].count*relevancy_cutoff): 
                    overlap_count += 1
                    overlapping_nodes[node1][node2] = overlaps[pair]
                    overlapping_nodes[node2][node1] = overlaps[pair]
                    
                '''
                node1_count = node_lookup[node1].count
                node2_count = node_lookup[node2].count
                temp_count += 1
                if temp_count % 1000 == 0:
                    print_ngram(node1)
                    print_ngram(node2)
                    print overlaps[pair]
                    print node1_count
                    print node2_count
                if node1_count*cover_cutoff < overlaps[pair] or node2_count*overlap_cutoff < overlaps[pair]:
                    print "here!"
                    if node1_count > node2_count:
                        overlapping_nodes[node2].add(node1)
                    else:
                        overlapping_nodes[node1].add(node2)
                    overlap_count +=1
                '''
                        

            print "filtered overlaps"
            print overlap_count
            
                        
                    
            print "finished overlaps"
            to_delete = []
            overlaps = []
        '''

        print "doing pos drop out"

        to_sort = []

        for pos_id in pos_lookup_dict:
            if pos_id in patterns:
                count = len(MWEs.intersection(pos_lookup_dict[pos_id]))
                if count > 1:
                    to_sort.append((count,pos_id))
                    
        to_sort.sort()
        pos_changed_pattern_count = 0
        pos_changed_MWE_count =0
        
        for pair in to_sort:
            pos_id = pair[1]
            nodes = list(MWEs.intersection(pos_lookup_dict[pos_id]))

            affected_nodes = get_all_nodes_down(nodes)
            #print "total"
            curr_likelihood = 0
            fake_cache = {"g":{},"gp":{}}
            for node in affected_nodes:
                node_likelihood = calculate_node_likelihood(explained_count_dict,MWEs, node)
                curr_likelihood += node_likelihood
            #print calculate_global_likelihood(MWEs,fake_cache)
            curr_likelihood += calculate_pos_likelihood(pos_total_count_dict, pos_pattern_count_dict,[pos_id], MWEs,pos_total_count_dict,fake_cache,try_change=False)
            curr_likelihood += calculate_global_likelihood(MWEs,fake_cache)

            temp_explained_counts, temp_pos_pattern_count_dict = get_plain_counts(nodes)
            
            temp_patterns = TempSet(patterns)
            temp_patterns.remove(pos_id)
            temp_MWEs = get_temp_MWEs(nodes,[False]*len(nodes))           


            for affected_node in affected_nodes:
                 node_likelihood = calculate_node_likelihood(temp_explained_counts,temp_MWEs, affected_node)
                 if node_likelihood == None:
                     #print "conflicting node"
                     likelihood = None
                     break
                 #node_like.append(node_likelihood)
                 likelihood += node_likelihood
            if likelihood == None:
                continue

            likelihood += calculate_pos_likelihood(pos_total_count_dict, temp_pos_pattern_count_dict,temp_patterns, temp_MWEs,affected_pos,cache,try_change=False)
            likelihood += calculate_global_likelihood(temp_MWEs,cache)

            if likelihood > curr_likelihood:
                temp_explained_counts.finalize_changes()
                temp_pos_pattern_count_dict.finalize_changes()
                temp_MWEs.finalize_changes()
                temp_patterns.finalize_changes()

                pos_changed_pattern_count += 1
                pos_changed_MWE_count += len(nodes)


        print "total pos changed"
        print pos_changed_pattern_count
        print pos_changed_MWE_count


        print jfkldsjflkf

        '''

         
        if it_count < 2:
           fout = open("%s_temp_MWEs_%d.dat" % (output_string,it_count),"wb")
           if not get_overlaps:
               cPickle.dump(MWEs,fout,-1)
           if not load_overlaps:
               cPickle.dump(overlapping_nodes,fout,-1)
           #cPickle.dump(patterns,fout,-1)
           fout.close()
        changed = len(last_MWEs.symmetric_difference(MWEs))
        print "end iteration"
        print "changed"
        print len(changed_dict)
        print "num MWEs"
        print len(MWEs)
        if len(changed_dict) < 20000:
           new_changed_dict = set()
           new_changed_dict.update(get_all_nodes_up(changed_dict))
           new_changed_dict.update(get_all_nodes_down(changed_dict))
           for node_id in changed_dict:
              if node_id in overlapping_nodes:
                 new_changed_dict.update(overlapping_nodes[node_id])

        else:
           new_changed_dict = set(node_lookup.keys())
        changed_dict = new_changed_dict
        #print "num patterns"
        #print len(patterns)
        sys.stdout.flush()
        it_count += 1
        if get_overlaps:
            break

    if get_overlaps:
        for inQ in inQs:
            inQ.put(None)
    if not get_overlaps:
        #output_set = set()
        #for MWE in MWEs:
        #    output_set.add(ngram_lookup[MWE])
            

        #fout = open("multiword_vocab_tfweighted_prodropmin_upxordown_patternfixed_200kmean.dat","wb")
        fout = open("final_vocab_%s.dat" % output_string,"wb")
        #cPickle.dump(output_set,fout,-1)
        cPickle.dump(MWEs, fout,-1)
        fout.close()
                
        
    









