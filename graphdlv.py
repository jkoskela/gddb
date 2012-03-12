#----------------------------------------------------------------------
# Graph Dlv 
# Jade Koskela
#
# This module provides parsing and graphing functions dlv.
#----------------------------------------------------------------------

import re
import sys
import pydot
import pickle
from collections import defaultdict
from collections import namedtuple
from collections import deque
import pydot as pd

f_out_dot = 'graphdlv.dot' 
f_out_gif = 'graphdlv.gif' 
f_out_pdf = 'graphdlv.pdf' 
f_out_png = 'graphdlv.png' 
tb_styles = { 'root':defaultdict(lambda:{},{'graph':{'bgcolor':'#336699','ranksep':'2'},'nodes':{'shape':'plaintext'}}), 
			 'trace':defaultdict(lambda:{},{'edges':{'color':'red'}, 'nodes':{'fontcolor':'red'}}),
			   'aux':defaultdict(lambda:{},{'nodes':{'shape':'point'}})}

# Graph class. 
# Parse map is a pickled dictionary of rule mappings created by parsedlv. 
# Dlv output is the output file from dlv using aux rules.
# Style is a external style sheet 
class Graph:
	def __init__(self, parse_map, dlv_output):
		rules = pickle.load(open(parse_map))
		dlv_out = open(dlv_output).read()
		self.p_graph, self.adj_list = graph_map(rules, dlv_out)  #Graph is used for styling and rendering using pydot. Adj_list is used for tracing.

	#Returns the pydot graph for rendering of a trace only.
	def trace(self, atom):
		if atom not in self.adj_list:
			return 
		trace_graph = defaultdict(lambda: {'nodes':set(), 'edges':set()})
		pred = predicate(atom)
		trace_graph[pred]['nodes'].add(atom)

		#Do BFS search backwards.
		q = deque()
		q.append(atom)
		while(q):
			v = q.popleft()
			v_pred = predicate(v)
			for u in self.adj_list[v].enter:
				u_pred = predicate(u)
				if re.match('aux', u_pred):
					u_pred = 'aux'
					if u not in trace_graph[u_pred]['nodes']:
						q.append(u)
						trace_graph[u_pred]['nodes'].add(u)
						trace_graph[v_pred]['edges'].add((u,v))
				else:
					if u not in trace_graph[u_pred]['nodes']:
						q.append(u)
						trace_graph[u_pred]['nodes'].add(u)
						trace_graph[u_pred]['edges'].add((u,v))

		return trace_graph

	#Returns a graph,style tuple of a trace rendered with the main graph.
	def trace_full(self, atom):
		if atom not in self.adj_list:
			return ('','')
		trace_graph = defaultdict(lambda: {'nodes':set(), 'edges':set()})
		styles = defaultdict(lambda: defaultdict(lambda: {}))
		t_set = set()
		styles.update(tb_styles)

		pred = predicate(atom)
		trace_graph['trace']['nodes'].add(atom)
		t_set.add(atom)                               #To test for membership in the trace

		#Do BFS search backwards.
		q = deque()
		q.append(atom)
		while(q):
			v = q.popleft()
			v_pred = predicate(v)
			for u in self.adj_list[v].enter:
				u_pred = predicate(u)
				if re.match('aux', u_pred):
					u_pred = 'aux'
					if u not in trace_graph['aux']['nodes']:
						q.append(u)
						t_set.add(u)
						t_set.add((u,v))
						trace_graph['aux']['nodes'].add(u)
						trace_graph['trace']['edges'].add((u,v))
				else:
					if u not in trace_graph[u_pred]['nodes']:
						q.append(u)
						t_set.add(u)
						t_set.add((u,v))
						trace_graph['trace']['nodes'].add(u)
						trace_graph['trace']['edges'].add((u,v))

		for k,subg in self.p_graph.iteritems():
			for n in subg['nodes']:
				if n not in t_set:
					trace_graph['root']['nodes'].add(n)	
			for e in subg['edges']:
				if e not in t_set:
					trace_graph['root']['edges'].add(e)	
		return trace_graph, styles


		


# Creates edge tuples and nodes from aux firings and places into graph maps.
# There are two representations of the graph. 
# graph is a collection of subgraphs for drawing and styling.
# adj_list is used for tracing. 
def graph_map(rules, dlv_out):
	adj = namedtuple('adj', ['enter','exit'])           #Adjacency list element with in and out edges. 
	adj_list = defaultdict(lambda: adj([],[]))          #Create an adjancecy list with in and out edges 
	aux_count = 0
	m = re.findall('(aux[^(]*)\(([^)]*)\)', dlv_out)    #Grab all aux tuples
	graph = {}
	graph['aux'] = {'nodes':set(), 'edges':set()}          #Create aux subgraph
	for g in m:
		aux_count = aux_count + 1
		aux = g[0]
		aux_terms = g[1].split(',')
		p_list = rules[aux]                             #Get the mapping from the aux tuple to the body/head
		aux_atom = '%s(%s)' % (aux, g[1])
		graph['aux']['nodes'].add(aux_atom)
		
		# Aux -> Head
		head = p_list[0][0]                              #Create aux->edges, insert into graph and adj_list
		atom = head + '('
		term_i = p_list[0][1]
		for i in term_i:								#Create head atom using mapping from aux atom
			atom = atom + aux_terms[i] + ','
		atom = atom.rstrip(',') + ')'
		if head not in graph:							 #Create new subgraph if not existent
			graph[head] = {'nodes': set(), 'edges':set()}

		graph[head]['nodes'].add(atom)                   #Add nodes,edges to head subgraph     
		graph[head]['edges'].add((aux_atom, atom))
		#graph['aux']['edges'].add((aux_atom, atom))      #Out edges from aux belong to aux subgraph
		adj_list[atom].enter.append(aux_atom)
		adj_list[aux_atom].exit.append(aux_atom)         #Add nodes to adj list  
		
		# Body -> Aux                                   #Create body->aux edges
		for t in p_list[1:]:
			pred, term_i = t[0], t[1]
			atom = pred + '('
			for i in term_i:
				atom = atom + aux_terms[i] + ','
			atom = atom.rstrip(',') + ')'

			if pred not in graph:
				graph[pred] = {'nodes':set(), 'edges':set()}	#Create subgraph for body atoms if not existent
			graph[pred]['nodes'].add(atom)					#Add nodes,edges to body predicates subgraphs
			graph[pred]['edges'].add((atom, aux_atom))
			adj_list[atom].exit.append(aux_atom)			#Add nodes to adj list 
			adj_list[aux_atom].enter.append(atom)

	return (graph, adj_list)

# Reads style sheets in from file.
def read_styles(f_in):
	styles = defaultdict(lambda: defaultdict(lambda: {}))
	s = open(f_in,'rb').readlines() 
	for line in s:
		line = line.split('.')
		subg = line[0]
		line = line[1].split(':')
		ssubg = line[0]
		if len(line) > 1: 
			m = re.findall('([\w^=]*)=(#?\w*)',line[1])
		for g in m:
			styles[subg][ssubg].update( ((g[0],g[1]),))
	
	return styles
	
# Renders the graph to a png and dot file using the graphviz layout.
def draw(graph, styles, layout):
	G = pd.Dot()         #Dot is derived class of Graph

	#Set attributes for root graph.
	graph_attr = styles['root']['graph']
	node_attr = styles['root']['nodes']
	edge_attr = styles['root']['edges']
	G.set_node_defaults(**node_attr)
	G.set_edge_defaults(**edge_attr)
	G.set_graph_defaults(**graph_attr)

	#Aux attributes must be added first or will default to styles in incident edges.
	#Aux does not have any edges of it's own. All edges belong to other incident predicates.
	subG = pd.Subgraph()
	edge_attr = styles['aux']['graph']
	node_attr = styles['aux']['nodes']
	subG.set_graph_defaults(**graph_attr)
	subG.set_node_defaults(**node_attr)
	for n in graph['aux']['nodes']:
		n = pd.Node(n)
		subG.add_node(n)
	G.add_subgraph(subG)

	#Add remaining nodes and attributes by subgraph.
	for key,subg in graph.iteritems():
		if key =='aux': continue
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

	G.write_gif(f_out_gif,prog=layout)
	G.write(f_out_dot,prog=layout)
					
# Returns the predicate of an atom																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																								
def predicate(atom):
	m = re.search('([^(]*)', atom)
	return m.group(1)