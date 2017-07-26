import cPickle
import gc
import sys
gc.disable()
from multi_helper import *
from pos_helper import matches_gap_en
import math

pronouns = set(["he","she","i","you","we","they","his","her","him","me","us","it","them","their","my","your","yours","mine","our","ours","theirs","hers"])

matches_gap = matches_gap_en

class Node:
    def __init__(self,id_num, pos_num, count, topic_predictability, syntactic_predictability,length):
        self.id_num = id_num
        self.pos_num = pos_num
        self.count = count
        self.log_count = math.log(count)
        self.topic_predictability = topic_predictability
        self.syntactic_predictability = syntactic_predictability
        self.length = length
        self.above_nodes = []
        self.below_nodes = []

    def __hash__(self):
        return self.id_num


    def __cmp__(self,other):
        if self.length < other.length:
            return -1
        if self.length > other.length:
            return 1
        this_num = self.syntactic_predictability #+ self.topic_predictability
        that_num = other.syntactic_predictability #+ other.topic_predictability
        if this_num > that_num:
            return -1
        elif this_num == that_num:
            return 0
        else:
            return 1
        #return (self.syntactic_predictability + self.topic_predictability).__cmp__(other.syntactic_predictability + other.topic_predictability)


def get_real_pos(ngram,pos_id):
    pos = decode_id(pos_id)
    words = decode_id(ngram)
    if len(words) == len(pos):
        return pos_id
    else:
        print pos
        return get_multi_id(pos[2:pos[1] + 2] + pos[pos[0] + 2:])

syntactic_predictability_counts = {}
lexical_predictability_counts = {}

syntactic_predictability_skip_counts = {}
lexical_predictability_skip_counts = {}

for i in range(8):
  
    syntactic_predictability_counts[i] = {}
    lexical_predictability_counts[i] = {}

    syntactic_predictability_skip_counts[i] = {}
    lexical_predictability_skip_counts[i] = {}  

def get_syntactic_predictability(ngram,words,pos,pos_counts,ngrams,unigrams):
    total_count = float(ngrams[ngram])
    #print "-------"

    #rarest_ngram_count = 1000000000000000
    #if len(words) == 2:
    #    best_syn_pred= 999999999
    #else:
    best_syn_pred= 0.0
    
    #print "main"
    #print [id_dict[word] for word in words]
    #print [POS_id_dict[pos[k]] for k in range(len(pos))]
    if len(pos) > len(words):
        start = pos[1]
        end = pos[0]
        pos = pos[2:]
        temp_words = words[:start] + [0]*(end-start) + words[start:]
        #print start
        #print end
        #print len(pos)
        for k in range(0,start) + range(end, len(pos)):
            #print k
            if k < start:
                temp_ngram_id = get_multi_id_range_multi_skip(temp_words,0, k, k+1, start, end, len(pos))
            else:
                temp_ngram_id = get_multi_id_range_multi_skip(temp_words,0, start, end, k, k+1, len(pos))
            #print "sub"
            #print [id_dict[word] for word in decode_id(temp_ngram_id)]
            if temp_ngram_id in ngrams:
                #print "yes"
                if not is_multi(temp_ngram_id):
                    if k == 0:
                        ID = temp_words[-1]
                        ID = ID << 18 | pos[-1]
                        #id_dict[0] = "missing"
                        #print [id_dict[word] for word in words]
                        #print id_dict[words[j-1]]
                        #print [POS_id_dict[pos_i] for pos_i in pos]
                        #print POS_id_dict[pos[j-1]]
                        sub_count = unigrams[ID]
                    else:
                        ID = temp_words[0]
                        ID = ID << 18 | pos[0]
                        sub_count = unigrams[ID]

                else:
                    sub_count = ngrams[temp_ngram_id]

                if sub_count < total_count:
                    sub_count = total_count
                #if sub_count < rarest_ngram_count:                
                #    rarest_ngram_count = sub_count
                #else:
                #    continue
                for i in range(0, len(pos) - 1):
                    for j in range(i+2,  len(pos) + 1):
                #if True:
                            #i = 0
                            #j = len(pos)
                            if i <=k <j and i < start and end < j:
                
                                #print "here"
                                #print k
                                #print i
                                #print j

                                num = float(pos_counts[get_multi_id_range_one_word(pos,temp_words,i,j,k)])
                                denom = float(pos_counts[get_multi_id_range_wild(pos,i,j,k)])
                                print k
                                print "skip"
                                print num
                                print denom
                                print total_count
                                print sub_count
                            
                                if pos[k] in POS_id_dict and POS_id_dict[pos[k]].startswith("PP"):
                                #if id_dict[temp_words[k]] in pronouns:
                                    result = 1 - (total_count/sub_count)
                                    print "pronoun"
                                else:
                                    #result =  min(1 - (total_count/sub_count),(num/denom)*(sub_count/total_count)*(1 - total_count/num))
                                    #result =  min(1 - (total_count/sub_count),(num/denom)*(sub_count/total_count)*(1 - sub_count/denom))
                                    #result =  (num/denom)*(sub_count/total_count)
                                    #result = (num/denom)*(sub_count/total_count)*max(0,(1 - (total_count/num))) + (1 - (total_count/sub_count))*min(1,(total_count/num))
                                    result = min((num/denom)*(sub_count/total_count),(1 - (total_count/sub_count)))
                                    #result = (num/denom)*(sub_count/total_count)*(1.0/(len(words) - 1)) + (1 - (total_count/sub_count))*((len(words) - 2.0)/(len(words) - 1))
                                
                                #result = result = (num/denom)*(sub_count/total_count)
                                #print num/denom
                                #print result
                                if result > best_syn_pred:
                                #if (len(words) > 2 and result > best_syn_pred) or (len(words) == 2 and result < best_syn_pred):
                                    best_syn_pred = result
                                    best_k = k
                        
                        
    else:
        for k in range(0,len(pos)):

            temp_ngram_id = get_multi_id_range_skip(words,0,k,k+1,len(pos))

            if temp_ngram_id in ngrams:

                if not is_multi(temp_ngram_id):
                    if k == 0:
                        ID = words[1]
                        ID = ID << 18 | pos[1]
                        sub_count = unigrams[ID]
                    else:
                        ID = words[0]
                        ID = ID << 18 | pos[0]
                        sub_count = unigrams[ID]
                else:
                    sub_count = ngrams[temp_ngram_id]

                if sub_count < total_count:
                    sub_count = total_count


                #if sub_count < rarest_ngram_count:
                #    rarest_ngram_count = sub_count
                #else:
                #    continue                    
                #print "sub"
                #print [id_dict[word] for word in decode_id(temp_ngram_id)]
                for i in range(0,len(pos)-1):
                    for j in range(i + 2, len(pos) + 1):
                            if i <=k <j:
                                #print "here"
                                #print k
                                #print i
                                #print j

                                num = float(pos_counts[get_multi_id_range_one_word(pos,words,i,j,k)])
                                denom =  float(pos_counts[get_multi_id_range_wild(pos,i,j,k)])
                                print k
                                print "regular"
                                print num
                                print denom
                                print total_count
                                print sub_count
                                
                                if pos[k] in POS_id_dict and POS_id_dict[pos[k]].startswith("PP"):
                                #if id_dict[words[k]] in pronouns:
                                    print "pronoun"
                                    result = 1 - (total_count/sub_count)
                                else:
                                    #result =  min(1 - (total_count/sub_count),(num/denom)*(sub_count/total_count)*(1 - total_count/num))
                                    #result =  min(1 - (total_count/sub_count),(num/denom)*(sub_count/total_count)*(1 - sub_count/denom))
                                    #result =  (num/denom)*(sub_count/total_count)
                                    result = min((num/denom)*(sub_count/total_count),(1 - (total_count/sub_count)))
                                    #result = (num/denom)*(sub_count/total_count)*(1.0/(len(words) - 1) + (1 - (total_count/sub_count))*((len(words) - 2.0)/(len(words) - 1))
                                    #result = (num/denom)*(sub_count/total_count)*max(0,(1 - (total_count/num))) + (1 - (total_count/sub_count))*min(1,(total_count/num))                                
                                #result = result = (num/denom)*(sub_count/total_count)
                                print result
                                #if (len(words) > 2 and result > best_syn_pred) or (len(words) == 2 and result < best_syn_pred):
                                if result > best_syn_pred:
                                    best_syn_pred = result
                                    best_k = k


    if best_syn_pred == 0:
        print "!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        print [id_dict[word] for word in words]
    #else:
    #    print "......"

        best_syn_pred = 0.0000001
    best_syn_pred = 1/best_syn_pred

    return best_syn_pred
                        
                        
                    


        

def get_topic_predictability(ngram,words,total_counts,paired_counts):
    max_topic = 0.0
    #print [id_dict[word] for word in words]
    if ngram in total_counts:
        total_df = float(total_counts[ngram])
        for i in range(1, len(words)):
            #print i
            first_part = get_multi_id_range(words,0,i)
            second_part = get_multi_id_range(words,i, len(words))
            if first_part in paired_counts and second_part in paired_counts[first_part]:
                temp_pred =(paired_counts[first_part][second_part] - total_df)/paired_counts[first_part][second_part]
                #print temp_pred
                if temp_pred > max_topic:
                    max_topic = temp_pred
    return max_topic
    

    

def get_predictabilities(ngram,pos,pos_counts,total_counts,paired_counts,ngrams,unigrams):
    words = decode_id(ngram)
    pos = decode_id(pos)
    return get_syntactic_predictability(ngram,words,pos,pos_counts,ngrams, unigrams), get_topic_predictability(ngram,words, total_counts,paired_counts)
    

def get_relevant_nodes(node,node_lookup):
    #print "node:"

    #print [id_dict[word] for word in decode_id(ngram_lookup[node.id_num])]
    #print node.count
           
    compare = node.count
    new_nodes = set([node.id_num])
    all_nodes = set()
    while new_nodes:
        temp_nodes = set()
        for new_node in new_nodes:
            for below_node in node_lookup[new_node].below_nodes:
                if compare > node_lookup[below_node].count*relevant_node_cutoff:
                    temp_nodes.add(below_node)
        new_nodes = temp_nodes.difference(all_nodes)
        #for below_node in new_nodes:
        #    print "relevant below"
        #    print [id_dict[word] for word in decode_id(ngram_lookup[below_node])]
        #    print node_lookup[below_node].count
        all_nodes.update(temp_nodes)

    new_nodes = set([node.id_num])
    all_nodes2 = set()
    while new_nodes:
        temp_nodes = set()
        for new_node in new_nodes:
            for above_node in node_lookup[new_node].above_nodes:
                if node_lookup[above_node].count > compare*relevant_node_cutoff:
                    temp_nodes.add(above_node)
        new_nodes = temp_nodes.difference(all_nodes)
        #for above_node in new_nodes:
        #    print "relevant above"
        #    print [id_dict[word] for word in decode_id(ngram_lookup[above_node])]
        #    print node_lookup[above_node].count
        all_nodes.update(temp_nodes)
    all_nodes.update(all_nodes2)
    all_nodes.add(node.id_num)
    return list(all_nodes)


use_brown_nouns = False

if __name__ == "__main__":
    relevant_node_cutoff = 0.05

    #def load_lattice():
    ngram_count = 0
    f = open("initial_ngrams_2.dat","rb")
    id_dict = cPickle.load(f)
    ngrams = cPickle.load(f)
    token_count = cPickle.load(f)
    sentence_count = cPickle.load(f)
    POS_id_dict = cPickle.load(f)
    f.close()
    id_dict[wild_card] = "*"

    f = open("best_POS_2.dat","rb")
    #f = open("best_POS_wbrown.dat","rb")
    #f = open("best_brown_2.dat","rb")
    best_pos_dict = cPickle.load(f)
    cPickle.load(f)
    unigrams = cPickle.load(f)
    f.close()

    '''

    f = open("brown_clusters_2.dat","rb")
    brown_id_dict = cPickle.load(f)    
    f.close()
    '''
    '''
    print len(unigrams)
    
    for ngram in best_pos_dict:
        words = decode_id(ngram)
        pos = decode_id(best_pos_dict[ngram])
        
        if len(words) == len(pos):
            print [id_dict[word] for word in words]
            print [brown_id_dict[word] for word in words]
            print pos
            for i in range(len(words)):
                print id_dict[words[i]]
                print pos[i]
                ID = words[i]
                ID = ID << 18 | pos[i]
                try:
                    print unigrams[ID]
                except:
                    print "BAD!!!"
        else:
            print [id_dict[word] for word in words]
            print [brown_id_dict[word] for word in words]
            print pos
    print djslkdfjs
    '''
       
        

    #f = open("best_POS_2.dat","rb")
    #f = open("best_POS_wbrown.dat","rb")
    #best_true_pos_dict = cPickle.load(f)
    #f.close()


    f = open("pos_stats_2.dat", "rb")
    #f = open("pos_stats_wbrown.dat", "rb")
    #f = open("brown_stats_2.dat", "rb")
    pos_stats = cPickle.load(f)
    f.close()

    f = open("compositionality_info_2.dat","rb")
    total_counts = cPickle.load(f)
    paired_counts = cPickle.load(f)
    f.close()

    nodes_dict = {}
    pos_dict = {}
    type_dict = {}
    id_num = 0
    pos_id = 0

    ngram_list = ngrams.keys()
    ngram_list.sort(reverse=True)
    for ngram in ngram_list:
        if not is_multi(ngram):
            continue
        ngram_count += 1
        if ngram_count % 1000 == 0:
            print ngram_count
        if ngram not in nodes_dict:
            print "initial"
            print " ".join([id_dict[word] for word in decode_id(ngram)])
            print best_pos_dict[ngram]
            real_pos = get_real_pos(ngram,best_pos_dict[ngram])
            if real_pos not in pos_dict:
                pos_dict[real_pos] = pos_id
                pos_id += 1
            syntactic_predictability,topic_predictability = get_predictabilities(ngram,best_pos_dict[ngram],pos_stats,total_counts,paired_counts,ngrams,unigrams)
            print syntactic_predictability
            print topic_predictability
            print ngrams[ngram]
            nodes_dict[ngram] = Node(id_num,pos_dict[real_pos],ngrams[ngram],topic_predictability, syntactic_predictability,len(decode_id(ngram)))
            id_num += 1
        words = decode_id(ngram)
        #pos = decode_id(best_true_pos_dict[ngram])
        pos = decode_id(best_pos_dict[ngram])
        if len(pos) > words:
            start = pos[1]
            end = pos[0]
            pos = pos[2:]
        else:
            start = -1
            end = -1

        if use_brown_nouns:
            for i in range(len(pos)):
                if pos[i] > len(POS_id_dict):
                    pos[i] = pos[i] % len(POS_id_dict)

        pos = [POS_id_dict[item] for item in pos]
            
        if len(words) > 2:
            for i in range(len(words)):
                below_ngram = get_multi_id_range_skip(words,0,i,i+1,len(words))
                if below_ngram in ngrams:
                    if i != 0 and i != len(words) - 1:
                        if start == -1:
                            if not matches_gap(pos,i,i+1):
                                continue

                        elif i == start - 1:
                            if not matches_gap(pos,start -1,end):
                                continue

                        elif i == end:
                            if not matches_gap(pos,start,end + 1):
                                continue

                        else:
                            continue
                            
                        
                    if below_ngram not in nodes_dict:
                        print "below"
                        print " ".join([id_dict[word] for word in decode_id(below_ngram)])
                        print best_pos_dict[ngram]
                        real_pos = get_real_pos(below_ngram,best_pos_dict[below_ngram])
                        if real_pos not in pos_dict:
                            pos_dict[real_pos] = pos_id
                            pos_id += 1

                        syntactic_predictability,topic_predictability = get_predictabilities(below_ngram,best_pos_dict[below_ngram],pos_stats,total_counts,paired_counts,ngrams,unigrams)                       
                        print syntactic_predictability
                        print topic_predictability
                        print ngrams[below_ngram]

                        nodes_dict[below_ngram] = Node(id_num,pos_dict[real_pos],ngrams[below_ngram],topic_predictability, syntactic_predictability,len(words) -1)
                        id_num += 1
                    #nodes_dict[below_ngram].above_nodes.append(nodes_dict[ngram])
                    #nodes_dict[ngram].below_nodes.append(nodes_dict[below_ngram])
                    nodes_dict[below_ngram].above_nodes.append(nodes_dict[ngram].id_num)
                    nodes_dict[ngram].below_nodes.append(nodes_dict[below_ngram].id_num)                

    nodes = nodes_dict.values()

    ngram_lookup = {}
    node_lookup = {}
    for ngram in nodes_dict:
        ngram_lookup[nodes_dict[ngram].id_num] = ngram
        node_lookup[nodes_dict[ngram].id_num] = nodes_dict[ngram]

    '''

    f = open("initial_ngrams.dat","rb")
    id_dict = cPickle.load(f)
    f.close()


    f = open("lattice.dat","rb")
    nodes = cPickle.load(f)
    pos_id = cPickle.load(f)
    ngram_lookup = cPickle.load(f)
    node_lookup = cPickle.load(f)
    f.close()
    '''
    '''
    relevant_node_total = 0.0
    ngram_count = 0
    for node in nodes:
        ngram_count += 1
        if ngram_count % 1000 == 0:
            #break
            print ngram_count
        relevant_nodes = get_relevant_nodes(node,node_lookup)
        relevant_nodes.sort()
        node.relevant_nodes = relevant_nodes
        relevant_node_total += len(relevant_nodes)

    print relevant_node_total/len(nodes)
    '''
    nodes.sort()
    #return nodes,pos_id,ngram_lookup

    fout = open("lattice.dat","wb")
    cPickle.dump(nodes,fout,-1)
    cPickle.dump(pos_dict,fout,-1)
    cPickle.dump(ngram_lookup, fout, -1)
    cPickle.dump(node_lookup,fout,-1)
    fout.close()


    '''
    sys.setrecursionlimit(3000000)
    fout = open("lattice.dat","wb")
    cPickle.dump(nodes,fout,-1)
    cPickle.dump(nodes_dict,fout,-1)
    cPickle.dump(pos_id,fout,-1)
    fout.close()
    '''        
        
    
