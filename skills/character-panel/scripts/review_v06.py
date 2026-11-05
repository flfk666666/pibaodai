"""Experimental v0.6 review: content ratings and evidence coverage stay separate.

Pure calculation only.  No dates, raw evidence, archival scores or external
resources are changed.  The declared mappings are project choices, not norms.
"""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import itertools
import json
import math
from pathlib import Path

VERSION = 'weighted-character-v0.6'
PROTOCOL_VERSION = 'character-rules-v0.6'
RULES_PATH = Path(__file__).resolve().parents[1] / 'references' / 'rubric-v06.json'
ANCHORS = (0, 25, 50, 75, 100)
KINDS = {'A1':'height_preference','B2':'bench_platform_proxy','B3':'continuous_swim_task',
         'E1':'saturating_ratio','E2':'saturating_ratio','E3':'saturating_ratio',
         'E4':'debt_burden','E5':'surplus_margin','F1':'gated_capacity'}


def _number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Use finite numeric inputs, not booleans')
    return float(value)


def _interval(value):
    if isinstance(value, dict):
        if 'value' in value:
            value = value['value']
        elif 'low' in value and 'high' in value:
            value = [value['low'], value['high']]
    if value is None:
        return None
    result = [_number(v) for v in value] if isinstance(value, (list, tuple)) else [_number(value)] * 2
    if len(result) != 2 or result[0] > result[1]:
        raise ValueError('Use a finite ordered [low, high] input interval')
    return result


def _pick(inputs, *names):
    return next((inputs[name] for name in names if name in inputs), None)


def _mid(interval):
    return sum(interval) / 2


def _clip(value):
    return max(0.0, min(100.0, value))


def _round(value):
    return int(Decimal(str(round(value, 12))).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def _linear(value, points):
    points = [[_number(x), _number(y)] for x, y in points]
    if len(points) < 2 or any(a[0] >= b[0] for a, b in zip(points, points[1:])):
        raise ValueError('Numeric curve requires increasing raw-value points')
    if value <= points[0][0]:
        return _clip(points[0][1])
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if value <= x2:
            return _clip(y1 + (y2-y1) * (value-x1) / (x2-x1))
    return _clip(points[-1][1])


def _result(score, bounds, formula, inputs, note):
    return {'score':score, 'score_range':list(bounds),
            'calculation':{'formula':formula, 'inputs':deepcopy(inputs), 'score':score,
                           'score_range':list(bounds), 'note':note}}


def numeric_result(identifier, inputs, rule=None):
    """Calculate from declared raw values; unknown stays unknown, not basic."""
    inputs = inputs if isinstance(inputs, dict) else {}
    numeric = (rule or {}).get('numeric_rule', {})
    kind = numeric.get('kind', (rule or {}).get('kind', KINDS.get(identifier)))
    params = numeric.get('params', {})
    missing = lambda note: _result(None, [0, 100], kind or 'unknown', inputs, note)
    if kind in ('height_preference', 'bench_platform_proxy', 'continuous_swim_task'):
        keys = {'height_preference':('height_cm',),
                'bench_platform_proxy':('bench_press_1rm_kg','bench_1rm_kg'),
                'continuous_swim_task':('continuous_swim_m','distance_m')}[kind]
        value = _interval(_pick(inputs, *keys))
        if value is None:
            return missing('Raw task value is missing; no default score.')
        if kind == 'height_preference':
            points = params.get('points', [[155,0],[165,25],[175,50],[185,75],[195,100]])
            note = 'Declared height preference, not attractiveness or population percentile.'
        elif kind == 'bench_platform_proxy':
            weight = _interval(_pick(inputs, 'body_weight_kg','weight_kg'))
            reference_weight = _number(params.get('reference_weight',85))
            if reference_weight != 85 or weight != [85,85]:
                return missing('Built-in training-platform row is for 85kg only; no extrapolation.')
            if value[0] < 0:
                raise ValueError('Bench load cannot be negative')
            loads = params.get('loads',[60,80,104,130,158])
            scores = params.get('scores',[20,40,60,80,100])
            if len(loads) != len(scores):
                raise ValueError('Bench reference loads and scores must match')
            points = params.get('points', [params.get('origin_point',[0,0]),*zip(loads,scores)])
            note = 'Selected standard barbell single-rep task and training-platform row only; self-report is usable.'
        else:
            if value[0] < 0:
                raise ValueError('Continuous distance cannot be negative')
            points = params.get('points', [[0,0],[25,25],[50,50],[200,75],[800,100]])
            note = 'Continuous swimming task proxy, not comprehensive cardiorespiratory fitness.'
        calculate = lambda x: _linear(x, points)
        return _result(calculate(_mid(value)), [calculate(value[0]), calculate(value[1])],
                       'piecewise_linear(raw_value, ' + json.dumps(points) + ')', inputs, note)
    if kind == 'saturating_ratio':
        keys = {
            'E1':(('after_tax_recurring_income','income','income_cny'),('necessary_expenses_same_period','necessary','necessary_expenses_cny'),1),
            'E2':(('personal_net_assets_cny','assets','net_assets_cny'),('necessary_annual_expenses_cny','annual_expenses','necessary'),1),
            'E3':(('available_liquid_funds_cny','cash','cash_cny'),('necessary_monthly_expenses_cny','monthly_expenses','necessary'),3)}
        if identifier not in keys:
            raise ValueError('Unknown ratio protocol identifier')
        numerator_keys, denominator_keys, default_k = keys[identifier]
        if params.get('numerator_field'):
            numerator_keys = (params['numerator_field'], *numerator_keys)
        if params.get('denominator_field'):
            denominator_keys = (params['denominator_field'], *denominator_keys)
        numerator = _interval(_pick(inputs,*numerator_keys))
        denominator = _interval(_pick(inputs,*denominator_keys))
        k = _number(params.get('k', default_k))
        if k <= 0:
            raise ValueError('Saturation k must be positive')
        if numerator is None or denominator is None or denominator[0] <= 0:
            return missing('A positive matching-period expense denominator and numerator are needed.')
        if identifier != 'E2' and numerator[0] < 0:
            raise ValueError('Income and available cash cannot be negative')
        calculate = lambda x: 100 * max(0,x) / (max(0,x)+k)
        ratios = [n/d for n,d in itertools.product(numerator,denominator)]
        values = [calculate(x) for x in ratios]
        return _result(calculate(_mid(numerator)/_mid(denominator)), [min(values),max(values)],
                       f'100 × max(0, numerator / denominator) / (max(0, numerator / denominator) + {k:g})',
                       inputs, 'Continuous declared capacity curve; k is a project parameter, not a calibrated norm.')
    if kind == 'debt_burden':
        service = _interval(_pick(inputs,'monthly_debt_service_cny','debt_service','service'))
        income = _interval(_pick(inputs,'monthly_after_tax_income_cny','income','after_tax_income'))
        if service is not None and service[0] < 0:
            raise ValueError('Debt service cannot be negative')
        if service == [0,0] and inputs.get('confirmed_no_debt') is True:
            return _result(100, [100,100], 'confirmed_no_debt and service = 0 → burden score 100', inputs,
                           'Low debt-service burden only, not complete financial ability.')
        if service is None or income is None:
            return missing('Debt-service period or income is missing.')
        if income[1] <= 0 and service[0] > 0:
            return _result(0,[0,0],'no positive income with positive service → 0',inputs,'Observed payment burden, not personal worth.')
        if income[0] <= 0:
            return missing('Income crosses or lacks a positive denominator; no fabricated ratio.')
        calculate = lambda n,d: 100 * (1-min(1,max(0,n/d)))
        values = [calculate(n,d) for n,d in itertools.product(service,income)]
        return _result(calculate(_mid(service),_mid(income)),[min(values),max(values)],
                       '100 × (1 − clip(service / income, 0, 1))',inputs,'Reverse burden indicator, not financial achievement.')
    if kind == 'surplus_margin':
        income = _interval(_pick(inputs,'after_tax_income','income'))
        spending = _interval(_pick(inputs,'actual_expenses','actual_spending','expenses'))
        if income is None or income[0] <= 0 or spending is None or inputs.get('same_period') is not True:
            return missing('Need matching-period actual total spending; necessary costs cannot substitute.')
        if spending[0] < 0:
            raise ValueError('Actual spending cannot be negative')
        calculate = lambda inc,exp: _clip(100*(inc-exp)/inc)
        values = [calculate(inc,exp) for inc,exp in itertools.product(income,spending)]
        return _result(calculate(_mid(income),_mid(spending)),[min(values),max(values)],
                       '100 × clip((income − actual_expenses) / income, 0, 1)',inputs,'Actual surplus margin only.')
    if kind == 'gated_capacity':
        availability = _pick(inputs,'availability','availability_status')
        if availability == 'unavailable':
            return _result(0,[0,0],'explicitly unavailable → 0',inputs,'Unusable capacity cannot compensate for an access gate.')
        amount = _interval(_pick(inputs,'available_support_cny','support_cny','potential_support_cny'))
        expenses = _interval(_pick(inputs,'necessary_annual_expenses_cny','annual_expenses','necessary'))
        if amount is not None and amount[0] < 0:
            raise ValueError('Support amount cannot be negative')
        if amount is None or expenses is None or expenses[0] <= 0:
            return missing('Support capacity or expense denominator is missing.')
        k = _number(params.get('k',1))
        if k <= 0:
            raise ValueError('Support capacity k must be positive')
        capacity = lambda n,d: 100*(n/d)/(n/d+k)
        values = [capacity(n,d) for n,d in itertools.product(amount,expenses)]
        formula = f'availability gate, then 100 × (available_support / annual_expenses) / (available_support / annual_expenses + {k:g})'
        if availability in (None,'unknown'):
            return _result(None,[0,max(values)],formula,inputs,'Potential capacity known; availability unresolved, not zero ability.')
        if availability not in ('self_reported_available','confirmed_available'):
            raise ValueError('Use explicit support availability status')
        return _result(capacity(_mid(amount),_mid(expenses)),[min(values),max(values)],formula,inputs,
                       'Claimed usable support capacity; potential support is not personal net assets.')
    raise ValueError('Unknown numeric kind: ' + str(kind))


def _book():
    result = json.loads(Path(RULES_PATH).read_text(encoding='utf-8'))
    axes = result.get('axes')
    if not isinstance(axes,list) or [a.get('id') for a in axes] != list('ABCDEF'):
        raise ValueError('Rulebook must define six ordered axes')
    for axis in axes:
        if _number(axis.get('weight_units',1)) <= 0:
            raise ValueError('Every axis needs positive weight units')
        if [i.get('id') for i in axis.get('items',[])] != [axis['id']+str(n) for n in range(1,7)]:
            raise ValueError('Every rule axis needs six ordered items')
        if any(_number(item.get('weight_units',1)) <= 0 for item in axis['items']):
            raise ValueError('Every item needs positive weight units')
    return result


def _evidence(item):
    evaluation = item.get('evaluation')
    coverage = item.get('coverage')
    if not isinstance(evaluation,dict) or evaluation.get('status') not in ('rated','provisional','missing'):
        raise ValueError('Every item needs an explicit evaluation status')
    if not isinstance(evaluation.get('reason'),str) or not evaluation['reason'].strip():
        raise ValueError('Every item needs a concrete evaluation reason')
    evidence = evaluation.get('evidence')
    if not isinstance(evidence,list):
        raise ValueError('Evidence must be a list, including [] for missing material')
    for row in evidence:
        if not isinstance(row,dict) or not row.get('source_type') or not row.get('summary') or 'observed_at' not in row:
            raise ValueError('Evidence needs source, summary and original date or explicit null')
    if not isinstance(coverage,dict) or coverage.get('level') not in ('limited','usable','broad'):
        raise ValueError('Coverage is separate metadata with limited/usable/broad level')
    if not isinstance(coverage.get('scope'),str) or not isinstance(coverage.get('gaps'),list) or type(coverage.get('higher_unassessed')) is not bool:
        raise ValueError('Coverage needs scope, gaps and higher_unassessed flag')
    return bool(evidence)


def _bounds(item, calculated, numeric):
    bounds = item.get('score_range')
    if bounds is None:
        return calculated['score_range']
    values = _interval(bounds)
    if values[0] < 0 or values[1] > 100:
        raise ValueError('Score range must stay inside 0–100')
    if not numeric and any(value not in ANCHORS for value in values):
        raise ValueError('A qualitative unresolved range must use declared anchor endpoints')
    if (not numeric and calculated['score'] is None
            and item.get('selected_anchor') is None
            and item.get('evaluation',{}).get('status') == 'provisional'
            and item.get('evaluation',{}).get('evidence')
            and isinstance(item.get('range_reason'),str) and item['range_reason'].strip()):
        # Material can rule out some anchors without selecting one remaining
        # anchor.  This is neither no evidence nor permission to invent a midpoint.
        return values
    if values[0] > calculated['score_range'][0]+1e-8 or values[1] < calculated['score_range'][1]-1e-8:
        raise ValueError('Declared range hides raw-input uncertainty or selected anchor')
    return values


def _summarize(axes):
    global_rows = []
    for axis in axes:
        rows = []
        for item in axis['items']:
            rows.append((item['within_axis_weight'],item['score'],*item['score_range']))
            global_rows.append((item['global_weight'],item['score'],*item['score_range']))
        axis.update(_summary(rows))
        for item in axis['items']:
            item['axis_contribution'] = item['score']*item['within_axis_weight']/axis['known_weight_pct'] if item['score'] is not None and axis['known_weight_pct'] else None
    overall = _summary(global_rows)
    overall['label'] = '六维均衡读数（可选；非完整能力或人口排名）'
    overall['known_items'] = sum(score is not None for _,score,_,_ in global_rows)
    overall['total_items'] = 36
    for axis in axes:
        for item in axis['items']:
            item['contribution'] = item['score']*item['global_weight']/overall['known_weight_pct'] if item['score'] is not None and overall['known_weight_pct'] else None
            item['full_weight_contribution'] = item['score']*item['global_weight']/100 if item['score'] is not None else None
        axis['contribution'] = math.fsum(i['contribution'] or 0 for i in axis['items'])
    return overall


def _summary(rows):
    known = math.fsum(weight for weight,score,low,high in rows if score is not None)
    numerator = math.fsum(weight*score for weight,score,low,high in rows if score is not None)
    exact = numerator/known if known else None
    lower = math.fsum(weight*low for weight,score,low,high in rows)/100
    upper = math.fsum(weight*high for weight,score,low,high in rows)/100
    return {'score':_round(exact) if exact is not None else None,'score_exact':exact,
            'weighted_numerator':numerator,'known_weight_pct':known,'lower':lower,'upper':upper,
            'score_low':math.floor(lower+1e-8),'score_high':math.ceil(upper-1e-8),
            'partial':known<100-1e-8 or upper-lower>1e-8}


def _score_axes(report, book):
    axes = report.get('axes')
    if not isinstance(axes,list) or [a.get('id') for a in axes] != list('ABCDEF'):
        raise ValueError('Provide all six axes in A–F order')
    total_axis_units = math.fsum(a.get('weight_units',1) for a in book['axes'])
    for axis, axis_rule in zip(axes,book['axes']):
        axis.update(name=axis_rule.get('name',axis['id']),axis_weight=axis_rule.get('weight_units',1)/total_axis_units*100)
        if [i.get('id') for i in axis.get('items',[])] != [axis['id']+str(n) for n in range(1,7)]:
            raise ValueError('Provide all six ordered items; missing items retain their place')
        item_units = math.fsum(i.get('weight_units',1) for i in axis_rule['items'])
        for item, rule in zip(axis['items'],axis_rule['items']):
            has_evidence = _evidence(item)
            numeric = rule.get('score_kind') == 'numeric' or item['id'] in KINDS
            if numeric:
                result = numeric_result(item['id'],item.get('numeric_inputs'),rule)
            else:
                selected = item.get('selected_anchor')
                if selected is not None and (type(selected) not in (int,float) or selected not in ANCHORS):
                    raise ValueError('Selected anchor must be 0/25/50/75/100 or null')
                selected = selected if has_evidence else None
                result = _result(selected,[selected,selected] if selected is not None else [0,100],
                                 'matched content anchor; evidence coverage is not a score multiplier',{},
                                 'Higher unassessed conditions remain separate; no default basic rating.')
            if not has_evidence:
                result = _result(None,[0,100],result['calculation']['formula'],item.get('numeric_inputs',{}),'No material: unknown, not low ability.')
            item['score'] = result['score']
            item['score_range'] = _bounds(item,result,numeric)
            item['calculation'] = result['calculation']
            item['calculation']['score_range'] = list(item['score_range'])
            item['name'] = rule.get('name',item.get('name',item['id']))
            item['within_axis_weight'] = rule.get('weight_units',1)/item_units*100
            item['global_weight'] = axis['axis_weight']*item['within_axis_weight']/100
            item['rule'] = deepcopy(rule)
            pending_qualitative = (not numeric and has_evidence
                and item.get('selected_anchor') is None
                and item['evaluation']['status'] == 'provisional'
                and isinstance(item.get('range_reason'),str) and item['range_reason'].strip()
                and item.get('score_range') is not None)
            if item['score'] is None and not pending_qualitative:
                item['evaluation']['status'] = 'missing'
    return axes


def _replace(item, score, bounds, formula, inputs, note):
    item.update(score=score,score_range=list(bounds),calculation={'formula':formula,'inputs':deepcopy(inputs),
                'score':score,'score_range':list(bounds),'note':note},score_origin='regional_coordinate')


def _regional_review(report, region):
    base = report['axes']
    lookup = {i['id']:i for a in base for i in a['items']}
    height = _interval(_pick(lookup['A1'].get('numeric_inputs',{}),'height_cm'))
    reference = region.get('height_reference_cm')
    if reference is not None:
        reference = _number(reference)
    own = _pick(region,'self_annual_cny','own_annual_income_cny')
    if own is None:
        own = _pick(report.get('assessment_facts',{}),'self_annual_cny','own_annual_income_cny')
    if own is None:
        own = _pick(report,'self_annual_cny','own_annual_income_cny')
    own = _interval(own)
    if own is not None and own[0] < 0:
        raise ValueError('Regional own gross annual income cannot be negative')
    rows = region.get('income_rows',[])
    if not isinstance(rows,list):
        raise ValueError('Regional income rows must be a list')
    rows = rows or [{'label':'No applicable regional income reference','annual_cny':None}]
    cases = []
    for row in rows:
        axes = deepcopy(base)
        items = {i['id']:i for a in axes for i in a['items']}
        if height is not None and reference is not None and items['A1']['score'] is not None:
            raw = 50+2*(_mid(height)-reference)
            points = _clip(raw)
            bounds = [_clip(50+2*(h-reference)) for h in height]
            _replace(items['A1'],points,bounds,'clip(50 + 2 × (height_cm − reference_mean_cm), 0, 100)',
                     {'height_cm':lookup['A1']['numeric_inputs']['height_cm'],'reference_mean_cm':reference},
                     'Declared height-prominence coordinate, not attractiveness or an inferred percentile.')
        annual = row.get('annual_cny')
        if annual is not None:
            annual = _number(annual)
            if annual <= 0:
                raise ValueError('Regional salary reference must be positive')
        if own is not None and annual is not None:
            calculate = lambda value: 100*value/(value+annual)
            _replace(items['E1'],calculate(_mid(own)),[calculate(own[0]),calculate(own[1])],
                     '100 × own_gross_annual_cny / (own_gross_annual_cny + reference_gross_annual_cny)',
                     {'own_gross_annual_cny':own,'reference_gross_annual_cny':annual},
                     'Nominal income coordinate only. Asset, cash and support denominators remain actual expenses.')
        else:
            _replace(items['E1'],None,[0,100],'regional income coordinate unavailable',{},
                     'No applicable own gross annual income or regional wage reference; no invented low ability.')
        overall = _summarize(axes)
        cases.append({'label':row.get('label','Declared wage reference'),'axes':axes,'overall':overall,'income_row':deepcopy(row)})
    selected = min(cases,key=lambda c:c['overall']['score_exact'] if c['overall']['score_exact'] is not None else 101)
    overall = deepcopy(selected['overall'])
    overall.update(lower=min(c['overall']['lower'] for c in cases),upper=max(c['overall']['upper'] for c in cases),
                   score_low=min(c['overall']['score_low'] for c in cases),score_high=max(c['overall']['score_high'] for c in cases))
    height_info = {'status':'referenced' if height is not None and reference is not None else 'unavailable',
                   'height_cm':_mid(height) if height else None,'reference_cm':reference,
                   'delta_cm':_mid(height)-reference if height is not None and reference is not None else None,
                   'raw_score':50+2*(_mid(height)-reference) if height is not None and reference is not None else None,
                   'score':selected['axes'][0]['items'][0]['score'] if height is not None and reference is not None else None,
                   'source':deepcopy(region.get('height_source'))}
    annual = selected['income_row'].get('annual_cny')
    income_info = {'status':'referenced' if own is not None and annual is not None else 'unavailable',
                   'own_annual_cny':_mid(own) if own else None,'reference_annual_cny':annual,
                   'ratio':_mid(own)/annual if own is not None and annual else None,
                   'source':selected['income_row']}
    return {'axes':selected['axes'],'overall':overall,'selected_case':selected['label'],
            'case_scores':[{'label':c['label'],**c['overall'],'income_row':c['income_row']} for c in cases],
            'height':height_info,'income':income_info,
            'limitations':['Six axes retain the same demonstrated tasks; unchanged scores are not equal local population ranks.',
                'Only height prominence and declared income coordinates alter A1/E1; actual asset, cash and support capacity remain intact.',
                'No national label changes cognition, facial preference, language, eligibility or resource availability.',
                'The lower unrounded income case is a disclosed display convention, not a statistically privileged population.']}


def calculate_report(report):
    """Return an independent, idempotent derived report without mutating input."""
    if not isinstance(report,dict) or report.get('version') != VERSION or report.get('protocol_version') != PROTOCOL_VERSION or report.get('rating_type') != 'weighted_character':
        raise ValueError('Declare weighted-character-v0.6 and character-rules-v0.6')
    result = deepcopy(report)
    book = _book()
    result['rulebook'] = deepcopy(book)
    result['axes'] = _score_axes(result,book)
    result['overall'] = _summarize(result['axes'])
    for region in result.get('regions',[]):
        region['review'] = _regional_review(result,region)
    result['quality_review'] = {'items':36,'scored_items':result['overall']['known_items'],
        'content_coverage_separated':True,'calibrated_population_scale':False,
        'followups':[{'id':i['id'],**deepcopy(i['followup'])} for a in result['axes'] for i in a['items'] if isinstance(i.get('followup'),dict)]}
    return result
