#Programmer: Oscar Lewczuk / Barry Preston
#Class: CS5500 - Compilers
#Assignment: HW8 - Convertion of MIPL to Python
import re
import collections
import sys
import logging

Token = collections.namedtuple('Token', ['type', 'value', 'line'])

class Symbol:
	def __init__(self, name=None, classif=None, line=None, info=None):
		self.name = name
		self.classif = classif
		self.line = line
		self.info = info

token_specs = [
	('T_ASSIGN', r':='),
	('T_MULT', r'[*]'),
    ('T_INTCONST', r'[+-]?[0-9]+'),
	('T_PLUS', r'[+]'),
	('T_MINUS', r'-'),
	('T_DIV', r'div(?!\w)'),
	('T_AND', r'and(?!\w)'),
	('T_OR', r'or'),
	('T_NOT', r'not'),
	('T_NE', r'<>'),
	('T_LE', r'<='),
	('T_GE', r'>='),
	('T_LT', r'<'),
	('T_GT', r'>'),
	('T_EQ', r'='),
	('T_VAR', r'var(?!\w)'),
	('T_ARRAY', r'array(?!\w)'),
	('T_OF', r'of(?!\w)'),
	('T_BOOL', r'boolean(?!\w)'),
	('T_CHAR', r'char(?!\w)'),
	('T_INT', r'integer(?!\w)'),
	('T_PROG', r'program(?!\w)'),
	('T_PROC', r'procedure(?!\w)'),
	('T_BEGIN', r'begin(?!\w)'),
	('T_END', r'end(?!\w)'),
	('T_WHILE', r'while(?!\w)'),
	('T_DO', r'do(?!\w)'),
	('T_IF', r'if(?!\w)'),
	('T_THEN', r'then(?!\w)'),
	('T_ELSE', r'else(?!\w)'),
	('T_READ', r'read(?!\w)'),
	('T_WRITE', r'write(?!\w)'),
	('T_TRUE', r'true(?!\w)'),
	('T_FALSE', r'false(?!\w)'),
	('T_LBRACK', r'\['),
	('T_RBRACK', r'\]'),
	('T_SCOLON', r';'),
	('T_COLON', r':'),
	('T_COMMENT', r'\(\*([^*]*|.*)\*\)'),
	('T_LPAREN', r'\('),
	('T_RPAREN', r'\)'),
	('T_COMMA', r','),
	('T_DOTDOT', r'\.\.'),
	('T_DOT', r'\.'),
	('T_CHARCONST', r'\'.\''),
	('T_INVALIDCHAR', r'(\'\')|\''),
	('T_WHITESPACE', r'[ \t]+'),
    ('T_NEWLINE', r'\n'),
	('T_IDENT', r'[A-Za-z_\d]+'),
    ('T_EOF', r'\Z'),
	('UNKNOWN', r'.')
]

tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specs)

#opens passed file name/output file name
filein = open(sys.argv[1])
fileout = open(sys.argv[2],'w')

depth = 0
def tabs():
	return '\t' * depth

code = filein.read()
line_num = 1
token = None


symbolStack = []

def getToken():
    global code, line_num, token
    while True:
        mo = re.match(tok_regex, code)
        kind = mo.lastgroup
        value = mo.group()
        code = code[len(value):]
        if kind == 'T_NEWLINE':
            line_num += 1
            continue
        if kind == 'T_WHITESPACE' or kind == 'T_COMMENT':
            if kind == 'T_COMMENT':
                line_num += value.count('\n')
            continue
        if kind == 'T_INVALIDCHAR':
            logging.warning('**** Invalid character constant: %s' % value)
            exit()
        if kind == 'T_INTCONST' and int(value) > 2147483647:
            logging.warning('**** Invalid integer constant: %s' % value)
            exit()
        token = Token(kind, value, line_num)
        if kind == 'T_EOF':
        	break
        logging.debug('TOKEN: %sLEXEME: %s' % ((token.type).ljust(12), token.value))
        break

def main():
	try:
		getToken()
		prog()
		if token.type != 'T_EOF':
			logging.error('Syntax error: unexpected chars at end of program!')
			exit()
		fileout.write('print(\'\\nProgram execution completed.\')\n')
	except SyntaxError as e:
		print('Line %d: syntax error' % token.line)
		exit()
	#print('---- Completed parsing ----')

#
# Symbol Table Management
#
def open_scope():
	logging.debug('>>> Entering new scope...')
	symbolStack.append({})

def close_scope():
	logging.debug('<<< Exiting scope...')
	symbolStack.pop()

def new_id(symbol):
	if symbol.classif == 'PROGRAM':
		logging.debug('+++ Adding %s to symbol table with type PROGRAM' % symbol.name)
	elif symbol.classif == 'PROCEDURE':
		logging.debug('+++ Adding %s to symbol table with type PROCEDURE' % symbol.name)
	elif symbol.classif == 'ARRAY':
		logging.debug('+++ Adding %s to symbol table with type ARRAY %d .. %d OF %s' % (symbol.name,symbol.info[0],symbol.info[1],symbol.info[2]))
	elif symbol.classif == 'INTEGER':
		logging.debug('+++ Adding %s to symbol table with type INTEGER' % symbol.name)
	elif symbol.classif == 'CHAR':
		logging.debug('+++ Adding %s to symbol table with type CHAR' % symbol.name)
	elif symbol.classif == 'BOOLEAN':
		logging.debug('+++ Adding %s to symbol table with type BOOLEAN' % symbol.name)
	
	if symbol.name in symbolStack[-1]:
		print('Line %d: Multiply defined identifier' % symbol.line)
		exit()
	else:
		symbolStack[-1][symbol.name] = symbol

def search_ident(name, line):
	for item in symbolStack:
		if name in item:
			return
	print('Line %d: Undefined identifier' % line)
	exit()

def get_ident(name):
	for item in symbolStack:
		if name in item:
			return item[name]
#
# End STM
#

#
# The start of the cancer :)
#
def prog():
	logging.debug('N_PROG -> N_PROGLBL T_IDENT T_SCOLON N_BLOCK T_DOT')
	proglbl()
	if token.type == 'T_IDENT':
		name = token.value
		getToken()
		if token.type == 'T_SCOLON':
			getToken()
			block(name, 'PROGRAM')
			if token.type == 'T_DOT':
				getToken()
			else:
				raise SyntaxError(token.line)
		else:
			raise SyntaxError(token.line)
	else:
		raise SyntaxError(token.line)

def proglbl():
	logging.debug('N_PROGLBL -> T_PROG')
	if token.type == 'T_PROG':
		getToken()
	else:
		raise SyntaxError(token.line)

def block(name, blocktype):
	logging.debug('N_BLOCK -> N_VARDECPART N_PROCDECPART N_STMTPART')
	open_scope()
	if blocktype == 'PROGRAM':
		new_id(Symbol(name, blocktype))
	#hw8:print
	fileout.write('%s#Variable Declaration\n' % tabs())
	vardecpart()
	#hw8:print
	fileout.write('\n%s#Procedure Declaration\n' % tabs())
	procdecpart()
	#hw8:print
	fileout.write('\n%s#Statement Declaration\n' % tabs())
	stmtpart()
	close_scope()

def vardecpart():
	if token.type == 'T_VAR':
		logging.debug('N_VARDECPART -> T_VAR N_VARDEC T_SCOLON N_VARDECLST')
		getToken()
		vardec()
		if token.type == 'T_SCOLON':
			getToken()
			vardeclst()
		else:
			raise SyntaxError(token.line)
	else:
		logging.debug('N_VARDECPART -> epsilon')

def vardeclst():
	if token.type == 'T_IDENT':
		vardec()
		if token.type == 'T_SCOLON':
			getToken()
			vardeclst()
		else:
			raise SyntaxError(token.line)
	else:
		logging.debug('N_VARDECLST -> epsilon')

def vardec():
	logging.debug('N_VARDEC -> N_IDENT N_IDENTLST T_COLON N_TYPE')
	idents = []
	temp = Symbol()
	temp.name,temp.line = ident()
	idents.append(temp)
	identlst(idents)
	if token.type == 'T_COLON':
		getToken()
		typeinfo = Type()
		for sym in idents:
			sym.classif = typeinfo[0]
			if typeinfo[0] == 'ARRAY':
				sym.info = [typeinfo[1],typeinfo[2],typeinfo[3]]
			new_id(sym)
			#hw8:arrayReferences (this is gross making array larger than it should)
			arrayornot = 'None' if typeinfo[0] != 'ARRAY' else '{}'
			fileout.write('%s%s = %s\n' % (tabs(), sym.name, arrayornot))
	else:
		raise SyntaxError(token.line)

#returns name/line
def ident():
	if token.type == 'T_IDENT':
		logging.debug('N_IDENT -> T_IDENT')
		name = token.value
		line = token.line
		getToken()
		return name,line
	else:
		raise SyntaxError(token.line)

#adds any idents to idents
def identlst(idents):
	if token.type == 'T_COMMA':
		logging.debug('N_IDENTLST -> T_COMMA N_IDENT N_IDENTLST')
		getToken()
		temp = Symbol()
		temp.name,temp.line = ident()
		idents.append(temp)
		identlst(idents)
	else:
		logging.debug('N_IDENTLST -> epsilon')

#returns type and any other info
def Type():
	if token.type == 'T_ARRAY':
		logging.debug('N_TYPE -> N_ARRAY')
		info = array()
		return ['ARRAY']+info
	else:
		logging.debug('N_TYPE -> N_SIMPLE')
		return [simple()]

#returns array info [start, end, basetype]
def array():
	if token.type == 'T_ARRAY':
		logging.debug('N_ARRAY -> T_ARRAY T_LBRACK N_IDXRANGE T_RBRACK T_OF N_SIMPLE')
		getToken()
		if token.type == 'T_LBRACK':
			getToken()
			idxs,idxe = idxrange()
			if idxs > idxe:
				print('Line %d: Start index must be less than or equal to end index of array' % token.line)
				exit()
			if token.type == 'T_RBRACK':
				getToken()
				if token.type == 'T_OF':
					getToken()
					symType = simple()
					return [idxs, idxe, symType]
				else:
					raise SyntaxError(token.line)
			else:
				raise SyntaxError(token.line)
		else:
			raise SyntaxError(token.line)
	else:
		raise SyntaxError(token.line)

#returns value
def idx():
	if token.type == 'T_INTCONST':
		logging.debug('N_IDX -> T_INTCONST')
		temp = int(token.value)
		getToken()
		return temp
	else:
		raise SyntaxError(token.line)

#returns range for idx [start, end]
def idxrange():
	logging.debug('N_IDXRANGE -> N_IDX T_DOTDOT N_IDX')
	t1 = idx()
	if token.type == 'T_DOTDOT':
		getToken()
		t2 = idx()
		return [t1, t2]
	else:
		raise SyntaxError(token.line)

#returns the basetype
def simple():
	if token.type in ['T_INT', 'T_CHAR', 'T_BOOL']:
		logging.debug('N_SIMPLE -> %s' % token.type)
		temp = ''
		if token.type == 'T_INT':
			temp = 'INTEGER'
		elif token.type == 'T_CHAR':
			temp = 'CHAR'
		else:
			temp = 'BOOLEAN'
		getToken()
		return temp
	else:
		raise SyntaxError(token.line)

def procdecpart():
	if token.type == 'T_PROC':
		logging.debug('N_PROCDECPART -> N_PROCDEC T_SCOLON N_PROCDECPART')
		procdec()
		if token.type == 'T_SCOLON':
			getToken()
			procdecpart()
		else:
			raise SyntaxError(token.line)
	else:
		logging.debug('N_PROCDECPART -> epsilon')

def procdec():
	logging.debug('N_PROCDEC -> N_PROCHDR N_BLOCK')
	global depth
	prochdr()
	block(None,'PROCEDURE')
	depth -= 1
	fileout.write('\n')

def prochdr():
	logging.debug('N_PROCHDR -> T_PROC T_IDENT T_SCOLON')
	global depth
	if token.type == 'T_PROC':
		getToken()
		if token.type == 'T_IDENT':
			new_id(Symbol(token.value, 'PROCEDURE', token.line))
			fileout.write('def %s():\n' % token.value)
			depth += 1
			getToken()
			if token.type == 'T_SCOLON':
				getToken()
			else:
				raise SyntaxError(token.line)
		else:
			raise SyntaxError(token.line)
	else:
		raise SyntaxError(token.line)

def stmtpart():
	logging.debug('N_STMTPART -> N_COMPOUND')
	compound()

def compound():
	logging.debug('N_COMPOUND -> T_BEGIN N_STMT N_STMTLST T_END')
	if token.type == 'T_BEGIN':
		getToken()
		stmt()
		stmtlst()
		if token.type == 'T_END':
			getToken()
		else:
			raise SyntaxError(token.line)
	else:
		raise SyntaxError(token.line)

def stmtlst():
	if token.type == 'T_SCOLON':
		logging.debug('N_STMTLST -> T_SCOLON N_STMT N_STMTLST')
		getToken()
		stmt()
		stmtlst()
	else:
		logging.debug('N_STMTLST -> epsilon')

def stmt():
	if token.type == 'T_READ':
		logging.debug('N_STMT -> N_READ')
		read()
	elif token.type == 'T_WRITE':
		logging.debug('N_STMT -> N_WRITE')
		write()
	elif token.type == 'T_IF':
		logging.debug('N_STMT -> N_CONDITION')
		condition()
	elif token.type == 'T_WHILE':
		logging.debug('N_STMT -> N_WHILE')
		While()
	elif token.type == 'T_IDENT':
		search_ident(token.value, token.line)
		symbol = get_ident(token.value)
		if symbol.classif == 'PROCEDURE':
			logging.debug('N_STMT -> N_PROCSTMT')
			procstmt()
		else:
			logging.debug('N_STMT -> N_ASSIGN')
			assign()
	else:
		logging.debug('N_STMT -> N_COMPOUND')
		compound()

def assign():
	logging.debug('N_ASSIGN -> N_VARIABLE T_ASSIGN N_EXPR')
	fileout.write(tabs())
	var = variable()
	identType = var.classif
	line = token.line
	fileout.write(' = ')
	if identType == 'ARRAY':
		identType = var.info[2]
	if token.type == 'T_ASSIGN':
		getToken()
		retType = expr()
		fileout.write('\n')
		if retType == 'PROCEDURE':
			print('Line %d: Procedure/variable mismatch' % line)
			exit()
		if retType != identType:
			print('Line %d: Expression must be of same type as variable' % line)
			exit()
	else:
		raise SyntaxError(token.line)

def procstmt():
	procident()

def procident():
	if token.type == 'T_IDENT':
		search_ident(token.value, token.line)
		fileout.write('%s%s()\n' % (tabs(), token.value))
		getToken()
	else:
		raise SyntaxError(token.line)

def read():
	logging.debug('N_READ -> T_READ T_LPAREN N_INPUTVAR N_INPUTLST T_RPAREN')
	if token.type == 'T_READ':
		getToken()
		if token.type == 'T_LPAREN':
			getToken()
			fileout.write(tabs())
			varType = inputvar()
			if varType not in ['INTEGER', 'CHAR']:
				print('Line %d: Input variable must be of type integer or char' % token.line)
				exit()
			if varType == 'INTEGER':
				fileout.write(' = int(input())\n')
			else:
				fileout.write(' = input()\n')
			inputlst()
			if token.type == 'T_RPAREN':
				getToken()
			else:
				raise SyntaxError(token.line)
		else:
			raise SyntaxError(token.line)
	else:
		raise SyntaxError(token.line)

#returns possible list of types
def inputlst():
	if token.type == 'T_COMMA':
		logging.debug('N_INPUTLST -> T_COMMA N_INPUTVAR N_INPUTLST')
		getToken()
		fileout.write(tabs())
		varType = inputvar()
		if varType == 'INTEGER':
			fileout.write(' = int(input())\n')
		else:
			fileout.write(' = input()\n')
		inputlst()
	else:
		logging.debug('N_INPUTLST -> epsilon')

#returns type of variable
def inputvar():
	logging.debug('N_INPUTVAR -> N_VARIABLE')
	var = variable()
	return var.classif

def write():
	logging.debug('N_WRITE -> T_WRITE T_LPAREN N_OUTPUT N_OUTPUTLST T_RPAREN')
	if token.type == 'T_WRITE':
		fileout.write('%sprint('%tabs())
		getToken()
		if token.type == 'T_LPAREN':
			getToken()
			varType = output()
			if varType not in ['INTEGER', 'CHAR']:
				print('Line %d: Output expression must be of type integer or char' % token.line)
				exit()
			outputlst()
			if token.type == 'T_RPAREN':
				fileout.write(', end=\'\', sep=\'\')\n')
				getToken()
			else:
				raise SyntaxError(token.line)
		else:
			raise SyntaxError(token.line)
	else:
		raise SyntaxError(token.line)

def outputlst():
	if token.type == 'T_COMMA':
		logging.debug('N_OUTPUTLST -> T_COMMA N_OUTPUT N_OUTPUTLST')
		fileout.write(', ')
		getToken()
		output()
		outputlst()
	else:
		logging.debug('N_OUTPUTLST -> epsilon')

def output():
	logging.debug('N_OUTPUT -> N_EXPR')
	return expr()

def condition():
	logging.debug('N_CONDITION -> T_IF N_EXPR T_THEN N_STMT N_ELSEPART')
	if token.type == 'T_IF':
		fileout.write('%sif ' % tabs())
		getToken()
		retType = expr()
		if retType != 'BOOLEAN':
			print('Line %d: Expression must be of type boolean' % token.line)
			exit()
		if token.type == 'T_THEN':
			global depth
			fileout.write(':\n')
			depth += 1
			getToken()
			stmt()
			depth -= 1
			elsepart()
		else:
			raise SyntaxError(token.line)
	else:
		raise SyntaxError(token.line)

def elsepart():
	if token.type == 'T_ELSE':
		logging.debug('N_ELSEPART -> T_ELSE N_STMT')
		global depth
		fileout.write('%selse:\n' % tabs())
		depth += 1
		getToken()
		stmt()
		depth -= 1
	else:
		logging.debug('N_ELSEPART -> epsilon')

def While():
	logging.debug('N_WHILE -> T_WHILE N_EXPR T_DO N_STMT')
	global depth
	if token.type == 'T_WHILE':
		fileout.write('%swhile '% tabs())
		getToken()
		retType = expr()
		if retType != 'BOOLEAN':
			print('Line %d: Expression must be of type boolean' % token.line)
			exit()
		if token.type == 'T_DO':
			getToken()
			fileout.write(':\n')
			depth += 1
			stmt()
			depth -= 1
		else:
			raise SyntaxError(token.line)
	else:
		raise SyntaxError(token.line)

def expr():
	logging.debug('N_EXPR -> N_SIMPLEEXPR N_OPEXPR')
	simpType = simpleexpr()
	operType = opexpr()
	if operType != 'EPSILON':
		if simpType in ['CHAR', 'INTEGER', 'BOOLEAN'] and simpType != operType:
			print('Line %d: Expressions must both be int, or both char, or both boolean' % token.line)
			exit()
		return 'BOOLEAN'
	return simpType

def opexpr():
	if token.type in ['T_LT', 'T_LE', 'T_NE', 'T_EQ', 'T_GT', 'T_GE']:
		logging.debug('N_OPEXPR -> N_RELOP N_SIMPLEEXPR')
		relop()
		return simpleexpr()
	else:
		logging.debug('N_OPEXPR -> epsilon')
		return 'EPSILON'

def simpleexpr():
	logging.debug('N_SIMPLEEXPR -> N_TERM N_ADDOPLST')
	retType = term()
	addoplst()
	return retType

def addoplst():
	if token.type in ['T_PLUS', 'T_MINUS', 'T_OR']:
		logging.debug('N_ADDOPLST -> N_ADDOP N_TERM N_ADDOPLST')
		addop()
		retType = term()
		addoplst()
		return retType
	else:
		logging.debug('N_ADDOPLST -> epsilon')
		return 'EPSILON'

def term():
	logging.debug('N_TERM -> N_FACTOR N_MULTOPLST')
	retType = factor()
	multoplst()
	return retType

def multoplst():
	if token.type in ['T_MULT', 'T_DIV', 'T_AND']:
		logging.debug('N_MULTOPLST -> N_MULTOP N_FACTOR N_MULTOPLST')
		oper = multop()
		retType = factor()
		if oper in ['MULT', 'DIV'] and retType != 'INTEGER':
			print('Line %d: Expression must be of type integer' % token.line)
			exit()
		multoplst()
		return retType
	else:
		logging.debug('N_MULTOPLST -> epsilon')
		return 'EPSILON'

def factor():
	if token.type == 'T_LPAREN':
		logging.debug('N_FACTOR -> T_LPAREN N_EXPR T_RPAREN')
		getToken()
		retType = expr()
		if token.type == 'T_RPAREN':
			getToken()
			return retType
		else:
			raise SyntaxError(token.line)
	elif token.type == 'T_NOT':
		logging.debug('N_FACTOR -> T_NOT N_FACTOR')
		fileout.write('not ')
		getToken()
		retType = factor()
		if retType != 'BOOLEAN':
			print('Line %d: Expression must be of type boolean' % token.line)
			exit()
		return 'BOOLEAN'
	elif token.type in ['T_INTCONST', 'T_CHARCONST', 'T_TRUE', 'T_FALSE']:
		logging.debug('N_FACTOR -> N_CONST')
		return const()
	else:
		logging.debug('N_FACTOR -> N_SIGN N_VARIABLE')
		ret = sign()
		ident = variable()
		if ident.classif == 'ARRAY':
			return ident.info[2]
		if ident.classif != 'INTEGER' and ret != 'EPSILON':
			print('Line %d: Expression must be of type integer' % token.line)
			exit()
		return ident.classif

def sign():
	if token.type == 'T_PLUS':
		logging.debug('N_SIGN -> T_PLUS')
		getToken()
		return 'PLUS'
	elif token.type == 'T_MINUS':
		logging.debug('N_SIGN -> T_MINUS')
		getToken()
		return 'MINUS'
	else:
		logging.debug('N_SIGN -> epsilon')
		return 'EPSILON'

def addop():
	retType = token.type[2:]
	if token.type == 'T_PLUS':
		logging.debug('N_ADDOP -> T_PLUS')
		fileout.write(' + ')
		getToken()
		return retType
	elif token.type == 'T_MINUS':
		logging.debug('N_ADDOP -> T_MINUS')
		fileout.write(' - ')
		getToken()
		return retType
	elif token.type == 'T_OR':
		logging.debug('N_ADDOP -> T_OR')
		fileout.write(' or ')
		getToken()
		return retType
	else:
		raise SyntaxError(token.line)

def multop():
	retType = token.type[2:]
	if token.type == 'T_MULT':
		logging.debug('N_MULTOP -> T_MULT')
		fileout.write(' * ')
		getToken()
	elif token.type == 'T_DIV':
		logging.debug('N_MULTOP -> T_DIV')
		fileout.write(' // ')
		getToken()
	elif token.type == 'T_AND':
		logging.debug('N_MULTOP -> T_AND')
		fileout.write(' and ')
		getToken()
	else:
		raise SyntaxError(token.line)
	return retType

def relop():
	if token.type == 'T_LT':
		logging.debug('N_RELOP -> T_LT')
		fileout.write(' < ')
		getToken()
	elif token.type == 'T_LE':
		logging.debug('N_RELOP -> T_LE')
		fileout.write(' <= ')
		getToken()
	elif token.type == 'T_NE':
		logging.debug('N_RELOP -> T_NE')
		fileout.write(' != ')
		getToken()
	elif token.type == 'T_EQ':
		logging.debug('N_RELOP -> T_EQ')
		fileout.write(' == ')
		getToken()
	elif token.type == 'T_GT':
		logging.debug('N_RELOP -> T_GT')
		fileout.write(' > ')
		getToken()
	elif token.type == 'T_GE':
		logging.debug('N_RELOP -> T_GE')
		fileout.write(' >= ')
		getToken()
	else:
		raise SyntaxError(token.line)

#returns the ident symbol with its information
def variable():
	logging.debug('N_VARIABLE -> T_IDENT N_IDXVAR')
	if token.type == 'T_IDENT':
		search_ident(token.value, token.line)
		line = token.line
		ident = get_ident(token.value)
		fileout.write(ident.name)
		getToken()
		value = idxvar()
		if ident.classif == 'ARRAY' and value == 'EPSILON':
			print('Line %d: Array variable must be indexed' % line)
			exit()
		if ident.classif != 'ARRAY' and value != 'EPSILON':
			print('Line %d: Indexed variable must be of array type' % line)
			exit()
		return ident
	else:
		raise SyntaxError(token.line)

def idxvar():
	if token.type == 'T_LBRACK':
		logging.debug('N_IDXVAR -> T_LBRACK N_EXPR T_RBRACK')
		fileout.write('[')
		getToken()
		retType = expr()
		if retType == 'PROCEDURE':
			print('Line %d: Procedure/variable mismatch' % token.line)
			exit()
		if retType != 'INTEGER':
			print('Line %d: Index expression must be of type integer' % token.line)
			exit()
		if token.type == 'T_RBRACK':
			fileout.write(']')
			getToken()
		else:
			raise SyntaxError(token.line)
	else:
		logging.debug('N_IDXVAR -> epsilon')
		return 'EPSILON'

def const():
	if token.type == 'T_INTCONST':
		logging.debug('N_CONST -> T_INTCONST')
		fileout.write(token.value)
		getToken()
		return 'INTEGER'
	elif token.type == 'T_CHARCONST':
		logging.debug('N_CONST -> T_CHARCONST')
		if token.value == '\'\\\'':
			fileout.write('\'\\n\'')
		else:
			fileout.write(token.value)
		getToken()
		return 'CHAR'
	else:
		logging.debug('N_CONST -> N_BOOLCONST')
		return boolconst()

def boolconst():
	if token.type == 'T_TRUE':
		logging.debug('N_BOOLCONST -> T_TRUE')
		fileout.write('True')
		getToken()
		return 'BOOLEAN'
	elif token.type == 'T_FALSE':
		logging.debug('N_BOOLCONST -> T_FALSE')
		fileout.write('False')
		getToken()
		return 'BOOLEAN'
	else:
		raise SyntaxError(token.line)

#
# The end of the cancer :)
#

main()

filein.close()
fileout.close()
