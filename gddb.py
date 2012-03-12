#----------------------------------------------------------------------
# GDDB 
# Jade Koskela
# Command line interpreter for graphical datalog debugging.
#----------------------------------------------------------------------

import cmd
import sys
import pickle
import graphdlv
draw = graphdlv.draw
from collections import defaultdict

f_out_dot = 'graphdlv.dot' 
f_out_pdf = 'graphdlv.pdf' 

class GraphCMD(cmd.Cmd):
	def load_p(self, parse_map, dlv_out, styles):
		self.graph = graphdlv.Graph(parse_map, dlv_out)
		self.styles = graphdlv.read_styles(styles)
		self.auto = False 
		self.layout = 'dot'
		
	def do_set(self, line):
		"""Set attribute of the graph or subgraphs.\nUsage: set [subgraph] [edge|nodes] [attribute] [value]\n"""
		if len(line.split()) < 4: 
			print "Usage: set [subgraph] [graph|edges|nodes] [attribute] [value]\nTo reference entire graph use 'root' for subgraph name.\n"
			return
		subg, en, attr, value = line.split()
		self.styles[subg][en][attr] = value

	def do_autodraw(self, line):
		"""Toggle Autodraw. When enabled graph is redrawn after each attribute is updated."""	
		self.auto = not self.auto	
		if(self.auto):
			print 'Enabled'
		else:
			print 'Disabled'

	def do_clear(self,line):
		"""Clear all styles from the graph."""
		self.styles = defaultdict(lambda: defaultdict(lambda: {}))	

	def do_layout(self,line):
		"""Set layout of graph.\nUsage: layout [dot|circo|neato|twopi|fdp|sfdp]"""
		self.layout = line
		if(self.auto): 	draw(self.graph, self.styles, self.layout)
	
	def do_ls(self, line):
		"""List subgraphs or attributes of the graph.\nUsage: ls [-a | -s]\n
		   Options: -a, -attributes; -s, -subgraphs"""
		if line == '-s' or line == '-subgraphs':
			print "----Subgraphs----"
			for subg in self.graph.p_graph.keys():
				print subg

		elif line == '-a' or line == '-attributes':
			print "----Attributes----"
			if self.styles['root']['graph']: 
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
				print

			for subg_k,subg_v in self.styles.iteritems():
				if subg_k == 'root': continue
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
				print
		else:
			print "***Incorrect ls option***"
		print 

		if(self.auto): 	draw(self.graph, self.styles, self.layout)
			
			
	def do_draw(self,line):
		"""Draw graph format. Default layout format is dot and pdf."""
		draw(self.graph.p_graph, self.styles, self.layout)

	def do_trace(self,line):
		"""Render a trace graph for the atom."""	
		line = line.split()
		if line[0] == '-f' or line[0] =='-full':
			trace_graph, styles = self.graph.trace_full(line[1])
			if not trace_graph:
				print 'Atom not found.'
				return
			draw(trace_graph, styles, self.layout)
		else:	   
			trace_graph = self.graph.trace(line[0])
			if not trace_graph:
				print 'Atom not found.'
				return
			draw(trace_graph, self.styles, self.layout)

	def help_trace(self):
		print '\n'.join(['Render a trace graph for the atom.',
			'Usage: trace [Options] [atom]',
			'Options: -f, -full',
			'If full is specified the trace will be layed over the full graph.',
			'The default is to render the trace only.\n'])

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
	if(len(sys.argv) < 3):
		print "Usage gddb.py [parse_map] [dlv_out] [styles]"
		sys.exit(1)
	else:
		print "Graphical Datalog Debugger"
	c.load_p(sys.argv[1], sys.argv[2], sys.argv[3])
	c.cmdloop()
	
