from owlready2 import *
from pprint import pprint
from nltk.corpus import wordnet as wn

import itertools as iter
import jellyfish
import time
import re

def compute_string_similarity(ont_A, ont_B):
    timein = time.time()
    jaro_matches = []
    jaro_indices = []
    hamming_matches = []
    hamming_indices = []
    matches = []
    match_indices = []
    classes_A = list(ont_A.classes())
    classes_B = list(ont_B.classes())
    for i, concept1 in enumerate(classes_A):
        if i < 100:
            concept1 = str(concept1).split('.')[-1]
            for j, concept2 in enumerate(classes_B):
                concept2 = str(concept2).split('.')[-1]
                matches, match_indices = compute_exact_match(concept1, concept2, matches, match_indices, i, j)
                hamming_matches, hamming_indices = compute_hamming(hamming_matches, hamming_indices, concept1, concept2, i, j)
                jaro_matches, jaro_indices = compute_jaro(jaro_matches, jaro_indices, concept1, concept2, i, j)
    timeout = time.time()
    pprint("Run time: " + str(timeout - timein) + " seconds")
    return match_indices, hamming_indices, jaro_indices


def compute_synonym_similarity(syns_A, syns_B):
    timein = time.time()
    hamming_indices = []
    jaro_indices = []
    match_indices = []
    for i, concept1 in enumerate(syns_A):
        if i < 100:
            for j, concept2 in enumerate(syns_B):
               match_indices = compute_exact_match_syns(match_indices, concept1, concept2, i, j)
               hamming_indices = compute_hamming_syns(hamming_indices, concept1, concept2, i, j)
               jaro_indices = compute_jaro_syns(jaro_indices, concept1, concept2, i, j)
    timeout = time.time()
    pprint("Run time: " + str(timeout - timein) + " seconds")
    return match_indices, hamming_indices, jaro_indices


def compute_exact_match(concept1, concept2, matches, match_indices, i, j):
    if (concept2 == concept1):
        matches.append((concept1, concept2))
        match_indices.append((i,j))
    return matches, match_indices


def compute_exact_match_syns(match_indices, concept1, concept2, i, j):
    common = list(set(concept1).intersection(set(concept2)))
    if common:
        match_indices.append((i,j))
    return match_indices


def compute_jaro(matches, match_indices, concept1, concept2, i, j, threshold=1):
    jaro_dist = jellyfish.jaro_distance(concept1, concept2)
    if jaro_dist > threshold:
        matches.append((concept1, concept2))
        match_indices.append((i,j))
    return matches, match_indices


def compute_jaro_syns(match_indices, concept1, concept2, i, j, threshold=1):
    combinations = list(itertools.product(*[concept1, concept2]))
    scores = [jellyfish.jaro_distance(comb[0], comb[1]) for comb in combinations]
    if max(scores) > threshold:
        match_indices.append((i,j))
    return match_indices



def compute_hamming(matches, match_indices, concept1, concept2, i, j, threshold=1):
    hamming_dist = jellyfish.hamming_distance(concept1, concept2)
    if hamming_dist > threshold:
        matches.append((concept1, concept2))
        match_indices.append((i,j))
    return matches, match_indices


def compute_hamming_syns(match_indices, concept1, concept2, i, j, threshold=1):
    combinations = list(itertools.product(*[concept1, concept2]))
    scores = [jellyfish.hamming_distance(comb[0], comb[1]) for comb in combinations]
    if max(scores) > threshold:
        match_indices.append((i,j))
    return match_indices


def synonyms(ont_A, ont_B):
    classes_A = list(ont_A.classes())
    classes_B = list(ont_B.classes())
    syns_A = []
    syns_B = []
    for cls in classes_A:
        cls = re.sub("([a-z])([A-Z])","\g<1>_\g<2>", str(cls).split('.')[-1])
        lemma_list = [lemma for ss in wn.synsets(cls) for lemma in ss.lemma_names()]
        if lemma_list:
            syns_A.append(list(set(lemma_list)))
        else:
            syns_A.append([cls.lower()])
    for cls in classes_B:
        cls = re.sub("([a-z])([A-Z])","\g<1>_\g<2>", str(cls).split('.')[-1])
        lemma_list = [lemma for ss in wn.synsets(cls) for lemma in ss.lemma_names()]
        if lemma_list:
            syns_B.append(list(set(lemma_list)))
        else:
            syns_B.append([cls])
    return syns_A, syns_B


def init():
    onto_path.append(r'D:\Users\Jeroen\Documents\GitHub\KROTW\milestone2')
    ont_A = get_ontology("file://animalsA.owl").load()
    ont_B = get_ontology("file://animalsB.owl").load()
    return ont_A, ont_B


# Exact match, Jaro, Hamming
# + Synonyms
def main():
    ont_A, ont_B = init()
    match_indices, hamming_indices, jaro_indices = compute_string_similarity(ont_A, ont_B)

    syns_A, syns_B = synonyms(ont_A, ont_B)
    syn_match_indices, syn_hamming_indices, syn_jaro_indices = compute_synonym_similarity(syns_A, syns_B)

    # classes_A = list(ont_A.classes())
    # classes_B = list(ont_B.classes())
    # for i in syn_match_indices:
    #     print(classes_A[i[0]])
    #     print(classes_B[i[1]])
    #     print(" ")


if __name__ == '__main__':
    main()
