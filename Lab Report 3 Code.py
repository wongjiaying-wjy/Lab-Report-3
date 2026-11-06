import io
import json
import operator
from typing import Any, Dict, List, Tuple
 
import pandas as pd
import streamlit as st
 
# ======================================================================
# 1) Knowledge base: rules (exactly as given in the case study)
# ======================================================================
DEFAULT_RULES_JSON = """[
  {
    "name": "Top merit candidate",
    "priority": 100,
    "conditions": [
      ["cgpa", ">=", 3.7],
      ["co_curricular_score", ">=", 80],
      ["family_income", "<=", 8000],
      ["disciplinary_actions", "==", 0]
    ],
    "action": {
      "decision": "AWARD_FULL",
      "reason": "Excellent academic & co-curricular performance, with acceptable need"
    }
  },
  {
    "name": "Good candidate - partial scholarship",
    "priority": 80,
    "conditions": [
      ["cgpa", ">=", 3.3],
      ["co_curricular_score", ">=", 60],
      ["family_income", "<=", 12000],
      ["disciplinary_actions", "<=", 1]
    ],
    "action": {
      "decision": "AWARD_PARTIAL",
      "reason": "Good academic & involvement record with moderate need"
    }
  },
  {
    "name": "Need-based review",
    "priority": 70,
    "conditions": [
      ["cgpa", ">=", 2.5],
      ["family_income", "<=", 4000]
    ],
    "action": {
      "decision": "REVIEW",
      "reason": "High need but borderline academic score"
    }
  },
  {
    "name": "Low CGPA – not eligible",
    "priority": 95,
    "conditions": [
      ["cgpa", "<", 2.5]
    ],
    "action": {
      "decision": "REJECT",
      "reason": "CGPA below minimum scholarship requirement"
    }
  },
  {
    "name": "Serious disciplinary record",
    "priority": 90,
    "conditions": [
      ["disciplinary_actions", ">=", 2]
    ],
    "action": {
      "decision": "REJECT",
      "reason": "Too many disciplinary records"
    }
  }
]"""
DEFAULT_RULES: List[Dict[str, Any]] = json.loads(DEFAULT_RULES_JSON)
 
# ======================================================================
# 2) Rule engine
# ======================================================================
OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}
 
FACT_FIELDS = ["cgpa", "co_curricular_score", "family_income", "disciplinary_actions"]
 
DECISION_STYLE = {          # decision -> (icon, colour function name)
    "AWARD_FULL": ("🏆", "success"),
    "AWARD_PARTIAL": ("🎓", "info"),
    "REVIEW": ("🔎", "warning"),
    "REJECT": ("⛔", "error"),
}
 
 
def check_condition(facts: Dict[str, Any], cond: List[Any]) -> Tuple[bool, Any]:
    """Evaluate [field, op, value]. Returns (passed, actual_value)."""
    if not isinstance(cond, list) or len(cond) != 3:
        return False, None
    field, op, value = cond
    if field not in facts or op not in OPS:
        return False, None
    try:
        return bool(OPS[op](facts[field], value)), facts[field]
    except Exception:
        return False, facts[field]
 
 
def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """All conditions must be true (AND)."""
    return all(check_condition(facts, c)[0] for c in rule.get("conditions", []))
 
 
def run_rules(facts: Dict[str, Any], rules: List[Dict[str, Any]]):
    """Returns (best_action, winning_rule, fired_rules_sorted_by_priority)."""
    fired = [r for r in rules if rule_matches(facts, r)]
    if not fired:
        return {"decision": "REVIEW", "reason": "No rule matched - refer to the committee"}, None, []
    fired = sorted(fired, key=lambda r: r.get("priority", 0), reverse=True)  # stable: ties keep file order
    return fired[0].get("action", {"decision": "REVIEW", "reason": "No action"}), fired[0], fired
 
 
def validate_rules(rules: Any) -> List[str]:
    """Return a list of human-readable problems (empty list = rules are fine)."""
    if not isinstance(rules, list):
        return ["Rules must be a JSON array [ ... ]."]
    problems = []
    for i, r in enumerate(rules, start=1):
        label = f"Rule {i}"
        if not isinstance(r, dict):
            problems.append(f"{label}: must be an object.")
            continue
        label = f"Rule {i} ({r.get('name', 'unnamed')})"
        if "conditions" not in r or not isinstance(r["conditions"], list):
            problems.append(f"{label}: needs a 'conditions' list.")
        else:
            for c in r["conditions"]:
                if not (isinstance(c, list) and len(c) == 3):
                    problems.append(f"{label}: condition {c} must look like [field, operator, value].")
                    continue
                if c[0] not in FACT_FIELDS:
                    problems.append(f"{label}: unknown field '{c[0]}' (use {', '.join(FACT_FIELDS)}).")
                if c[1] not in OPS:
                    problems.append(f"{label}: unknown operator '{c[1]}' (use {', '.join(OPS)}).")
        if not isinstance(r.get("action"), dict) or "decision" not in r.get("action", {}):
            problems.append(f"{label}: needs an 'action' with a 'decision'.")
    return problems
 
 
def explain_rule(facts: Dict[str, Any], rule: Dict[str, Any]) -> pd.DataFrame:
    """Condition-by-condition table for one rule."""
    rows = []
    for c in rule.get("conditions", []):
        ok, actual = check_condition(facts, c)
        field, op, value = (c + [None, None, None])[:3] if isinstance(c, list) else (str(c), "", "")
        rows.append({"Condition": f"{field} {op} {value}", "Applicant value": actual,
                     "Result": "✅ pass" if ok else "❌ fail"})
    return pd.DataFrame(rows)
 
 
def show_decision(decision: str, reason: str):
    icon, style = DECISION_STYLE.get(decision, ("ℹ️", "warning"))
    getattr(st, style)(f"{icon} **{decision.replace('_', ' ')}** — {reason}")
 
 
# ======================================================================
# 3) Streamlit UI
# ======================================================================
st.set_page_config(page_title="Scholarship Advisory System", page_icon="🎓", layout="wide")
 
PRESETS = {
    "Custom (enter your own)": None,
    "Top merit student": dict(cgpa=3.85, co=90, income=6000, disc=0),
    "Good student, moderate need": dict(cgpa=3.5, co=70, income=10000, disc=1),
    "High need, borderline CGPA": dict(cgpa=2.8, co=40, income=3000, disc=0),
    "Low CGPA": dict(cgpa=2.2, co=85, income=3000, disc=0),
    "Serious disciplinary record": dict(cgpa=3.9, co=95, income=5000, disc=2),
    "No rule matches": dict(cgpa=3.0, co=50, income=10000, disc=0),
}
INIT = dict(cgpa=3.50, co=70, income=6000, disc=0)
 
for k, v in INIT.items():
    st.session_state.setdefault(k, v)
st.session_state.setdefault("rules_text", DEFAULT_RULES_JSON)
st.session_state.setdefault("preset", "Custom (enter your own)")
 
 
def load_preset():
    p = PRESETS[st.session_state["preset"]]
    if p:
        for k, v in p.items():
            st.session_state[k] = v
 
 
def reset_rules():
    st.session_state["rules_text"] = DEFAULT_RULES_JSON
 
 
st.title("🎓 Scholarship Advisory System")
st.caption("A rule-based expert system that helps the university decide the eligibility and type of "
           "scholarship for each applicant. Enter the applicant's facts, edit the rules if needed, and evaluate.")
 
# ---------------- Sidebar: facts + how to use ----------------
with st.sidebar:
    st.header("👤 Applicant Facts")
    st.selectbox("Load an example applicant", list(PRESETS), key="preset", on_change=load_preset,
                 help="Quickly fill in the facts for a typical case.")
    cgpa = st.number_input("CGPA (0.00 – 4.00)", 0.0, 4.0, step=0.01, key="cgpa", format="%.2f")
    co = st.number_input("Co-curricular score (0 – 100)", 0, 100, step=1, key="co")
    income = st.number_input("Family income (MYR / month)", 0, 100000, step=100, key="income")
    disc = st.number_input("Disciplinary actions (count)", 0, 20, step=1, key="disc")
    evaluate = st.button("Evaluate applicant", type="primary", use_container_width=True)
 
    st.divider()
    st.header("📖 How to use")
    st.info(
        "1. Pick an example or type the applicant's facts.\n"
        "2. (Optional) edit the rules in the **Rules** tab.\n"
        "3. Click **Evaluate applicant**.\n"
        "4. Read the decision and see which rules fired.\n"
        "5. Use **Batch evaluation** to score many applicants from a CSV file."
    )
 
facts = {
    "cgpa": float(cgpa),
    "co_curricular_score": int(co),
    "family_income": float(income),
    "disciplinary_actions": int(disc),
}
 
# ---------------- Parse + validate rules ----------------
rules = DEFAULT_RULES
rules_ok = True
try:
    parsed = json.loads(st.session_state["rules_text"])
    problems = validate_rules(parsed)
    if problems:
        rules_ok = False
    else:
        rules = parsed
except json.JSONDecodeError as e:
    parsed, problems, rules_ok = None, [f"JSON syntax error at line {e.lineno}, column {e.colno}: {e.msg}"], False
 
tab_eval, tab_rules, tab_batch, tab_info = st.tabs(
    ["✅ Evaluation", "📝 Rules (JSON editor)", "📦 Batch evaluation", "🧠 How it works"])
 
# ================= Tab 1: evaluation =================
with tab_eval:
    st.subheader("Applicant facts")
    m = st.columns(4)
    m[0].metric("CGPA", f"{facts['cgpa']:.2f}")
    m[1].metric("Co-curricular score", facts["co_curricular_score"])
    m[2].metric("Family income (MYR)", f"{facts['family_income']:,.0f}")
    m[3].metric("Disciplinary actions", facts["disciplinary_actions"])
 
    if not rules_ok:
        st.error("The rules in the editor have problems, so the default rules are being used.")
 
    if evaluate:
        action, winner, fired = run_rules(facts, rules)
        left, right = st.columns([1, 1])
 
        with left:
            st.subheader("Decision")
            show_decision(action.get("decision", "REVIEW"), action.get("reason", "-"))
            if winner:
                st.caption(f"Decided by **{winner.get('name', '(unnamed)')}** "
                           f"(priority {winner.get('priority', 0)}). "
                           f"{len(fired)} of {len(rules)} rules matched; the highest priority wins.")
            else:
                st.caption("No rule matched, so the system falls back to REVIEW.")
 
        with right:
            st.subheader("Matched rules (by priority)")
            if not fired:
                st.info("No rules matched.")
            for i, r in enumerate(fired, start=1):
                crown = " 👑" if i == 1 else ""
                with st.expander(f"{i}. {r.get('name', '(unnamed)')} — priority {r.get('priority', 0)}{crown}"):
                    st.write(f"Action: **{r.get('action', {}).get('decision')}** — "
                             f"{r.get('action', {}).get('reason', '')}")
                    st.dataframe(explain_rule(facts, r), hide_index=True, use_container_width=True)
 
        st.subheader("Audit of every rule")
        audit = []
        for r in sorted(rules, key=lambda r: r.get("priority", 0), reverse=True):
            checks = [check_condition(facts, c)[0] for c in r.get("conditions", [])]
            audit.append({
                "Rule": r.get("name", "(unnamed)"),
                "Priority": r.get("priority", 0),
                "Decision if matched": r.get("action", {}).get("decision"),
                "Conditions met": f"{sum(checks)}/{len(checks)}",
                "Status": "✅ Fired" if all(checks) else "❌ Not fired",
            })
        st.dataframe(pd.DataFrame(audit), hide_index=True, use_container_width=True)
        st.caption("Rules that did not fire show how many of their conditions were still satisfied.")
 
        # Sensitivity: how would the decision change with a different CGPA?
        st.subheader("What-if: how the decision changes with CGPA")
        sweep = []
        for g in [x / 10 for x in range(20, 41, 2)]:
            a, w, _ = run_rules({**facts, "cgpa": g}, rules)
            sweep.append({"CGPA": g, "Decision": a.get("decision"), "Rule": w.get("name") if w else "—"})
        st.dataframe(pd.DataFrame(sweep), hide_index=True, use_container_width=True)
        st.caption("All other facts stay the same. Useful to see the CGPA thresholds of the rules.")
    else:
        st.info("Set the applicant facts in the sidebar and click **Evaluate applicant**.")
 
# ================= Tab 2: JSON editor =================
with tab_rules:
    st.subheader("Rules (JSON editor)")
    st.caption("The editor starts with the rules given in the case study. A rule fires when ALL its "
               "conditions are true; if several rules fire, the one with the highest priority decides. "
               f"Available facts: {', '.join(FACT_FIELDS)}. Operators: {', '.join(OPS)}.")
    st.text_area("Edit rules here", key="rules_text", height=520)
    st.button("Reset rules to the case-study defaults", on_click=reset_rules)
    if rules_ok:
        st.success(f"Rules are valid — {len(rules)} rules loaded.")
        st.dataframe(pd.DataFrame([{
            "Priority": r.get("priority", 0), "Rule": r.get("name"),
            "Conditions": " AND ".join(f"{c[0]} {c[1]} {c[2]}" for c in r["conditions"]),
            "Decision": r["action"]["decision"],
        } for r in sorted(rules, key=lambda r: r.get("priority", 0), reverse=True)]),
            hide_index=True, use_container_width=True)
    else:
        for p in problems:
            st.error(p)
 
# ================= Tab 3: batch =================
with tab_batch:
    st.subheader("Batch evaluation")
    st.caption("Upload a CSV with the columns " + ", ".join(f"`{f}`" for f in FACT_FIELDS) +
               " to evaluate many applicants at once.")
    template = pd.DataFrame([
        [3.85, 90, 6000, 0], [3.5, 70, 10000, 1], [2.8, 40, 3000, 0], [2.2, 85, 3000, 0], [3.9, 95, 5000, 2],
    ], columns=FACT_FIELDS)
    st.download_button("Download CSV template", template.to_csv(index=False),
                       file_name="applicants_template.csv", mime="text/csv")
    up = st.file_uploader("Upload applicants CSV", type="csv")
    if up is not None:
        try:
            df = pd.read_csv(io.BytesIO(up.getvalue()))
            missing = [f for f in FACT_FIELDS if f not in df.columns]
            if missing:
                st.error(f"Missing columns: {', '.join(missing)}")
            else:
                out = []
                for _, row in df.iterrows():
                    a, w, _ = run_rules({f: row[f] for f in FACT_FIELDS}, rules)
                    out.append({"Decision": a.get("decision"), "Deciding rule": w.get("name") if w else "—",
                                "Reason": a.get("reason")})
                result = pd.concat([df, pd.DataFrame(out)], axis=1)
                counts = result["Decision"].value_counts()
                c = st.columns(4)
                for col, d in zip(c, DECISION_STYLE):
                    col.metric(f"{DECISION_STYLE[d][0]} {d.replace('_', ' ').title()}", int(counts.get(d, 0)))
                st.dataframe(result, hide_index=True, use_container_width=True)
                st.bar_chart(counts)
                st.download_button("Download results", result.to_csv(index=False),
                                   file_name="scholarship_results.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Could not read the file: {e}")
 
# ================= Tab 4: explanation =================
with tab_info:
    st.subheader("How the rule-based system works")
    st.markdown("""
1. **Facts:** the applicant's CGPA, co-curricular score, family income and number of disciplinary actions.
2. **Rules (knowledge base):** each rule has *conditions* (IF part), a *priority* and an *action* (THEN part).
3. **Matching:** a rule fires only when **all** its conditions are true (AND).
4. **Conflict resolution:** if several rules fire, the rule with the **highest priority** decides the outcome.
5. **Default:** if no rule fires, the applicant goes to **REVIEW**.
""")
    st.subheader("Decisions")
    st.table(pd.DataFrame([
        ["AWARD_FULL", "Full scholarship"],
        ["AWARD_PARTIAL", "Partial scholarship"],
        ["REVIEW", "Needs manual review by the committee"],
        ["REJECT", "Not eligible"],
    ], columns=["Decision", "Meaning"]).set_index("Decision"))
    st.subheader("Why priorities matter")
    st.markdown("""
The rejection rules have high priority (*Low CGPA* = 95, *Serious disciplinary record* = 90), so a very
strong profile in one area cannot override a disqualifying problem in another. For example, an applicant
with a CGPA of 3.9 but 2 disciplinary actions is rejected.
""")
st.caption("Demo for a university lab exercise. Final scholarship decisions rest with the committee.")
