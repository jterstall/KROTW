from __future__ import division
from rdflib import Graph, Namespace, URIRef, Literal, XSD, RDF 
import logging
import pandas

def read_in_xls(path_to_file_1, path_to_file_2, path_to_file_3, path_to_file_4, g, GMNTS, SCHOOLS):
	excel1 = pandas.read_excel(path_to_file_1)
	excel2 = pandas.read_excel(path_to_file_2)
	excel3 = pandas.read_excel(path_to_file_3)
	excel4 = pandas.read_excel(path_to_file_4)

	excel4 = excel4.iloc[2::3,:]
	excel4.index = range(len(excel4))
	gm_codes_1 = excel1["GemeentecodeGM"]
	gm_codes_4 = excel4["GBD"]

	gm_leefbaar = excel3['KL16']
	gm_woning = excel4['RLBWON']
	gm_bewoners = excel4['RLBBEV']
	gm_voorzien = excel4['RLBVRZ']
	gm_veilig = excel4['RLBVEI']
	gm_fysiek = excel4['RLBFYS']

	d = {"VESTIGINGSNUMMER": "first", "GEMEENTENAAM VESTIGING": "first", "EXAMENKANDIDATEN": "sum", "GESLAAGDEN": "sum", "GEMIDDELD CIJFER CIJFERLIJST": "mean"}
	excel2 = excel2.groupby("INSTELLINGSNAAM VESTIGING", as_index=False).aggregate(d).reindex(columns=excel2.columns)

	gm_scholen = excel2["INSTELLINGSNAAM VESTIGING"]
	gm_kandidaten = excel2['EXAMENKANDIDATEN']
	gm_geslaagden = excel2['GESLAAGDEN']
	gm_gemeente_scholen = excel2['GEMEENTENAAM VESTIGING']
	gm_school_nummers = excel2["VESTIGINGSNUMMER"]
	gm_cijfers = excel2['GEMIDDELD CIJFER CIJFERLIJST']
	gm_names = excel1["Gemeentenaam"]
	for i, gm_code in enumerate(gm_codes_1):
		g.add((GMNTS[gm_code], RDF.type, GMNTS['Gemeentecode']))
		g.add((GMNTS[gm_code], GMNTS['Gemeentenaam'], Literal(gm_names[i].title(), lang='nl')))

	for i, gm_code in enumerate(gm_codes_4):
		g.add((GMNTS[gm_code], GMNTS['leefbaarheid_score'], Literal(gm_leefbaar[i], lang='nl')))
		g.add((GMNTS[gm_code], GMNTS['woning_score'], Literal(gm_woning[i], lang='nl')))
		g.add((GMNTS[gm_code], GMNTS['bewoners_score'], Literal(gm_bewoners[i], lang='nl')))
		g.add((GMNTS[gm_code], GMNTS['voorzieningen_score'], Literal(gm_voorzien[i], lang='nl')))
		g.add((GMNTS[gm_code], GMNTS['veiligheid_score'], Literal(gm_veilig[i], lang='nl')))
		g.add((GMNTS[gm_code], GMNTS['fysieke_omgeving_score'], Literal(gm_fysiek[i], lang='nl')))

	for i, gm_school_nummer in enumerate(gm_school_nummers):
		g.add((SCHOOLS[gm_school_nummer], RDF.type, SCHOOLS['School']))
		g.add((SCHOOLS[gm_school_nummer], SCHOOLS['Schoolnaam'], Literal(gm_scholen[i], lang='nl')))
		g.add((SCHOOLS[gm_school_nummer], SCHOOLS['slagingspercentage'], Literal((float(gm_geslaagden[i]/gm_kandidaten[i])*100), lang='nl')))
		g.add((SCHOOLS[gm_school_nummer], SCHOOLS['gemiddelde_cijfer'], Literal(gm_cijfers[i], lang='nl')))
		g.add((SCHOOLS[gm_school_nummer], SCHOOLS['Gemeentenaam'], Literal(gm_gemeente_scholen[i].title(), lang='nl')))



	return g




path_to_file_1 = "Gemeenten alfabetisch 2018.xls"
path_to_file_2 = "07.-geslaagden,-gezakten-en-cijfers-2016-2017.xlsx"
path_to_file_3 = "Gemeente/score_gemeente.xlsx"
path_to_file_4 = "Gemeente/dimensiescore_gemeente (stand).xlsx"
g = Graph()
GMNTS = Namespace("https://gemeentesnederland.com/")
SCHOOLS = Namespace("https://scholennederland.com/")
g.bind('gm', GMNTS)
g.bind('schl', SCHOOLS)
g = read_in_xls(path_to_file_1, path_to_file_2, path_to_file_3, path_to_file_4, g, GMNTS, SCHOOLS)
g.serialize(format='turtle')
with open("Gemeentes-2.ttl", "w+") as f:
	f.write(g.serialize(format='turtle'))
	f.close()

