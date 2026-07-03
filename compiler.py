"""
Simulasi Tahapan Kompilasi untuk Konstruksi Perulangan (WHILE LOOP)
=====================================================================
Tugas Proyek Akhir - Teknik Kompilasi

Tahapan yang direpresentasikan:
    1. Analisis Leksikal  -> class Lexer          (source code -> token)
    2. Analisis Sintaksis -> class Parser          (token -> Abstract Syntax Tree / AST)
    3. Analisis Semantik  -> class SemanticAnalyzer(AST -> validasi tipe & deklarasi variabel)
    4. Generasi Kode      -> class TACGenerator    (AST -> Three-Address Code)

Konstruksi yang dipilih : WHILE LOOP
Grammar (BNF) ada di README.md
"""

import re


# =====================================================================
# 1. ANALISIS LEKSIKAL (LEXER)
# =====================================================================

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"<{self.type}:{self.value}>"


class Lexer:
    """Memecah source code menjadi deretan token (tokenisasi)."""

    KEYWORDS = {"while"}

    # Urutan penting: operator 2-karakter dicek lebih dulu daripada 1-karakter
    TOKEN_SPEC = [
        ("WHITESPACE", r"[ \t\n]+"),
        ("NUMBER",     r"\d+(\.\d+)?"),
        ("ID",         r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ("RELOP",      r"==|!=|<=|>=|<|>"),
        ("ASSIGN",     r"="),
        ("PLUS",       r"\+"),
        ("MINUS",      r"-"),
        ("STAR",       r"\*"),
        ("SLASH",      r"/"),
        ("LPAREN",     r"\("),
        ("RPAREN",     r"\)"),
        ("LBRACE",     r"\{"),
        ("RBRACE",     r"\}"),
        ("SEMI",       r";"),
    ]

    def __init__(self, source_code):
        self.source_code = source_code
        master_pattern = "|".join(f"(?P<{name}>{pattern})" for name, pattern in self.TOKEN_SPEC)
        self.regex = re.compile(master_pattern)

    def tokenize(self):
        tokens = []
        pos = 0
        while pos < len(self.source_code):
            match = self.regex.match(self.source_code, pos)
            if not match:
                raise SyntaxError(f"Karakter tidak dikenali pada posisi {pos}: "
                                   f"'{self.source_code[pos]}'")
            kind = match.lastgroup
            value = match.group()
            pos = match.end()

            if kind == "WHITESPACE":
                continue
            if kind == "ID" and value in self.KEYWORDS:
                tokens.append(Token("WHILE", value))
            elif kind == "ID":
                tokens.append(Token("ID", value))
            elif kind == "NUMBER":
                tokens.append(Token("NUMBER", value))
            else:
                tokens.append(Token(kind, value))

        tokens.append(Token("EOF", None))
        return tokens


# =====================================================================
# 2. ANALISIS SINTAKSIS (PARSER -> AST)
# =====================================================================
# Setiap node AST direpresentasikan sebagai instance class sederhana.

class WhileNode:
    def __init__(self, condition, body):
        self.condition = condition   # ConditionNode
        self.body = body             # list of statement nodes


class ConditionNode:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class AssignNode:
    def __init__(self, var_name, expr):
        self.var_name = var_name
        self.expr = expr


class BinOpNode:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class IdNode:
    def __init__(self, name):
        self.name = name


class NumNode:
    def __init__(self, value):
        self.value = value


class SyntaxErrorCustom(Exception):
    pass


class Parser:
    """
    Grammar (BNF) yang diimplementasikan:

    <program>      ::= { <statement> }
    <statement>    ::= <assign_stmt> | <while_stmt>
    <assign_stmt>  ::= ID "=" <expr> ";"
    <while_stmt>   ::= "while" "(" <condition> ")" "{" { <statement> } "}"
    <condition>    ::= ID relop <expr>
    <expr>         ::= <term> { ("+" | "-") <term> }
    <term>         ::= <factor> { ("*" | "/") <factor> }
    <factor>       ::= ID | NUMBER | "(" <expr> ")"
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def eat(self, expected_type):
        tok = self.current()
        if tok.type != expected_type:
            raise SyntaxErrorCustom(
                f"Diharapkan token '{expected_type}', tetapi ditemukan '{tok.type}' ({tok.value})"
            )
        self.pos += 1
        return tok

    def parse_program(self):
        statements = []
        while self.current().type != "EOF":
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self):
        if self.current().type == "WHILE":
            return self.parse_while()
        elif self.current().type == "ID":
            return self.parse_assign()
        else:
            raise SyntaxErrorCustom(f"Statement tidak dikenali pada token: {self.current()}")

    def parse_while(self):
        self.eat("WHILE")
        self.eat("LPAREN")
        condition = self.parse_condition()
        self.eat("RPAREN")
        self.eat("LBRACE")
        body = []
        while self.current().type != "RBRACE":
            body.append(self.parse_statement())
        self.eat("RBRACE")
        return WhileNode(condition, body)

    def parse_assign(self):
        var_tok = self.eat("ID")
        self.eat("ASSIGN")
        expr = self.parse_expr()
        self.eat("SEMI")
        return AssignNode(var_tok.value, expr)

    def parse_condition(self):
        left = self.parse_expr()
        op_tok = self.eat("RELOP")
        right = self.parse_expr()
        return ConditionNode(left, op_tok.value, right)

    def parse_expr(self):
        node = self.parse_term()
        while self.current().type in ("PLUS", "MINUS"):
            op = self.eat(self.current().type).value
            right = self.parse_term()
            node = BinOpNode(node, op, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.current().type in ("STAR", "SLASH"):
            op = self.eat(self.current().type).value
            right = self.parse_factor()
            node = BinOpNode(node, op, right)
        return node

    def parse_factor(self):
        tok = self.current()
        if tok.type == "ID":
            self.eat("ID")
            return IdNode(tok.value)
        elif tok.type == "NUMBER":
            self.eat("NUMBER")
            return NumNode(tok.value)
        elif tok.type == "LPAREN":
            self.eat("LPAREN")
            node = self.parse_expr()
            self.eat("RPAREN")
            return node
        else:
            raise SyntaxErrorCustom(f"Faktor tidak valid pada token: {tok}")


# =====================================================================
# 3. ANALISIS SEMANTIK
# =====================================================================

class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    """
    Melakukan pengecekan dasar:
      - Variabel harus sudah 'dideklarasikan' (di-assign) sebelum dipakai
        di sisi kanan ekspresi / kondisi.
      - Semua nilai dianggap bertipe numerik (int/float); pengecekan
        tipe numerik dilakukan pada literal NUMBER.
    Symbol table berupa set nama variabel yang sudah pernah di-assign.
    """

    def __init__(self):
        self.symbol_table = set()

    def analyze(self, statements):
        for stmt in statements:
            self.visit(stmt)
        return self.symbol_table

    def visit(self, node):
        if isinstance(node, AssignNode):
            self.check_expr(node.expr)
            self.symbol_table.add(node.var_name)   # deklarasi implisit saat assignment

        elif isinstance(node, WhileNode):
            self.check_condition(node.condition)
            for stmt in node.body:
                self.visit(stmt)

        else:
            raise SemanticError(f"Node AST tidak dikenali: {type(node)}")

    def check_condition(self, cond):
        self.check_expr(cond.left)
        self.check_expr(cond.right)
        valid_ops = {"<", ">", "<=", ">=", "==", "!="}
        if cond.op not in valid_ops:
            raise SemanticError(f"Operator relasi tidak valid: {cond.op}")

    def check_expr(self, node):
        if isinstance(node, IdNode):
            if node.name not in self.symbol_table:
                raise SemanticError(
                    f"Variabel '{node.name}' digunakan sebelum dideklarasikan/diinisialisasi."
                )
        elif isinstance(node, NumNode):
            try:
                float(node.value)
            except ValueError:
                raise SemanticError(f"Literal numerik tidak valid: {node.value}")
        elif isinstance(node, BinOpNode):
            self.check_expr(node.left)
            self.check_expr(node.right)
        else:
            raise SemanticError(f"Ekspresi tidak dikenali: {type(node)}")


# =====================================================================
# 4. GENERASI KODE ANTARA (THREE-ADDRESS CODE / TAC)
# =====================================================================

class TACGenerator:
    def __init__(self):
        self.temp_counter = 1
        self.label_counter = 1
        self.code = []

    def new_temp(self):
        t = f"t{self.temp_counter}"
        self.temp_counter += 1
        return t

    def new_label(self):
        l = f"L{self.label_counter}"
        self.label_counter += 1
        return l

    def emit(self, instr):
        self.code.append(instr)

    def generate(self, statements):
        for stmt in statements:
            self.gen_statement(stmt)
        return self.code

    def gen_statement(self, node):
        if isinstance(node, AssignNode):
            result = self.gen_expr(node.expr)
            self.emit(f"{node.var_name} = {result}")

        elif isinstance(node, WhileNode):
            l_start = self.new_label()
            l_end = self.new_label()
            self.emit(f"{l_start}:")
            cond_temp = self.gen_condition(node.condition)
            self.emit(f"ifFalse {cond_temp} goto {l_end}")
            for stmt in node.body:
                self.gen_statement(stmt)
            self.emit(f"goto {l_start}")
            self.emit(f"{l_end}:")

    def gen_condition(self, cond):
        left = self.gen_expr(cond.left)
        right = self.gen_expr(cond.right)
        t = self.new_temp()
        self.emit(f"{t} = {left} {cond.op} {right}")
        return t

    def gen_expr(self, node):
        if isinstance(node, IdNode):
            return node.name
        if isinstance(node, NumNode):
            return node.value
        if isinstance(node, BinOpNode):
            left = self.gen_expr(node.left)
            right = self.gen_expr(node.right)
            t = self.new_temp()
            self.emit(f"{t} = {left} {node.op} {right}")
            return t
        raise SemanticError(f"Node ekspresi tidak dikenali saat generate TAC: {type(node)}")


# =====================================================================
# DRIVER / DEMO
# =====================================================================

def compile_source(source_code, label=""):
    print(f"{'='*70}\nSOURCE CODE {label}\n{'='*70}")
    print(source_code.strip())

    # 1. Lexical
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    print(f"\n--- 1. Analisis Leksikal (Tokens) ---")
    print(tokens)

    # 2. Syntax -> AST
    parser = Parser(tokens)
    ast = parser.parse_program()
    print(f"\n--- 2. Analisis Sintaksis (AST berhasil dibentuk) ---")
    print(f"Jumlah statement top-level: {len(ast)}")
    for i, stmt in enumerate(ast):
        print(f"  [{i}] {type(stmt).__name__}")

    # 3. Semantic
    analyzer = SemanticAnalyzer()
    symtab = analyzer.analyze(ast)
    print(f"\n--- 3. Analisis Semantik (Sukses) ---")
    print(f"Symbol table (variabel terdeklarasi): {sorted(symtab)}")

    # 4. TAC
    tac_gen = TACGenerator()
    tac_code = tac_gen.generate(ast)
    print(f"\n--- 4. Generasi Three-Address Code (TAC) ---")
    print("\n".join(tac_code))
    print()
    return tac_code


if __name__ == "__main__":
    # Contoh 1: while loop menjumlahkan angka 0..9 -> sum
    source_1 = """
    i = 0;
    sum = 0;
    while ( i < 10 ) {
        sum = sum + i;
        i = i + 1;
    }
    """
    compile_source(source_1, "#1 - Penjumlahan 0..9")

    # Contoh 2: while loop dengan ekspresi lebih kompleks (nested binop)
    source_2 = """
    n = 5;
    hasil = 1;
    while ( n > 1 ) {
        hasil = hasil * n;
        n = n - 1;
    }
    """
    compile_source(source_2, "#2 - Faktorial (perkalian berulang)")

    # Contoh 3: DEMO ERROR SEMANTIK (variabel belum dideklarasikan)
    print(f"{'='*70}\nDEMO ERROR SEMANTIK\n{'='*70}")
    source_err = """
    while ( x < 5 ) {
        y = y + 1;
    }
    """
    try:
        compile_source(source_err, "#3 - Error (x, y belum dideklarasikan)")
    except SemanticError as e:
        print(f"[SemanticError tertangkap sesuai ekspektasi]: {e}")
