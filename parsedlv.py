#------------------------------------------------------------------------------------------
# parsedlv.py
#
# tokenizer for the Datalog language
# Adapted from parseddl.py by Eric Gribkoff
#------------------------------------------------------------------------------------------
import sys
import ply.lex as lex
import pickle
import re

#------------------------------------------------------------------------------------------
# Class Definitions

class Atom:
	def __init__(self, predicate, terms):
		self.predicate = predicate
		self.terms = terms
		self.terms_list = re.split('\W+', terms)
	def __str__(self):
		return self.predicate + '(' + self.terms + ')'

# Creates mapping from firing atom to the head and body of the associated clause 
class Clause:
	def __init__(self, head, body, index):
		self.head, self.body = head, body   
		self.aux_terms = set(head.terms_list)
		self.aux_key = '%s%s%s%s' % ('aux_', head.predicate, '_', index)
		self.aux_str = self.aux_key + '('
		self.term_map = dict()

		for atom in self.body:
			self.aux_terms = self.aux_terms.union(set(atom.terms_list))
		for i, elem in enumerate(self.aux_terms):
			self.term_map[elem] = i
			self.aux_str = self.aux_str + elem + ','
		self.aux_str = self.aux_str.rstrip(',') + ')'
		t_clause = [(head.predicate, self.str_to_index(head.terms))]
		for atom in self.body:
			t_clause.append((atom.predicate, self.str_to_index(atom.terms)))
		self.clause_map = {self.aux_key: t_clause}

	# For a given atom such as aux(X,Y,Z)
	# Transforms a string such as '(Z,X,Y)' into a list of indexes into terms of the atom(2, 0, 1) 
	def str_to_index(self, s):
		s = s.split(',')
		l = [] 
		for st in s:
			l.append(self.term_map[st])
		return l		

	def __str__(self):
		st = '%s :- %s. \n%s :- ' % (self.head, self.aux_str, self.aux_str)
		for atom in self.body[:-1]:
			st += '%s,' % atom
		st += self.body[-1].__str__() + '.'
		return st

#------------------------------------------------------------------------------------------
# Tokenizer

# List of reserved names. Checked by the t_ID function
reserved = {'not' : 'NOT'}

# List of token names.   This is always required
tokens = [
    'ID',
    'COLONDASH',
    'LPAREN',
    'RPAREN',
    'COMMA',
    'PERIOD',
] + list(reserved.values()) # Include reserved words with tokens

# Regular expression rules for simple tokens
#t_STRING     = r'\".*\"'
t_COLONDASH  = r':-'
t_PERIOD     = r'\.'
t_COMMA      = r','
t_LPAREN     = r'\('
t_RPAREN     = r'\)'

# A regular expression rule with some action code
def t_ID(t):
    r'([_A-Za-z0-9]+)'
    t.type = reserved.get(t.value, 'ID') # Lookup value in reserved
                                         # Second param 'ID' specifies
                                         # default.
    return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

#Comments
def t_comment(t):
    r'%.*'
    pass


#------------------------------------------------------------------------------------------
# Parser

lexer = lex.lex()
import ply.yacc as yacc
clause_map = dict()
aux_index = 0

# Get the token map from the lexer.  This is required.
# from calclex import tokens

def p_program(p):
    'program : clause_plural'
    p[0] = p[1]
    print p[0]

def p_clause_plural(p):
    'clause_plural : clause_single clause_plural'
    p[0] = p[1] + '\n' + p[2]

def p_clause_plural_one(p):
    'clause_plural : clause_single'
    p[0] = p[1]

def p_clause_single(p):
    'clause_single : atom COLONDASH atoms PERIOD'
    global aux_index
    c = Clause(p[1], p[3], aux_index)
    aux_index = aux_index + 1
    clause_map.update(c.clause_map)
    p[0] = c.__str__()

def p_terms_plural(p):
    'terms : term COMMA terms'
    p[0] = p[1] + p[2] + p[3] 

def p_terms_one(p):
    'terms : term'
    p[0] = p[1]

def p_term_id(p):
    'term : ID'
    p[0] = p[1]

def p_atoms_plural(p):
    'atoms : atom COMMA atoms'
    temp = [p[1]]	
    temp.extend(p[3])
    p[0] = temp

def p_atoms_not_one(p):
    'atoms : NOT atom'
    p[2].predicate = 'not ' + p[2].predicate
    p[0] = [p[2]]

def p_atoms_one(p):
    'atoms : atom'
    p[0] = [p[1]]

def p_atom(p):
    'atom : ID LPAREN terms RPAREN'
    p[0] = Atom(p[1],p[3])

def p_error(p):
    print "Syntax error in input!"

# Build the parser
parser = yacc.yacc()
data = open(sys.argv[1]).read()
result = parser.parse(data)
pickle.dump(clause_map, open('parse_map.p', 'wb'))



