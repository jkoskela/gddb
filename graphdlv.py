#======================================================================
# GDDB: Graphical Datalog Debugger 
# Author: Jade Koskela <jtkoskela@ucdavis.edu>
# http://github.com/jkoskela/gddb
#
#======================================================================
"""
This module provides parsing and graphing functionality to the gddb command line interpreter.
"""

import re
import sys
import pickle
import json
import pydot as pd
from collections import defaultdict
from collections import namedtuple
from copy import deepcopy

format_types = set(['gif', 'png', 'pdf', 'jpeg', 'ps'])
layout_types = set(['dot','neato','twopi','circo','fdp','sfdp'])
f_out_name = 'graph'   #Default output filename
nt_color   = 'black'   #Default color for elements not included in the trace subgraph
t_color    = 'red'     #Default color for elements included in the trace subgraph

d_styles=('{"root":{"nodes":{"shape":"plaintext"}},'
          '"aux" :{"nodes":{"shape":"point"}},'
          '"negation_in":{"edges":{"color":"green","style":"dashed"}},'
          '"negation_out":{"edges":{"color":"red"}}}')

def build(parse_map, dlv_output):
   """
   Builds agencency list and subgraph dictonary. Returns these as a tuple. 
   Subgraph dictionary is used for rendering. Adjacency list is used for tracing provenance.  
   parse_map  - serialized dictionary of rule mappings created by parsedlv. 
   dlv_output - the output model created by dlv using the auxiliary rules.
   """
   rules = pickle.load(open(parse_map))
   dlv_out = open(dlv_output).read()

   aux_count = 0
   adj = namedtuple('adj', ['in_edge','out_edge'])     
   adj_list = defaultdict(lambda: adj([],[]))   
   m = re.findall('(aux[^(]*)\(([^)]*)\)', dlv_out) 
   graph = defaultdict(lambda:{'nodes':set(), 'edges':set()})
   negations = set() 
   
   for g in m:
      aux_count = aux_count + 1
      pred = g[0]
      argv = g[1].split(',')
      p_list = rules[pred]     #Get the mapping from the aux tuple to the body/head
      aux_atom = '%s(%s)' % (pred, g[1])
      graph['aux']['nodes'].add(aux_atom)
      
      # Aux -> Head Edges
      pred = p_list[0][0]     #Create aux->head edges, insert into graph and adj_list
      argi = p_list[0][1]
      args = [argv[i] for i in argi]
      atom = "%s(%s)" % (pred, ','.join(args))

      graph[pred]['nodes'].add(atom)                      
      graph[pred]['edges'].add((aux_atom, atom))
      adj_list[atom].in_edge.append(aux_atom)
      adj_list[aux_atom].out_edge.append(aux_atom)  
      
      # Body -> Aux Edges                    
      for p in p_list[1:]:
         pred, argi = p[0], p[1]
         args = [argv[i] for i in argi]
         atom = "%s(%s)" % (pred, ','.join(args))

         n = re.search('not (.+)', pred)   #Find negations
         if n:
            n_pred = n.group(1)  
            neg_class = '{%s}' % n_pred
            negations.add(n_pred)                    
            graph['negation_out']['edges'].add((neg_class, atom))
            adj_list[atom].in_edge.append(neg_class)
            adj_list[neg_class].out_edge.append(atom)

         graph[pred]['nodes'].add(atom) #Add nodes,edges to body predicates subgraphs
         graph[pred]['edges'].add((atom, aux_atom))
         adj_list[atom].out_edge.append(aux_atom) 
         adj_list[aux_atom].in_edge.append(atom)

   for pred in negations:                          #Create negation class
      neg_class = '{%s}' % pred
      graph['negation']['nodes'].add(neg_class)
      for n in graph[pred]['nodes']:
         graph['negation_in']['edges'].add((n,'{%s}' % pred))
         adj_list[n].out_edge.append(neg_class)    
         adj_list[neg_class].in_edge.append(n)
   return (graph, adj_list)


def read_styles(f_in):
   """ Reads styles from external style sheet, f_in. """
   l = lambda:defaultdict(l)
   if not f_in:                            
      styles = json.loads(d_styles, object_hook=lambda x: defaultdict(l, x))
   else:
      styles = json.load(open(f_in), object_hook=lambda x: defaultdict(l, x))
   return styles

   
def draw(graph, styles, layout, out_format, trace={}):
   """
   Renders the graph to dot file using specified graphviz layout and file format.
   Parameters:
     graph  -  subgraph dict
     styles -  style dict
     layout -  graphviz layout eg. dot, circo
     format -  output file format eg. pdf, gif
     trace  -  a provenance trace
   """

   G = pd.Dot()  #Dot is derived class of Graph

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
   f_out = "%s.%s" % (f_out_name,out_format)
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


def trace(adj_list, atom):
   """ Returns provenance trace of atom. """
   trace = {'nodes': set(), 'back_edges':set(), 'edges': set()}
   color_n = defaultdict(dict)
   if atom not in adj_list: return None
   DFS(adj_list, atom, trace, color_n) 
   return trace 

def DFS(adj_list, v, trace, color_n):
   """ Reverse depth first search. u -> v Returns set traversed by search and set of backedges (cycles). """
   v_pred = predicate(v)
   color_n[v] = 'grey'
   trace['nodes'].add(v)
   for u in adj_list[v].in_edge:
      if not color_n[u]:
         trace['edges'].add((u,v))
         DFS(adj_list, u, trace, color_n)
      elif color_n[u] == 'grey':
         trace['back_edges'].add((u,v))
      else:
         trace['edges'].add((u,v))
   color_n[v] = 'black'
   return 

def proc_ft(graph, trace, color):
   """ Colors the full trace. """
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

def proc_pt(graph, be):
   """ Styles backedges """
   for e in be:
      pred = '"%s"' % edge_pred(e)
      e = ('"%s"' % e[0], '"%s"' % e[1])
      e_ref = graph.get_subgraph(pred)[0].get_edge(e)[0]
      e_ref.set_style('dashed')
      e_ref.set_constraint('false')

def pt_graph(trace):
   """ Returns trace only graph. """
   graph = defaultdict(lambda:{'nodes':set(), 'edges':set()})
   nodes = [node_pred(n) for n in trace['nodes']]
   graph[pred]['nodes'].add(nodes)
   edges = [edge_pred(e) for e in trace['edges']]
   graph[pred]['edges'].add(edges)
   edges = [edge_pred(e) for e in trace['back_edges']]
   graph[pred]['edges'].add(edges)
   return graph

def predicate(atom):
   """ Returns the predicate of an atom. """
   m = re.search('([^(]*)(.+)', atom)
   return m.group(1)

def edge_pred(e):
   """ Returns subgraph predicate of an edge. """
   if re.match('{', e[0]):
      return 'negation_out'
   if re.match('{', e[1]):
      return 'negation_in'
   if re.match('aux', e[0]):
      return predicate(e[1])
   else:
      return predicate(e[0])

def node_pred(n):
   """ Returns predicate of node. """
   if re.match('aux', n):
      return 'aux'
   if re.match('{', n):
      return 'negation'
   else:
      return predicate(n)

def trace_color(styles):
   """ Colors all nodes and edges in the trace. Returns new style dict. """
   new_styles = deepcopy(styles)
   new_styles['trace']['color'] = t_color
   for key,subg in new_styles.iteritems():
      if key == 'trace': continue
      if 'fontcolor' in subg['nodes'].iterkeys():
         subg['nodes']['fontcolor'] = nt_color  
      if 'color' in subg['edges'].iterkeys():
         subg['edges']['color'] = nt_color   
   return new_styles
