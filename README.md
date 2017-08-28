#  Building Lexicons of Formulaic Sequences 

This repository contains code, lexicons, test sets, and annotation guidelines associated with the following paper

Julian Brooke, Jan Snajder, and Timothy Baldwin. In press. Unsupervised Acquisition of Comprehensive Multiword Lexicons using Competition in an n-gram Lattice. *Transactions of the ACL*.

## Code

- multi_helper.py: internal library for representation of multiword phrases using a single Python int
- lang_specific_helper.py: internal library with language specific functions, including pos matching for gaps
- corpus_reader.py: internal library for reading in corpora
- get_ngram_statistics.py: extracts initial n-gram statistics and applies n-gram frequency threshold
- get_best_POS.py: identifies the single best POS for each n-gram, which is used for calculating LPR statistics
- get_LPR_statistics.py: derives LPR statistics for n-grams
- build_lattice.py: creates lattice representation
- optimize_FS_lattice.py: optimize lattice to identify formulaic sequences
- Lattice_FS.py: main script which runs the all the above scripts end-to-end to create an FS lexicon. Run without options
  to see list of options with explanations. See comments in code for additional information.
- evaluate_FS_lexicon.py: calculates precision/recall/f-score for a lexicon by comparison to a test set        

## Lexicons

Note: all these lexicons consist entirely of lemmatized forms and should be matched to inflected forms to improve human readability if needed.

- ICWSM-FS.txt: Lexicon of English FS built using the 2009 ICWSM dataset
- BNC-FS.txt : Lexicon of English FS built using the British National Corpus
- Croatian-FS.txt: Lexicon of Croatian FS built using fhrWaC
- Japanese-FS.txt: Lexicon of Japanese FS built using a Japanese web corpus 

## Test sets

These test sets were used to evaluate the models in the paper. 0 indicates non-FS, 2 indicates an FS, 4 indicates an example which was excluded due to annotator disagreement. Like the lexicons, they are lemmatized.

- ICWSM-test.txt: Test set for the ICWSM 2009 corpus (Burton et al. 2009)
- BNC-test.txt: Test set for the BNC corpus (Burrard 2000)
- Croatian-test.txt: Test set for the fhrWaC Croatian corpus (Snajder et al. 2013)
- Japanese-test.txt: Test set for the Japanese web corpus (Hasimoto and Kawahara 2008)

## Annotation Guidelines

Annotators were provided with a copy of relevant sections of Wray (2008), namely Chapter 1, pp. 9-16, which offers initial defintions, Chapter 8 pp. 93-99, which discusses how to identify FS in general terms, and Chapter 9 pp. 113-127, which provides explicit diagnostic criteria. As such, the guidelines below are intended to supplement an existing understanding of FS with practical tips for annotation. Note that the "recalls" annotation was folded into the "not an FS" annotation, it was mostly included to allow annotators to give a near-miss "partial credit".

- FS-annotation-English.pdf: The original guidelines
- FS-annotation-Croatian.pdf: Addendum to English guidelines in Croatian
- FS-annotation-Japanese.pdf: Addendum to English guidelines in Japanese
