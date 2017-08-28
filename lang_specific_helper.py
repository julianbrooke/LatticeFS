# -*- coding: utf-8 -*-
### These functions define what counts as a gap for the various languages and
### other language specific stuff (stop words, pronouns). Support for
### other languages can be added by including relevant functions here,
### setting the global function identifiers to point to your new function
### as part of the set_lang operation.

import re

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

def matches_gap_ja(pos,start,end):
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


pronouns_en = set(["he","she","i","you","we","they","his","her","him","me","us","it","them","their","my","your","yours","mine","our","ours","theirs","hers"])


def has_pronoun_ja(words, pos):
    return any([pos_id == u"代名詞" for pos_id in pos])

def has_pronoun_hr(words,pos):
    return any([pos_id == "P" for pos_id in pos])

french_pronoun_pos = set(["PRO:PER","DET:POS", "PRO:POS"])

def has_pronoun_fr(words,pos):
    return any([pos_id in french_pronoun_pos  for pos_id in pos])

def has_pronoun_en(words,pos):
    return any([word in pronouns_en for word in words])
    


not_wanted_en = set(["im", "dont", "didnt","doesnt","cant","wont","shouldnt","aint","ive","whats","arent","couldnt", "hadnt","hasnt","havent","isnt","shes","wasnt","werent","whod","wouldnt","youre","youve","whos","thats","wheres"])
not_wanted_web = set(["www","http","com"])
not_wanted_ja = set()

good_word = re.compile("^[A-Za-z]+([A-Za-z']*|[A-Za-z\-]+[A-Za-z]+)$")

bad_ja_word = set(u"０１２３４５６７８９＞｛　｝（　）［　］【　】、，…‥。・「　」『　』　〜：！？♪.,'-?!<>[]{}|“／”；−┐▲．＿卍■Г×┘〕＊＾’→●￣☆〇ＸＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ")


def check_good_en(pair):
    return good_word.search(pair[0])    

def all_good_words_en(span,start,end): # used to exclude nonalphabetic words from gaps
    for i in range(start,end):
        if not good_word.search(span[i][0]):
            return False
    return True

def check_good_ja(pair):
    return pair[0] not in bad_ja_word

def all_good_words_ja(span,start,end):
    for i in range(start,end):
        if not check_good_word(span[i]):
            return False

    return True

not_wanted = None
matches_gap = None
check_good_word = None
all_good_words = None
has_pronoun = None

def set_lang(lang,corpus):
    global not_wanted
    global matches_gap
    global check_good_word
    global all_good_words
    global has_pronoun

    if lang == "fr":
        not_wanted = not_wanted_web
        matches_gap = matches_gap_fr
        check_good_word = check_good_en
        all_good_words = all_good_words_en
        has_pronoun  = has_pronoun_fr
    if lang == "hr":
        not_wanted = not_wanted_web
        matches_gap = matches_gap_hr
        check_good_word = check_good_en
        all_good_words = all_good_words_en
        has_pronoun  = has_pronoun_hr
    elif lang == "ja":
        not_wanted = not_wanted_ja
        matches_gap = matches_gap_ja
        check_good_word = check_good_ja
        all_good_words = all_good_words_ja
        has_pronoun  = has_pronoun_ja
    elif lang == "en":
        if "bnc" in corpus: # use BNC tags
            matches_gap = matches_gap_en_bnc
            not_wanted = set([])
        else: # default to Penn treebank tegs
            matches_gap = matches_gap_en
            not_wanted = not_wanted_web.union(not_wanted_en)
        check_good_word = check_good_en
        all_good_words = all_good_words_en
        has_pronoun  = has_pronoun_en
