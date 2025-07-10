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

class Token:
    def __init__(self,type_,value=None):
        self.type =  type_
        self.value = value
        
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
        return result
    
class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Character", details)
        
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
        
    def advance(self):
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
                tokens.append(Token(TT_PLUS))
                self.advance()
            elif self.current_char == "-":
                tokens.append(Token(TT_MINUS))
                self.advance()
            elif self.current_char == "*":
                tokens.append(Token(TT_MUL))
                self.advance()
            elif self.current_char == "/":
                tokens.append(Token(TT_DIV))
                self.advance()
            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN))
                self.advance()
            else:
                pos_start = self.pos.copy()# save the position before we advance
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"Error on {pos_start.idx} to {self.pos.idx} since '{char}' is not a valid token") # return no tokens and an error if we encounter an illegal character
          
        
        return tokens, None # return the list of tokens and None for no error
    
    def make_number(self):
        num_str = ""
        dot_count = 0 #is it a float or an int?
        
        while self.current_char != None and self.current_char in DIGITS + ".":
            if self.current_char == ".":
                if dot_count == 1: break # can't have more than one dot in a number
                
                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char
            self.advance()
            
        if dot_count == 0:
            return Token(TT_INT, int(num_str))
        else:
            return Token(TT_FLOAT, float(num_str))
        

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
        return res
        
    def factor(self): #if token is int or float advance and return number node class
        tok = self.current_tok
        
        if tok.type in (TT_INT, TT_FLOAT):
            self.advance()
            return NumberNode(tok) #recursive functions since call eachother
    
    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))
        
    
    def expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))
    
    
    def bin_op(self, func, ops): # pass in rule and accepted operations
        # since term and expression is basically the same with the difference being it's either doing the same operation on a factor or a term, we can create a code that can be used for both 
        #scenarios
        
        left =  func()
        
        while self.current_tok.type in ops: #if current tok is operation token
            op_tok = self.current_tok
            self.advance() #advance to next
            right = func()
            left = BinOpNode(left,op_tok,right)
            
        return left #now a binary operation node because we re-assigned it - becomes a term
        
        

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
    
    return ast, None