# Bug Fix Report: mathsquiz.py

The following table summarizes the bugs detected and fixed in the `mathsquiz.py` file:

| Bug | Line | Before | After | Severity |
|---|---|---|---|---|
| Python 2 Print Statement | 3-4 | `print "..."` | `print("...")` | CRITICAL |
| Missing `int()` cast, Assignment (`=`), Wrong Expected Answer (55 -> 56) | 14 | `if answer = 55:` | `if int(answer) == 56:` | HIGH |
| Missing Score Increment | 15 | `print("Correct!")` | `print("Correct!")`<br>`    score += 1` | HIGH |
| Copy-Paste Label | 22 | `print("Question 1:")` | `print("Question 2:")` | MEDIUM |
| Missing `int()` cast, Assignment (`=`), Wrong Expected Answer (49 -> 36) | 25 | `if answer = 49:` | `if int(answer) == 36:` | HIGH |
| Missing Score Increment | 26 | `print("Correct!")` | `print("Correct!")`<br>`    score += 1` | HIGH |
| Copy-Paste Label | 33 | `print("Question 1:")` | `print("Question 3:")` | MEDIUM |
| Missing `int()` cast, Assignment (`=`), Wrong Expected Answer (126 -> 72) | 36 | `if answer = 126:` | `if int(answer) == 72:` | HIGH |
| Missing Score Increment | 37 | `print("Correct!")` | `print("Correct!")`<br>`    score += 1` | HIGH |
| Copy-Paste Label | 44 | `print("Question 1:")` | `print("Question 4:")` | MEDIUM |
| Missing `int()` cast, Assignment (`=`), Wrong Expected Answer (668 -> 48) | 47 | `if answer = 668:` | `if int(answer) == 48:` | HIGH |
| Missing Score Increment | 48 | `print("Correct!")` | `print("Correct!")`<br>`    score += 1` | HIGH |
| Copy-Paste Label | 55 | `print("Question 1:")` | `print("Question 5:")` | MEDIUM |
| Missing `int()` cast, Assignment (`=`), Wrong Expected Answer (77 -> 49) | 58 | `if answer = 77:` | `if int(answer) == 49:` | HIGH |
| Missing Score Increment | 59 | `print("Correct!")` | `print("Correct!")`<br>`    score += 1` | HIGH |
| Copy-Paste Label | 67 | `print("Question 1:")` | `print("Question 6:")` | MEDIUM |
| Missing `int()` cast, Assignment (`=`), Wrong Expected Answer (60 -> 66) | 70 | `if answer = 60:` | `if int(answer) == 66:` | HIGH |
| Missing Score Increment | 71 | `print("Correct!")` | `print("Correct!")`<br>`    score += 1` | HIGH |
| Syntax Error: `else if` | 91 | `else if score < 8:` | `elif score < 8:` | CRITICAL |
| Syntax Error: `else if` & Assignment (`=`) | 93 | `else if score = 10:` | `elif score == 10:` | CRITICAL |
| Syntax Error: Python 2 Object | 2 (polygons) | `class Polygon(Object):` | `class Polygon:` | CRITICAL |
| Syntax Error: `new` keyword | 29 (polygons) | `poly = new Polygon(...)` | `poly = Polygon(...)` | CRITICAL |
