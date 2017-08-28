import sys
import codecs


if len(sys.argv) < 3 or len(sys.argv) > 3:
    print "usage: python evaluate_FS_lexicon.py <lexicon> <test_set>"
    sys.exit()


def harmonic_mean(first,second):
    return 2*(first*second)/(first+second)


FS_list = set()

f = codecs.open(sys.argv[1],encoding="utf-8")

for line in f:
    entry = line.strip().split("\t")[0]
    FS_list.add(entry)


tp = 0
tn = 0
fp = 0
fn = 0

f = codecs.open(sys.argv[2],encoding="utf-8")

for line in f:
    if line[0] != "\t":
        lemma_form = line.strip().split("\t")[2]
        if line[0] == "4":
            pass
        elif line[0] == "2":
            if lemma_form in FS_list:
                tp += 1
            else:
                fn += 1
        else:
            if lemma_form in FS_list:
                fp += 1
            else:
                tn += 1

print tp
print fp
print fn
print tn

try:
    precision = tp/float(tp + fp)
except:
    precision = 0
try:
    recall = tp/float(tp + fn)
except:
    recall = 0

print "precision"
print precision
print "recall"
print recall

try:
    fscore= harmonic_mean(precision,recall)
except:
    fscore = 0           

print "f-score"
print fscore
    
