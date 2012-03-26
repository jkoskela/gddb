#----------------------------------------------------------------------
# Graph Dlv 
# Jade Koskela
# This module provides parsing and graphing functions for gddb.
#----------------------------------------------------------------------

import re
import sys
sys.path.append("./pydot")
import pydot
import dot_parser
import pickle
from collections import defaultdict
from collections import namedtuple
import pydot as pd
from copy import deepcopy

format_types = set(['gif', 'png', 'pdf', 'jpeg', 'ps'])
layout_types = set(['dot','neato','twopi','circo','fdp','sfdp'])
f_out_base = "graphdlv."
nt_color = 'black'             #Default color for elements not included in the trace subgraph
t_color  = 'red'               #Default color for elements included in the trace subgraph

d_styles  = defaultdict(lambda:defauldict(lambda:{}),   #Default styles
            {'root':defaultdict(lambda:{},{'nodes':{'shape':'plaintext'}}), 
             'aux':defaultdict(lambda:{},{'nodes':{'shape':'point'}}),
	     'negation_in':defaultdict(lambda:{},{'edges':{'color':'green', 'style':'dashed'}}),	
	     'negation_out':defaultdict(lambda:{},{'edges':{'color':'red'}})	
	    })


# Parse map is a pickled dictionary of rule mappings created by parsedlv. 
# Dlv output is the output file from dlv using aux rules.
# Style is a external style sheet 
# Returns subg_dict and adj_list
# subg_dict is used for styling & rendering using pydot. adj_list is used for tracing.
def build(parse_map, dlv_output):
	rules = pickle.load(open(parse_map))
	dlv_out = open(dlv_output).read()
    	return(graph_map(rules, dlv_out))    
    
    
# Creates edge tuples and nodes from aux firings and places into graph maps.
# There are two representations of the graph. 
# graph is a collection of subgraphs for drawing and styling.
# adj_list is used for tracing. 
# Returns graph, adj_list tuple
def graph_map(rules, dlv_out):
	adj = namedtuple('adj', ['enter','exit'])           #Adjacency list element with in and out edges. 
	adj_list = defaultdict(lambda: adj([],[]))          #Create an adjancecy list with in and out edges 
	aux_count = 0
	m = re.findall('(aux[^(]*)\(([^)]*)\)', dlv_out)           #Grab all aux tuples
	graph = defaultdict(lambda:{'nodes':set(), 'edges':set()})
	negations = set()	
	
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
		for i in term_i:				#Create head atom using mapping from aux atom
			atom = atom + aux_terms[i] + ','
		atom = atom.rstrip(',') + ')'

		graph[head]['nodes'].add(atom)                      
		graph[head]['edges'].add((aux_atom, atom))
		adj_list[atom].enter.append(aux_atom)
		adj_list[aux_atom].exit.append(aux_atom)         #Add nodes to adj list  
		
		# Body -> Aux                                   #Create body->aux edges
		for t in p_list[1:]:
			pred, term_i = t[0], t[1]
			atom = pred + '('
			for i in term_i:
				atom = atom + aux_terms[i] + ','
			atom = atom.rstrip(',') + ')'

			m = re.search('not (.+)', pred)       	      #Find negations
			if m:
				n_pred = m.group(1)	
				neg_class = '{%s}' % n_pred
				negations.add(n_pred)                    
				graph['negation_out']['edges'].add((neg_class, atom))
				adj_list[atom].enter.append(neg_class)
				adj_list[neg_class].exit.append(atom)

			graph[pred]['nodes'].add(atom)				#Add nodes,edges to body predicates subgraphs
			graph[pred]['edges'].add((atom, aux_atom))
			adj_list[atom].exit.append(aux_atom)			#Add nodes to adj list 
			adj_list[aux_atom].enter.append(atom)

	for pred in negations:                                                      #Create negation class
		neg_class = '{%s}' % pred
		graph['negation']['nodes'].add(neg_class)
		for n in graph[pred]['nodes']:
			graph['negation_in']['edges'].add((n,'{%s}' % pred))
			adj_list[n].exit.append(neg_class)			#Add nodes to adj list 
			adj_list[neg_class].enter.append(n)

	return (graph, adj_list)


# Reads style sheets in from file.
def read_styles(f_in):
	styles = defaultdict(lambda: defaultdict(lambda: {}))
	if not f_in:                                                            #If no external style sheet was supplied
		styles.update(d_styles)
		return styles 
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

	
# Renders the graph to dot file using specified graphviz layout and file format.
def draw(graph, styles, layout, out_format, trace={}):
	G = pd.Dot()         #Dot is derived class of Graph
		
	#Set attributes for root graph.
	graph_attr = styles['root']['graph']
	node_attr = styles['root']['nodes']
	edge_attr = styles['root']['edges']
	G.set_node_defaults(**node_attr)
	G.set_edge_defaults(**edge_attr)
	G.set_graph_defaults(**graph_attr)

	#Add aux subgraph first
	subG_aux = pd.Subgraph('"aux"')
	node_attr = styles['aux']['nodes']
	subG_aux.set_node_defaults(**node_attr)
	for n in graph['aux']['nodes']:
		n = pd.Node(n)
		subG_aux.add_node(n)
	G.add_subgraph(subG_aux)

	#Add remaining nodes and attributes by subgraph.
	for key,subg in graph.iteritems():
		if key =='aux': continue

		node_attr = styles[key]['nodes']
		edge_attr = styles[key]['edges']
		graph_attr = styles[key]['graph']
		subG = pd.Subgraph('"%s"'% key)
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

	if trace: 
		if trace['type'] == 'full': 
			proc_ft(G, trace, styles['trace']['color'])
		else:
			proc_pt(G, trace['back_edges'])

	#G.write(f_out_dot,prog=layout)
	f_out = f_out_base + out_format 	
	if out_format == 'pdf':
		G.write_pdf(f_out,prog=layout)
	elif out_format == 'png':
		G.write_png(f_out,prog=layout)
	elif out_format == 'gif':
		G.write_gif(f_out,prog=layout)
	elif out_format == 'jpeg':
		G.write_jpeg(f_out,prog=layout)
	elif out_format == 'ps':
		G.write_ps(f_out,prog=layout)
	else:
		print 'File type not supported'	


# Returns provenance trace of atom.
def trace(adj_list, atom):
	trace = {'nodes': set(), 'back_edges':set(), 'edges': set()}
	color_n = defaultdict(lambda:{})
	if atom not in adj_list: return None
	DFS(adj_list, atom, trace, color_n)	
	return trace 

# Reverse depth first search. u -> v 
# Returns trace set and backedge set.
def DFS(adj_list, v, trace, color_n):
	v_pred = predicate(v)
	color_n[v] = 'grey'
	trace['nodes'].add(v)
	for u in adj_list[v].enter:
		if not color_n[u]:
			trace['edges'].add((u,v))
			DFS(adj_list, u, trace, color_n)
		elif color_n[u] == 'grey':
			trace['back_edges'].add((u,v))
		else:
			trace['edges'].add((u,v))
	color_n[v] = 'black'
	return 

# Colors the full trace.
def proc_ft(graph, trace, color):
	for n in trace['nodes']:
		pred = '"%s"' % node_pred(n)
		n = '"%s"' % n
		n_ref = graph.get_subgraph(pred)[0].get_node(n)[0]
		n_ref.set_fontcolor(color)
	for e in trace['edges']:
		pred = '"%s"' % edge_pred(e)
		e = ('"%s"' % e[0], '"%s"' % e[1])
		e_ref = graph.get_subgraph(pred)[0].get_edge(e)[0]
		e_ref.set_color(color)
	for e in trace['back_edges']:
		pred = '"%s"' % edge_pred(e)
		e = ('"%s"' % e[0], '"%s"' % e[1])
		e_ref = graph.get_subgraph(pred)[0].get_edge(e)[0]
		e_ref.set_color(color)
		e_ref.set_style('dashed')
		#e_ref.set_constraint('false')

# Styles backedges
def proc_pt(graph, be):
	for e in be:
		pred = '"%s"' % edge_pred(e)
		e = ('"%s"' % e[0], '"%s"' % e[1])
		e_ref = graph.get_subgraph(pred)[0].get_edge(e)[0]
		e_ref.set_style('dashed')
		e_ref.set_constraint('false')

# Returns trace only graph.
def pt_graph(trace):
	graph = defaultdict(lambda:{'nodes':set(), 'edges':set()})
	for n in trace['nodes']:
		pred = node_pred(n)
		graph[pred]['nodes'].add(n)
	for e in trace['edges']:
		pred = edge_pred(e)
		graph[pred]['edges'].add(e)
	for e in trace['back_edges']:
		pred = edge_pred(e)
		graph[pred]['edges'].add(e)
	return graph


#Returns the predicate of an atom
def predicate(atom):
	m = re.search('([^(]*)(.+)', atom)
	return m.group(1)

# Returns predicate atom in the edge
def edge_pred(e):
	if re.match('{', e[0]):
		return 'negation_out'
	if re.match('{', e[1]):
		return 'negation_in'
	if re.match('aux', e[0]):
		return predicate(e[1])
	else:
		return predicate(e[0])

# Returns predicate of node
def node_pred(n):
	if re.match('aux', n):
		return 'aux'
	if re.match('{', n):
		return 'negation'
	else:
		return predicate(n)

# Sets trace color 
# Returns new style dict
def trace_color(styles):
	new_styles = deepcopy(styles)
	new_styles['trace']['color'] = t_color
	for key,subg in new_styles.iteritems():
		if key == 'trace': continue
		if 'fontcolor' in subg['nodes'].iterkeys():
			subg['nodes']['fontcolor'] = nt_color	
		if 'color' in subg['edges'].iterkeys():
			subg['edges']['color'] = nt_color	
	return new_styles
