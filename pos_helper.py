# -*- coding: utf-8 -*-
### These functions define what counts as a gap for English and French. Support
### for other languages can be added by adding a new function here, and setting
### matches_gap to point to that function in each script.


noun_pos_en = set(["PP","PDT","DT","CD","JJ","NN","NP","PP$","POS"])

noun_pos_fr = set(["PRO:IND","PRO:PER","DET:ART","NUM","ADJ","NOM","NAM","PRP","DET:POS"])

def matches_gap_en(pos,start,end):
    if end - start > 4:
        return False
    if pos[end-1] not in noun_pos_en: # quick check
        return False
    i = start
    if pos[i].startswith("PP"): #or pos[i] == "PPO":
        if end - start == 1:
            return True
        else:
            return False
    if pos[i] == "PDT":
        i += 1
        if i == end:
            return True
    if pos[i] == "DT" or pos[i] == "CD":
        i += 1
        if i == end:
            return True
    while pos[i] == "JJ":
        i += 1
        if i == end:
            return True
    while pos[i] == "NN" or pos[i] == "NP":
        i += 1
        if i == end:
            return True
    if pos[i] == "POS" or pos[i] == "PP$":
        i += 1
        if i == end:
            return True
    while pos[i] == "JJ":
        i += 1
        if i == end:
            return True
    while pos[i] == "NN":
        i += 1
        if i == end:
            return True
    return False


noun_pos_ja = set([u'代名詞',u'連体詞',u'形状詞-一般',u'助動詞',u'形容詞-一般',u'助動詞',u'助詞-格助詞',u"接尾辞-名詞的-",u'助詞-POS',u'補助記号-一般',u'接頭辞',u"助詞-係助詞"])

simple_pos_ja = set([u'形状詞-一般',u'助動詞連用形-ニ',u'形容詞-一般連用形-一般',u'名詞-数詞',u'接尾辞-名詞的-一般',u'助詞-係助詞'])

def matches_gap_ja_simple(pos,start,end):
    if end - start > 4:
        return False
    if pos[end-1] not in noun_pos_ja: # quick check
        return False

    i = start

    while pos[i].startswith(u"形状詞-") or pos[i].startswith(u"形容詞-一般連用形-一般"):
        i += 1
        if i == end:
            return True
        if pos[i].startswith(u"助動詞連用形-ニ"):
            i+= 1
            if i == end:
                return True

    if pos[i].startswith(u"名詞-数詞"):
        i += 1
        if i == end:
            return True
        if pos[i].startswith(u'接尾辞-名詞的-一般'):
            i += 1
            if i == end:
                return True

    if pos[i].startswith(u"助詞-係助詞"):
        i += 1
        if i == end:
            return True
    return False
    

def matches_gap_ja(pos,start,end):
    #print "here!"
    #print " ".join(pos[start:end])
    if end - start > 4:
        return False
    if pos[end-1] not in noun_pos_ja and not (pos[end-1].startswith(u"名詞-") or pos[end-1].startswith(u'接尾辞-名詞的-')): # quick check
        return False

    #print "this far"
    #if pos[start].startswith(u"代名詞") and (start == len(pos) - 1 or not pos[start+1].startswith(u"助詞-格助詞")):
    #    if end - start == 1:
    #        return True
    #    else:
    #        return False
    i = start
    if pos[i].startswith(u"連体詞"): #or pos[i] == "PPO":
        i += 1
        if i == end:
            return True
        
    while pos[i].startswith(u"形状詞-") or pos[i].startswith(u"形容詞-"):
        i += 1
        if i == end:
            return True
        if pos[i].startswith(u"助動詞"):
            i+= 1
            if i == end:
                return True

    if pos[i].startswith(u'接頭辞'):
        i+= 1
        if i == end:
            return True    

    if pos[i].startswith(u"代名詞"):
        i += 1
        if i == end:
            return True
            
    elif pos[i].startswith(u"形容詞-一般"):
        i += 1
        if i == end:
            return True
        if pos[i].startswith(u'接尾辞-名詞的-一般'):
            i += 1
            if i == end:
                return True


    else:
        if pos[i].startswith(u"名詞-"):
            #print "in first noun"
            while pos[i].startswith(u"名詞-"):
                i += 1
                if i == end:
                    return True
                
    while pos[i].startswith(u"助詞-POS") or pos[i].startswith(u'補助記号-一般') or pos[i].startswith(u'接尾辞-名詞的-'):
        i += 1
        if i == end:
            return True


    if pos[i].startswith(u'接頭辞'):
        i+= 1
        if i == end:
            return True  

    if pos[i].startswith(u"代名詞"):
        i += 1
        if i == end:
            return True
    elif pos[i].startswith(u"形容詞-一般"):
        i += 1
        if i == end:
            return True
        if pos[i].startswith(u'接尾辞-名詞的-一般'):
            i += 1
            if i == end:
                return True
    else:
        while pos[i].startswith(u"名詞-"):
            i += 1
            if i == end:
                return True
            
    while pos[i].startswith(u"接尾辞-名詞的-"):
        i += 1
        if i == end:
            return True        

    if pos[i].startswith(u"助詞-係助詞"):
        i += 1
        if i == end:
            return True  

    return False
    

def matches_gap_hr(pos,start,end):
    pass

noun_pos_en_bnc = set(["PN","DT","AT","CR","AJ","NN","NP","DP","PO"])


def matches_gap_en_bnc(pos,start,end):
    #print "here!"
    #print pos
    if end - start > 4:
        return False
    if pos[end-1] not in noun_pos_en_bnc: # quick check
        return False
    i = start
    if pos[i].startswith("PN"): #or pos[i] == "PPO":
        if end - start == 1:
            return True
        else:
            return False
    if pos[i] == "DT" or pos[i] == "AT" or pos[i] == "CR":
        i += 1
        if i == end:
            return True
    while pos[i] == "AJ":
        i += 1
        if i == end:
            return True
    while pos[i] == "NN" or pos[i] == "NP":
        i += 1
        if i == end:
            return True
    if pos[i] == "PO" or pos[i] == "DP":
        i += 1
        if i == end:
            return True
    while pos[i] == "AJ":
        i += 1
        if i == end:
            return True
    while pos[i] == "NN":
        i += 1
        if i == end:
            return True
    return False

noun_pos_en_ark = set(["O","X","D","S","Z","A","^","N"])

def matches_gap_en_ark(pos,start,end):
    if end - start > 4:
        return False
    if pos[end-1] not in noun_pos_en_ark: # quick check
        return False
    i = start
    if pos[i].startswith("O"): #or pos[i] == "PPO":
        if end - start == 1:
            return True
        else:
            return False
    if pos[i] == "X":
        i += 1
        if i == end:
            return True
    if pos[i] == "D":
        i += 1
        if i == end:
            return True
    while pos[i] == "A":
        i += 1
        if i == end:
            return True
    if pos[i] == "S" or pos[i] == "Z":
        i += 1
        if i == end:
            return True
    while pos[i] == "A":
        i += 1
        if i == end:
            return True
    while pos[i] == "N" or pos[i] == "^":
        i += 1
        if i == end:
            return True
    return False

def matches_gap_fr(pos,start,end):
    if end - start > 4:
        return False
    if pos[end-1] not in noun_pos_fr: # quick check
        return False
    i = start
    if pos[i].startswith("PRO:PER"): #or pos[i] == "PPO":
        if end - start == 1:
            return True
        else:
            return False
    if pos[i] == "PRO:IND":
        i += 1
        if i == end:
            return True
    if pos[i] == "DET:ART" or pos[i] == "NUM":
        i += 1
        if i == end:
            return True
    if pos[i] == "ADJ":
        i += 1
        if i == end:
            return True
    while pos[i] == "NOM" or pos[i] == "NAM":
        i += 1
        if i == end:
            return True
    if pos[i] == "PRP" or pos[i] == "DET:POS" or pos[i] == "ADJ":
        i += 1
        if i == end:
            return True
    if pos[i] == "NOM" or pos[i] == "NAM":
        i += 1
        if i == end:
            return True
    return False

pos_allowed = set(["N", "A", "Q", "P", "R", "Ec", "Ep"])

def matches_gap_hr(pos, start, end):
    if end - start > 4:
        return False
    else:
        for pos in pos[start:end]:
            if pos not in pos_allowed:
                return False
        return True

def matches_gap_universal(pos,start,end):
    if end - start > 2:
        return False
    return True
