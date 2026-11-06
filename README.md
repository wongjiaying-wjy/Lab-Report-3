[# 🎓 Scholarship Advisory System: Rule-Based Decision Support

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


## Application Features

### 1. Applicant Facts

Enter the applicant's six facts in the sidebar: CGPA, monthly family income, co-curricular score, community service hours, current semester, and disciplinary actions. You can also select an example applicant to automatically fill in the values. The applicant information is displayed as summary cards in the Evaluation tab.

Click **Evaluate applicant** to run the scholarship rules.

![Applicant facts](image/app_overview.png)

### 2. Scholarship Decision and Matched Rules

The system displays the scholarship recommendation in a colour-coded banner: green for `AWARD_FULL`, blue for `AWARD_PARTIAL`, yellow for `REVIEW`, and red for `REJECT`.

The result includes the reason, winning rule, and its priority. All matching rules are displayed in priority order. If multiple rules match, the rule with the highest priority determines the recommendation.

![Scholarship decision](image/scholarship_results.png)

### 3. Rule Audit and Explanation

The rule audit table shows the evaluation of all five scholarship rules. Each rule is marked as **Fired** or **Not fired**, together with its priority and the number of conditions satisfied.

For matched rules, you can expand the rule to view each condition, the applicant's actual value, and whether the condition passed. This makes the scholarship recommendation transparent and explainable.

![Rule audit](image/rule_audit.png)

### 4. CGPA What-if Analysis

The what-if analysis evaluates how the scholarship recommendation changes when the applicant's CGPA is adjusted while all other facts remain unchanged.

The results are displayed in a table showing different CGPA values, scholarship decisions, and the corresponding deciding rules.

![CGPA what-if analysis](image/what_if_analysis.png)

### 5. Editable Scholarship Rules

The **Rules (JSON editor)** tab contains the five predefined scholarship rules from the lab requirement. Each rule includes a name, priority, conditions, and action.

Users can modify the rule configuration without changing the Python source code. The system validates the JSON structure and displays errors if the configuration is invalid. Evaluation is disabled until the errors are corrected.

A **Reset rules to case-study defaults** button restores the original rules.

![JSON rule editor](image/json_editor.png)

### 6. How It Works

The **How it works** dropdown explains the rule-based inference process, including fact collection, IF–THEN rule matching, priority-based conflict resolution, scholarship decisions, and default handling.

The explanation is collapsed by default to keep the interface clean.

![How it works](image/how_it_works.png)


## How to Run

```bash
pip install -r requirements.txt
streamlit run SD24048_Lab3.py
```

The app usually opens at http://localhost:8501.

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
](https://lab-report-3-4tzykpqy2deq68nppsiztr.streamlit.app/)
