from owlready2 import *
from pprint import pprint
from nltk.corpus import wordnet as wn
from smith_waterman import smith_waterman

import itertools
import jellyfish
import time
import re

LIMIT = 10

def dist_ranking(fn, concept, cls, inverted=True):
    scores = [(fn(concept, str(concept2).split('.')[-1]), concept2) for concept2 in cls]
    return sorted(scores, key=lambda x: x[0], reverse=inverted)


def dist_ranking_syns(fn, syn_A, cls, syns_B, inverted=True):
    if inverted:
        scores = [(max(retrieve_scores(fn, syn_A, syn_B)), cls[i]) for i, syn_B in enumerate(syns_B)]
    else:
        scores = [(min(retrieve_scores(fn, syn_A, syn_B)), cls[i]) for i, syn_B in enumerate(syns_B)]
    return sorted(scores, key=lambda x: x[0], reverse=inverted)


def ranking_similarity(classes_A, classes_B, syns_A, syns_B):
    pprint("Ranking concept similarity")
    timein = time.time()
    ranking_hamming = []
    ranking_jaro = []
    ranking_waterman = []
    ranking_hamming_syns = []
    ranking_jaro_syns = []
    ranking_waterman_syns = []
    for i, concept in enumerate(classes_A):
        if i < LIMIT:
            ranking_hamming.append((concept, dist_ranking(jellyfish.hamming_distance, str(concept).split('.')[-1], classes_B, inverted=False)))
            ranking_jaro.append((concept, dist_ranking(jellyfish.jaro_distance, str(concept).split('.')[-1], classes_B)))
            ranking_waterman.append((concept, dist_ranking(smith_waterman, str(concept).split('.')[-1], classes_B)))
            syns_concept = syns_A[i]
            ranking_hamming_syns.append((concept, dist_ranking_syns(jellyfish.hamming_distance, syns_concept, classes_B, syns_B, inverted=False)))
            ranking_jaro_syns.append((concept, dist_ranking_syns(jellyfish.jaro_distance, syns_concept, classes_B, syns_B)))
            ranking_waterman_syns.append((concept, dist_ranking_syns(smith_waterman, syns_concept, classes_B, syns_B)))
    for i, concept in enumerate(classes_B):
        if i < LIMIT:
            ranking_hamming.append((concept, dist_ranking(jellyfish.hamming_distance, str(concept).split('.')[-1], classes_A, inverted=False)))
            ranking_jaro.append((concept, dist_ranking(jellyfish.jaro_distance, str(concept).split('.')[-1], classes_A)))
            ranking_waterman.append((concept, dist_ranking(smith_waterman, str(concept).split('.')[-1], classes_A)))
            syns_concept = syns_B[i]
            ranking_hamming_syns.append((concept, dist_ranking_syns(jellyfish.hamming_distance, syns_concept, classes_A, syns_A, inverted=False)))
            ranking_jaro_syns.append((concept, dist_ranking_syns(jellyfish.jaro_distance, syns_concept, classes_A, syns_A)))
            ranking_waterman_syns.append((concept, dist_ranking_syns(smith_waterman, syns_concept, classes_A, syns_A)))
    timeout = time.time()
    pprint("Run time: " + str(timeout - timein) + " seconds")
    return ranking_hamming, ranking_jaro, ranking_waterman, ranking_hamming_syns, ranking_jaro_syns, ranking_waterman_syns


def create_triples(cls_A, cls_B, indices):
    triples = []
    for i in indices:
        triple = "{0} owl:equivalentClass {1}".format(cls_A[i[0]], cls_B[i[1]])
        triples.append(triple)
    return set(list(triples))


def compute_exact_match_syns(match_indices, concept1, concept2, i, j):
    common = list(set(concept1).intersection(set(concept2)))
    if common:
        match_indices.append((i, j))
    return match_indices


def compute_dist_syns_ge(fn, match_indices, concept1, concept2, i, j, threshold):
    scores = retrieve_scores(fn, concept1, concept2)
    if max(scores) >= threshold:
        match_indices.append((i,j))
    return match_indices


def compute_dist_syns_le(fn, match_indices, concept1, concept2, i, j, threshold):
    scores = retrieve_scores(fn, concept1, concept2)
    if min(scores) <= threshold:
        match_indices.append((i,j))
    return match_indices


def retrieve_scores(fn, concept1, concept2):
    combinations = list(itertools.product(*[concept1, concept2]))
    scores = [fn(comb[0], comb[1]) for comb in combinations]
    return scores


def compute_synonym_similarity(syns_A, syns_B, hamming_threshold=1, jaro_threshold=0.95, waterman_threshold=5):
    pprint("Calculating synonym similarity")
    timein = time.time()
    hamming_indices = []
    jaro_indices = []
    waterman_indices = []
    match_indices = []
    for i, concept1 in enumerate(syns_A):
        if i < LIMIT:
            for j, concept2 in enumerate(syns_B):
                match_indices = compute_exact_match_syns(match_indices, concept1, concept2, i, j)
                hamming_indices = compute_dist_syns_le(jellyfish.hamming_distance, hamming_indices, concept1, concept2, i, j, hamming_threshold)
                jaro_indices = compute_dist_syns_ge(jellyfish.jaro_distance, jaro_indices, concept1, concept2, i, j, jaro_threshold)
                waterman_indices = compute_dist_syns_ge(smith_waterman, waterman_indices, concept1, concept2, i, j, waterman_threshold)
    timeout = time.time()
    pprint("Run time: " + str(timeout - timein) + " seconds")
    return match_indices, hamming_indices, jaro_indices, waterman_indices


def fetch_synonym(cls, syns):
    cls = re.sub("([a-z])([A-Z])","\g<1>_\g<2>", str(cls).split('.')[-1])
    lemma_list = [lemma for ss in wn.synsets(cls) for lemma in ss.lemma_names()]
    if lemma_list:
        syns.append(list(set(lemma_list)))
    else:
        syns.append([cls.lower()])
    return syns


def convert_to_synonyms(classes_A, classes_B):
    syns_A = []
    syns_B = []
    for cls in classes_A:
        syns_A = fetch_synonym(cls, syns_A)
    for cls in classes_B:
        syns_B = fetch_synonym(cls, syns_B)
    return syns_A, syns_B


def compute_exact_match(concept1, concept2, matches, match_indices, i, j):
    if (concept2 == concept1):
        matches.append((concept1, concept2))
        match_indices.append((i,j))
    return matches, match_indices


def compute_dist_ge(fn, matches, match_indices, concept1, concept2, i, j, threshold):
    dist = fn(concept1, concept2)
    if dist >= threshold:
        matches.append((concept1, concept2))
        match_indices.append((i,j))
    return matches, match_indices


def compute_dist_le(fn, matches, match_indices, concept1, concept2, i, j, threshold):
    dist = fn(concept1, concept2)
    if dist <= threshold:
        matches.append((concept1, concept2))
        match_indices.append((i, j))
    return matches, match_indices


def compute_string_similarity(classes_A, classes_B, hamming_threshold=1, jaro_threshold=0.95, waterman_threshold=5):
    pprint("Calculating concept similarity")
    timein = time.time()
    jaro_matches = []
    jaro_indices = []
    hamming_matches = []
    hamming_indices = []
    waterman_matches = []
    waterman_indices = []
    matches = []
    match_indices = []
    for i, concept1 in enumerate(classes_A):
        if i < LIMIT:
            concept1 = str(concept1).split('.')[-1]
            for j, concept2 in enumerate(classes_B):
                concept2 = str(concept2).split('.')[-1]
                matches, match_indices = compute_exact_match(concept1, concept2, matches, match_indices, i, j)
                hamming_matches, hamming_indices = compute_dist_le(jellyfish.hamming_distance, hamming_matches, hamming_indices, concept1, concept2, i, j, hamming_threshold)
                jaro_matches, jaro_indices = compute_dist_ge(jellyfish.jaro_distance, jaro_matches, jaro_indices, concept1, concept2, i, j, jaro_threshold)
                waterman_matches, waterman_indices = compute_dist_ge(smith_waterman, waterman_matches, waterman_indices, concept1, concept2, i, j, waterman_threshold)
    timeout = time.time()
    pprint("Run time: " + str(timeout - timein) + " seconds")
    return match_indices, hamming_indices, jaro_indices, waterman_indices


def load_ontologies(path1, path2):
    onto_path.append(r'D:\Users\Jeroen\Documents\GitHub\KROTW\milestone2')
    ont_A = get_ontology(path1).load()
    ont_B = get_ontology(path2).load()
    return ont_A, ont_B


def main():
    path1 = "file://people+petsA.owl"
    path2 = "file://people+petsB.owl"
    ont_A, ont_B = load_ontologies(path1, path2)
    classes_A = list(ont_A.classes())
    classes_B = list(ont_B.classes())

    match_indices, hamming_indices, jaro_indices, waterman_indices = compute_string_similarity(classes_A, classes_B)

    syns_A, syns_B = convert_to_synonyms(classes_A, classes_B)
    syn_match_indices, syn_hamming_indices, syn_jaro_indices, syn_waterman_indices = compute_synonym_similarity(syns_A, syns_B)

    match_triples = create_triples(classes_A, classes_B, match_indices)
    syn_match_triples = create_triples(classes_A, classes_B, syn_match_indices)

    hamming_triples = create_triples(classes_A, classes_B, hamming_indices)
    syn_hamming_triples = create_triples(classes_A, classes_B, syn_hamming_indices)

    jaro_triples = create_triples(classes_A, classes_B, jaro_indices)
    syn_jaro_triples = create_triples(classes_A, classes_B, syn_jaro_indices)

    waterman_triples = create_triples(classes_A, classes_B, waterman_indices)
    syn_waterman_triples = create_triples(classes_A, classes_B, syn_waterman_indices)

    hamming_ranking, jaro_ranking, waterman_ranking, hamming_syns_ranking, jaro_syns_ranking, waterman_syns_ranking = ranking_similarity(classes_A, classes_B, syns_A, syns_B)


if __name__ == '__main__':
    main()
