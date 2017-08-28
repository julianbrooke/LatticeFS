### this is the code which identifies the best FS (MWE) from the n-grams arranged
### in the lattice. See the paper for details on how it works, though note that
### the problem is formulated differently than in the paper: instead
### of maximizing "explainedness" this code actually minimizes its inverse


import cPickle
import gc
import math
import copy
import time
import sys
import codecs
from build_lattice import Node
from collections import Counter, defaultdict
from multi_helper import *
import random
gc.disable()


f = open("%s_options.dat" % sys.argv[1],"rb")
options = cPickle.load(f)
f.close()

use_overlaps = True
use_block = True   # block = clearing in the paper

MWE_cost = options.C  # the C parameter
cover_cutoff = 2.0/3.0 # hard covering cutoff
max_relevant_nodes = 5 # used to restrict the search


MWE_cost_log = math.log(MWE_cost,2)
cover_cutoff_log =  math.log(cover_cutoff,2)


# the temp classes are used to effect temporary changes to the corresponding
# data structure without conflict among multiple paths or having to make
# full copies. Finalize changes is called when the changes can be made
# permanant
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
        if item not in self.fixed_dict:
            self.changed_dict[item] = value
        else:
            if self.fixed_dict[item] == value:
                if item in self.changed_dict:
                    del self.changed_dict[item]
            else:
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
            self.fixed_dict[item] = self.changed_dict[item]


    def copy(self):
        new_dict = TempDict(self.fixed_dict)
        new_dict.changed_dict = self.changed_dict.copy()
        return new_dict


### lattice traversal helper functions


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




def get_all_nodes_down_notcovered(ref_node):
    new_nodes = node_lookup[ref_node].below_nodes
    good_nodes = set()
    while new_nodes:
        next_nodes = set()
        for node in new_nodes:
               if not node_lookup[node].is_covered:
                   good_nodes.add(node)
               next_nodes.update(node_lookup[node].below_nodes)
        new_nodes = next_nodes
    return good_nodes



blocked_lookup = {}

def get_all_nodes_up_blocked(ref_node):
    if ref_node in blocked_lookup:
        return blocked_lookup[ref_node]
    else:
        ref_pred = node_lookup[ref_node].syntactic_predictability
        new_nodes = node_lookup[ref_node].above_nodes
        good_nodes = set()
        while new_nodes:
            next_nodes = set()
            for node in new_nodes:
                if not node_lookup[node].is_covered and node_lookup[node].syntactic_predictability < ref_pred: 
                     good_nodes.add(node)
                next_nodes.update(node_lookup[node].above_nodes)
            new_nodes = next_nodes
        if len(good_nodes) > 5:
            blocked_lookup[ref_node] = good_nodes
        return good_nodes





def get_ratio(anchor, compare):
    if anchor > compare:
        return compare/float(anchor)
    else:
        return anchor/float(compare)



# Given a node in the lattice and a current state as represented by the
# set of current MWEs, find nodes which are relevant, narrow them to down
# to max_relevant_nodes using pairwise influence on cost function, and then
# find all nodes that are affected by the relevant nodes choices
def get_relevant_and_affected_nodes(ref_node,MWEs):
    ref_count = float(node_lookup[ref_node].count)
    ref_syntax = node_lookup[ref_node].syntactic_predictability
 
    overlap_cutoff = ref_count * cover_cutoff
    if use_block:
        block_affected_nodes = get_all_nodes_up_blocked(ref_node)
        block_relevant_nodes = MWEs.intersection(get_all_nodes_up([ref_node]))

        if len(block_relevant_nodes) > 0:
            blocking_factor = ref_syntax
    else:
        block_affected_nodes = []
        block_relevant_nodes = []

    cover_affected_nodes = get_all_nodes_down_notcovered(ref_node)
    cover_relevant_nodes = MWEs.intersection(cover_affected_nodes)



    if use_overlaps:
        overlap_affected_nodes = node_lookup[ref_node].overlaps
        overlap_relevant_nodes = MWEs.intersection(overlap_affected_nodes)
        overlap_affected_nodes = overlap_relevant_nodes
    else:
        overlap_relevant_nodes = []
        overlap_affected_nodes = []
    

    overlapped_count = 0
    relevant_nodes = set()
    if len(overlap_relevant_nodes) + len(block_relevant_nodes) + len(cover_relevant_nodes) > max_relevant_nodes:
       to_sort = []
       for node_id in overlap_relevant_nodes:
           overlap_count = float(node_lookup[ref_node].overlaps[node_id])
           other_count = node_lookup[node_id].count
           if other_count > ref_count:
              affected_percent = overlap_count/ref_count
           else:
              affected_percent = overlap_count/other_count

           to_sort.append((affected_percent,node_lookup[node_id].count,node_id))

       
       for node_id in block_relevant_nodes:

           if node_id not in block_affected_nodes:
              affected_percent = node_lookup[node_id].count/ref_count
           else:
              affected_percent = 1
           to_sort.append((affected_percent, node_lookup[node_id].count,node_id))
                   
       for node_id in cover_relevant_nodes:

           affected_percent = ref_count/node_lookup[node_id].count
           if node_lookup[node_id].syntactic_predictability > ref_syntax:
              affected_percent = 1

           to_sort.append((0,affected_percent, node_lookup[node_id].count,node_id))
                   
       to_sort.sort(reverse=True)

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
    
    affected_nodes_by_relevant = []
    if relevant_nodes:
       affected_nodes_by_relevant.append(copy.copy(affected_nodes))
        
    for relevant_node in relevant_nodes:
        temp_affected = affected_nodes
        affected_nodes = set()
        if use_block:
            affected_nodes.update(get_all_nodes_up_blocked(relevant_node))
        affected_nodes.update(get_all_nodes_down_notcovered(relevant_node))
        if use_overlaps:
            affected_nodes.update(MWEs.intersection(node_lookup[relevant_node].overlaps))                
        affected_nodes.add(relevant_node)
        affected_nodes.add(ref_node)
        affected_nodes_by_relevant.append(affected_nodes)
        temp_affected.update(affected_nodes)
        affected_nodes = temp_affected
    relevant_nodes.insert(0,ref_node)
    return relevant_nodes,[affected_nodes,affected_nodes_by_relevant]


# calculate the cost (inverse explainedness) of a specific node at a given
# state
def calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict, affected_node_id):
    affected_node = node_lookup[affected_node_id]
    count = float(affected_node.count)
    if affected_node_id in temp_MWEs:
        result = MWE_cost_log
        if use_overlaps:
            overlap_count = sum([affected_node.overlaps[other_node] for other_node in [node for node in affected_node.overlaps if node in temp_MWEs]])
            overlap_count += sum(temp_covering_dict[affected_node_id])
            if overlap_count >= count:
                result = 999999999
            else:
                result*=(count/(count-overlap_count))
        return result
    else:

        result = affected_node.syntactic_predictability
        modifier = 0
        temp = sum(temp_covering_dict[affected_node_id])
        modifier += temp
            
        if modifier > 0:
            modifier = -(min(count, modifier)/count)*result
            result += modifier

        if use_block:
            modifier = -sum(temp_blocking_dict[affected_node_id])
            result*= 2**modifier


        if result <= 0:
            result = 0

        return result



# Make temporary changages to the state of the lattice
def update_lattice(relevant_nodes,config,MWEs,blocking_dict,covering_dict,cost_memory=None,affected_nodes=None):
    temp_blocking_dict = {}
    temp_covering_dict = {}
    for i in range(len(relevant_nodes)):
        relevant_node = relevant_nodes[i]
        count = node_lookup[relevant_node].count
        changed_true = config[i] and relevant_node not in MWEs
        changed_false = not config[i] and relevant_node in MWEs
        blocking_factor = node_lookup[relevant_node].syntactic_predictability
        if changed_true or changed_false:
            cost_memory[relevant_node] = None
            if use_overlaps:
                   for node in node_lookup[relevant_node].overlaps:
                       if node in MWEs:
                           cost_memory[node] = None

            wanted_cover = get_all_nodes_down_notcovered(relevant_node)
            if affected_nodes:
                wanted_cover = wanted_cover.intersection(affected_nodes)
            for node in wanted_cover:
                if node not in temp_covering_dict:
                    temp_covering_dict[node] = copy.copy(covering_dict[node])
                if node not in MWEs:
                    cost_memory[node] = None
                if changed_true:
                    temp_covering_dict[node].append(count)
                else:
                    temp_covering_dict[node].remove(count)
            if use_block:
                wanted_block = get_all_nodes_up_blocked(relevant_node)
                if affected_nodes:
                    wanted_block = wanted_block.intersection(affected_nodes)
                for node in wanted_block:
                    if node not in temp_blocking_dict:
                        temp_blocking_dict[node] = copy.copy(blocking_dict[node])                    
                    if node not in MWEs:
                        cost_memory[node] = None
                    if changed_true:
                        temp_blocking_dict[node].append(blocking_factor - node_lookup[node].syntactic_predictability)
                    else:                
                        temp_blocking_dict[node].remove(blocking_factor - node_lookup[node].syntactic_predictability)

            if changed_true:
                MWEs.add(relevant_node)
            else:
                MWEs.remove(relevant_node)
    for node in temp_blocking_dict:
        blocking_dict[node] = temp_blocking_dict[node]
    
    for node in temp_covering_dict:
        covering_dict[node] = temp_covering_dict[node]       
         



    

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



if __name__ == "__main__":

    my_count = 0
    


    f = open("%s_ngrams.dat" % options.output,"rb")
    sentence_count = cPickle.load(f)
    id_dict = cPickle.load(f)
    word_counts = cPickle.load(f)
    skip_word_counts = cPickle.load(f)
    token_count = cPickle.load(f)
    f.close() 


    rev_id_dict = {}
    for ID in id_dict:
        rev_id_dict[id_dict[ID]] = ID


    f = open("%s_lattice.dat" % options.output ,"rb")
    nodes = cPickle.load(f)
    f.close()

    node_lookup = {}
    for node in nodes:
        node_lookup[node.id_num] = node
    total_nodes = float(len(nodes))

    changed_dict = set(iter(node_lookup))

    MWEs= set()
    blocking_dict = defaultdict(list)
    covering_dict = defaultdict(list)
    cost_memory = {}
    it_count = 0        
    output = False

    while len(changed_dict) > 0:
        old_changed = changed_dict
        changed_dict = set()
        if not options.silent:
            print "start iteration % d" % it_count
        node_count = 0
        last_MWEs = copy.copy(MWEs)
        for node in nodes:

            
            if node_count % 10000 == 0:
                if not options.silent:
                    print "checked %d nodes out of %d" % (node_count,len(nodes))
                    print "current FS lexicon size: %d" % len(MWEs)


            node_count += 1

            if node.is_covered or node.id_num not in old_changed:
                continue


            relevant_nodes,affected_nodes = get_relevant_and_affected_nodes(node.id_num,MWEs)

            starting_config = get_starting_config(relevant_nodes)

            affected_nodes, affected_nodes_by_relevant = affected_nodes
            
            costs = []
            if len(relevant_nodes) > 1 and len(affected_nodes) > 5:
                 #precalculate costs for affected nodes which are affected
                 #only by one relevant node
                 solo_affected_nodes = []
                 for i in range(len(relevant_nodes)):
                     costs.append([0,0,[]])
                     solo_affected = copy.copy(affected_nodes_by_relevant[i])
                     relevant_node = relevant_nodes[i]
                     for j in range(0,len(relevant_nodes)):
                         if i != j:
                             solo_affected.difference_update(affected_nodes_by_relevant[j])

                     solo_affected_nodes.append(solo_affected)
                     if solo_affected:                                
                         temp_MWEs = TempSet(MWEs)
                         temp_cost_memory = TempDict(cost_memory)
                         
                         if use_block:
                             temp_blocking_dict = TempDict(blocking_dict)
                         else:
                             temp_blocking_dict = {}
                        
                         temp_covering_dict = TempDict(covering_dict)

                         update_lattice([relevant_node],[False],temp_MWEs,temp_blocking_dict,temp_covering_dict,temp_cost_memory,solo_affected)
                         for affected_node in solo_affected:
                                if temp_cost_memory.get(affected_node, None) == None:
                                   temp_cost = calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict,affected_node)
                                   temp_cost_memory[affected_node] = temp_cost
                                   costs[-1][0] += temp_cost
                                else:
                                   costs[-1][0] += temp_cost_memory[affected_node]
                         costs[-1][2].append(temp_cost_memory)
                         temp_cost_memory = TempDict(cost_memory)
                         temp_MWEs = TempSet(MWEs)
                         if use_block:
                             temp_blocking_dict = TempDict(blocking_dict)
                         else:
                             temp_blocking_dict = {}
                         
                         temp_covering_dict = TempDict(covering_dict)                          
                         update_lattice([relevant_node],[True],temp_MWEs,temp_blocking_dict,temp_covering_dict,temp_cost_memory,solo_affected)
                         for affected_node in solo_affected:
                              if temp_cost_memory.get(affected_node, None) == None:
                                   temp_cost = calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict,affected_node)
                                   temp_cost_memory[affected_node] = temp_cost
                                   costs[-1][1] += temp_cost
                              else:
                                   costs[-1][1] += temp_cost_memory[affected_node]

                         costs[-1][2].append(temp_cost_memory)
          
                
            best_cost = None
            best_configuration = None
            empty_config = [False]*len(relevant_nodes)
            config_queue = [[None,[True]*len(relevant_nodes)]]
            config_count = 0
            has_starting = False

            while config_queue:
                config_count += 1
                current_config = config_queue.pop()

                temp_MWEs = TempSet(MWEs)
                if use_block:
                    temp_blocking_dict = TempDict(blocking_dict)
                else:
                    temp_blocking_dict = {}

                temp_covering_dict = TempDict(covering_dict)

                temp_cost_memory = TempDict(cost_memory)


                cost = 0

                if costs:
                    temp_affected_nodes = affected_nodes
                    affected_nodes = copy.copy(affected_nodes)
                    for i in range(len(relevant_nodes)):
                        if current_config[1][i]:
                            cost += costs[i][1]
                        else:
                            cost += costs[i][0]
                            
                        affected_nodes.difference_update(solo_affected_nodes[i])

                    
                    update_lattice(relevant_nodes,current_config[1],temp_MWEs,temp_blocking_dict,temp_covering_dict, temp_cost_memory,affected_nodes)

                else:

                    update_lattice(relevant_nodes,current_config[1],temp_MWEs,temp_blocking_dict,temp_covering_dict, temp_cost_memory)
                if best_cost != None and cost > best_cost:
                   continue

                for affected_node in affected_nodes:

                     if temp_cost_memory.get(affected_node, None) == None:
                         node_cost = calculate_node_cost(temp_MWEs,temp_blocking_dict,temp_covering_dict,affected_node)
                         temp_cost_memory[affected_node] = node_cost
                     else:
                         node_cost = cost_memory[affected_node]

                    
                     if node_cost == None:
                         cost = None
                         break
                     cost += node_cost
                     if best_cost != None and cost > best_cost:
                        break

                if cost == None:
                    continue

                if best_cost == None or cost < best_cost:
                    best_cost = cost
                    temp_changed = 0
                    for relevant_node in relevant_nodes:
                        if temp_MWEs.is_changed(relevant_node):
                            temp_changed += 1
                    best_configuration = [temp_changed,temp_MWEs,temp_blocking_dict,temp_covering_dict,temp_cost_memory,current_config[1]]
                if current_config[0] == None or cost < current_config[0]:
                    i = len(current_config[1]) - 1
                    while i >= 0 and current_config[1][i]:
                        new_config = current_config[1][:i]
                        new_config.append(False)
                        while len(new_config) < len(relevant_nodes):
                            new_config.append(True)
                        config_queue.append([cost,new_config])
                        i -= 1
                if costs:
                    affected_nodes = temp_affected_nodes  
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
                      
                        
                
                for i in range(len(relevant_nodes)):
                       update_lattice(relevant_nodes,best_configuration[-1],MWEs,blocking_dict,covering_dict,cost_memory)
                       if costs:
                          for i in range(len(relevant_nodes)):
                              if costs[i][2]:
                                  if best_configuration[-1][i]:
                                      costs[i][2][1].finalize_changes()
                                  else:
                                      costs[i][2][0].finalize_changes()
                       
                       temp_cost_dict.finalize_changes()
 
         
        changed = len(last_MWEs.symmetric_difference(MWEs))
        if not options.silent:
            print "end iteration %d" % it_count
            print "%d nodes changed" % (len(changed_dict))
            print "%d FS in lexicon" % len(MWEs)
        if len(changed_dict) < 20000:
           new_changed_dict = set()
           new_changed_dict.update(get_all_nodes_up(changed_dict))
           new_changed_dict.update(get_all_nodes_down(changed_dict))
           for node_id in changed_dict:
              new_changed_dict.update(node_lookup[node_id].overlaps)
        else:
           new_changed_dict = set(node_lookup.keys())
        changed_dict = new_changed_dict
        sys.stdout.flush()
        it_count += 1

    fout = codecs.open(options.output,"w",encoding="utf-8")
    for MWE in MWEs:
        ngram = node_lookup[MWE].ngram
        if ngram in skip_word_counts:
            words = decode_id(ngram)
            loc = words[0]
            words = words[1:]
            words = [id_dict[num] for num in words]
            words = words[:loc + 1] + ["*"] + words[loc + 1:]
        else:
            words = [id_dict[num] for num in decode_id(ngram)]
        fout.write(" ".join(words) + "\n")
    fout.close()
      

            

    
                
        
    









