# Hot Nodes & Bug Investigation

## Top 5 Hubs
1. [[mathsquiz-step2.py]] (Degree: 15)
2. [[ask_question]] (Degree: 11)
3. [[mathsquiz-step3.py]] (Degree: 9)
4. [[welcome_message]] (Degree: 2)
5. [[print_final_scores]] (Degree: 2)

## Source Code: mathsquiz.py
```python
# welcome the player and explain stuff

print "Hello! I'm going to ask you 10 maths questions."
print "Let's see how many you can get right!"

# set the score to zero
score = 0

# question 1

print("Question 1:")
print("What is 8 x 7")
answer = input("Answer: ")
if answer = 55:
    print("Correct!")
else:
    print("Wrong!")


# question 2

print("Question 1:")
print("What is 4 x 9")
answer = input("Answer: ")
if answer = 49:
    print("Correct!")
else:
    print("Wrong!")


# question 3

print("Question 1:")
print("What is 12 x 6")
answer = input("Answer: ")
if answer = 126:
    print("Correct!")
else:
    print("Wrong!")


# question 4

print("Question 1:")
print("What is 6 x 8")
answer = input("Answer: ")
if answer = 668:
    print("Correct!")
else:
    print("Wrong!")


# question 5

print("Question 1:")
print("What is 7 x 7")
answer = input("Answer: ")
if answer = 77:
    print("Correct!")
else:
    print("Wrong!")



# question 6

print("Question 1:")
print("What is 11 x 6")
answer = input("Answer: ")
if answer = 60:
    print("Correct!")
else:
    print("Wrong!")











# print the final scores

print("That's all the questions done. So...what was your score...?")
print("You scored", score, "points out of a possible 10.")
if score < 5:
    print("You need to practice your maths!")
else if score < 8:
    print("That's pretty good!")
else if score = 10:
    print("Wow! What a maths star you are!! I'm impressed!")

```

## Root Cause Analysis
The following architectural and logic issues were detected:

### PYTHON_2_MIGRATION_ISSUE
- **Description:** Syntax issue found: SyntaxError: Missing parentheses in call to 'print'. Did you mean print(...)? (<unknown>, line 3)
- **Fix / Recommendation:** Fix the syntax error to ensure modern Python compatibility.

### SYNTAX_ERROR
- **Description:** Syntax issue found: SyntaxError: invalid syntax (<unknown>, line 29)
- **Fix / Recommendation:** Fix the syntax error to ensure modern Python compatibility.

### LOGIC_ERROR
- **Description:** Assignment operator '=' used instead of equality operator '==' in if condition.
- **Fix / Recommendation:** Replace '=' with '==' in if conditions.

### COPY_PASTE_ERROR
- **Description:** Multiple questions are labeled as 'Question 1:'.
- **Fix / Recommendation:** Update question labels to reflect the correct question number.

### LOGIC_ERROR
- **Description:** Wrong expected answer for 8x7: expects 55 instead of 56.
- **Fix / Recommendation:** Fix the expected answer for 8x7 to 56.

### LOGIC_ERROR
- **Description:** Wrong expected answer for 4x9: expects 49 instead of 36.
- **Fix / Recommendation:** Fix the expected answer for 4x9 to 36.

### SYNTAX_ERROR
- **Description:** 'else if' is used instead of Python's 'elif'.
- **Fix / Recommendation:** Replace 'else if' with 'elif'.

## Navigation
Return to [[index]]