"""Evidence and decision requirements for experimental character reports v0.5."""
from copy import deepcopy
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION='character-rules-v0.5'
NUMERIC_IDS={'A1','B2','B3','E1','E2','E3','E4','E5','F1'}
FIELDS=('definition','required_inputs','evidence_protocol','decision_rule','missing_policy','range_policy',
        'weight_reason','regional_policy','freshness','review_trigger','cannot_infer','worked_example')

def load_contract():
    contract=json.loads((ROOT/'references'/'rule-protocols-v05.json').read_text(encoding='utf-8'))
    items=contract.get('items',[])
    if contract.get('version')!=VERSION or [i.get('id') for i in items]!=[a+str(n) for a in 'ABCDEF' for n in range(1,7)]:
        raise ValueError('Provide the complete ordered 36-item protocol contract')
    for item in items:
        for field in FIELDS:
            if not item.get(field):raise ValueError(f'{item["id"]}: missing protocol {field}')
    return contract

def _interval(value):
    if value is None:return None
    values=list(value) if isinstance(value,(list,tuple)) else [value,value]
    if len(values)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in values) or values[0]>values[1]:
        raise ValueError('Use a finite numeric value or ordered [low, high] interval')
    return values

def _linear(value,points):
    if value<=points[0][0]:return points[0][1]
    for (x1,y1),(x2,y2) in zip(points,points[1:]):
        if value<=x2:return y1+(y2-y1)*(value-x1)/(x2-x1)
    return points[-1][1]

def _band(value,bands):
    value=round(value,12)
    for band in bands:
        lo,hi=band.get('min'),band.get('max')
        if band.get('exact'):
            if value==lo:return band['score']
            continue
        low_ok=lo is None or (value>=lo if band.get('min_inclusive',True) else value>lo)
        high_ok=hi is None or (value<=hi if band.get('max_inclusive',False) else value<hi)
        if low_ok and high_ok:return band['score']
    raise ValueError('No declared score band covers the numeric value')

def numeric_result(identifier,inputs):
    rules=json.loads((ROOT/'references'/'rubric-v04.json').read_text(encoding='utf-8'))
    item=next(i for a in rules['axes'] for i in a['items'] if i['id']==identifier)
    rule=item.get('numeric_rule',{})
    missing={'score':None,'score_range':[0,100],'note':'必要原值或适用协议未齐，不填默认分'}
    if not isinstance(inputs,dict):return missing
    if identifier in {'A1','B2','B3'}:
        key={'A1':'height_cm','B2':'bench_1rm_kg','B3':'continuous_swim_m'}[identifier]
        values=_interval(inputs.get(key))
        if values is None:return missing
        if values[0]<0:raise ValueError('Measurements must be nonnegative')
        points=rule['points']
        if identifier=='B2':
            weight=inputs.get('body_weight_kg')
            if type(weight) not in (int,float) or not math.isfinite(weight) or weight<=0:return missing
            reference=inputs.get('strength_reference')
            if reference is not None:
                if not isinstance(reference,dict) or not str(reference.get('source_url','')).startswith('https://strengthlevel.com/') or not reference.get('population') or not reference.get('verified_at'):
                    raise ValueError('Registered strength references need source, population and verification date')
                rows=reference.get('rows',[])
                if not rows:raise ValueError('Register at least one source body-weight row')
                rows=sorted(rows,key=lambda row:row['body_weight_kg'])
                body_weights=[row['body_weight_kg'] for row in rows]
                if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in body_weights) or len(set(body_weights))!=len(body_weights):
                    raise ValueError('Source body-weight rows must be finite, positive and unique')
                for row in rows:
                    loads=row.get('loads_kg',[])
                    if len(loads)!=5 or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in loads) or any(a>=b for a,b in zip(loads,loads[1:])):
                        raise ValueError('A source strength row needs five increasing positive loads')
                exact=next((row for row in rows if row['body_weight_kg']==weight),None)
                if exact:loads=exact['loads_kg']
                else:
                    pair=next(((a,b) for a,b in zip(rows,rows[1:]) if a['body_weight_kg']<weight<b['body_weight_kg']),None)
                    if pair is None:return {**missing,'note':'没有对应或包围当前体重的原表行，不外推'}
                    a,b=pair;t=(weight-a['body_weight_kg'])/(b['body_weight_kg']-a['body_weight_kg'])
                    loads=[x+(y-x)*t for x,y in zip(a['loads_kg'],b['loads_kg'])]
                points=[[0,0],*zip(loads,[20,40,60,80,100])]
            elif weight!=85:
                return {**missing,'note':'内置卧推阈值仅对应男性85kg参考行；其他体重需先登记同源适用行，不硬套'}
        calculate=lambda value:_linear(value,points)
    elif identifier=='F1':
        amount=_interval(inputs.get('potential_support_cny'))
        if amount==[0,0]:return {'score':0,'score_range':[0,0],'note':'明确无可给本人的支援'}
        expenses=_interval(inputs.get('necessary_annual_expenses_cny'));access=_interval(inputs.get('access_score'))
        if amount is not None and amount[0]<0 or access is not None and (access[0]<0 or access[1]>100):
            raise ValueError('Invalid family-support inputs')
        points=rule['components'][0]['numeric_rule']['points']
        if access is None and amount is not None and expenses is not None and expenses[0]>0:
            return {'score':None,'score_range':[.5*_linear(amount[0]/expenses[1],points),.5*_linear(amount[1]/expenses[0],points)+50],
                    'note':'容量已知、可调用条件未知；保留另一半原权重范围，不补默认条件分'}
        if amount is None and access is not None:
            return {'score':None,'score_range':[.5*access[0],50+.5*access[1]],'note':'条件已知、支持容量未知；不补默认金额'}
        if amount is None or expenses is None or expenses[0]<=0 or access is None:return missing
        if amount[0]<0 or access[0]<0 or access[1]>100:raise ValueError('Invalid family-support inputs')
        low=.5*_linear(amount[0]/expenses[1],points)+.5*access[0]
        high=.5*_linear(amount[1]/expenses[0],points)+.5*access[1]
        mid=.5*_linear(sum(amount)/sum(expenses),points)+.25*sum(access)
        return {'score':mid,'score_range':[low,high],'note':'容量与可调用条件各50%；潜在支持不计本人资产'}
    elif identifier=='E4':
        debt=_interval(inputs.get('monthly_debt_service_cny'));income=_interval(inputs.get('monthly_after_tax_income_cny'))
        if debt==[0,0] and inputs.get('confirmed_no_debt') is True:
            return {'score':100,'score_range':[100,100],'note':'明确无负债，仅偿付负担一项为100'}
        if debt==[0,0]:return {**missing,'note':'到期偿付为0但债务与期间状态未明确，保留待核对，不推断无负债'}
        if debt is None or income is None:return missing
        if debt[0]<0:raise ValueError('Debt service cannot be negative')
        if income[1]<=0 and debt[0]>0:return {'score':0,'score_range':[0,0],'note':'无正收入且有到期偿付'}
        if income[0]<=0:return missing
        values=[debt[0]/income[1],debt[1]/income[0]];calculate=lambda value:_band(value,rule['bands'])
    elif identifier=='E5':
        income=_interval(inputs.get('after_tax_income'));expenses=_interval(inputs.get('actual_expenses'))
        if income is None or expenses is None or income[0]<=0 or inputs.get('same_period') is not True:return missing
        if expenses[0]<0:raise ValueError('Actual expenses cannot be negative')
        values=[1-expenses[1]/income[0],1-expenses[0]/income[1]];calculate=lambda value:_band(value,rule['bands'])
    else:
        numerator=_interval(inputs.get(rule.get('numerator_field')));denominator=_interval(inputs.get(rule.get('denominator_field')))
        if numerator is None or denominator is None or denominator[0]<=0:return missing
        endpoints=[n/d for n in numerator for d in denominator]
        values=[min(endpoints),max(endpoints)];calculate=lambda value:_band(value,rule['bands'])
    scores=[calculate(value) for value in values]
    return {'score':calculate(sum(values)/2),'score_range':[min(scores),max(scores)],'note':'按公开节点/档界重算；端点包含关系见规则'}

def validate_item(item):
    identifier=item.get('id');evaluation=item.get('evaluation')
    if not isinstance(evaluation,dict):raise ValueError(f'{identifier}: evaluation is required')
    status=evaluation.get('status')
    if status not in {'rated','estimated','deferred','awaiting_evidence','not_applicable'}:
        raise ValueError(f'{identifier}: explicit evaluation status is required')
    if not evaluation.get('decision') or not isinstance(evaluation.get('limits'),list) or not evaluation['limits']:
        raise ValueError(f'{identifier}: decision and concrete limits are required')
    score=item.get('score')
    if score is None:
        if status in {'rated','estimated'}:raise ValueError(f'{identifier}: missing score cannot be rated')
        if identifier in NUMERIC_IDS and isinstance(evaluation.get('numeric_inputs'),dict):
            result=numeric_result(identifier,evaluation['numeric_inputs'])
            bounds=item.get('score_range',[0,100])
            if bounds[0]>result['score_range'][0]+.11 or bounds[1]<result['score_range'][1]-.11:
                raise ValueError(f'{identifier}: range hides known numeric components')
            if result['score_range']!=[0,100] and not evaluation.get('evidence'):
                raise ValueError(f'{identifier}: evidence is required for known partial components')
            evaluation['numeric_recompute']=result
        return
    evidence=evaluation.get('evidence')
    if not isinstance(evidence,list) or not evidence or any(not e.get('source_type') or not e.get('summary') or 'observed_at' not in e for e in evidence):
        raise ValueError(f'{identifier}: dated or explicitly unknown-date evidence is required')
    if status not in {'rated','estimated'}:raise ValueError(f'{identifier}: unscored status cannot carry a score')
    if identifier in NUMERIC_IDS:
        if not isinstance(evaluation.get('numeric_inputs'),dict):raise ValueError(f'{identifier}: numeric_inputs are required')
        if identifier=='B2' and (evaluation.get('task_protocol')!='self_reported_or_recorded_standard_barbell_bench_1rm' or not evaluation.get('reference_population')):
            raise ValueError('B2: task protocol and reference population are required; self-report is acceptable')
        result=numeric_result(identifier,evaluation['numeric_inputs'])
        if result['score'] is None or abs(result['score']-score)>.11:
            raise ValueError(f'{identifier}: score differs from numeric recompute or protocol is not applicable')
        bounds=item.get('score_range',[score,score])
        if bounds[0]>result['score_range'][0]+.11 or bounds[1]<result['score_range'][1]-.11:
            raise ValueError(f'{identifier}: declared range hides numeric-input uncertainty')
        evaluation['numeric_recompute']=result
        # Accept legacy display rounding, but aggregate the raw-input calculation.
        # Preserve the entered value once so revalidating a derived report is stable.
        if score!=result['score']:
            item.setdefault('score_entered',score)
        item['score']=result['score']
        if 'score_range' in item:
            exact_bounds=result['score_range']
            # A rounded point is a display value, not a new uncertainty interval.
            normalized=list(exact_bounds) if bounds[0]==bounds[1] else [
                min(bounds[0],exact_bounds[0]),max(bounds[1],exact_bounds[1])]
            if normalized!=bounds:
                item.setdefault('score_range_entered',deepcopy(bounds))
                item['score_range']=normalized
        elif result['score_range'][0]!=result['score_range'][1]:
            item['score_range']=list(result['score_range'])
    elif evaluation.get('matched_anchor_score')!=score or score not in (0,20,40,60,80,100):
        raise ValueError(f'{identifier}: score needs an exactly matched supported anchor')

def validate_and_attach(report):
    contract=load_contract()
    if report.get('protocol_version')!=VERSION:raise ValueError('Declare protocol_version character-rules-v0.5')
    rules=json.loads((ROOT/'references'/'rubric-v04.json').read_text(encoding='utf-8'))
    protocols={item['id']:item for item in contract['items']}
    benchmarks=report.get('benchmarks',{})
    own=report.get('assessment_facts',{}).get('self_annual_cny')
    if own is not None and benchmarks.get('self_annual_cny')!=own:
        raise ValueError('Regional annual income inputs disagree across assessment facts and benchmark inputs')
    for group in benchmarks.get('groups',[]):
        for row in group.get('income_rows',[]):
            if row.get('source_amount') is not None and (not str(row.get('source_url','')).startswith('https://') or not row.get('source_value') or not row.get('age_note')):
                raise ValueError('Regional source URL, source year/period/basis and age-scope note are required')
        settings=group.get('character_settings',{})
        if settings.get('height_reference_cm') is not None and (not settings.get('height_reference_label') or not str(settings.get('height_reference_source_url','')).startswith('https://')):
            raise ValueError('Local height references need explicit source URL and population/year label')
    scored=numeric=estimated=0;deferred=[]
    for axis,rule_axis in zip(report['axes'],rules['axes']):
        if axis['axis_weight']!=rule_axis['axis_weight']:raise ValueError('Changed main weights require an explicitly versioned alternative profile')
        for item,rule in zip(axis['items'],rule_axis['items']):
            if item['id']!=rule['id'] or item['weight']!=rule['weight']:raise ValueError('Item identity/weight differs from declared default profile')
            validate_item(item)
            item['rule_detail']={**deepcopy(protocols[item['id']]),'anchors':rule['anchors'],'numeric_rule':rule.get('numeric_rule')}
            if item['score'] is not None:
                scored+=1;numeric+=item['id'] in NUMERIC_IDS;estimated+=item['evaluation']['status']=='estimated'
            else:deferred.append(item['id'])
    # Share one verified set of original values across the global and regional views.
    verified_inputs={i['id']:i['evaluation'].get('numeric_inputs',{}) for a in report['axes'] for i in a['items']}
    facts=report.setdefault('assessment_facts',{})
    if facts.get('self_annual_cny') is None and benchmarks.get('self_annual_cny') is not None:
        facts['self_annual_cny']=benchmarks['self_annual_cny']
    for identifier,input_key,fact_key,range_key in (
        ('A1','height_cm','height_cm','height_range_cm'),
        ('E2','personal_net_assets_cny','net_assets_snapshot_cny','net_assets_snapshot_range_cny'),
        ('F1','potential_support_cny','family_support_cny','family_support_range_cny'),
        ('F1','access_score','family_availability_score','family_availability_range')):
        values=_interval(verified_inputs[identifier].get(input_key))
        if values is None:
            if facts.get(fact_key) is not None:raise ValueError(f'{fact_key}: regional facts disagree with absent verified numeric input')
            continue
        middle=sum(values)/2
        if facts.get(fact_key) is not None and abs(facts[fact_key]-middle)>1e-7:
            raise ValueError(f'{fact_key}: global and regional values disagree')
        facts[fact_key]=middle;facts[range_key]=values
    cash=_interval(verified_inputs['E3'].get('available_liquid_funds_cny'))
    if cash is not None:
        for key,value in zip(('cash_low_cny','cash_high_cny'),cash):
            if facts.get(key) is not None and abs(facts[key]-value)>1e-7:raise ValueError(f'{key}: global and regional values disagree')
            facts[key]=value
    elif facts.get('cash_low_cny') is not None or facts.get('cash_high_cny') is not None:
        raise ValueError('Regional cash facts disagree with absent verified numeric input')
    report['rulebook']=contract
    report['quality_review']={'protocol_items':36,'scored_items':scored,'numeric_items':numeric,'estimated_items':estimated,
        'anchor_60_items':sum(i.get('score')==60 for a in report['axes'] for i in a['items']),
        'deferred_items':deferred,'label':'规则与证据已逐项核对 · 项目评阅',
        'scope_note':'协议完整不等于科学常模。数字来自明确项目刻度；人口排名、跨文化审美和临床结论没有被验证。'}
    return report
