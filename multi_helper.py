### These set of functions handle the various needs of the code relevant to
### creating bitwise representations of multiword/multitag units. This version
### uses 18 bits to represent each word or POS tag, taking advantage of the
### python long int type (which is variable in size, and a much more efficient
### representation than, for instance, a tuple or list of strings or ints).

wild_card = 262143

def get_multi_id(ids):
    if not ids:
        return 0
    final = ids[-1]
    for i in range(len(ids) -2,-1,-1):
        final = final << 18 | ids[i]
    return final


def get_multi_id_mixed(new_id, old_id):
    final = old_id << 18 | new_id
    return final

def get_multi_id_range(sentence,start,end):
    if sentence[end-1] == -2:
        return 0
    final = sentence[end -1]
    for i in range(end -2, start -1,-1):
        if sentence[i] == -2:
            return 0
        final = final << 18 | sentence[i]
    return final

def get_multi_id_range_skip(sentence,start,midend,midstart,end):
    if sentence[end-1] == -2:
        return 0
    final = 0
    for i in range(end -1, midstart -1,-1):
        if sentence[i] == -2:
            return 0
        final = final << 18 | sentence[i]
        
    for i in range(midend -1, start -1,-1):
        if sentence[i] == -2:
            return 0
        final = final << 18 | sentence[i]
    final = final << 18 | midend - start - 1
    return final

def get_multi_id_range_wild(sentence,start,end,wild):
    if sentence[end-1] == -2:
        return 0
    final = 0
    for i in range(end -1, start -1,-1):
        if sentence[i] == -2:
            return 0
        if i == wild:
            final = final << 18 | wild_card
        else:
            final = final << 18 | sentence[i]
    return final

def get_multi_id_range_wild_skip(sentence,start,midend,midstart,end,wild):
    final = 0
    for i in range(end -1, midstart -1,-1):
        if sentence[i] == -2:
            return 0
        if i == wild:
            final = final << 18 | wild_card
        else:
            final = final << 18 | sentence[i]  

    for i in range(midend -1, start -1,-1):
        if sentence[i] == -2:
            return 0
        if i == wild:
            final = final << 18 | wild_card
        else:
            final = final << 18 | sentence[i]

    final = final << 18 | midend - start - 1
    return final

def get_multi_id_range_both_one_word(POSes,sentence,start,end,word_loc):
    if sentence[word_loc] == -2:
        return 0
    final = 0
    for i in range(end -1, start -1,-1):
        if POSes[i] == -2:
            return 0
        if i == word_loc:
            final = final << 18 | sentence[i]
        final = final << 18 | POSes[i]
    return final

def get_multi_id_range_both_one_word_skip(POSes,sentence,start,midend,midstart,end,word_loc):

    final = 0
    for i in range(end -1, midstart -1,-1):
        if POSes[i] == -2:
            return 0
        if i == word_loc:
            final = final << 18 | sentence[i]
        final = final << 18 | POSes[i]  

    for i in range(midend -1, start -1,-1):
        if POSes[i] == -2:
            return 0
        if i == word_loc:
            final = final << 18 | sentence[i]
        final = final << 18 | POSes[i]

    final = final << 18 | midend - start - 1
    return final


def get_multi_id_range_one_word(POSes,sentence,start,end,word_loc):
    if sentence[word_loc] == -2:
        return 0
    final = 0
    for i in range(end -1, start -1,-1):
        if POSes[i] == -2:
            return 0
        if i == word_loc:
            final = final << 18 | sentence[i]
        else:
            final = final << 18 | POSes[i]
    return final

def get_multi_id_range_one_word_skip(POSes,sentence,start,midend,midstart,end,word_loc):

    final = 0
    for i in range(end -1, midstart -1,-1):
        if POSes[i] == -2:
            return 0
        if i == word_loc:
            final = final << 18 | sentence[i]
        else:
            final = final << 18 | POSes[i]  

    for i in range(midend -1, start -1,-1):
        if POSes[i] == -2:
            return 0
        if i == word_loc:
            final = final << 18 | sentence[i]
        else:
            final = final << 18 | POSes[i]

    final = final << 18 | midend - start - 1

    return final



def get_multi_id_range_both(sentence,POSes,start,end):
    if sentence[end-1] == -2:
        return 0
    final = 0
    for i in range(end -1, start -1,-1):
        if sentence[i] == -2:
            return 0
        final = final << 18 | sentence[i]
        final = final << 18 | POSes[i]

    return final


def get_multi_id_range_both_wild(sentence,POSes,start,end,wild):
    if sentence[end-1] == -2:
        return 0
    final = 0
    for i in range(end -1, start -1,-1):
        if sentence[i] == -2:
            return 0
        if i == wild:
            final = final << 18 | wild_card
        else:
            final = final << 18 | sentence[i]
            final = final << 18 | POSes[i]

    return final

def get_multi_id_range_both_skip(sentence,POSes,start,midend,midstart,end):
    if sentence[end-1] == -2:
        return 0
    final = 0
    for i in range(end -1, midstart -1,-1):
        if sentence[i] == -2:
            return 0
        final = final << 18 | sentence[i]
        final = final << 18 | POSes[i]
 

    for i in range(midend -1, start -1,-1):
        if sentence[i] == -2:
            return 0
        final = final << 18 | sentence[i]
        final = final << 18 | POSes[i]
    
    final = final << 18 | midend - start - 1

    return final


def get_multi_id_range_both_wild_skip(sentence,POSes,start,midend,midstart,end,wild):
    if sentence[end-1] == -2:
        return 0
    final = 0
    for i in range(end -1, midstart -1,-1):
        if sentence[i] == -2:
            return 0
        if i == wild:
            final = final << 18 | wild_card
        else:
            final = final << 18 | sentence[i]
            final = final << 18 | POSes[i]   

    for i in range(midend -1, start -1,-1):
        if sentence[i] == -2:
            return 0
        if i == wild:
            final = final << 18 | wild_card
        else:
            final = final << 18 | sentence[i]
            final = final << 18 | POSes[i]

    final = final << 18 | midend - start - 1

    return final



def decode_id(multi_id):
    ids = []
    while multi_id != 0:
        ids.append(int(multi_id & 262143))
        multi_id = multi_id >> 18
    return ids

def is_multi(multi_id):
    return multi_id > 262143


