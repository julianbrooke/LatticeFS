#  Building Lexicons of Formulaic Sequences 

This repository contains code, lexicons, test sets, and annotation guidelines associated with the following paper

Julian Brooke, Jan Snajder, and Tim Baldwin. In press. Unsupervised Acquisition of Comprehensive Multiword Lexicons using Competition in an n-gram Lattice. *Transactions of the ACL*.

## Code

coming soon

## Lexicons

Note: all these lexicons consist entirely of lemmatized forms and should be matched to inflected forms to improve human readability if needed.

- ICWSM-FS.txt: Lexicon of English FS built using the 2009 ICWSM dataset
- BNC-FS.txt : Lexicon of English FS built using the British National Corpus
- Croatian-FS.txt: Lexicon of Croatian FS built using 
- Japanese-FS.txt: Lexicon of Japanese FS built using

## Test sets

These test sets were used to evaluate the models in the paper. 0 indicates non-FS, 2 indicates an FS, 4 indicates an example which was excluded due to annotator disagreement. They are also lemmatized.

- ICWSM-test.txt: Test set for the ICWSM (English)
- BNC-test.txt: Test set for the BNC (English)
- Croation-test.txt: Test set for the fhrWaC Croatian corpus
- Japanese-test.txt: Test set for the Japanese web corpus

## Annotation Guidelines

Annotators were provided with a copy of relevant sections of Wray (2008), namely Chapter 1, pp. 9-16, which offers initial defintions, Chapter 8 pp. 93-99, which discusses how to identify FS in general terms, and Chapter 9 pp. 113-127, which provides explicit diagnostic criteria. As such, the guidelines below are intended to supplement an existing understanding of FS with detailed guidelines. The "recalls" annotation was folded into the "not an FS" annotation, it was mostly included to allow annotators to give a near-miss partial credit.

- FS-annotation-English.pdf: The original guidelines
- FS-annotation-Croatian.pdf: Translation of the English guidelines into Croatian, with Croatian specific examples
- FS-annotation-Japanese.pdf: Translation of the English guidelines into Japanese, with Japanese specific examples
