import io
import json
import math
import operator
from typing import Any

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Scholarship Advisory System", page_icon="🎓", layout="wide")

DEFAULT_RULES_JSON = '''[
  {
    "name": "Top merit candidate",
    "priority": 100,
    "conditions": [["cgpa", ">=", 3.7], ["co_curricular_score", ">=", 80], ["family_income", "<=", 8000], ["disciplinary_actions", "==", 0]],
    "action": {"decision": "AWARD_FULL", "reason": "Excellent academic & co-curricular performance, with acceptable need"}
  },
  {
    "name": "Good candidate - partial scholarship",
    "priority": 80,
    "conditions": [["cgpa", ">=", 3.3], ["co_curricular_score", ">=", 60], ["family_income", "<=", 12000], ["disciplinary_actions", "<=", 1]],
    "action": {"decision": "AWARD_PARTIAL", "reason": "Good academic & involvement record with moderate need"}
  },
  {
    "name": "Need-based review",
    "priority": 70,
    "conditions": [["cgpa", ">=", 2.5], ["family_income", "<=", 4000]],
    "action": {"decision": "REVIEW", "reason": "High need but borderline academic score"}
  },
  {
    "name": "Low CGPA – not eligible",
    "priority": 95,
    "conditions": [["cgpa", "<", 2.5]],
    "action": {"decision": "REJECT", "reason": "CGPA below minimum scholarship requirement"}
  },
  {
    "name": "Serious disciplinary record",
    "priority": 90,
    "conditions": [["disciplinary_actions", ">=", 2]],
    "action": {"decision": "REJECT", "reason": "Too many disciplinary records"}
  }
]'''
DEFAULT_RULES = json.loads(DEFAULT_RULES_JSON)

OPS = {
    "==": operator.eq, "!=": operator.ne,
    ">": operator.gt, ">=": operator.ge,
    "<": operator.lt, "<=": operator.le,
    "in": lambda actual, choices: actual in choices,
    "not_in": lambda actual, choices: actual not in choices,
}
FACT_FIELDS = [
    "cgpa", "co_curricular_score", "family_income",
    "community_service_hours", "semester", "disciplinary_actions"
]
INTEGER_FIELDS = {
    "co_curricular_score", "community_service_hours", "semester", "disciplinary_actions"
}
LIMITS = {
    "cgpa": (0, 4), "co_curricular_score": (0, 100),
    "family_income": (0, 100000), "community_service_hours": (0, 10000),
    "semester": (1, 20), "disciplinary_actions": (0, 20)
}
DECISIONS = {
    "AWARD_FULL": ("🏆", "success", "Full scholarship"),
    "AWARD_PARTIAL": ("🎓", "info", "Partial scholarship"),
    "REVIEW": ("🔎", "warning", "Manual review"),
    "REJECT": ("⛔", "error", "Not eligible"),
}


def validate_rules(rules: Any) -> list[str]:
    """Return descriptive errors. An empty list means rules are valid."""
    if not isinstance(rules, list) or not rules:
        return ["Rules must be a non-empty JSON array."]
    errors = []
    seen_names = set()
    for i, rule in enumerate(rules, 1):
        label = f"Rule {i}"
        if not isinstance(rule, dict):
            errors.append(f"{label}: expected a JSON object.")
            continue
        name = rule.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{label}: name must be non-empty text.")
        elif name in seen_names:
            errors.append(f"{label}: duplicate name '{name}'.")
        else:
            seen_names.add(name)
        if type(rule.get("priority")) is not int:
            errors.append(f"{label}: priority must be an integer.")
        conditions = rule.get("conditions")
        if not isinstance(conditions, list) or not conditions:
            errors.append(f"{label}: conditions must be a non-empty list.")
        else:
            for j, cond in enumerate(conditions, 1):
                where = f"{label}, condition {j}"
                if not isinstance(cond, list) or len(cond) != 3:
                    errors.append(f"{where}: use [field, operator, value].")
                    continue
                field, op, threshold = cond
                if not isinstance(field, str) or field not in FACT_FIELDS:
                    errors.append(f"{where}: unknown field {field!r}.")
                if not isinstance(op, str) or op not in OPS:
                    errors.append(f"{where}: unsupported operator {op!r}.")
                if isinstance(op, str) and op in ("in", "not_in"):
                    if not isinstance(threshold, list) or not threshold or any(
                        type(x) not in (int, float) or not math.isfinite(x)
                        for x in threshold
                    ):
                        errors.append(f"{where}: membership operator needs a non-empty numeric list.")
                elif type(threshold) not in (int, float) or not math.isfinite(threshold):
                    errors.append(f"{where}: threshold must be a finite number.")
        action = rule.get("action")
        if not isinstance(action, dict):
            errors.append(f"{label}: action must be an object.")
        else:
            decision = action.get("decision")
            if not isinstance(decision, str) or decision not in DECISIONS:
                errors.append(f"{label}: invalid decision.")
            reason = action.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"{label}: reason must be non-empty text.")
    return errors


def check_condition(facts: dict, cond: list) -> bool:
    field, op, threshold = cond
    return bool(OPS[op](facts[field], threshold))


def run_rules(facts: dict, rules: list):
    """Return action, winning rule, matching rules, and complete audit."""
    fired = []
    audit = []
    for rule in rules:
        checks = [check_condition(facts, c) for c in rule["conditions"]]
        matched = all(checks)
        audit.append({
            "Rule": rule["name"], "Priority": rule["priority"],
            "Decision if matched": rule["action"]["decision"],
            "Conditions met": f"{sum(checks)}/{len(checks)}",
            "Status": "✅ Fired" if matched else "❌ Not fired",
        })
        if matched:
            fired.append(rule)
    # Python's sort is stable, preserving JSON order when priorities tie.
    fired.sort(key=lambda r: r["priority"], reverse=True)
    if fired:
        return fired[0]["action"], fired[0], fired, audit
    return {"decision": "REVIEW", "reason": "No rule matched; refer to the scholarship committee."}, None, [], audit


def explain_rule(facts: dict, rule: dict) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Condition": f"{field} {op} {value}",
            "Applicant value": facts[field],
            "Result": "✅ Pass" if check_condition(facts, [field, op, value]) else "❌ Fail"
        }
        for field, op, value in rule["conditions"]
    ])


def validate_batch(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Check required columns, missing values, ranges, and integer counts."""
    missing = [field for field in FACT_FIELDS if field not in df.columns]
    if missing:
        return df, ["Missing columns: " + ", ".join(missing)]
    if df.empty:
        return df, ["CSV must contain at least one applicant."]
    result = df.copy()
    errors = []
    for field in FACT_FIELDS:
        result[field] = pd.to_numeric(result[field], errors="coerce")
        minimum, maximum = LIMITS[field]
        invalid = result[field].isna() | ~result[field].map(math.isfinite)
        invalid |= (result[field] < minimum) | (result[field] > maximum)
        if field in INTEGER_FIELDS:
            invalid |= result[field].notna() & (result[field] % 1 != 0)
        if invalid.any():
            errors.append(f"{field}: invalid value(s) in CSV row(s) " + ", ".join(str(i + 2) for i in result.index[invalid]))
    return result, errors


PRESETS = {
    "Custom (enter your own)": None,
    "Top merit student": (3.85, 90, 6000, 30, 4, 0),
    "Good student, moderate need": (3.50, 70, 10000, 20, 4, 1),
    "High need, borderline CGPA": (2.80, 40, 3000, 50, 2, 0),
    "Low CGPA": (2.20, 85, 3000, 15, 3, 0),
    "Serious disciplinary record": (3.90, 95, 5000, 80, 5, 2),
    "No rule matches": (3.00, 50, 10000, 10, 4, 0),
}
INPUT_KEYS = ("cgpa", "co", "income", "hours", "semester", "disc")
for key, default in zip(INPUT_KEYS, (3.50, 70, 6000, 30, 4, 0)):
    st.session_state.setdefault(key, default)
st.session_state.setdefault("preset", "Custom (enter your own)")
st.session_state.setdefault("rules_text", DEFAULT_RULES_JSON)


def load_preset():
    preset = PRESETS[st.session_state["preset"]]
    if preset is not None:
        for key, value in zip(INPUT_KEYS, preset):
            st.session_state[key] = value


def reset_rules():
    st.session_state["rules_text"] = DEFAULT_RULES_JSON


# Parse rules BEFORE the sidebar button, so invalid rules disable evaluation.
try:
    parsed_rules = json.loads(st.session_state["rules_text"])
    rule_errors = validate_rules(parsed_rules)
except json.JSONDecodeError as exc:
    parsed_rules = None
    rule_errors = [f"JSON syntax error at line {exc.lineno}, column {exc.colno}: {exc.msg}"]
rules_ok = not rule_errors
rules = parsed_rules if rules_ok else None

st.title("🎓 Scholarship Advisory System")
st.caption("BSD3513 Introduction to Artificial Intelligence · Lab Report 3 · SD24048 WONG JIA YING")
st.info("This is a transparent decision-support demonstration. Final scholarship decisions belong to the university committee.")

with st.sidebar:
    st.header("👤 Applicant Facts")
    st.selectbox("Load an example applicant", list(PRESETS), key="preset", on_change=load_preset)
    cgpa = st.number_input("CGPA (0.00–4.00)", 0.0, 4.0, step=0.01, format="%.2f", key="cgpa")
    co = st.number_input("Co-curricular score (0–100)", 0, 100, step=1, key="co")
    income = st.number_input("Family income (MYR/month)", 0, 100000, step=100, key="income")
    hours = st.number_input("Community service hours", 0, 10000, step=1, key="hours")
    semester = st.number_input("Current semester", 1, 20, step=1, key="semester")
    disc = st.number_input("Disciplinary actions", 0, 20, step=1, key="disc")
    evaluate = st.button("Evaluate applicant", type="primary", use_container_width=True, disabled=not rules_ok)
    if not rules_ok:
        st.error("Fix the JSON rules in the Rules tab before evaluating.")
    st.divider()
    st.header("📖 How to use")
    st.write("1. Select an example or enter six applicant facts.\n\n2. Edit JSON rules if needed.\n\n3. Click **Evaluate applicant**.\n\n4. Review the decision and rule audit.\n\n5. Upload a CSV for batch evaluation.")

facts = {
    "cgpa": float(cgpa), "co_curricular_score": int(co),
    "family_income": float(income), "community_service_hours": int(hours),
    "semester": int(semester), "disciplinary_actions": int(disc)
}

tab_eval, tab_rules, tab_batch, tab_info = st.tabs([
    "✅ Evaluation", "📝 Rules (JSON editor)", "📦 Batch evaluation", "🧠 How it works"
])

with tab_eval:
    st.subheader("Applicant facts")
    first = st.columns(3)
    first[0].metric("CGPA", f"{facts['cgpa']:.2f}")
    first[1].metric("Co-curricular score", facts["co_curricular_score"])
    first[2].metric("Family income (MYR)", f"{facts['family_income']:,.0f}")
    second = st.columns(3)
    second[0].metric("Community service hours", facts["community_service_hours"])
    second[1].metric("Current semester", facts["semester"])
    second[2].metric("Disciplinary actions", facts["disciplinary_actions"])
    st.caption("Community service hours and semester are recorded but not used by the five original rules.")
    if evaluate and rules_ok:
        action, winner, fired, audit = run_rules(facts, rules)
        left, right = st.columns(2)
        with left:
            st.subheader("Scholarship decision")
            decision = action["decision"]
            icon, style, meaning = DECISIONS[decision]
            getattr(st, style)(f"{icon} **{decision} — {meaning}**: {action['reason']}")
            if winner:
                st.write(f"**Winning rule:** {winner['name']} (priority {winner['priority']})")
                st.caption(f"{len(fired)} of {len(rules)} rules matched; the highest priority wins.")
            else:
                st.caption("No rule matched; fallback recommendation is REVIEW.")
        with right:
            st.subheader("Matched rules")
            if not fired:
                st.info("No rules matched.")
            for index, rule in enumerate(fired, 1):
                with st.expander(f"{index}. {rule['name']} (priority {rule['priority']})" + (" 👑" if index == 1 else "")):
                    st.write(f"**Action:** {rule['action']['decision']}")
                    st.write(rule["action"]["reason"])
                    st.dataframe(explain_rule(facts, rule), hide_index=True, use_container_width=True)
        st.subheader("Audit of every rule")
        st.dataframe(pd.DataFrame(sorted(audit, key=lambda row: row["Priority"], reverse=True)), hide_index=True, use_container_width=True)
        st.subheader("What-if: decision changes with CGPA")
        sweep = []
        for g in [round(x / 10, 1) for x in range(20, 41, 2)]:
            result, deciding_rule, _, _ = run_rules({**facts, "cgpa": g}, rules)
            sweep.append({"CGPA": g, "Decision": result["decision"], "Rule": deciding_rule["name"] if deciding_rule else "Fallback"})
        st.dataframe(pd.DataFrame(sweep), hide_index=True, use_container_width=True)
        st.caption("All other applicant facts remain unchanged during the what-if analysis.")
    else:
        st.info("Enter applicant facts in the sidebar and click **Evaluate applicant**.")

with tab_rules:
    st.subheader("Rules (JSON editor)")
    st.caption("The five original case-study rules are loaded by default. Conditions within a rule use AND logic; the highest-priority matching rule wins.")
    st.text_area("Edit rules here", key="rules_text", height=520)
    st.button("Reset rules to case-study defaults", on_click=reset_rules)
    if rules_ok:
        st.success(f"Rules are valid — {len(rules)} rule(s) loaded.")
        st.dataframe(pd.DataFrame([
            {"Priority": r["priority"], "Rule": r["name"],
             "Conditions": " AND ".join(f"{c[0]} {c[1]} {c[2]}" for c in r["conditions"]),
             "Decision": r["action"]["decision"]}
            for r in sorted(rules, key=lambda r: r["priority"], reverse=True)
        ]), hide_index=True, use_container_width=True)
    else:
        for error in rule_errors:
            st.error(error)

with tab_batch:
    st.subheader("Batch evaluation")
    st.caption("Upload a CSV with all six required applicant fact columns.")
    template = pd.DataFrame([
        [3.85, 90, 6000, 30, 4, 0],
        [3.50, 70, 10000, 20, 4, 1],
        [2.80, 40, 3000, 50, 2, 0],
        [2.20, 85, 3000, 15, 3, 0],
        [3.90, 95, 5000, 80, 5, 2],
    ], columns=FACT_FIELDS)
    st.download_button("Download CSV template", template.to_csv(index=False), "applicants_template.csv", "text/csv")
    uploaded = st.file_uploader("Upload applicants CSV", type="csv")
    if uploaded is not None:
        if not rules_ok:
            st.error("Correct the JSON rules before batch evaluation.")
        else:
            try:
                df = pd.read_csv(io.BytesIO(uploaded.getvalue()))
                clean, batch_errors = validate_batch(df)
                if batch_errors:
                    for error in batch_errors:
                        st.error(error)
                else:
                    output = []
                    for _, row in clean.iterrows():
                        applicant = {field: row[field] for field in FACT_FIELDS}
                        action, winner, _, _ = run_rules(applicant, rules)
                        output.append({
                            "Decision": action["decision"],
                            "Deciding rule": winner["name"] if winner else "Fallback",
                            "Reason": action["reason"]
                        })
                    result = pd.concat([clean.reset_index(drop=True), pd.DataFrame(output)], axis=1)
                    counts = result["Decision"].value_counts()
                    columns = st.columns(4)
                    for col, decision in zip(columns, DECISIONS):
                        col.metric(f"{DECISIONS[decision][0]} {decision}", int(counts.get(decision, 0)))
                    st.dataframe(result, hide_index=True, use_container_width=True)
                    st.bar_chart(counts.rename_axis("Decision").rename("Applicants"))
                    st.download_button("Download results", result.to_csv(index=False), "scholarship_results.csv", "text/csv")
            except (pd.errors.ParserError, UnicodeError, ValueError, OSError) as exc:
                st.error(f"Could not read the CSV: {exc}")

with tab_info:
    st.subheader("How the rule-based system works")
    st.markdown("""
1. **Facts:** collect six applicant attributes.
2. **Knowledge base:** five JSON rules contain conditions, priorities and actions.
3. **Matching:** all conditions within a rule must be true (AND).
4. **Conflict resolution:** the highest-priority matching rule wins; equal priorities retain JSON order.
5. **Decision:** recommend AWARD_FULL, AWARD_PARTIAL, REVIEW or REJECT.
6. **Fallback:** if no rule matches, recommend REVIEW.
7. **Explanation:** show matched rules and a condition-by-condition audit.
""")
    st.table(pd.DataFrame([{"Decision": k, "Meaning": v[2]} for k, v in DECISIONS.items()]).set_index("Decision"))
    st.warning("Rule priorities are applied exactly as supplied in the lab. Editing rules may change the recommendation.")

st.caption("University lab demonstration only. Final scholarship decisions rest with the scholarship committee.")
