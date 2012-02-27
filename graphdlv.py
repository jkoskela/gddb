import re
import sys
import pickle
import pygraphviz as pgv
from collections import defaultdict
#debug
import pprint

def main():
	if(len(sys.argv) < 3):
		print('usage: python parse.py [parse map] [dlv output] [styles]  \n')
		sys.exit(1)
	f_out_dot = 'graphdlv.dot' 
	f_out_pdf = 'graphdlv.pdf' 
	f_out_graph = 'graph.p'

	rules = pickle.load(open(sys.argv[1], 'rb'))
	s = open(sys.argv[2]).read()

	g = graph_map(rules, s)
	styles = read_styles(sys.argv[3])
	#pp = pprint.PrettyPrinter(indent=4)
	#pp.pprint(styles)	
	#pp.pprint(g)	
	draw(g, styles, f_out_dot, f_out_pdf)
	pickle.dump(g, open(f_out_graph, 'wb'))


#Creates edge tuples and nodes from aux firings and places into graph map
def graph_map(rules, s):
	
	aux_count = 0
	m = re.findall('(aux[^(]*)\(([^)]*)\)', s)
	subg = {}
	subg['aux'] = {'nodes':set(), 'edges':[]} 
	for g in m:
		aux_count = aux_count + 1
		aux = g[0]
		aux_terms = g[1].split(',')
		p_list = rules[aux]
		aux_atom = '%s(%s)' % (aux, g[1])
		subg['aux']['nodes'].add(aux_atom)

		# Aux -> Head
		head = p_list[0][0] 
		atom = head + '('
		term_i = p_list[0][1]
		for i in term_i:
			atom = atom + aux_terms[i] + ','
		atom = atom.rstrip(',') + ')'
		if head not in subg:
			subg[head] = {'nodes': set(), 'edges':[]}
		subg[head]['nodes'].add(atom)
		subg[head]['edges'].append((aux_atom, atom))
		
		# Body -> Aux
		for t in p_list[1:]:
			pred = t[0]
			term_i = t[1]
			atom = pred + '('
			for i in term_i:
				atom = atom + aux_terms[i] + ','
			atom = atom.rstrip(',') + ')'

			if pred not in subg:
				subg[pred] = {'nodes':set(), 'edges':[]}
			subg[pred]['nodes'].add(atom)
			subg[pred]['edges'].append((atom, aux_atom))

	print('There were %s firings.' % aux_count)
	return subg;


def read_styles(f_in):
	styles = {}
	s = open(f_in,'rb').readlines() 
	for line in s:
		line = line.split('.')
		head = line[0]
		line = line[1].split(':')
		subg = line[0]
		if head not in styles:
			styles[head] = {}
			styles[head]['nodes'] = {}
			styles[head]['edges'] = {}
		if len(line) > 1: m = re.findall('([\w^=]*)=(\w*)',line[1])
		for g in m:
			styles[head][subg].update( ((g[0],g[1]),))
	return styles
	

def draw(graph, styles, f_out_dot, f_out_pdf):
	default = {}
	G = pgv.AGraph()
	
	node_attr = styles['aux']['nodes']
	G.add_nodes_from(graph['aux']['nodes'], **node_attr)

	for key,subg in graph.iteritems():
		node_attr = styles[key]['nodes']
		edge_attr = styles[key]['edges']
		if not node_attr: node_attr = default
		if not edge_attr: edge_attr = default
		G.add_nodes_from(subg['nodes'], **node_attr)
		G.add_edges_from(subg['edges'], **edge_attr)
		
	G.draw(f_out_dot,prog='dot')
	G.draw(f_out_pdf,prog='dot')

	
if __name__=="__main__":
	main()
