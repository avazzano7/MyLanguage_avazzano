from sly import Lexer, Parser
from colorama import Fore, Style
import copy

DEBUG = True

def printCyan(s):
	print(Fore.CYAN, end='')
	print(s)
	print(Style.RESET_ALL, end='')

def printBlue(s):
	print(Fore.BLUE, end='')
	print(s)
	print(Style.RESET_ALL, end='')

def printGreen(s):
	print(Fore.GREEN, end='')
	print(s)
	print(Style.RESET_ALL, end='')

def printMagenta(s):
	print(Fore.MAGENTA, end='')
	print(s)
	print(Style.RESET_ALL, end='')

def printYellow(s):
	print(Fore.YELLOW, end='')
	print(s)
	print(Style.RESET_ALL, end='')

def apply(operation, lhs, rhs):
	if operation == '+':
		return lhs + rhs
	elif operation == '-':
		return lhs - rhs
	elif operation == '*':
		return lhs * rhs
	elif operation == '/':
		return lhs // rhs
	elif operation == '==':
		return lhs == rhs
	elif operation == '!=':
		return lhs != rhs
	elif operation == '>':
		return lhs > rhs
	elif operation == '>=':
		return lhs >= rhs
	elif operation == '<':
		return lhs < rhs
	elif operation == '<=':
		return lhs <= rhs


class Value:
	# Stores values of variables and expressions
	def __init__(self, dataType, components):
		# Components is a dictionary of the values, expressions or other
		# data needed to define a value
		self.dataType = dataType
		
		if DEBUG: printMagenta(f'Value construction {dataType} {repr(components)}')
		
		if dataType in ['int', 'bool']:
			self.value = components['value']
		elif dataType == 'expr':
			self.expression = components['expression']
		elif dataType == 'expr_list':
			self.expressions = components['expressions']
		elif dataType == 'function':
			self.variable = components['variable']
			self.result = components['result']
		elif dataType == 'operation':
			self.lhs = components['lhs']
			self.operation = components['operation']
			self.rhs = components['rhs']
		elif dataType == 'id':
			self.id = components['id']
		elif dataType == 'conditional':
			self.condition = components['condition']
			self.then_clause = components['then_clause']
			self.else_clause = components['else_clause']
		elif dataType == 'list':
			self.elements = components['elements']
		else:
			print(f'ERROR: constructor fall through {dataType} {repr(components)}')
			
		if DEBUG: printMagenta(f'Constructor result {repr(self)}')
			
	def replace(self, variable, value, valueLookup):
		# Make a copy and perform appropriate substitutions
		if self.dataType in ['int','bool']:
			v = Value(self.dataType, {'value': self.value})
		elif self.dataType == 'expr':
			v = Value('expr', {'expr': self.expr.replace(variable, value, valueLookup)})
		elif self.dataType == 'expr_list':
			newExpressions = [e.replace(variable, value, valueLookup) for e in self.expressions]
			v = Value('expr_list', {'expressions': newExpressions})
		elif self.dataType == 'function':
			v = Value('function', {'variable': str(self.variable), 'result': self.result.replace(variable, value, valueLookup)})
		elif self.dataType == 'operation':
			v = Value('operation', {'lhs': self.lhs.replace(variable, value, valueLookup), 'operation': self.operation, 'rhs': self.rhs.replace(variable, value, valueLookup)})
		elif self.dataType == 'id':
			if self.id == variable:
				v = copy.deepcopy(value)
			else:
				v = Value('id', {'id': self.id})
		elif self.dataType == 'conditional':
			condition = self.condition.replace(variable, value, valueLookup).simplify(valueLookup)
			if condition.dataType == 'bool':
				if condition.value:
					v = self.then_clause.replace(variable, value, valueLookup).simplify(valueLookup)
				else:
					v = self.else_clause.replace(variable, value, valueLookup).simplify(valueLookup)
			else:
				then_clause = self.then_clause.replace(variable, value, valueLookup)
				else_clause = self.else_clause.replace(variable, value, valueLookup)
				v = Value('conditional', {'condition': condition, 'then_clause': then_clause, 'else_clause': else_clause})
		elif self.dataType == 'list':			
			newElements = [e.replace(variable, value, valueLookup) for e in self.elements]
			v = Value('list', {'elements': newElements})
		else:
			print('ERROR:  fall through in replace')
		
		if DEBUG and str(self) != str(v): printCyan(f'Replace {variable} in {repr(self)} with {repr(value)} to get {repr(v)}') 
		return v
		
	def simplify(self, valueLookup):
		if DEBUG:
			printYellow(f'Simplifying {repr(self)}')
			
		if self.dataType in ['int','bool']:
			v = Value(self.dataType, {'value': self.value})
		elif self.dataType == 'expr':
			v = Value('expr', {'expr': self.expression.simplify(valueLookup)})
		elif self.dataType == 'expr_list':
			newExpressions = [] # [e.simplify() for e in self.expressions]
			for i, e in enumerate(self.expressions):
				newExpressions.append(e.simplify(valueLookup))
			i = 0
			while i < len(newExpressions)-1:				
				if newExpressions[i].dataType == 'function' and newExpressions[i+1].dataType in ['int','bool']:
					prefix = newExpressions[:i]
					suffix = newExpressions[i+2:]
					clause = newExpressions[i].result.replace(newExpressions[i].variable, newExpressions[i+1], valueLookup)
					newExpressions = prefix + [clause] + suffix
				elif newExpressions[i].dataType == 'id' and newExpressions[i].id in valueLookup and valueLookup[newExpressions[i].id].dataType == 'function' and newExpressions[i+1].dataType in ['int','bool']:
					function = valueLookup[newExpressions[i].id]
					variable = function.variable
					result = function.result
					prefix = newExpressions[:i]
					suffix = newExpressions[i+2:]
					clause = result.replace(variable, newExpressions[i+1], valueLookup)
					newExpressions = prefix + [clause] + suffix
				else:
					i += 1
			if len(newExpressions) == 1:
				v = newExpressions[0].simplify(valueLookup)
			else:
				v = Value('expr_list', {'expressions': newExpressions})
		elif self.dataType == 'function':
			v = Value('function', {'variable': str(self.variable), 'result': self.result.simplify(valueLookup)})
		elif self.dataType == 'operation':
			if self.lhs.dataType == self.rhs.dataType and self.lhs.dataType in ['int', 'bool']:
				result = apply(self.operation, self.lhs.value, self.rhs.value)
				if self.operation in ['+', '-', '/', '*']:
					v = Value(self.lhs.dataType, {'value': result})
				else:
					v = Value('bool', {'value': result})
			else:
				v = Value('operation', {'lhs': self.lhs.simplify(valueLookup), 'operation': self.operation, 'rhs': self.rhs.simplify(valueLookup)})
		elif self.dataType == 'id':
			v = Value('id', {'id': self.id})
		elif self.dataType == 'conditional':
			condition = self.condition.simplify(valueLookup)
			if condition.dataType == 'bool':
				if condition.value:
					v = self.then_clause.simplify(valueLookup)
				else:
					v = self.else_clause.simplify(valueLookup)
			else:
				v = Value('conditional', {'condition': condition, 'then_clause': self.then_clause, 'else_clause': self.else_clause})
		elif self.dataType == 'list':			
			newElements = [e.simplify(valueLookup) for e in self.elements]
			v = Value('list', {'elements': newElements})
		else:
			print('ERROR:  fall through in simplify')
			
		if DEBUG: printYellow(f'Simplified {repr(self)} to {repr(v)}') 
		return v
		
	def __str__(self):
		if self.dataType in ['int', 'bool']:
			s = str(self.value)
		elif self.dataType == 'expr':
			s = str(self.expr)
		elif self.dataType == 'expr_list':
			s = '(' + ' . '.join(str(e) for e in self.expressions) + ')'
		elif self.dataType == 'operation':
			s = ' '.join(['(', str(self.lhs), self.operation, str(self.rhs), ')'])
		elif self.dataType == 'id':
			s = self.id		
		elif self.dataType == 'conditional':
			s = f'if {self.condition} then {self.then_clause} else {self.else_clause}'
		elif self.dataType == 'function':
			s = f'\\ {self.variable} => {(self.result)}'
		elif self.dataType == 'list':
			s = f'[ {", ".join(str(e) for e in self.elements)} ]'
			
		while s.startswith('((') and s.endswith('))'):
			s = s[1:-1]
			
		return s
		
	def __repr__(self):
		if self.dataType == 'int':
			return f'Value(int, {self.value})'
		elif self.dataType == 'bool':
			return f'Value(bool, {self.value})'
		elif self.dataType == 'expr':
			return f'Value(expr, {repr(self.expr)})'
		elif self.dataType == 'expr_list':
			return f'Value(expr_list, [{", ".join(repr(e) for e in self.expressions)}])'
		elif self.dataType == 'operation':
			return f'Value(operation, {repr(self.lhs)}, {self.operation}, {repr(self.rhs)})'
		elif self.dataType == 'id':
			return f'Value(id, {self.id})'
		elif self.dataType == 'conditional':
			return f'Value(conditional, {repr(self.condition)}, {repr(self.then_clause)}, {repr(self.else_clause)})'
		elif self.dataType == 'function':
			return f'Value(function, {self.variable}, {repr(self.result)})'
		elif self.dataType == 'list':
			return f'[ {", ".join(repr(e) for e in self.elements)} ]'

class MyLexer(Lexer):
	# Set of token names.   This is always required
	tokens = { NUMBER, ID,
			   ADD_OP, MULT_OP, ASSIGN,
			   LPAREN, RPAREN, SEP, ARROW, LAMBDA,
			   EQUAL_OP, COMPARE_OP,
			   PRINT, DUMP,
			   IF, THEN, ELSE, ENDIF,
			   LBRACKET, RBRACKET, COMMA,
			   HEAD, TAIL }

	# String containing ignored characters
	ignore = ' \t'

	# Regular expression rules for tokens
	ASSIGN  = r':='
	LPAREN	= r'\('
	RPAREN	= r'\)'
	SEP		= r'\.'
	ARROW	= r'=>'
	LAMBDA	= r'\\'
	ADD_OP	= r'\+|-'
	MULT_OP = r'\*|/'
	EQUAL_OP	= r'==|!='
	COMPARE_OP	= r'>=|<=|>|<'
	LBRACKET	= r'\['
	RBRACKET	= r'\]'
	COMMA	= r','

	@_(r'\d+')
	def NUMBER(self, t):
		t.value = int(t.value)
		return t

	# Identifiers and keywords
	ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
	
	ID['print'] = PRINT
	ID['dump'] = DUMP
	ID['if'] = IF
	ID['else'] = ELSE
	ID['then'] = THEN
	ID['endif'] = ENDIF
	ID['head'] = HEAD
	ID['tail'] = TAIL

	ignore_comment = r'\#.*'

	# Line number tracking
	@_(r'\n+')
	def ignore_newline(self, t):
		self.lineno += t.value.count('\n')

	def error(self, t):
		print('Line %d: Bad character %r' % (self.lineno, t.value[0]))
		self.index += 1

class MyParser(Parser):
	def __init__(self):
		Parser.__init__(self)
		self._values = {}
		
	debugfile = 'parser.out'
	
	# Get the token list from the lexer (required)
	tokens = MyLexer.tokens

	# Grammar rules and actions
	@_('ID ASSIGN expr_list')
	def statement(self, p):
		printGreen(f'Rule: statement => ID ASSIGN expr_list ({p.ID}, {repr(p.expr_list)})')
		self._values[p.ID] = p.expr_list
		
	@_('PRINT expr_list')
	def statement(self, p):
		s = str(p.expr_list)
		while s.startswith('(') and s.endswith(')'):
			s = s[1:-1]
		print(s)
		
	@_('DUMP')
	def statement(self, p):
		for k, v in self._values.items():
			print(f'{k}: {repr(v)}')
			
	@_('expr SEP expr_list')
	def expr_list(self, p):
		if p.expr_list.dataType == 'expr_list':
			v = Value('expr_list', {'expressions': [p.expr] + p.expr_list.expressions})			
		else:
			v = Value('expr_list', {'expressions': [p.expr, p.expr_list]})
		v = v.simplify(self._values)
		
		if DEBUG: printGreen(f'Rule: expr_list -> expr SEP expr_list ({repr(v)})')
		return v
		
	@_('expr')
	def expr_list(self, p):
		if DEBUG: printGreen(f'Rule: expr_list -> expr ({p.expr})')
		return p.expr
		
	@_('LAMBDA ID ARROW expr_list')
	def expr(self, p):
		v = Value('function', {'variable': p.ID, 'result': p.expr_list})
		
		if DEBUG: printGreen(f'Rule: expr -> LAMBDA ID ARROW expr_list ({repr(v)})')
		return v
	
	@_('expr ADD_OP term')
	def expr(self, p):
		if p.expr.dataType == 'int' and p.term.dataType == 'int':
			result = apply(p[1], p.expr.value, p.term.value)
			v = Value('int', {'value': result})
		else:
			v = Value('operation', {'lhs': p.expr, 'operation': p[1], 'rhs': p.term})
		
		if DEBUG: printGreen(f'Rule: expr -> expr ADD_OP term ({repr(v)})')
		return v

	@_('term')
	def expr(self, p):
		if DEBUG: printGreen(f'Rule: expr -> term ({p.term})')
		return p.term
	
	@_('IF expr THEN expr ELSE expr ENDIF')
	def expr(self, p):
		if p.expr0.dataType == 'bool':
			if p.expr0.value:
				v = p.expr1
			else:
				v = p.expr2
		else:
			v = Value('conditional', {'condition': p.expr0, 'then_clause': p.expr1, 'else_clause': p.expr2})

		if DEBUG: printGreen(f'Rule: expr -> IF expr THEN expr ELSE expr ENDIF ({repr(v)})')
		return v
			
	@_('term EQUAL_OP term')
	def expr(self, p):
		if p.term0.dataType == p.term1.dataType and p.term0.dataType in ['int','bool']:
			result = apply(p[1], p.term0.value, p.term1.value)
			v = Value('bool', {'value': result})
		else:
			v = Value('operation', {'lhs': p.term0, 'operation': p[1], 'rhs': p.term1})
				
		if DEBUG: printGreen(f'Rule: expr -> term EQUAL_OP term ({repr(v)})')
		return v
		
	@_('term COMPARE_OP term')
	def expr(self, p):
		if p.term0.dataType == p.term1.dataType == 'int':
			result = apply(p[1], p.term0.value, p.term1.value)
			v = Value('bool', {'value': result})
		else:
			v = Value('operation', {'lhs': p.term0, 'operation': p[1], 'rhs': p.term1})
		
		if DEBUG: printGreen(f'Rule: expr -> term COMPARE_OP term ({repr(v)})')
		return v

	@_('term MULT_OP factor')
	def term(self, p):
		if p.term.dataType == p.factor.dataType == 'int':
			result = apply(p[1], p.term.value, p.factor.value)
			v = Value('int', {'value': result})
		else:
			v = Value('operation', {'lhs': p.term, 'operation': p[1], 'rhs': p.factor})
		
		if DEBUG: printGreen(f'expr -> term MULT_OP term ({repr(v)})')
		return v

	@_('factor')
	def term(self, p):
		if DEBUG: printGreen(f'Rule: term -> factor ({repr(p.factor)})')
		return p.factor

	@_('NUMBER')
	def factor(self, p):
		if DEBUG: printGreen(f'Rule: factor -> NUMBER ({p.NUMBER})')
		return Value('int', {'value': p.NUMBER})
		
	@_('ID')
	def factor(self, p):
		if p.ID in self._values:
			if DEBUG: printGreen(f'Rule: id -> factor ({p.ID}, {self._values[p.ID]})')
			return self._values[p.ID]
		else:
			if DEBUG: printGreen(f'Rule: id -> factor ({p.ID})')
			return Value('id', {'id': p.ID})

	@_('LPAREN expr_list RPAREN')
	def factor(self, p):
		if DEBUG: printGreen(f'Rule: LPAREN expr_list RPAREN ({p.expr_list})')
		return p.expr_list
		
	@_('list')
	def expr(self, p):
		if DEBUG: printGreen(f'Rule: list -> expr ({repr(p.list)})')
		return p.list
		
	@_('LBRACKET RBRACKET')
	def list(self, p):
		if DEBUG: printGreen('Rule: LBRACKET RBRACKET -> list ([])')
		return Value('list', {'elements': []})
		
	@_('LBRACKET comma_sep_list RBRACKET')
	def list(self, p):
		if DEBUG: printGreen(f'Rule: LBRACKET comma_sep_list RBRACKET -> list ({repr(p.comma_sep_list)})')
		return p.comma_sep_list
		
	@_('expr')
	def comma_sep_list(self, p):
		if DEBUG: printGreen(f'Rule: expr -> comma_sep_list ([{repr(p.expr)}])')
		return Value('list', {'elements': [p.expr]})
		
	@_('expr COMMA comma_sep_list')
	def comma_sep_list(self, p):
		v = Value('list', {'elements': [p.expr] + p.comma_sep_list.elements})
		if DEBUG: printGreen(f'Rule: expr COMMA comma_sep_list -> comma_sep_list ({repr(v)})')
		return v
		
	@_('HEAD SEP list')
	def term(self, p):
		v = p.list.elements[0]
		if DEBUG: printGreen(f'Rule: HEAD list -> term ({repr(v)})')
		return v
		
	@_('TAIL SEP list')
	def term(self, p):
		v = Value('list', {'elements': p.list.elements[1:]})
		if DEBUG: printGreen(f'Rule: TAIL list -> term ({repr(v)})')
		return v

if __name__ == '__main__':
	lexer = MyLexer()
	parser = MyParser()

	while True:
		try:
			text = input('>> ')
			for t in lexer.tokenize(text):
				printBlue(t)
			result = parser.parse(lexer.tokenize(text))
		except EOFError:
			break

