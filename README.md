# Project 3
Anthony Samaha, Christiaan Rutten, Melissa Ng

## report.pdf
A reference on how the tool was implemented and how to use it.
 
## Check-in 1
File: check-in1.py
Outputs all variables and written variables for the 3 input files

## Check-in 2 Task 1
File: check-in2-t1.py
Outputs the function prototype for the 3 input files.

## Check-in 2 Task 2
File: checkin-in2-t2.py
Modified minic_ast.py to represent a function language
Comments at top included on what was added and removed

## Check-in 3
File: func-ast.py
- Started to add string representations for different nodes:
- Let, Id, Assignment ...
- Added a new AST node to represent a function def.

File: checkin3.py
- Added code to convert all blocks into a functional ast.
- Then with the new ast, output functional code that was converted from our source c coude.
- Currently support all basic code (binary, unary, variable, constant, Decl, array ref and array decl, list expr) except if and iteration nodes.


## Check-in 4
- File: checkin4.py
- Added if, else if, else statement support
- simply run python checkin4.py to try it!

## Check-in 5
- File: checkin5.py
- Optimized function code to remove unnecessary lets

## Check-in 6
- File: checkin6.py
- Added support for for and while loops. 
- Output can be optimized or unoptimized depending on user. checkin6.py will prompt for what todo. 
