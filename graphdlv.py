#----------------------------------------------------------------------
# Graph Dlv 
# Jade Koskela
#
# This program will output a graphviz .dot file based on the output of dlv.
# Parsedlv must be run first to provide the parse map.
#----------------------------------------------------------------------

import re
import sys
import pickle
import pydot
from collections import defaultdict
from collections import namedtuple
import pydot as pd

f_out_dot = 'graphdlv.dot' 
f_out_pdf = 'graphdlv.pdf' 
f_out_graph = 'graph.p'
f_out_adj = 'adj.p'


def main():
	if(len(sys.argv) < 4):
		print('usage: python parse.py [parse map] [dlv output] [styles]  \n')
		sys.exit(1)

	rules = pickle.load(open(sys.argv[1], 'rb'))
	dlv_out = open(sys.argv[2]).read()
	graph, adj_list = graph_map(rules, dlv_out)
	styles = read_styles(sys.argv[3])
	draw(graph, styles, 'dot')
	pickle.dump(graph, open(f_out_graph, 'wb'))
	pickle.dump(adj_list, open(f_out_adj, 'wb'))


#Creates edge tuples and nodes from aux firings and places into graph maps.
#There are two representations of the graph. 
#graph is a collection of subgraphs for drawing and styling.
#adj_list is used for tracing. 
def graph_map(rules, dlv_out):
	
	adj = namedtuple('adj', ['enter','exit'])           #Can't use keyword for attribute name 
	adj_list = defaultdict(lambda: adj([],[]))          #Create an adjancecy list with in and out edges 
	aux_count = 0
	m = re.findall('(aux[^(]*)\(([^)]*)\)', dlv_out)    #Grab all aux tuples
	graph = {}
	graph['aux'] = {'nodes':set(), 'edges':[]}          #Create aux subgraph
	for g in m:
		aux_count = aux_count + 1
		aux = g[0]
		aux_terms = g[1].split(',')
		p_list = rules[aux]                         #Graph the predicate list defining the relationship between the head and body in the aux
		aux_atom = '%s(%s)' % (aux, g[1])
		graph['aux']['nodes'].add(aux_atom)
		
		# Aux -> Head
		head = p_list[0][0] 
		atom = head + '('
		term_i = p_list[0][1]
		for i in term_i:
			atom = atom + aux_terms[i] + ','
		atom = atom.rstrip(',') + ')'
		if head not in graph:
			graph[head] = {'nodes': set(), 'edges':[]}

		graph[head]['nodes'].add(atom)
		graph[head]['edges'].append((aux_atom, atom))
		adj_list[atom].enter.append(aux_atom)
		adj_list[aux_atom].exit.append(aux_atom)
		
		# Body -> Aux
		for t in p_list[1:]:
			pred, term_i = t[0], t[1]
			atom = pred + '('
			for i in term_i:
				atom = atom + aux_terms[i] + ','
			atom = atom.rstrip(',') + ')'

			if pred not in graph:
				graph[pred] = {'nodes':set(), 'edges':[]}
			graph[pred]['nodes'].add(atom)
			graph[pred]['edges'].append((atom, aux_atom))
			adj_list[atom].exit.append(aux_atom)
			adj_list[aux_atom].enter.append(atom)

	print('There were %s firings.' % aux_count)
	return (graph, adj_list)


def read_styles(f_in):
	styles = defaultdict(lambda: defaultdict(lambda: {}))
	s = open(f_in,'rb').readlines() 
	for line in s:
		line = line.split('.')
		subg = line[0]
		line = line[1].split(':')
		ssubg = line[0]
		if len(line) > 1: m = re.findall('([\w^=]*)=(#?\w*)',line[1])
		for g in m:
			styles[subg][ssubg].update( ((g[0],g[1]),))
	
	return styles
	

def draw(graph, styles, layout):
	default = {}
	G = pd.Dot()         #Dot is derived class of Graph
	
	#Set attributes for root graph.
	graph_attr = styles['root']['graph']
	node_attr = styles['root']['nodes']
	edge_attr = styles['root']['edges']
	G.set_node_defaults(**node_attr)
	G.set_edge_defaults(**edge_attr)
	G.set_graph_defaults(**graph_attr)

	#Aux attributes must be added first or will default to styles in incident edges.
	node_attr = styles['aux']['nodes']     
	subG = pd.Subgraph()
	subG.set_node_defaults(**node_attr)
	for n in graph['aux']['nodes']:
		n = pd.Node(n)
		subG.add_node(n)
	G.add_subgraph(subG)

	#Add remaining nodes and attributes by subgraph.
	for key,subg in graph.iteritems():
		if key=='aux': continue
		node_attr = styles[key]['nodes']
		edge_attr = styles[key]['edges']
		graph_attr = styles[key]['graph']
		subG = pd.Subgraph()
		subG.set_node_defaults(**node_attr)
		subG.set_edge_defaults(**edge_attr)
		subG.set_graph_defaults(**graph_attr)
		for n in subg['nodes']:
			n = pd.Node(n)
			subG.add_node(n)
		for e in subg['edges']:
			e = pd.Edge(e[0],e[1])
			subG.add_edge(e)
		G.add_subgraph(subG)
		
	G.write_pdf('graphdlv.pdf',prog=layout)
	
if __name__=="__main__":
	main()
