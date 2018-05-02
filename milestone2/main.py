import rdflib
import time
from pprint import pprint


def exact_match(g, g2):
    timein = time.time()
    matches = []
    match_indices = []
    for i, concept in enumerate(g):
        if i < 100:
            uri1 = concept[0].split('/')[-1]
            for j, concept2 in enumerate(g2):
                uri2 = concept2[0].split('/')[-1]
                if (uri2 == uri1) and not any(uri1 in match[0] for match in matches):
                    matches.append((uri1, uri2))
                    match_indices.append((i,j))
    timeout = time.time()
    print("Run time: " + str(timeout - timein) + " seconds")
    return matches


def tf_idf():
    return


def init():
    g = rdflib.Graph()
    g2 = rdflib.Graph()
    g.parse('Gemeentes-2.ttl', format="ttl")
    g2.parse('Gemeentes-2.ttl', format="ttl")
    return g, g2


def main():
    g, g2 = init()
    matches = exact_match(g, g2)
    print(matches)


if __name__ == '__main__':
    main()
