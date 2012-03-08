import cmd
import sys
import pickle
from graphdlv import draw
from graphdlv import read_styles 
from collections import defaultdict

f_out_dot = 'graphdlv.dot' 
f_out_pdf = 'graphdlv.pdf' 

class GraphCMD(cmd.Cmd):
	"""Command line processor for manipulating output of graphdlv."""
	def load_p(self, g, s):
		self.graph = pickle.load(open(g, 'rb'))
		self.styles = read_styles(s)
		
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
	
	def do_ls(self, line):
		"""List subgraphs or attributes of the graph.\nUsage: ls [attr | subg]\n"""
		if line == 'subg':
			print "----Subgraphs----"
			for subg in self.graph.keys():
				print subg

		elif line == 'attr':
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
		"""Draw graph format. Default layout format is .dot and pdf."""
		draw(self.graph, self.styles, self.layout)
	
	def my_init(self):
		self.auto = False 
		self.layout = 'dot'
		
    
	def do_EOF(self, line):
		return True

if __name__ == '__main__':
	c = GraphCMD()
	c.my_init()
	if(len(sys.argv) < 3):
		print "Usage int.py [graph dump] [styles]"
		sys.exit(1)
	else:
		print "Command line processor for manipulating output of graphdlv."
	c.load_p(sys.argv[1], sys.argv[2])
	c.cmdloop()
	
