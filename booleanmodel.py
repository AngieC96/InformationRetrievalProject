# -*- coding: utf-8 -*-
"""BooleanModel.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1FKIwIlsGUG0HKftv6VVFOs2JzYjTWecF

# A Boolean Retrieval System
"""

from functools import total_ordering, reduce  # not essential but reduces the code we have to write
import csv     # for csv files
import re      # for regular expressions
import pickle  # to save the index
import time
import os.path
import copy

"""## Postings

A `Posting` object is simply the docID of a document. It has a method `get_from_corpus` that given the corpus retrieves the document corresponding to that docID. Then it has some comparison methods to check if two docID are equal, one greater than the other, etc.
"""

@total_ordering   # takes a class where we have defined at least the methods `eq` and `gt`/`lt` and defines in a consistent way all the other methods (otherwise we should implement them all by hand)
class Posting:
    
    def __init__(self, docID):
        """ Class constructor.
        """
        self._docID = docID
        
    def get_from_corpus(self, corpus):  # return from the corpus the doc corresponding to that docID. In the list you only save the docID, not the all document
        """ Returns the document corresponding to that docID from the corpus.
        """
        return corpus[self._docID]
    
    def __eq__(self, other: 'Posting'):  # euqality comparator
        """ Performs the comparison between this posting and another one.
        Since the ordering of the postings is only given by their docID,
        they are equal when their docIDs are equal.
        """
        return self._docID == other._docID
    
    def __gt__(self, other: 'Posting'):  # greather than comparator
        """ As in the case of __eq__, the ordering of postings is given
        by the ordering of their docIDs.
        """
        return self._docID > other._docID
    
    def __repr__(self):       # for debagging purposes to print the class
        """ String representation of the class.
        """
        return str(self._docID)

"""## Posting Lists

A `PostingList` object is a list of `Posting`s. You can construct an empty `PostingList` with `__init__`, or construct and initialize a `PostingList` directly with one docID with `from_docID`, or you can create a `PostingList` object with an already existing list using `from_posting_list`. Then you can merge two posting list with `merge` (the one in input will be added at the end of the one on which the mehod `merge` is called, without any checking on the total ordering of the list), you can intersect them with `intersection` or you can unify them with `union`. With `get_from_corpus` we can retrieve the documents corresponding to the docID stored in this `PostingList`.
"""

class PostingList:

    _postings: list
    
    def __init__(self):
        """ Class constructor.
        """
        self._postings = []    # it has as an attribute a list of posting
        
    @classmethod     # to define another constructor. It will return another PostingList like a constructor
    def from_docID(cls, docID):
        """ A posting list can be constructed starting from a single docID.
        """
        plist = cls()
        plist._postings = [(Posting(docID))]
        return plist
    
    @classmethod
    def from_posting_list(cls, postingList):
        """ A posting list can also be constructed by using another posting list.
        """
        plist = cls()
        plist._postings = postingList   # we use it as the postins of this PostingList
        return plist
    
    def merge(self, other: 'PostingList'):  # we have to merge postinglists
        """ Merges the other posting list to this one in a desctructive
        way, i.e., modifying the current posting list. This method assumes
        that all the docIDs of the second list are higher than the ones
        in this list. It assumes the two posting lists to be ordered
        and non-empty. Under those assumptions duplicate docIDs are
        discarded.
        """
        i = 0
        last = self._postings[-1]   # the self element of the current postinglist
        while (i < len(other._postings) and last == other._postings[i]):  # we can have the same docID multiple times and when e merge them we don't want them multiple times
            i += 1
        self._postings += other._postings[i:]
        
    def intersection(self, other: 'PostingList'):
        """ Returns a new posting list resulting from the intersection
        of this one and the one passed as argument.
        """
        intersection = []
        i = 0
        j = 0
        while (i < len(self._postings) and j < len(other._postings)):  # until we reach the end of a posting list
            if (self._postings[i] == other._postings[j]):
                intersection.append(self._postings[i])
                i += 1
                j += 1
            elif (self._postings[i] < other._postings[j]):
                i += 1
            else:
                j += 1
        return PostingList.from_posting_list(intersection)
    
    def union(self, other: 'PostingList'):
        """ Returns a new posting list resulting from the union of this
        one and the one passed as argument.
        """
        union = []
        i = 0
        j = 0
        while (i < len(self._postings) and j < len(other._postings)):
            if (self._postings[i] == other._postings[j]):
                union.append(self._postings[i])
                i += 1
                j += 1
            elif (self._postings[i] < other._postings[j]):
                union.append(self._postings[i])   # because i is the smallest one
                i += 1
            else:
                union.append(other._postings[j]) 
                j += 1
        for k in range(i, len(self._postings)):  # we have to append the remaining elements of the non emptied list
            union.append(self._postings[k])
        for k in range(j, len(other._postings)):
            union.append(other._postings[k])
        return PostingList.from_posting_list(union)

    def difference(self, other: 'PostingList'):
      difference = []

      return PostingList.from_posting_list(difference)
    
    def get_from_corpus(self, corpus):   # used when we have a posting list that is the result of a query, but I don't want the docID, I want the docs!
        return list(map(lambda x: x.get_from_corpus(corpus), self._postings))  # I return a list of documents
    
    def __getitem__(self, key):
        return self._postings[key]
    
    def __len__(self):
        return len(self._postings)
    
    def __repr__(self):
        return ", ".join(map(str, self._postings))

"""## Terms

A `Term` object contains both the word itself and the `PostingList` with all the docIDs of the documents in which the word is contained. The `merge` function merges the `PostingList`s of two equal `Term`s. Then we have some comparison methods to check if two `Term`s are equal or one is greater then the other, etc.
"""

class ImpossibleMergeError(Exception):
    pass

@total_ordering  # to have all the ordering methods defined automatically
class Term:

    posting_list: PostingList
    
    def __init__(self, term, docID):   # we create a term with a DocID, we sort them and we merge the equal terms
        self.term = term
        self.posting_list = PostingList.from_docID(docID)
        
    def merge(self, other: 'Term'):   # when we merge two terms
        """ Merges (destructively) this term and the corresponding posting list
        with another equal term and its corrsponding posting list.
        """
        if (self.term == other.term): # cannot merge posting lists with different terms!
            self.posting_list.merge(other.posting_list)  # merge the current posting list with the one of the other
        else: 
            raise ImpossibleMergeError # (some kind of error) error of impossible merge
            
    def __eq__(self, other: 'Term'):
        return self.term == other.term
    
    def __gt__(self, other: 'Term'):
        return self.term > other.term
    
    def __repr__(self):
        return self.term + ": " + repr(self.posting_list)

"""## Inverted Index"""

# We have to do some step of tokenization and normalization

def normalize(text):
    """ A simple funzion to normalize a text.
    It removes everything that is not a word, a space or an hyphen
    and downcases all the text.
    """
    no_punctuation = re.sub(r'[^\w^\s^-]', '', text)  # the text that matches a certain pattern will be substittuted with the second expression. ^\w → not something alphanumeric, ^\s → not some space, ^- → not a dash, replace it with '', the empty string
    downcase = no_punctuation.lower()  # put everything to lower case
    return downcase

def tokenize(movie: 'MovieDescription'):
    """ Returns a list, which is a posting list, from a movie
    description of all tokens present in the description.
    """
    text = normalize(movie.description)
    return list(text.split())

"""Function to print a progress bar, taken from [here](https://stackoverflow.com/questions/3160699/python-progress-bar)."""

import time, sys

def update_progress(progress):
    """ Displays or updates a console progress bar.
    Accepts a float between 0 and 1. Any int will be converted to a float.
    A value under 0 represents a 'halt'.
    A value at 1 or bigger represents 100%
    """
    barLength = 40 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done!\r\n"
    block = int(round(barLength*progress))
    text = "\r[{0}] {1}% {2}".format( "#"*block + "."*(barLength-block), round(progress*100, 2), status)
    sys.stdout.write(text)
    sys.stdout.flush()

"""In an inverted index we store, for each term, the list of documents containing it.

So an `InvertedIndex` object contains a dictionary `_dictionary` with as keys the words themselves and as values the `Term` associated to each word, which, we recall, contains the `PostingList` associated to the word.\
It also stores a list with all the Postings, `complete_plist`, used to answer the NOT queries.


#### Phrase queries

Answering a phrase query with positional indexing
We perform something like the intersection only that now we have to go inside and check the
position.
We need to check if the two terms appear in adjacent positions → We search if they are contained
in the same document and if they are one after the other.

#### Data structure

Python dictionaries aren’t always what you need: the most important case is where you want to store a very large mapping. When a Python dictionary is accessed, the whole dictionary has to be unpickled and brought into memory.

BTrees are a balanced tree data structure that behave like a binary tree but distribute keys throughout a number of tree nodes and each node has between $a$ and $b$ children. The nodes are stored in sorted order. Nodes are then only unpickled and brought into memory as they’re accessed, so the entire tree doesn’t have to occupy memory (unless you really are touching every single key).
"""

from typing import List

class InvertedIndex:

    _dictionary: List
    complete_plist: PostingList
    
    def __init__(self):
        self._dictionary = []
        self.complete_plist = PostingList() # PostingList of all the documents
        
    @classmethod  # instead of having this method associated to a specific instance/object of the class InvertedIndex we write InvertedIndex.from_corpus(). Because you can have only one __init__ method, so you use @classmethod to have multiple constructors. It's like a static method in Java
    def from_corpus(cls, corpus: list):
        # Here we "cheat" by using python dictionaries
        intermediate_dict = {}   # we cheat a little bit and use a Python dictionary → we should create a big list, sort it and merge everything
        print("Processing the corpus to create the index...")
        for docID, document in enumerate(corpus): # NB: corpus: collection (list) of objects of type MovieDescription
            if docID == 0:
                plist = PostingList.from_docID(docID)
            else:
                plist.merge(PostingList.from_docID(docID)) # I update the PostingList of all the docs
            tokens = tokenize(document) # document is a MovieDescription object
            for token in tokens:
                term = Term(token, docID)
                try:
                    intermediate_dict[token].merge(term)  # I merge the two posting lists → Term.merge() which calls PostingList.merge()
                except KeyError:
                    intermediate_dict[token] = term # for when the term is not present in the dict
            # To observe the progressing of our indexing
            update_progress(docID/len(corpus))
        
        idx = cls()  # we call the constructor of the class = InvertedIndex
        idx._dictionary = sorted(intermediate_dict.values())  # list of all the sorted terms
        idx.complete_plist = plist
        return idx
    
    def __getitem__(self, key): # indexing the inverted index using as keys the terms
        for term in self._dictionary:  # we could do a binary search
            if term.term == key:
                return term.posting_list  # quering the index with a  word returns the PostingList associated to that word
        raise KeyError(f"The term '{key}' is not present in the index.") # the key is not present!
        
    def __repr__(self):
        return "A dictionary with " + str(len(self._dictionary)) + " terms"

"""## Reading the Corpus

A `MovieDescription` object has a title and a description.  We have some comparison methods to check if two `MovieDescription`s are equal or one is greater then the other, etc. The function `hash` computes the hash of a `MovieDescription` using the hash of its title and its description.

We have implemented the comparison methods to make `MovieDescription` a sortable object (so we can iterate on it), and the `hash` method to make it hashable (so we can put it in a `set`).
"""

@total_ordering
class MovieDescription:  # container for all the info we have about the movie
    
    def __init__(self, title: str, description: str):
        self.title = title
        self.description = description
        
    def __eq__(self, other: 'MovieDescription'):
        return self.title == other.title
    
    def __gt__(self, other: 'MovieDescription'):
        return self.title > other.title

    def __hash__(self):
      return hash((self.title, self.description))
        
    def __repr__(self):
        return self.title  # + "\n" + self.description + "\n"

def read_movie_descriptions():
    filename = 'data/plot_summaries.txt'   # not very portable but done for the sake of simplicity
    movie_names_file = 'data/movie.metadata.tsv'
    with open(movie_names_file, 'r') as csv_file:
        movie_names = csv.reader(csv_file, delimiter = '\t')   # we define the csv reader
        names_table = {}   # Python dictionary with all the names of the films: key = movieID, value = movie title
        for name in movie_names:
            names_table[name[0]] = name[2] # the first element is the ID, the third elemnt is the title
    # Now we have all the associations between ID and title, we miss the move description

    with open(filename, 'r') as csv_file:
        descriptions = csv.reader(csv_file, delimiter = '\t')
        corpus = []   # collection (list) of objects of type MovieDescription
        for desc in descriptions:
            try:      # at least in this dataset there are some errors so some descriptions have not a matching ID
                movie = MovieDescription(names_table[desc[0]], desc[1]) # the first element is the ID, the second the description
                corpus.append(movie)
            except KeyError:  # in case we don't find the title associated to that ID
                # We ignore the descriptions for which we cannot find a title
                pass
        return corpus

"""## Edit distance

By computing the edit distance we can find the set of words that are the closest to a misspelled word. However, computing the edit distance on the entire dictionary can be too expensive. We can use some heuristics to limit the number of words, like looking only at words with the same initial letter (hopefully this has not been misspelled). The latter is what is implemented in this model.
"""

def edit_distance(u, v, print = False):
    """ Computes the edit (or Levenshtein) distance between two words u and v.
    """
    nrows = len(u) + 1
    ncols = len(v) + 1
    M = [[0] * ncols for i in range(0, nrows)]  # matrix all filled with zeros
    for i in range(0, nrows):  # we fill the first row, the trivial one
        M[i][0] = i
    for j in range(0, ncols):  # we fill the first col, the trivial one
        M[0][j] = j
    for i in range(1, nrows):
        for j in range(1, ncols):
            candidates = [M[i-1][j] + 1, M[i][j-1] + 1]
            if (u[i-1] == v[j-1]):
                candidates.append(M[i-1][j-1])
            else:
                candidates.append(M[i-1][j-1] + 1)
            M[i][j] = min(candidates)
            # To print the distance matrix
            if print:
                print(M[i][j], end="\t")
        if print:
          print()
    return M[-1][-1]  # Bottom right element of M (-1 means the last element)

def find_nearest(word, dictionary, keep_first=False):
    if keep_first:
        # If keep_first is true then we only search across the words in the dictionary starting with the same letter
        dictionary = [w for w in dictionary if w[0] == word[0]]
    # Remove comment to see the reduction in the size of the dictionary when keeping fixed the first letter
    #print(len(dictionary))
    # Apply f(x) = edit_distance(word, x) to all words in the dictionary
    distances = map(lambda x: edit_distance(word, x), dictionary)
    # Produce all the pairs (distance, term) usng zip and find one with the minimal distance.
    return min(zip(distances, dictionary))[1]

"""## IR System

An `IRsystem` object contains the entire corpus and the `InvertedIndex`.
"""

class IRsystem:

    _corpus: list
    _index: InvertedIndex
    
    def __init__(self, corpus: list, index: 'InvertedIndex'):
        self._corpus = corpus
        self._index = index
        
    @classmethod
    def from_corpus(cls, corpus: list): # generate the entire inverted index calling the constructor
        index = InvertedIndex.from_corpus(corpus)
        return cls(corpus, index)  # retrun the constructor when we have yet the index

    def get_from_corpus(self, plist):
        return plist.get_from_corpus(self._corpus)

    def spelling_correction(self, norm_words: List[str]):
        postings = []
        for w in norm_words:
            try:
                res = self._index[w]
            except KeyError:
                dictionary = [t.term for t in self._index._dictionary]
                sub = find_nearest(w, dictionary, keep_first=True)
                print("{} not found. Did you mean {}?".format(w, sub))
                res = self._index[sub]
            postings.append(res)
        print()
        return postings

    def answer_and_query(self, words: List[str], spellingCorrection = False):
        """ AND-query, if `spellingCorrection` is `True` with spelling correction
        """
        norm_words = map(normalize, words)  # Normalize all the words. IMPORTANT!!! If the user uses upper-case we will not have ANY match! We have to perform the same normalization of the docs in the corpus on the query!
        if not spellingCorrection:
            postings = map(lambda w: self._index[w], norm_words) # get the posting list for each word → list of posting lists
        else:
            postings = self.spelling_correction(norm_words)
        plist = reduce(lambda x, y: x.intersection(y), postings)  # apply the function to the two items of the list, then apply it to the result with the third, then the result with the fourt term and so on until the end of the list
        return self.get_from_corpus(plist)

    def answer_or_query(self, words: List[str], spellingCorrection = False):
        """ OR-query, if `spellingCorrection` is `True` with spelling correction
        """
        norm_words = map(normalize, words)
        if not spellingCorrection:
            postings = map(lambda w: self._index[w], norm_words)
        else:
            postings = self.spelling_correction(norm_words)
        plist = reduce(lambda x, y: x.union(y), postings)
        return self.get_from_corpus(plist)

    def answer_not_query(self, words: List[str], spellingCorrection = False):
        """ NOT-query (if `words` is longer than 1, the words are connected using an AND and then the NOT is performed)
        """
        norm_words = map(normalize, words)
        if not spellingCorrection:
            postings = map(lambda w: self._index[w], norm_words)
        else:
            postings = self.spelling_correction(norm_words)
        words_plist = reduce(lambda x, y: x.union(y), postings)
        plist = copy.deepcopy(self._index.complete_plist)
        for i in words_plist:
            if i in plist:
                plist._postings.remove(i)
        return self.get_from_corpus(plist)

    def answer_query(self, op: str, words = None, word = None, postings = None, postings2 = None, NOT_switch = False):
        ''' Complex query.
        Arguments:
          NOT_switch -- Used to switch the order of the two posting lists `postings` and `postings2` in the NOT query, since this operator is not commutative.
        '''
        if words:
            postings = self._index[normalize(words[0])]
            postings2 = self._index[normalize(words[1])]
        elif word:
            postings2 = self._index[normalize(word)]

        if op == 'AND':
            plist = postings.intersection(postings2)
            return plist
        elif op == 'OR':
            plist = postings.union(postings2)
            return plist
        elif op == 'NOT':
            if not NOT_switch:
                postings_copy = copy.deepcopy(postings)
                for i in postings2:
                    if i in postings_copy:
                        postings_copy._postings.remove(i)
                return postings_copy
            else:
                postings2_copy = copy.deepcopy(postings2)
                for i in postings:
                    if i in postings2_copy:
                        postings2_copy._postings.remove(i)
                return postings2_copy

"""### Queries"""

def and_query(ir: IRsystem, text: str, noprint=True):
    words = text.split()
    answer = ir.answer_and_query(words)  # list of documents
    if not noprint:
        for movie in answer:
            print(movie)
    return answer
        
def or_query(ir: IRsystem, text: str, noprint=True):
    words = text.split()
    answer = ir.answer_or_query(words)
    if not noprint:
        for movie in answer:
            print(movie)
    return answer

def not_query(ir: IRsystem, text: str, noprint=True):
    words = text.split()
    answer = ir.answer_not_query(words)
    if not noprint:
        for movie in answer:
            print(movie)
    return answer

def query(ir: IRsystem, text: str, noprint=True):
    """ This query can answer complex queries with 'AND', 'OR' and 'NOT' but without parentheses.
    E.g. text = "yoda AND darth OR Gandalf NOT love"
    """
    words = text.split()
    if len(words) == 1:
        print("You cannot use one single word! Use at least two words connected with a logical operator.")
        return None
    for i, w in enumerate(words):
        if w in ['AND', 'OR', 'NOT']:
            if i == 1:
                plist = ir.answer_query(op = w, words = [words[i-1], words[i+1]])
            else:
                plist = ir.answer_query(op = w, word = words[i+1], postings = plist)
    answer = ir.get_from_corpus(plist)
    if not noprint:
        for movie in answer:
            print(movie)
    return answer

def query_with_pars(ir: IRsystem, text: str, noprint=True):
    """ This query can answer to any type of query, also complex ones. Use 'AND', 'OR' and 'NOT'
    and parenthesis to specify how to combine the words in the query.
    E.g. text = "(yoda AND darth) OR Gandalf NOT love"
    """
    # add a space after '(' and before ')' so to split them into separate tokens
    text = re.sub(r"\(", r'( ', text)
    text = re.sub(r"\)", r' )', text)
    # split the text in words (it eliminates spaces at the beginning/end of words, so even if we add them with the first passage it's not important)
    words = text.split()

    if len(words) == 1 or (len(words) == 3 and ("(" in words or ")" in words)):
        print("You cannot use one single word! Use at least two words connected with a logical operator.")
        return None

    # words_mod = copy.deepcopy(words) # For now not necessary, I don't reuse the array 'words'
    words_mod = words                  # I write it like this so it is easy to change is 'words' will be needed
    # Wrap the text in two parentheses so to perform the following while one last time, avoiding to repeat code, and compute the whole query
    words_mod.insert(0, "(")
    words_mod.append(")")
    
    openp = []
    closep = []
    for i, w in enumerate(words_mod):
        if w == "(": openp.append(i)
        elif w == ")": closep.append(i)
    
    if len(openp) != len(closep):
        print("The number of open parentheses is different from the number of closed parentheses.")
        return None

    while closep:
        c = closep[0]
        o = None
        for i in openp:
            if i < c:
                o = i
        #plist = PostingList()  # wrong, since if there are extra parentheses around all the query I overwrite the last plist and I store in words_mod an empty plist
        # Process the query in these parenthesis, the remove o in openp and c in closep
        for i, w in enumerate(words_mod[o+1 : c]):
            if w in ['AND', 'OR', 'NOT']:
                if i == 1:
                    item1 = words_mod[(o+1) + i-1]
                    item2 = words_mod[(o+1) + i+1]
                    # Checks to call `ir.answer_query` in the right way
                    if type(item1) == str and type(item2) == str:
                        plist = ir.answer_query(op = w, words = [item1, item2])
                    elif type(item1) == PostingList and type(item2) == str:
                        plist = ir.answer_query(op = w, word = item2, postings = item1)
                    elif type(item1) == str and type(item2) == PostingList:
                        plist = ir.answer_query(op = w, word = item1, postings = item2, NOT_switch = True)
                    elif type(item1) == PostingList and type(item2) == PostingList:
                        plist = ir.answer_query(op = w, postings = item1, postings2 = item2)
                else:
                    item2 = words_mod[(o+1) + i+1]
                    if type(item2) == str:
                        plist = ir.answer_query(op = w, word = item2, postings = plist)
                    elif type(item2) == PostingList:
                        plist = ir.answer_query(op = w, postings = plist, postings2 = item2)
        words_mod[o] = plist
        del words_mod[o+1:c+1]
        openp = []
        closep = []
        for i, w in enumerate(words_mod):
            if w == "(": openp.append(i)
            elif w == ")": closep.append(i)
    
    answer = ir.get_from_corpus(plist)
    if not noprint:
        for movie in answer:
            print(movie)
    return answer

"""### Queries with spelling correction"""

def and_query_sc(ir: IRsystem, text: str, noprint=True):
    words = text.split()
    answer = ir.answer_and_query(words, spellingCorrection=True)
    if not noprint:
        for movie in answer:
            print(movie)
    return answer

def or_query_sc(ir: IRsystem, text: str, noprint=True):
    words = text.split()
    answer = ir.answer_or_query(words, spellingCorrection=True)
    if not noprint:
        for movie in answer:
            print(movie)
    return answer

"""## Test queries

### Initialization
"""

corpus = read_movie_descriptions()
len(corpus)

"""#### Saving / loading the index

We will save the index using `Pickle`. `Pickle` is used for serializing and de-serializing Python object structures, also called marshalling or flattening. Serialization refers to the process of converting an object in memory to a byte stream that can be stored on disk or sent over a network. Later on, this character stream can then be retrieved and de-serialized back to a Python object.
"""

updated = True

filename = "index.pickle"

# If the index is saved and it is updated I load it, otherwise I create it and save it
if os.path.isfile(filename) and updated:
    print ("Index file exists. Loading the index...")
    # load the index
    tic = time.time()
    infile = open(filename, 'rb')
    idx = pickle.load(infile)
    infile.close()
    toc = time.time()
    print("Index loaded.")
    print(f"Time: {round(toc-tic, 3)}s")
else:
    print ("Index file does not exist.")
    tic = time.time()
    idx = InvertedIndex.from_corpus(corpus)
    toc = time.time()
    print(f"\n\nTime: {round(toc-tic, 3)}s")
    # save the index
    outfile = open(filename, 'wb')
    pickle.dump(idx, outfile)
    outfile.close()

print(idx)

ir = IRsystem(corpus, idx)

try:
  ir.get_from_corpus(ir._index[normalize("thig")])
except KeyError:
    print(sys.exc_info()[1])

"""### AND queries"""

fg_and_query = and_query(ir, "frodo Gandalf", noprint=False)

yld_and_query = and_query(ir, "yoda Luke darth", noprint=False)

frodo_query = ir.get_from_corpus(ir._index[normalize("frodo")])
frodo_set = set(frodo_query)

gandalf_query = ir.get_from_corpus(ir._index[normalize("Gandalf")])
gandalf_set = set(gandalf_query)

fg_and_set = frodo_set.intersection(gandalf_set)

assert set(fg_and_query) == fg_and_set

yoda_query = ir.get_from_corpus(ir._index[normalize("yoda")])
yoda_set = set(yoda_query)

luke_query = ir.get_from_corpus(ir._index[normalize("Luke")])
luke_set = set(luke_query)

darth_query = ir.get_from_corpus(ir._index[normalize("darth")])
darth_set = set(darth_query)

yld_and_set = yoda_set.intersection(luke_set).intersection(darth_set)

assert set(yld_and_query) == yld_and_set

"""### AND queries with spelling correction"""

mispelled_and_query = and_query_sc(ir, "yioda lukke darhth", noprint=False)

assert yld_and_query == mispelled_and_query

"""### OR queries"""

fy_or_query = or_query(ir, "frodo yoda", noprint=False)

fy_or_set = set(frodo_query + yoda_query)

assert set(fy_or_query) == fy_or_set

fyg_or_query = or_query(ir, "frodo yoda gandalf", noprint=False)

fyg_or_set = set(frodo_query + yoda_query + gandalf_query)

assert set(fyg_or_query) == fyg_or_set

love_query = ir.get_from_corpus(ir._index[normalize("love")])
fyl_or_query = or_query(ir, "frodo yoda love")
fyl_or_set = set(frodo_query + yoda_query + love_query)

assert set(fyl_or_query) == fyl_or_set

"""### OR queries with spelling correction"""

mispelled_or_query = or_query_sc(ir, "frodoo yioda ganalf", noprint=False)

assert fyg_or_query == mispelled_or_query

"""### NOT queries"""

a_not_query = not_query(ir, "a", noprint=True)

corpus_set = set(corpus)
a_query = ir.get_from_corpus(ir._index[normalize("a")])
a_set = set(a_query)
a_not_set = corpus_set.difference(a_set)

assert set(a_not_query) == a_not_set

lm_not_query = not_query(ir, "love mother", noprint=True)

love_set = set(love_query)
mother_query = ir.get_from_corpus(ir._index[normalize("mother")])
mother_set = set(mother_query)
lm_set = love_set.union(mother_set)
lm_not_set = corpus_set.difference(lm_set)

assert set(lm_not_query) == lm_not_set

yg_not_query = not_query(ir, "yoda Gandalf", noprint=True)

yg_set = yoda_set.union(gandalf_set)
yg_not_set = corpus_set.difference(yg_set)

assert set(yg_not_query) == yg_not_set

"""### Compex queries"""

query(ir, "yoda", noprint=False)

yAdOg_query = query(ir, "yoda AND darth OR Gandalf", noprint=False)

yd_and_set = yoda_set.intersection(darth_set)
yAdOg_set = yd_and_set.union(gandalf_set)

assert set(yAdOg_query) == yAdOg_set

yAdOg_query2 = query_with_pars(ir, "yoda AND darth OR Gandalf", noprint=False)

assert set(yAdOg_query2) == yAdOg_set

yOdAg_query = query(ir, "yoda OR darth AND Gandalf", noprint=False)

yd_or_set = yoda_set.union(darth_set)
yOdAg_set = yd_or_set.intersection(gandalf_set)

assert set(yOdAg_query) == yOdAg_set

yOdOgAl_query = query(ir, "yoda OR darth OR Gandalf AND love", noprint=False)

ydg_and_set = yoda_set.union(darth_set).union(gandalf_set)
yOdOgAl_set = ydg_and_set.intersection(love_set)

assert set(yOdOgAl_query) == yOdOgAl_set

yAdOgNl_query = query(ir, "yoda AND darth OR Gandalf NOT love", noprint=False)

yAdOgNl_set = yAdOg_set.difference(love_set)

assert set(yAdOgNl_query) == yAdOgNl_set

yNdOg_query = query(ir, "yoda NOT darth OR Gandalf", noprint=False)

yNd_set = yoda_set.difference(darth_set)
yNdOg_set = yNd_set.union(gandalf_set)

assert set(yNdOg_query) == yNdOg_set

"""#### Using parentheses"""

query_with_pars(ir, "(yoda)", noprint=False)

pyAdpOgNl_query = query_with_pars(ir, "(yoda AND darth) OR Gandalf NOT love", noprint=False)

assert set(pyAdpOgNl_query) == yAdOgNl_set

yApdOgpNl_query = query_with_pars(ir, "yoda AND (darth OR Gandalf) NOT love", noprint=False)

dOg_set = darth_set.union(gandalf_set)
yApdOgpNl = yoda_set.intersection(dOg_set).difference(love_set)

assert set(yApdOgpNl_query) == yApdOgpNl

yOgApdOlp_complex_query = query_with_pars(ir, "(yoda OR Gandalf AND (darth OR love))", noprint=False)

dOl_set = darth_set.union(love_set)
yOgApdNlp_set = yoda_set.union(gandalf_set).intersection(dOl_set)

assert set(yOgApdOlp_complex_query) == yOgApdNlp_set

yOpgApdOlpNmpOphNap_complex_query = query_with_pars(ir, "yoda OR (Gandalf AND (darth OR love) NOT mother) OR (hello NOT a)", noprint=False)

gApdOlpNm_set = gandalf_set.intersection(dOl_set).difference(mother_set)
hello_set = set(ir.get_from_corpus(ir._index[normalize("hello")]))
hNa_set = hello_set.difference(a_set)
yOpgApdOlpNmpOphNap_set = yoda_set.union(gApdOlpNm_set).union(hNa_set)

assert set(yOpgApdOlpNmpOphNap_complex_query) == yOpgApdOlpNmpOphNap_set

test = "hello OR ((how AND (are OR you) OR I AND (am AND fine) OR I) AND am AND (sleepy OR hungry) AND cold)"
hOphApaOypOiApaAfpOiAaApsOhpAcp_query = query_with_pars(ir, test, noprint=False)

are_set = set(ir.get_from_corpus(ir._index[normalize("are")]))
you_set = set(ir.get_from_corpus(ir._index[normalize("you")]))
aOy_set = are_set.union(you_set)
am_set = set(ir.get_from_corpus(ir._index[normalize("am")]))
aAf_set = am_set.intersection(set(ir.get_from_corpus(ir._index[normalize("fine")])))
i_set = set(ir.get_from_corpus(ir._index[normalize("I")]))
how_set = set(ir.get_from_corpus(ir._index[normalize("how")]))
hApaOypOiApaAfpOi_set = how_set.intersection(aOy_set).union(i_set).intersection(aAf_set).union(i_set)
sOh_set = set(ir.get_from_corpus(ir._index[normalize("sleepy")])).union(set(ir.get_from_corpus(ir._index[normalize("hungry")])))
hApaOypOiApaAfpOiAaApsOhpAc_set = hApaOypOiApaAfpOi_set.intersection(am_set).intersection(sOh_set).intersection(set(and_query(ir, "cold")))
hOphApaOypOiApaAfpOiAaApsOhpAcp_set = hello_set.union(hApaOypOiApaAfpOiAaApsOhpAc_set)

assert set(hOphApaOypOiApaAfpOiAaApsOhpAcp_query) == hOphApaOypOiApaAfpOiAaApsOhpAcp_set