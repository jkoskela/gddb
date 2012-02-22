import re
import sys
import pickle
import pygraphviz as pgv
#debug
import pprint

def main():
	if(len(sys.argv) < 3):
		print('usage: python parse.py [parse map] [dlv output] [styles] \n')
		sys.exit(1)
	f_out = 'graph_dlv.pdf' 
	rules = pickle.load(open(sys.argv[1], 'rb'))
	
	s = open(sys.argv[2]).read()

	g = graph_map(rules, s)
	styles = read_styles(sys.argv[3])
	draw(g, styles, f_out)


#Creates edge tuples and nodes from aux firings and places into graph map
def graph_map(rules, s):
	
	aux_count = 0
	m = re.findall('(aux[^(]*)\(([^)]*)\)', s)
	subg = dict()
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

	pp = pprint.PrettyPrinter(indent=4)
	pp.pprint(subg)	

	print('There were %s firings.' % aux_count)
	return subg;

def read_styles(f_in):
	styles = dict()
	s = open(f_in,'rb').readlines() 
	for line in s:
		line = line.split(':')
		head = line[0]
		attr = dict()
		m = re.findall('([^=]*)=(\w*)',line[1])
		for g in m:
			attr[g[0]] = g[1]
	

def draw(graph, styles, f_out):
	G = pgv.AGraph()
	for key,subg in graph.iteritems():
		attr = styles[key]
		G.add_nodes_from(subg['nodes'], **attr)
		G.add_edges_from(subg['edges'], **attr)
	G.draw(f_out,prog='dot')

	
if __name__=="__main__":
	main()
