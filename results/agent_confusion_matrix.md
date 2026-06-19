# CodeInspectorAgent Confusion Matrix

| Fact | Ground Truth | Agent Prediction | Result |
|---|---|---|---|
| mathsquiz-step2.py calls ask_question | True | True | TP |
| polygons.py imports turtle | True | True | TP |
| mathsquiz.py calls randint | False | False | TN |
| mathsquiz-step3.py calls welcome_message | True | True | TP |
| mathsquiz-step2.py calls print_final_scores | True | True | TP |
| mathsquiz-step3.py calls print_final_scores | True | True | TP |
| mathsquiz-step3.py calls randint | True | True | TP |
| mathsquiz-step3.py imports random | True | True | TP |
| mathsquiz.py has a Missing parentheses error | True | True | TP |
| polygons.py has a SyntaxError | True | True | TP |
| ask_question is defined in mathsquiz-step2.py | True | True | TP |
| welcome_message is defined in mathsquiz-step3.py | True | True | TP |
| polygons.py calls ask_question | False | False | TN |
| polygons.py imports random | False | False | TN |
| mathsquiz-step2.py calls randint | False | False | TN |
| mathsquiz-step2.py imports random | False | False | TN |
| mathsquiz-step3.py imports turtle | False | False | TN |
| welcome_message is defined in polygons.py | False | False | TN |
| print_final_scores is defined in mathsquiz.py | False | False | TN |
| mathsquiz.py calls ask_question | False | False | TN |
| The CLI module is decoupled from the core orchestration SDK | True | True | TP |
| The GraphLoader component can operate without a network connection | True | True | TP |
| ApiGatekeeper state is shared globally across the module without passing instances | False | False | TN |
| ContextBudgetManager implements a Dropping Skill fallback to prevent context overflow | True | False | FN |
| The improvement loop automatically overwrites original source code files | False | False | TN |

## Metrics
- **True Positives (TP):** 13
- **False Positives (FP):** 0
- **True Negatives (TN):** 11
- **False Negatives (FN):** 1

- **Precision:** 1.00
- **Recall:** 0.93
- **F1 Score:** 0.96

## False Negative Analysis: Context Boundary Resolution
In previous static runs, the agent encountered a False Positive where it hallucinated that `mathsquiz.py calls ask_question` because it conflated AST data from `mathsquiz-step2.py` in the same context batch. With the live API run, this issue did not reproduce (True Negative achieved). However, we observed a single False Negative where the agent missed that `ContextBudgetManager` implements a `Dropping Skill`. This indicates that while the context chunking is now strict enough to prevent conflation across files, it may occasionally drop long-tail semantic details if the prompt length triggers early truncation.