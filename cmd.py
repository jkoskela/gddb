import cmd
import pickle

class GraphCMD(cmd.Cmd):
	"""Command line processor for manipulating output of graphdlv."""
	def load(self,graph)
		
    
	def set(self, line):
		"""set [subgraph] [attribute] [value]"""
		print "hello"
    
	def do_EOF(self, line):
		return True

if __name__ == '__main__':
	GraphCMD.cmdloop()
	GraphCMD.load(sys.argv[1])
	
