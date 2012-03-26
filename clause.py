#----------------------------------------------------------------------
# Class definitions for GDDB Parser 
# Created by: Jade Koskela
# jtkoskela@ucdavis.edu
#----------------------------------------------------------------------

import re

# Represents an atom in the datalog language.
class Atom():
    anon_index = 0
    def __init__(self, predicate, terms):
        self.predicate = predicate
        self.terms = terms
        self.terms_list = re.split('\W+', terms)     #Create list of arguments

	#Replace anonymous variables. Anon variables cannot be used in aux predicates.
        for i, e in enumerate(self.terms_list):      
            if e == '_':
                self.terms_list[i] = 'ANON' + str(Atom.anon_index)
                Atom.anon_index += 1
        self.terms = ','.join(self.terms_list)    #Create argument string with new anon vars

    def __str__(self):
        return self.predicate + '(' + self.terms + ')'


# Represents a clause in the datalog language.
# Creates mapping from aux atom to the head and body of the associated clause 
# For instance the rule: anc(X,Z) :- anc(X,Y), anc(Y,Z).
# Will generate clause: {anc_aux_index:[('anc', [0, 2]), ('anc', [0, 1]), ('anc', [1, 2])]}
class Clause:
    def __init__(self, head, body, index):
        self.head, self.body = head, body   
        self.aux_terms = set(head.terms_list)
        self.aux_key = '%s%s%s%s' % ('aux_', head.predicate, '_', index)  #Create auxiliary predicate
        self.aux_str = self.aux_key + '('
        self.term_map = dict()

        for atom in self.body:        #The auxiliary predicate is a relationship between all the terms/arguments in the original clause
            self.aux_terms = self.aux_terms.union(set(atom.terms_list))    #Add all terms in the clause to the set and create aux atom
        self.aux_str = self.aux_str + ','.join(self.aux_terms) + ')'

        for i, elem in enumerate(self.aux_terms):                          #Map each term to a position in the argument to the aux atom
            self.term_map[elem] = i                                     

        t_clause = [(head.predicate, self.str_to_index(head.terms))]    #Create list of predicate and mappings
        for atom in self.body:
            t_clause.append((atom.predicate, self.str_to_index(atom.terms)))
        self.clause_map = {self.aux_key: t_clause}                      #Single entry dict 


    # For a given atom such as aux(X,Y,Z)
    # Transforms a string such as '(Z,X,Y)' into a list of indexes into argument list of the of the aux predicate
    def str_to_index(self, s):
        s = s.split(',')
        l = [] 
        for st in s:
            l.append(self.term_map[st])
        return l        


    # Returns string representaion of clause with aux predicate inserted. Printed on two lines.
    def __str__(self):
        st = '%s :- %s. \n%s :- ' % (self.head, self.aux_str, self.aux_str)
        for atom in self.body[:-1]:
            st += '%s,' % atom
        st += self.body[-1].__str__() + '.'
        return st



