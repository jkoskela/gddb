import re
import sys
import pickle
#debug
import pprint


def main():
	if(len(sys.argv) < 3):
		print('usage: python parse.py [parse map] [dlv output] \n')
		sys.exit(1)
	f_out = open('graph_dlv.dot', 'w')
	#f_in = open(sys.argv[1]).readlines()
	#rules = pickle.load(open('parse_map.p', 'rb'))
	rules = pickle.load(open(sys.argv[1], 'rb'))
	
	s = open(sys.argv[2]).read()
	f_out.write('digraph{')

	
	'''
	styles                =  dict()            #Graphviz styles
	styles['edge']        = '[color="blue"]'
	styles['anc']         = '[color="red"]'
	styles['com_anc']     = '[color="yellow"]'
	styles['aux']         = '[shape=point]'
	styles['not_lca']     = '[color="purple"]'
	styles['not not_lca'] = '[color="green"]'
	styles['lca']         = '[color="orange"]'
	'''
	
	#dot(rules, f_out, s, styles)
	sub = subgraph(rules, s)

	f_out.write('}')
	f_out.close()


#Creates edge tuples and nodes from aux firings and places into subgraph map
def subgraph(rules, s):
	
	aux_count = 0
	m = re.findall('(aux[^(]*)\(([^)]*)\)', s)
	subg = dict()
	subg['aux'] = set() 
	for g in m:
		aux_count = aux_count + 1
		aux = g[0]
		aux_terms = g[1].split(',')
		p_list = rules[aux]
		aux_atom = '%s(%s)' % (aux, g[1])
		subg['aux'].add(aux_atom)

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
		subg[head]['edges'].append('"%s" -> "%s"' % (aux_atom, atom))
		
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
			subg[pred]['edges'].append('"%s" -> "%s"' % (atom, aux_atom))

	pp = pprint.PrettyPrinter(indent=4)
	pp.pprint(subg)	

	print('There were %s firings.' % aux_count)
	return subg;
	

#Outputs .dot file from aux firings data
def dot(rules, f_out, s, styles):
	
	#aux_count = dict()
	aux_count = 0

	m = re.findall('(aux[^(]*)\(([^)]*)\)', s)
	for g in m:
		aux_count = aux_count + 1
		aux = g[0]
		aux_terms = g[1].split(',')
		p_list = rules[aux]
		f_out.write('"%s(%s)" %s\n' % (aux, g[1], styles['aux']))

		# Aux -> Head
		p = p_list[0][0]
		term_i = p_list[0][1]
		f_out.write('"%s(%s)" -> "%s(' % (aux, g[1], p))
		for i in term_i:
			f_out.write(aux_terms[i] + ',')
		f_out.write(')" %s\n' % styles[p])
			
		# Body -> Aux
		for t in p_list[1:]:
			p = t[0]
			term_i = t[1]
			f_out.write('"%s(' % p)
			for i in term_i:
				f_out.write(aux_terms[i] + ',')
			if styles[p]:
				f_out.write(')" -> "%s(%s)" %s\n' % (aux, g[1], styles[p]))
			else:
				f_out.write(')" -> "%s(%s)" %s\n' % (aux, g[1]))
				
	print('There were %s firings.' % aux_count)


if __name__=="__main__":
	main()
