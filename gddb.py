#----------------------------------------------------------------------
# GDDB 
# Jade Koskela
# Command line interpreter for graphical datalog debugging.
#----------------------------------------------------------------------

import cmd
import sys
import graphdlv
draw = graphdlv.draw
from copy import deepcopy
from collections import defaultdict
import pdb

default_format = 'pdf'
default_layout = 'dot'

class GraphCMD(cmd.Cmd):
	def load_p(self, parse_map, dlv_out, styles=False):
		self.subg_dict, self.adj_list = graphdlv.build(parse_map, dlv_out)         
		self.auto = False 
		self.layout = default_layout 
		self.fformat = default_format
		self.saved_styles = defaultdict(lambda:{'nodes':{}, 'styles':{}})   #For saving styles when hide/show predicates
		self.styles = graphdlv.read_styles(styles)
		self.render_set = set(self.subg_dict.keys())
		self.trace = None
		
	def do_set(self, line):
		"""Set attribute of the graph or subgraphs.\nUsage: set [subgraph] [edge|nodes] [attribute] [value]\n"""
		if len(line.split()) is not 4: 
			print "Usage: set [subgraph] [graph|edges|nodes] [attribute] [value]\nTo reference entire graph use 'root' for subgraph name.\n"
			return
		subg, en, attr, value = line.split()
		self.styles[subg][en][attr] = value
		if(self.auto): 	draw(self.subg_dict, self.styles, self.layout, self.render_set, self.fformat, self.trace)

	def do_auto(self, line):
		"""Toggle Autodraw. When enabled graph is redrawn after each attribute is updated."""	
		self.auto = not self.auto	
		if(self.auto):
			print 'Enabled'
		else:
			print 'Disabled'

	def do_show(self, line):
		"""Shows a predicate subgraph including all nodes and edges incident to those nodes.\nUsage: show [predicate]"""
		if not line:
			print "Usage: show [predicate]"
		elif line in self.styles:
			self.styles[line]['nodes'] = self.saved_styles[line]['nodes'];
			self.styles[line]['edges'] = self.saved_styles[line]['edges'];
			if(self.auto): 	draw(self.subg_dict, self.styles, self.layout, self.render_set, self.fformat, self.trace)
		else:
			print 'Predicate not found.'
		
	def do_hide(self, line):
		"""Hides a predicate subgraph including all nodes and edges incident to those nodes.\nUsage: hide [predicate]"""
		if not line:
			print "Usage: hide [predicate]"
		elif line in self.styles:
			self.saved_styles[line]['nodes'] = deepcopy(self.styles[line]['nodes']);   #Backup style
			self.saved_styles[line]['edges'] = deepcopy(self.styles[line]['edges']);
			self.styles[line]['edges']['style'] = 'invis'	
			self.styles[line]['nodes']['style'] = 'invis'	
			if(self.auto): 	draw(self.subg_dict, self.styles, self.layout, self.render_set, self.fformat, self.trace)
		else:
			print 'Predicate not found.'
	
	def do_remove(self, line):
		"""Removes a predicate subgraph including all nodes and edges incident to those nodes.\nUsage: remove [predicate]"""
		if not line:
			print "Usage: remove [predicate]"
		elif line in self.render_set:
			self.render_set.remove(line)
			if(self.auto): 	draw(self.subg_dict, self.styles, self.layout, self.render_set, self.fformat, self.trace)
		else:
			print 'Predicate not found.'

	def do_add(self, line):
		"""Add a predicate subgraph back to graph. Undo remove.\nUsage: add [predicate]"""
		if not line:
			print "Usage: add [predicate]"
		elif line in self.styles:
			self.render_set.add(line)
			if(self.auto): 	draw(self.subg_dict, self.styles, self.layout, self.render_set, self.fformat, self.trace)
		else:
			print 'Predicate not found.'
		

	def do_clear(self,line):
		"""Clear all styles from the graph."""
		self.styles = defaultdict(lambda: defaultdict(lambda: {}))	

	def do_layout(self,line):
		"""Set layout program of the graph.\nUsage: layout [dot|circo|neato|twopi|fdp|sfdp]"""
		if line in graphdlv.layout_types:
			self.layout = line
			if(self.auto): 	
				draw(self.subg_dict, self.styles, self.layout, self.render_set, self.fformat, self.trace)
		else:
			print 'Layout not supported.'	

	def do_format(self,line):
		"""Set file format of the graph.\nUsage: format [pdf|gif|jpeg|png|ps]"""
		if line in graphdlv.format_types:
			self.fformat = line
			if(self.auto): 	draw(self.subg_dict, self.styles, self.layout, self.render_set, self.fformat, self.trace)
		else:
			print 'Format not supported.'	
	
	def do_ls(self, line):
		"""List subgraphs or attributes of the graph.\nUsage: ls [-a | -s]\n
		   Options: -a, -attributes; -s, -subgraphs"""
		if line == '-s' or line == '-subgraphs':
			print "----Subgraphs----"
			for subg in self.subg_dict.keys():
				print subg

		elif line == '-a' or line == '-attributes':
			print "----Attributes----"
			if self.styles['root']: 
				print 'Root Graph:'
				for key,value in self.styles['root']['graph'].iteritems(): 
					print ('    %s=%s') % (key,value) 
				if self.styles['root']['nodes']: 
					print '  Node Attributes:'
				for key,value in self.styles['root']['nodes'].iteritems(): 
					print ('    %s=%s') % (key,value) 
				if self.styles['root']['edges']: 
					print '  Edge Attributes:'
				for key,value in self.styles['root']['edges'].iteritems(): 
					print ('    %s=%s') % (key,value) 

			for subg_k,subg_v in self.styles.iteritems():
				if subg_k == 'root': continue

				#Check for subgraphs with no styles. All subgraphs have node,edge,graph attrs initialized to {}	
				attrs = {}	
				for e in subg_v.itervalues():
					attrs.update(e)
				if not e: continue
					
				print subg_k + ':' 
				for key,value in self.styles[subg_k]['graph'].iteritems(): 
					print ('    %s=%s') % (key,value) 
				if subg_v['nodes']: 
					print '  Node Attributes:'
				for key,value in subg_v['nodes'].iteritems(): 
					print ('    %s=%s') % (key,value) 
				if subg_v['edges']: 
					print '  Edge Attributes:'
				for key,value in subg_v['edges'].iteritems(): 
					print ('    %s=%s') % (key,value) 
		else:
			print "ls: invalid option " + line

			
	def do_draw(self, line):
		"""Draw graph. Default format is pdf.\nUsage: draw [pdf|ps|jpeg|gif|png]"""
		if not line: line = self.fformat
		draw(self.subg_dict, self.styles, self.layout, self.render_set, line, self.trace)


	def do_trace(self,line):
		"""Trace provenance for the atom."""	
		line = line.split()
		if not line:
			print 'Usage: trace [-f] atom [color]'
			return
		if not self.trace: 
			self.save_g, self.save_s = self.subg_dict, self.styles # Backup main graph.  	
		else: self.untrace()

		if line[0] == '-f' or line[0] =='-full':
			trace = graphdlv.trace(self.adj_list, line[1])
			if not trace:
				print 'Atom not found.'
				return
			trace_styles = graphdlv.trace_color(self.styles)   #Remove coloring from non trace subgraphs
			if len(line) > 2:
				trace_styles['trace']['color'] = {'color':line[2]}
			trace_graph = self.subg_dict
			t_type = 'full'

		else:	   
			trace = graphdlv.trace(self.adj_list, line[0]) 
			if not trace:
				print 'Atom not found.'
				return
			trace_styles = self.styles                         #Partial trace retains colors of parent graph.
			trace_graph = graphdlv.pt_graph(trace)
			t_type = 'partial'
		if not trace:
			print 'Atom not found.'
			return
		
		trace['type'] = t_type
		self.subg_dict, self.styles, self.trace = trace_graph, trace_styles, trace
		if(self.auto): 	draw(self.subg_dict, self.styles, self.layout, self.render_set, self.fformat, self.trace)


	def do_untrace(self,line):
		"""Untrace; revert to main graph."""	
		if self.trace:
			self.untrace()
			if(self.auto): 	draw(self.subg_dict, self.styles, self.layout, self.render_set, self.fformat)

	def untrace(self):
		self.trace = None
		self.subg_dict, self.styles = self.save_g, self.save_s


	def help_trace(self):
		print '\n'.join(['Render a provenance trace for the atom.',
			'Usage: trace [Options] [atom] [color]',
			'Options: -f, -full',
			'If full is specified the trace will be drawn along with the parent graph.',
			'The default is to render the trace only.\n,'
			'Partial trace retains styles of the parent graph. Full trace will render trace as color. Default color red.'])

	def help_ls(self):
		print '\n'.join(['List subgraphs or attributes of the graph.',
						 'Usage: ls [-a | -s]',
		   				 'Options: -a, -attributes; -s, -subgraphs\n'])

	def do_EOF(self, line):
		return True

	def options(self, opt_l):
		'''Prints options'''
		print 'Options'
		for x,y in opt_l:
			print '-%s, --%s' %(x,y)

if __name__ == '__main__':
	c = GraphCMD()
	if len(sys.argv) < 3:
		print "Usage: gddb.py [parse_map] [dlv_out] [styles]"
		sys.exit(1)
	else:
		print "Graphical Datalog Debugger"
	if len(sys.argv) == 3:
		c.load_p(sys.argv[1], sys.argv[2])
	else:
		c.load_p(sys.argv[1], sys.argv[2], sys.argv[3])
	c.cmdloop()
	
