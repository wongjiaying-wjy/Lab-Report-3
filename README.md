# 🎓 Scholarship Advisory System: Rule-Based Decision Support

**BSD3513 Introduction to Artificial Intelligence · Lab Report 3**

**SD24048 WONG JIA YING**

🌐 **Live App:** [https://lab-report-3-4tzykpqy2deq68nppsiztr.streamlit.app/](https://lab-report-3-4tzykpqy2deq68nppsiztr.streamlit.app/)

💻 **Source Code:** [https://github.com/wongjiaying-wjy/Lab-Report-3](https://github.com/wongjiaying-wjy/Lab-Report-3)

![App overview](image/app_overview.png)

## About

An interactive Streamlit application that uses a rule-based expert system to evaluate scholarship eligibility based on predefined conditions from the case study. The system considers six applicant facts: CGPA, co-curricular involvement score, monthly family income, community service hours, current semester, and disciplinary actions.

The knowledge base contains **five predefined IF–THEN rules** with different priorities. The system evaluates applicant information against these rules and recommends one of four outcomes: **AWARD_FULL, AWARD_PARTIAL, REVIEW, or REJECT**. It also explains which rules matched and why a particular decision was made.

## Default Rules

**Original rules from the lab requirement (loaded by default)**

| Rule | Priority | Conditions | Decision |
|---|---|---|---|
| Top merit candidate | 100 | CGPA ≥ 3.7, co-curricular score ≥ 80, income ≤ RM8,000, disciplinary actions = 0 | AWARD_FULL |
| Good candidate – partial scholarship | 80 | CGPA ≥ 3.3, co-curricular score ≥ 60, income ≤ RM12,000, disciplinary actions ≤ 1 | AWARD_PARTIAL |
| Need-based review | 70 | CGPA ≥ 2.5, income ≤ RM4,000 | REVIEW |
| Low CGPA – not eligible | 95 | CGPA < 2.5 | REJECT |
| Serious disciplinary record | 90 | Disciplinary actions ≥ 2 | REJECT |

**Adjustable applicant facts**

| Variable | Default | Range |
|---|---|---|
| CGPA | 3.50 | 0.00 to 4.00 |
| Co-curricular score | 70 | 0 to 100 |
| Monthly family income | RM6,000 | RM0 to RM100,000 |
| Community service hours | 30 | 0 to 10,000 |
| Current semester | 4 | 1 to 20 |
| Disciplinary actions | 0 | 0 to 20 |

Community service hours and current semester are collected but do not affect scholarship decisions under the five original rules.

## Key Features

- Five predefined scholarship rules with priorities and IF–THEN conditions.
- Six applicant input fields with example applicant profiles.
- Four possible recommendations: full scholarship, partial scholarship, manual review, and rejection.
- Priority-based conflict resolution when multiple rules match.
- Detailed explanations showing matched rules, conditions, and decision reasons.
- Audit table displaying the evaluation status of every rule.
- Editable JSON knowledge base with validation and reset functionality.
- Batch evaluation using CSV uploads with downloadable results.
- Summary of batch scholarship decisions using tables and a bar chart.
- What-if analysis showing how different CGPA values affect scholarship recommendations.
- "How to use" guide and explanation of the rule-based inference process.

## Screenshots

**Application overview**

![App overview](image/app_overview.png)

**Scholarship recommendation and rule evaluation**

![Scholarship results](image/scholarship_results.png)

**JSON rule configuration**

![JSON editor](image/json_editor.png)

**Batch evaluation**

![Batch evaluation](image/batch_evaluation.png)

## How to Run

```bash
pip install -r requirements.txt
streamlit run SD24048_Lab3.py
```

The app usually opens at http://localhost:8501.

## How to Use the App

1. Select an example applicant or enter the six applicant facts in the sidebar.
2. Click **Evaluate applicant** to evaluate scholarship eligibility.
3. Read the scholarship recommendation, winning rule, and explanation.
4. Review the matched rules and audit table to understand the decision.
5. Open the **Rules (JSON editor)** tab to modify the rules or reset the original configuration.
6. Use **Batch evaluation** to upload a CSV file and evaluate multiple applicants.
7. Review the what-if analysis to observe how changing CGPA affects the scholarship recommendation.

## How the Rule-Based System Works

1. **Knowledge representation:** The system stores five scholarship rules in JSON format. Each rule contains a name, priority, conditions, and action.
2. **Fact collection:** The system collects CGPA, co-curricular score, family income, community service hours, semester, and disciplinary actions.
3. **Condition evaluation:** The inference engine compares applicant facts with rule conditions using logical operators such as >=, <=, <, and ==.
4. **Rule matching:** A rule fires only when all its conditions are satisfied using AND logic.
5. **Conflict resolution:** If multiple rules match, the rule with the highest priority determines the recommendation. Equal priorities retain the original JSON order.
6. **Decision generation:** The selected rule produces a scholarship recommendation and an explanation.
7. **Default handling:** If no rule matches, the system recommends REVIEW for further consideration by the scholarship committee.
8. **Explanation:** The application displays the winning rule, matched conditions, and audit results to make the decision transparent.

## Example Test Cases

| Case | CGPA | Co-curricular Score | Income (RM) | Disciplinary Actions | Expected Decision |
|---|---|---|---|---|---|
| Top merit student | 3.85 | 90 | 6,000 | 0 | AWARD_FULL |
| Good student, moderate need | 3.50 | 70 | 10,000 | 1 | AWARD_PARTIAL |
| High need, borderline CGPA | 2.80 | 40 | 3,000 | 0 | REVIEW |
| Low CGPA | 2.20 | 85 | 3,000 | 0 | REJECT |
| Serious disciplinary record | 3.90 | 95 | 5,000 | 2 | REJECT |
| No matching rule | 3.00 | 50 | 10,000 | 0 | REVIEW |

The last case uses the fallback REVIEW recommendation because none of the five predefined rules matches.

## Repository Structure

```text
Lab-Report-3/
├── SD24048_Lab3.py
├── requirements.txt
├── README.md
└── image/
    ├── app_overview.png
    ├── scholarship_results.png
    ├── json_editor.png
    └── batch_evaluation.png
```

## Built with

Python · Streamlit · pandas · JSON

## Complexity Note

The rule-based inference engine evaluates the conditions of each rule against the applicant's facts. If there are R rules and each rule contains at most C conditions, rule matching requires **O(R × C)** operations. Sorting the matched rules adds at most **O(R log R)** time.

The five original rules contain a total of 13 conditions. The system is deterministic: the same applicant facts and rule configuration produce the same recommendation.
