#======================================================================
# GDDB: Graphical Datalog Debugger 
# Author: Jade Koskela <jtkoskela@ucdavis.edu>
# http://github.com/jkoskela/gddb
# Class definitions for GDDB Parser
#======================================================================
import re

class Atom():
   '''Represents an atom in Datalog'''
   anon_index = 0
   def __init__(self, predicate, args):
      self.predicate = predicate
      self.args = args 
      self.args_list = re.split('\W+', args)     

      # Replace anonymous variables, which are not allowed in auxiliary rules. 
      for i, e in enumerate(self.args_list):      
         if e == '_':
            self.args_list[i] = 'ANON' + str(Atom.anon_index)
            self.anon_index += 1
      self.args = ','.join(self.args_list)     

   def __str__(self):
      return "%s(%s)" % (self.predicate, self.args)


class Rule:
   '''
   Represents a rule in Datalog.
   Creates mapping from aux atom to the head and body of the associated rule 
   For instance the rule: anc(X,Z) :- anc(X,Y), anc(Y,Z).
   Will generate rule: {anc_aux_index:[('anc', [0, 2]), ('anc', [0, 1]), ('anc', [1, 2])]}
   '''
   def __init__(self, head, body, index):
      self.head, self.body = head, body   
      self.aux_args = set(head.args_list)
      self.aux_pred = '%s%s%s%s' % ('aux_', head.predicate, '_', index)  
      self.arg_map = dict()

      # The auxiliary predicate is a function of all arguments in the original body.
      for atom in self.body:     
         self.aux_args = self.aux_args.union(set(atom.args_list))  
      self.aux_str = '%s(%s)' % (self.aux_pred, ','.join(self.aux_args)) 

      for i, elem in enumerate(self.aux_args):  # Map each argument to a position
         self.arg_map[elem] = i                                     

      t_rule = [(head.predicate, self.str_to_index(head.args))]  #Create list of predicate and mappings
      for atom in self.body:
         t_rule.append((atom.predicate, self.str_to_index(atom.args)))
      self.rule_map = {self.aux_pred: t_rule}                    

   def str_to_index(self, s):
      '''Transforms a string such as "(Z,X,Y)" into a list of indexes into arg list of the of the aux predicate.'''
      return [self.arg_map[a] for a in s.split(',')] 

   def __str__(self):
      ''' Returns string representation of rule with auxliary predicate.'''
      r1 = '%s :- %s.' % (self.head, self.aux_str)
      r2 = '%s :- %s.' % (self.aux_str, ','.join(map(str,self.body)))
      return '%s\n%s' % (r1, r2)
