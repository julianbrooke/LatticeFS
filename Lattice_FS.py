# This program implements the formulaic sequence identification described in
#
# Julian Brooke, Jan Snajder, and Timothy Baldwin. Unsupervised Acquisition of
# Comprehensive Multiword Lexicons using Competition in an n-gram Lattice
# In Transactions of the ACL.
#
# Run the program without arguments to see a list of options
#
# By default, this program expects a tokenized and tagged corpus with each
# line consisting of a token and a (POS) tag, separated by a tab
# and the SENT part of speech tag indicating the end of a sentence
# For best results, the tokens should be lemmatized and lower_cased
# and the POS tag should have any inflectional information stripped off
# (i.e., NNS -> NN). For a differently formatted corpora (or to do
# lemmatization, etc. on the fly) modify read_sentence_from_corpus
# in corpus_reader.py, or define your own
#
# This version of the program has support for standard tagsets in English,
# French, Croatian, and Japanese. For other languages, modify pos_helper.py
# 
# The number of workers (parallel processes) is fixed on the command line,
# default 1, but for large corpora more is recommended. This only affects
# the collection of n-gram and LPR statistics
#
# For historical reasons (and ensure that memory is freed at the end of each step),
# this script executes each of the major steps in an entirely separate python
# process. If your python 2.7 interpreter is not accessible as "python",
# change py_exe below.
#
# Large temporary files are created at each step of the process which
# are deleted at the end. If the program crashes due to lack of memory,
# these temporary files can be used to resume the process
# Note that the once per x tokens threshold should be chosen so that the minimum
# frequency is greater than 1 (and perferably much greater than 1)
# The default is what was used in the paper (at least once per 10 million tokens)
##########################################################################


from optparse import OptionParser
from subprocess import call
import cPickle
import sys
import os


py_exe = "python"


            

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-c","--corpus",dest="corpus",help="the corpus to be segmented, should be tokenized with one sentence per line")
    parser.add_option("-w","--workers",default=1,dest="workers",type="int", help="the number of worker processes used, improves speed for extraction of statistics but increases memory usage by a factor of w")
    parser.add_option("-n",dest="n",default=8,type="int",help="largest n considered for n-grams, default 8")
    parser.add_option("-f","--frequency",dest="frequency",type="int",default=10000000, help="lowest allowed frequency for output vocab, once per FREQUENCY, default 10000000")
    parser.add_option("-q","--quiet",default=False,dest="silent",action="store_true",help="don't show progress")
    parser.add_option("-s","--sentences",type="int",dest="sentences",default=-1, help="Limit the number of sentences of the corpus processed, useful for testing")
    parser.add_option("-o","--output",default="vocab.txt", dest="output",help="the output multiword vocabulary (with corpus counts), default vocab.txt")
    parser.add_option("-l","--language",dest="lang",default="en",help="the language, for aspects relevant to part of speech (in particular, the syntactic definition of a gap) and pronouns. By default, en, fr, hr, and ja are supported options")
    parser.add_option("-C","--Cparameter", dest="C",default=4,type="int",help="Larger C means a more restricted vocabulary. Should not be less than 2")
    options,arguments = parser.parse_args()
    fout = open("%s_options.dat" % options.output,"wb")
    cPickle.dump(options,fout,-1)
    fout.close()
    if not options.corpus:
        parser.print_help()
    else:
        if not options.silent:
            print "getting initial n-gram statistics"
        retcode = call([py_exe,"get_ngram_statistics.py", options.output])
        if retcode != 0:
            print "ngram statistics gathering failed"
            sys.exit()
        if not options.silent:
            print "finding best POS for ngrams"
        retcode = call([py_exe,"get_best_POS.py", options.output])
        if retcode != 0:
            print "best POS identification failed"
            sys.exit()            
        if not options.silent:
            print "getting LPR statistics"
            print "(this could take a while)"
        retcode = call([py_exe,"get_LPR_statistics.py", options.output])
        if retcode != 0:
            print "LPR statistics gathering failed"
            sys.exit()
        if not options.silent:
            print "building lattice"
        retcode = call([py_exe,"build_lattice.py", options.output])
        if retcode != 0:
            print "Lattice creation failed"
            sys.exit()

        if not options.silent:
            print "finding optimal FS vocabulary"
        retcode = call([py_exe,"optimize_FS_lattice.py", options.output])
        if retcode != 0:
            print "Lattice optimization failed"
            sys.exit()


        try:
            os.remove("%s_options.dat" % options.output)
        except:
            pass

        try:
            os.remove("%s_ngrams.dat" % options.output)
        except:
            pass
        try:
            os.remove("%s_best_POS.dat" % options.output)
        except:
            pass
        try:
            os.remove("%s_LPR_stats.dat" % options.output)
        except:
            pass
        try:
            os.remove("%s_lattice.dat" % options.output)
        except:
            pass

    
        
        
