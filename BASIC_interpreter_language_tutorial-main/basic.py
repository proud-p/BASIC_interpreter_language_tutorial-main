from utils.strings_with_arrows import string_with_arrows

#################################################
# TOKENS
#################################################

# TT stands for Token Type
TT_INT = "TT_INT"
TT_FLOAT = "FLOAT"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_LPAREN = "LPAREN"
TT_RPAREN  = "RPAREN"
TT_EOF  = "EOF" # End of File token, used to indicate the end of the input text

class Token:
    def __init__(self,type_,value=None, pos_start = None,pos_end = None):
        self.type =  type_
        self.value = value
        
        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy().advance()
            
        if pos_end: 
            self.pos_end = pos_end
        
    def __repr__(self): # representation method so it looks nice when printed out in the terminal window
        if self.value: return f"{self.type}:{self.value}"
        return f"{self.type}"
    
#################################################
# DIGITS CONSTNANTS
#################################################
    
DIGITS = "0123456789"

#################################################
# ERRORS
#################################################

class Error:
    def __init__(self,pos_start, pos_end, error_name, details):
        self.error_name = error_name
        self.details = details
        self.pos_start = pos_start
        self.pos_end = pos_end
    
    def as_string(self):
        result = f"{self.error_name}: {self.details}"
        result += f"\nFile {self.pos_start.fn}, line {self.pos_start.ln + 1}"
        result += f", column {self.pos_start.col + 1}"
        result += f" to {self.pos_end.ln + 1}, column {self.pos_end.col + 1}"
        result += "\n\n" + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result
    
class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Character", details)
        
class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Invalid Syntax", details)
        
#################################################
# POSITION
#################################################

class Position:
    def __init__(self,idx, ln,col, fn, ftxt=None):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn #file name
        self.ftxt = ftxt #file text, not used in this lexer but could be useful for error messages
    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1
        
        if current_char == "\n":
            self.ln += 1
            self.col = 0
            
        return self
    
    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt) # return a copy of the position so we can save the position before we advance it
    

#################################################
# LEXER
#################################################

class Lexer:
    """A lexer is a class that takes a string of text and breaks it down into tokens.
It is the first step in the process of interpreting or compiling a programming language.
In this case, it will take a string of BASIC code and break it down into tokens that can be used by the parser.
    The lexer will ignore whitespace and comments, and will return a list of tokens that represent the code.
    Each token will have a type and a value. The type will be one of the token types defined above, and the value will be the actual value of the token.
    For example, the string "1 + 2" will be broken down into three tokens: an integer token with value 1, a plus token with no value, and an integer token with value 2.
    """
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1,0,-1,fn=fn,ftxt=text) # initialize the position with -1 index, 0 line number, and -1 column number, -1 column number so we can advance to the first character to 0
        self.current_char = None
        self.advance() # initialize the lexer by setting the text, position, and current character
        
    def advance(self, current_char=None):
        self.pos.advance(self.current_char) # advance the position by one character
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None #advance the position and set the current character to None if we are at the end of the text
        
    def make_tokens(self):
        tokens = []
        
        while self.current_char != None:
            if self.current_char in "\t\n\r ": # ignore whitespace characters
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char == "+":
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == "-":
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == "*":
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == "/":
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()# save the position before we advance
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"Error on {pos_start.idx} to {self.pos.idx} since '{char}' is not a valid token") # return no tokens and an error if we encounter an illegal character
          
        tokens.append(Token(TT_EOF, pos_start=self.pos)) # add an end of file token to the list of tokens
        self.advance() # advance the position to the end of the file
        return tokens, None # return the list of tokens and None for no error
    
    def make_number(self):
        num_str = ""
        dot_count = 0 #is it a float or an int?
        pos_start = self.pos.copy() # save the position before we advance
        
        while self.current_char != None and self.current_char in DIGITS + ".":
            if self.current_char == ".":
                if dot_count == 1: break # can't have more than one dot in a number
                
                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char
            self.advance()
            
        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start=pos_start, pos_end=self.pos)
        else:
            return Token(TT_FLOAT, float(num_str),pos_start=pos_start, pos_end=self.pos)
        

#################################################
# NODES 
#################################################

class NumberNode:
    def __init__(self,token):
        self.token = token
    def __repr__(self): #return a string containing a printable representation of an object
        return f"{self.token}"
    
class BinOpNode:
    def __init__(self,left_node,op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node
        
    def __repr__(self):
        return f"({self.left_node}, {self.op_tok}, {self.right_node})"

class UnaryOpNode: # for unary operations like -5 or +5
    """Unary operations are operations that only have one operand, such as negation or positive sign"""
    def __init__(self,op_tok, node):
        self.op_tok = op_tok
        self.node = node
        
    def __repr__(self):
        return f"({self.op_tok}, {self.node})"
#################################################
# PARSE RESULT
#################################################
class ParseResult: 
    def __init__(self):
        self.error = None
        self.node = None
    
    def register(self, res): # register a result from a function call
        if isinstance(res,ParseResult): #if res is a parse result class object
            if res.error: self.error = res.error
            return res.node
        
        
    def success(self, node): # if the result is successful
        self.node = node
        return self
    
    def failure(self, error): # if the result is a failure
        self.error = error
        return self



#################################################
# PARSER
#################################################

class Parser:
    def __init__(self,tokens):
        self.tokens = tokens
        self.tok_idx = -1 #token index
        self.advance()
        
    def advance(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok 
    
    def parse(self): #call expression - advance till find plus or minus
        res = self.expr()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '+', '-', '*', '/' or EOF"))
        return res
        
    def factor(self): #if token is int or float advance and return number node class
        res = ParseResult() #create a parse result object
        tok = self.current_tok
        
        #unary operations
        if tok.type in (TT_PLUS,TT_MINUS): #if token is a plus sign, advance and return a unary operation node
            res.register(self.advance()) #advance to the next token
            node = res.register(self.factor()) #call factor again to get the next node
            if res.error: return res
            return res.success(UnaryOpNode(tok, node)) #return a unary operation node with the token and the node
        
        #normal operations
        elif tok.type in (TT_INT, TT_FLOAT):
            res.register(self.advance()) #wrap the advance in a parse result object but not doing anything yet
            return res.success(NumberNode(tok)) #recursive functions since call eachother
        
        #if token is a left parenthesis, call expression and return the node
        elif tok.type == TT_LPAREN:
            res.register(self.advance()) #advance to the next token
            node = res.register(self.expr()) #call expression to get the next node
            if res.error: return res #if there is an error, return the error
            
            if self.current_tok.type == TT_RPAREN: #if the next token is not a right parenthesis, return an error
               res.register(self.advance()) #advance to the next token if right parenthesis is found
            else:
                return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ')'"))
            return res.success(node) #return the node
        
        return res.failure(InvalidSyntaxError(tok.pos_start, tok.pos_end, "Expected int or float")) #if not an int or float, return an error
    
    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))
        
    
    def expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))
    
    
    def bin_op(self, func, ops): # pass in rule and accepted operations, func needs to be wrapped in ParseResult so we can register the result of the function call
        # since term and expression is basically the same with the difference being it's either doing the same operation on a factor or a term, we can create a code that can be used for both 
        #scenarios
        res = ParseResult() #create a parse result object
        left =  res.register(func()) #register will take in the parse result from the call to this function and return the node from the function call
        
        if res.error: return res # if there is an error, return the error
        
        while self.current_tok.type in ops: #if current tok is operation token
            op_tok = self.current_tok
            res.register(self.advance()) #advance to next
            right = res.register(func())
            
            if res.error: return res # if there is an error, return the error
            
            left = BinOpNode(left,op_tok,right)
            
        return res.success(left) #now a binary operation node because we re-assigned it - becomes a term
        
        

#################################################
# RUN
#################################################

def run(fn,text):
    lexer = Lexer(fn,text)
    tokens, error = lexer.make_tokens()
    
    if error: return None, error
    
    # Generate Abstract Syntax Tree
    parser = Parser(tokens)
    ast = parser.parse()
    
    return ast.node, ast.error