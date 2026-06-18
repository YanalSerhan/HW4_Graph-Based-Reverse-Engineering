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
| mathsquiz.py calls ask_question | False | True | FP |

## Metrics
- **True Positives (TP):** 11
- **False Positives (FP):** 1
- **True Negatives (TN):** 8
- **False Negatives (FN):** 0

- **Precision:** 0.92
- **Recall:** 1.00
- **F1 Score:** 0.96