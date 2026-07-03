Tugas Proyek Akhir — Representasi Tahapan Kompilasi

Konstruksi yang Dipilih: Perulangan (While Loop)


1. Deskripsi Umum

Proyek ini menyimulasikan empat tahapan utama dalam proses kompilasi terhadap satu
konstruksi bahasa pemrograman, yaitu perulangan while. Program ditulis dalam
bahasa Python (compiler.py) dan merepresentasikan tahapan berikut secara
berurutan:


Tahap	Kelas	Input → Output
1. Analisis Leksikal	Lexer	Source code (string) → deretan Token
2. Analisis Sintaksis	Parser	Token → Abstract Syntax Tree (AST)
3. Analisis Semantik	SemanticAnalyzer	AST → validasi (tervalidasi / error)
4. Generasi Kode Antara	TACGenerator	AST → Three-Address Code (TAC)


2. Pattern / Grammar (BNF)

Konstruksi while yang diimplementasikan mendukung kondisi relasional sederhana
dan badan perulangan berisi statement assignment dengan ekspresi aritmatika.


<program>      ::= { <statement> }

<statement>    ::= <assign_stmt> | <while_stmt>

<assign_stmt>  ::= ID "=" <expr> ";"

<while_stmt>   ::= "while" "(" <condition> ")" "{" { <statement> } "}"

<condition>    ::= <expr> <relop> <expr>
<relop>        ::= "<" | ">" | "<=" | ">=" | "==" | "!="

<expr>         ::= <term> { ("+" | "-") <term> }
<term>         ::= <factor> { ("*" | "/") <factor> }
<factor>       ::= ID | NUMBER | "(" <expr> ")"

Contoh konstruksi valid sesuai grammar di atas:


i = 0;
sum = 0;
while ( i < 10 ) {
    sum = sum + i;
    i = i + 1;
}


3. Penjelasan Tiap Tahap Implementasi

3.1 Analisis Leksikal — class Lexer


Menggunakan regular expression gabungan (re module) untuk memecah source code menjadi token: WHILE, ID, NUMBER, RELOP, ASSIGN, PLUS, MINUS, STAR, SLASH, LPAREN, RPAREN, LBRACE, RBRACE, SEMI.

Whitespace (spasi/tab/newline) diabaikan (tidak menghasilkan token).

Kata kunci (while) dikenali secara khusus melalui set KEYWORDS — jika token berjenis identifier tetapi nilainya cocok dengan keyword, token diberi tipe WHILE, bukan ID.

Token operator dua-karakter (<=, >=, ==, !=) dicek lebih dulu daripada satu-karakter (<, >) agar tidak salah tokenisasi.

Output: list objek Token(type, value).


Contoh hasil tokenisasi untuk i = 0;:


[<ID:i>, <ASSIGN:=>, <NUMBER:0>, <SEMI:;>]

3.2 Analisis Sintaksis — class Parser


Menggunakan teknik Recursive Descent Parsing, satu fungsi per rule grammar (parse_program, parse_statement, parse_while, parse_assign, parse_condition, parse_expr, parse_term, parse_factor).

Precedence operator ditangani melalui struktur fungsi bertingkat: expr (untuk + -) memanggil term (untuk * /) memanggil factor (identifier/angka/tanda kurung) — sehingga perkalian/pembagian otomatis memiliki presedensi lebih tinggi daripada penjumlahan/pengurangan.

Setiap rule membentuk node AST: WhileNode, AssignNode, ConditionNode, BinOpNode, IdNode, NumNode.

Jika token yang ditemukan tidak sesuai dengan yang diharapkan grammar, parser melempar SyntaxErrorCustom (contoh: kurung tidak ditutup, tanda ; hilang).


Contoh struktur AST (disederhanakan) untuk while (i < 10) { sum = sum + i; }:


WhileNode
├── condition: ConditionNode(left=IdNode(i), op="<", right=NumNode(10))
└── body:
    └── AssignNode(var="sum", expr=BinOpNode(IdNode(sum), "+", IdNode(i)))

3.3 Analisis Semantik — class SemanticAnalyzer


Membangun symbol table sederhana (Python set) berisi nama variabel yang sudah pernah menjadi target assignment (dianggap "dideklarasikan").

Melakukan pengecekan:
Variabel tidak boleh dipakai sebelum di-assign — jika IdNode muncul di sisi kanan ekspresi/kondisi tetapi belum ada di symbol table, akan dilempar SemanticError.
Validasi literal numerik — memastikan token NUMBER dapat dikonversi ke tipe numerik (float).
Validasi operator relasi pada kondisi while (harus salah satu dari < > <= >= == !=).

Program menyertakan demo kegagalan semantik (source_err) yang menggunakan variabel x dan y tanpa deklarasi sebelumnya, untuk membuktikan bahwa tahap ini benar-benar menangkap kesalahan:
SemanticError: Variabel 'x' digunakan sebelum dideklarasikan/diinisialisasi.


3.4 Generasi Kode Antara — class TACGenerator


Mengubah AST menjadi Three-Address Code (TAC), dengan setiap instruksi maksimal memiliki tiga alamat (1 hasil, maksimal 2 operand).

Variabel sementara (t1, t2, ...) dibuat untuk menyimpan hasil sub-ekspresi.

Label (L1, L2, ...) dibuat untuk menandai lompatan awal dan akhir loop.

Pola TAC standar yang dihasilkan untuk while (cond) { body }:
L_start:
    t = <hasil evaluasi cond>
    ifFalse t goto L_end
    <TAC dari body>
    goto L_start
L_end:

Ekspresi biner (BinOpNode) diuraikan secara rekursif — setiap operasi menghasilkan instruksi tiga-alamat baru dengan variabel sementara.



4. Contoh Eksekusi Program Lengkap

Input

i = 0;
sum = 0;
while ( i < 10 ) {
    sum = sum + i;
    i = i + 1;
}

Output — Analisis Leksikal (Token)

[<ID:i>, <ASSIGN:=>, <NUMBER:0>, <SEMI:;>, <ID:sum>, <ASSIGN:=>, <NUMBER:0>, <SEMI:;>,
 <WHILE:while>, <LPAREN:(>, <ID:i>, <RELOP:<>, <NUMBER:10>, <RPAREN:)>, <LBRACE:{>,
 <ID:sum>, <ASSIGN:=>, <ID:sum>, <PLUS:+>, <ID:i>, <SEMI:;>,
 <ID:i>, <ASSIGN:=>, <ID:i>, <PLUS:+>, <NUMBER:1>, <SEMI:;>, <RBRACE:}>, <EOF:None>]

Output — Analisis Sintaksis

Jumlah statement top-level: 3
  [0] AssignNode   (i = 0)
  [1] AssignNode   (sum = 0)
  [2] WhileNode    (while i < 10 { ... })

Output — Analisis Semantik

Symbol table (variabel terdeklarasi): ['i', 'sum']

Output — Three-Address Code (TAC)

i = 0
sum = 0
L1:
t1 = i < 10
ifFalse t1 goto L2
t2 = sum + i
sum = t2
t3 = i + 1
i = t3
goto L1
L2:

Interpretasi TAC: L1 menandai awal iterasi. Kondisi i < 10 dievaluasi ke
t1; jika false, program melompat ke L2 (keluar loop). Jika true, badan
loop dieksekusi (sum = sum + i, i = i + 1), lalu goto L1 mengulang
iterasi berikutnya.



5. Contoh Tambahan & Penanganan Error

File compiler.py menyertakan dua contoh valid lainnya (perhitungan
faktorial dengan perkalian berulang) dan satu demo kegagalan tahap
semantik untuk membuktikan bahwa validasi benar-benar berjalan, bukan
sekadar diterima begitu saja. Jalankan langsung dengan:


python3 compiler.py


6. Struktur File

.
├── compiler.py   # Implementasi lengkap: Lexer, Parser, SemanticAnalyzer, TACGenerator
└── README.md     # Dokumen penjelasan ini


7. Kesimpulan

Implementasi ini menunjukkan bagaimana satu konstruksi sederhana (while)
melewati seluruh pipeline kompilasi front-end hingga menghasilkan kode antara:
mulai dari pemecahan karakter menjadi token bermakna (leksikal), penyusunan
struktur pohon sintaksis (sintaksis), validasi penggunaan variabel (semantik),
hingga akhirnya diterjemahkan menjadi instruksi beralamat-tiga (TAC) yang siap
dioptimasi atau diterjemahkan lebih lanjut ke kode mesin/assembly pada tahap
back-end kompiler.

