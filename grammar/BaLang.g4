 grammar BaLang;

program: block
    ;

block: ( (statement|function)? NL)* 
    ;

expr: left=expr op=(ADD | SUB ) right=expr                       # expression
    | INT                                                       # number
    | DOUBLE                                                    # double 
    | ID                                                        # var
    | STRING                                                    # string 
    ;

statement: 'SHOW' name=(ID|STRING)                              # printing
    | 'IF' ifoperator = ifexpr 'THEN:' inblock = blockif 'ENDIF' # if
    | vartype=('I' | 'D' | 'S') 'WRITE'  name=ID                # reading
    | vartype=('D' | 'I' | 'S') name=ID EQ value=expr           # declare
    ;

ifexpr: left = ID op = EQUAL right = expr                                                     
    ;

blockif: block
    ;

function: 'DEF' fparm fblock 'ENDF'                                #dofunction
    ;

fparm: ID
    ;

fblock: (statement? NL)*
    ;


COMMENT: '#' ~( '\r' | '\n' )* -> skip
    ;

NL:	'\r'? '\n'
    ;

WS:   (' '|'\t')+ -> skip
    ;

INT   : [0-9]+
    ;

DOUBLE : [0-9]+ '.' [0-9]+
    ;

ID : [a-zA-Z][0-9a-zA-Z]*
    ;

ADD  : '+'
    ;

SUB : '-'
    ;

EQ    : '='
    ;

EQUAL: '=='
    ;

STRING: '"'(~('\\'|'"'|'#'))*'"'
    ;
