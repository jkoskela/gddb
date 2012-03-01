import cmd
import sys
import pickle
from graphdlv import draw

f_out_dot = 'graphdlv.dot' 
f_out_pdf = 'graphdlv.pdf' 

class GraphCMD(cmd.Cmd):
	"""Command line processor for manipulating output of graphdlv."""
	def load_p(self, g, s):
		self.graph = pickle.load(open(g, 'rb'))
		self.styles = pickle.load(open(s, 'rb'))
		
	def do_set(self, line):
		"""Set attribute of the graph or subgraphs.\nUsage: set [subgraph] [edge|nodes] [attribute] [value]\n"""
		if len(line.split()) < 4: 
			print "Usage: set [subgraph] [edge|nodes] [attribute] [value]\n"
			return
		subg, en, attr, value = line.split()
		self.styles[subg][en][attr] = value

	def do_autodraw(self, line):
		"""Toggle Autodraw. When enabled graph is redrawn after each attribute is updated."""	
		self.auto = not self.auto	
	
	def do_ls(self, line):
		"""List subgraphs or attributes of the graph.\n"""
		if line == 'subg':
			print "----Subgraphs----"
			for subg in self.graph.keys():
				print subg
		elif line == 'attr':
			print "----Attributes----"
			if self.styles['top_level']:
				print 'Top Level Graph:'
				if self.styles['top_level']['nodes']: print '  Node Attributes:'
				for key,value in self.styles['top_level']['nodes'].iteritems(): 
					print ('    %s=%s') % (key,value) 
				if self.styles['top_level']['edges']: print '  Edge Attributes:'
				for key,value in self.styles['top_level']['edges'].iteritems(): 
					print ('    %s=%s') % (key,value) 
			for subg_k,subg_v in self.styles.iteritems():
				if subg_k == 'top_level': continue
				print subg_k + ':' 
				if subg_v['nodes']: print '  Node Attributes:'
				for key,value in subg_v['nodes'].iteritems(): 
					print ('    %s=%s') % (key,value) 
				if subg_v['edges']: print '  Edge Attributes:'
				for key,value in subg_v['edges'].iteritems(): 
					print ('    %s=%s') % (key,value) 
		else:
			print "***Incorrect ls option***"
		print 
			

	def do_draw(self,line):
		"""Output graph in .dot and .pdf format.\n"""
		draw(self.graph, self.styles, f_out_dot, f_out_pdf)
	
	def auto_false(self):
		self.auto = False 
    
	def do_EOF(self, line):
		return True

if __name__ == '__main__':
	c = GraphCMD()
	c.auto_false()
	c.load_p(sys.argv[1], sys.argv[2])
	c.cmdloop()
	
