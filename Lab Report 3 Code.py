import json
import operator
import streamlit as st

st.set_page_config(page_title='Scholarship Advisory System', page_icon='🎓', layout='wide')

DEFAULT_RULES = [
    {'name':'Top merit candidate','priority':100,'conditions':[['cgpa','>=',3.7],['co_curricular_score','>=',80],['family_income','<=',8000],['disciplinary_actions','==',0]],'action':{'decision':'AWARD_FULL','reason':'Excellent academic & co-curricular performance, with acceptable need'}},
    {'name':'Good candidate - partial scholarship','priority':80,'conditions':[['cgpa','>=',3.3],['co_curricular_score','>=',60],['family_income','<=',12000],['disciplinary_actions','<=',1]],'action':{'decision':'AWARD_PARTIAL','reason':'Good academic & involvement record with moderate need'}},
    {'name':'Need-based review','priority':70,'conditions':[['cgpa','>=',2.5],['family_income','<=',4000]],'action':{'decision':'REVIEW','reason':'High need but borderline academic score'}},
    {'name':'Low CGPA – not eligible','priority':95,'conditions':[['cgpa','<',2.5]],'action':{'decision':'REJECT','reason':'CGPA below minimum scholarship requirement'}},
    {'name':'Serious disciplinary record','priority':90,'conditions':[['disciplinary_actions','>=',2]],'action':{'decision':'REJECT','reason':'Too many disciplinary records'}}
]
OPS = {'==':operator.eq,'!=':operator.ne,'>':operator.gt,'>=':operator.ge,'<':operator.lt,'<=':operator.le,'in':lambda a,b:a in b,'not_in':lambda a,b:a not in b}
FIELDS = {'cgpa','family_income','co_curricular_score','community_service_hours','semester','disciplinary_actions'}
DECISIONS = {'AWARD_FULL','AWARD_PARTIAL','REVIEW','REJECT'}

def validate_rules(rules):
    if not isinstance(rules,list) or not rules:
        return 'Rules must be a non-empty JSON array.'
    names=set()
    for i,rule in enumerate(rules,1):
        if not isinstance(rule,dict): return f'Rule {i} must be a JSON object.'
        name=rule.get('name')
        if not isinstance(name,str) or not name.strip(): return f'Rule {i} needs a valid name.'
        if name in names: return f'Duplicate rule name: {name}'
        names.add(name)
        if type(rule.get('priority')) is not int: return f'Rule {i} priority must be an integer.'
        conditions=rule.get('conditions')
        if not isinstance(conditions,list) or not conditions: return f'Rule {i} needs at least one condition.'
        for c in conditions:
            if not isinstance(c,list) or len(c)!=3: return f'Rule {i} has an invalid condition.'
            field,op,value=c
            if not isinstance(field,str) or field not in FIELDS: return f'Rule {i} has an unknown field.'
            if not isinstance(op,str) or op not in OPS: return f'Rule {i} has an invalid operator.'
            if op in ('in','not_in'):
                if not isinstance(value,list) or any(type(v) not in (int,float) for v in value): return f"Rule {i}: '{op}' requires a numeric list."
            elif type(value) not in (int,float): return f'Rule {i} condition value must be numeric.'
        action=rule.get('action')
        if not isinstance(action,dict): return f'Rule {i} needs an action.'
        if not isinstance(action.get('decision'),str) or action['decision'] not in DECISIONS: return f'Rule {i} has an invalid decision.'
        if not isinstance(action.get('reason'),str) or not action['reason'].strip(): return f'Rule {i} needs a valid reason.'
    return None

def evaluate_condition(facts,condition):
    field,op,value=condition
    try: return bool(OPS[op](facts[field],value))
    except (KeyError,TypeError,ValueError): return False

def run_rules(facts,rules):
    matched=[r for r in rules if all(evaluate_condition(facts,c) for c in r['conditions'])]
    matched.sort(key=lambda r:r['priority'],reverse=True)
    if matched: return matched[0]['action'],matched
    return {'decision':'REVIEW','reason':'No rule matched; refer to the scholarship committee'},[]

st.title('🎓 Scholarship Advisory System')
st.caption('BSD3513 Introduction to Artificial Intelligence · Lab Report 3 · SD24048 WONG JIA YING')
st.write('A rule-based expert system for evaluating university scholarship eligibility using predefined IF–THEN rules.')
with st.sidebar:
    st.header('👤 Applicant Facts')
    cgpa=st.number_input('CGPA',0.0,4.0,3.50,0.01,format='%.2f')
    income=st.number_input('Monthly family income (RM)',min_value=0,value=6000,step=100)
    co_score=st.number_input('Co-curricular score (0–100)',min_value=0,max_value=100,value=70)
    service_hours=st.number_input('Community service hours',min_value=0,value=30)
    semester=st.number_input('Current semester',min_value=1,value=4)
    disciplinary=st.number_input('Disciplinary actions',min_value=0,value=0)
facts={'cgpa':float(cgpa),'family_income':int(income),'co_curricular_score':int(co_score),'community_service_hours':int(service_hours),'semester':int(semester),'disciplinary_actions':int(disciplinary)}

st.subheader('📝 Scholarship Rules (JSON Editor)')
st.caption('The five predefined scholarship rules are loaded by default. You can edit the conditions, priorities, and decisions.')
def default_text(): return json.dumps(DEFAULT_RULES,indent=2,ensure_ascii=False)
if 'rules_text' not in st.session_state: st.session_state.rules_text=default_text()
def reset_rules(): st.session_state.rules_text=default_text()
rules_text=st.text_area('Edit rules here',key='rules_text',height=250)
st.button('Reset Rules',on_click=reset_rules)
try:
    rules=json.loads(rules_text)
    error=validate_rules(rules)
except json.JSONDecodeError as e:
    rules=None
    error=f'Invalid JSON syntax: {e.msg} (line {e.lineno}, column {e.colno})'
if error: st.error(error)
else: st.success(f'Valid JSON: {len(rules)} scholarship rules loaded.')
with st.expander('👤 View Applicant Facts',expanded=False): st.json(facts)
with st.expander('💡 How it works',expanded=False):
    st.markdown('''1. **Applicant facts:** Enter six student details.\n2. **Knowledge base:** Five predefined IF–THEN rules stored in JSON.\n3. **Rule matching:** Every condition in a rule must be true (AND).\n4. **Conflict resolution:** The highest-priority matching rule wins.\n5. **Decision:** The app recommends AWARD_FULL, AWARD_PARTIAL, REVIEW, or REJECT with an explanation.\n6. **Default:** If no rule matches, the recommendation is REVIEW.''')
run=st.button('Evaluate Applicant',type='primary',disabled=bool(error),use_container_width=True)
if run:
    action,matched=run_rules(facts,rules)
    st.divider()
    left,right=st.columns(2)
    with left:
        st.subheader('🎓 Scholarship Decision')
        decision=action['decision']
        message=f"**{decision.replace('_',' ')}** — {action['reason']}"
        if decision=='AWARD_FULL': st.success(message)
        elif decision=='AWARD_PARTIAL': st.info(message)
        elif decision=='REJECT': st.error(message)
        else: st.warning(message)
        if matched:
            st.write(f"**Winning rule:** {matched[0]['name']}")
            st.write(f"**Priority:** {matched[0]['priority']}")
        else: st.write('**Winning rule:** None (default REVIEW)')
    with right:
        st.subheader('📋 Matched Rules (by Priority)')
        if not matched: st.info('No predefined rule matched.')
        for i,rule in enumerate(matched,1):
            st.write(f"**{i}. {rule['name']}** (Priority: {rule['priority']})")
            with st.expander(f'View Conditions - Rule {i}'):
                for field,op,value in rule['conditions']:
                    status='✅ Pass' if evaluate_condition(facts,[field,op,value]) else '❌ Fail'
                    st.write(f'{status}: {field} {op} {value} (Applicant: {facts[field]})')
    st.caption('The highest-priority matching rule determines the recommendation. Final decisions remain with the university committee.')
else:
    st.info('Enter the applicant details and click **Evaluate Applicant**.')
