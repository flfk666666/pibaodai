"""Joint interpretation of existing v0.6 scores; never a new person rating.

The cutoffs refer to the existing declared item anchors/utility mappings.  They
are project conjunction rules, not population standards, attractiveness norms,
country thresholds or scientific effect estimates.  No raw value or score is
changed by this layer.
"""
from copy import deepcopy
import math

VERSION = 'joint-character-interpretation-v0.7'
RULE_ORIGIN = 'declared_project_conjunctions_not_population_standard'


def _criterion(identifier, minimum=75, *, strict=False):
    return {'id':identifier, 'minimum':minimum, 'strict':strict}


def _spec(identifier, label, paths, meaning, *, essential=True):
    return {'id':identifier, 'label':label,
            'paths':[[(_criterion(value) if isinstance(value,str) else value) for value in path] for path in paths],
            'meaning':meaning, 'essential':essential}


SPECS = {
 'A':{
  'core':['A1','A2','A3'], 'support':['A4','A5','A6'],
  'critical':['A2','A3','A4','A5','A6'],
  'checks':[
   _spec('A.profile','条件同向，或形象匹配路径成立',
         [['A1','A2','A3'],['A2','A3','A5']],
         '路径一看身高、面部、可见身形共同支持；路径二看面部、身形与穿搭匹配。身高不是人人必过的唯一门槛。'),
   _spec('A.presentation','仪容、风格与呈现共同到位',
         [['A4','A5','A6']],
         '形象基础仍需实际仪容和表达承接，不能用一项尺度优势抹掉其他呈现。') ]},
 'B':{
  'core':['B1','B2','B3','B4'], 'support':['B5','B6'],
  'critical':['B1','B4','B5','B6'],
  'checks':[
   _spec('B.activity','普通功能与已选动作/持续任务形成底盘',
         [['B1',_criterion('B2',60),_criterion('B3',50),'B4']],
         '日常活动、上肢推力、已选连续游泳和动作适配分别看。卧推60为既有训练节点；游泳50为既有任务节点，不是全面心肺常模。'),
   _spec('B.sustain','恢复感与清醒任务持续性分别支持',
         [['B5','B6']],
         '能完成任务不代表恢复充分，力量突出也不能取消已明确的恢复欠账。') ]},
 'C':{
  'core':['C1','C2','C3','C4'], 'support':['C5','C6'],
  'critical':['C2','C3','C4','C5','C6'],
  'checks':[
   _spec('C.reasoning','理解、推理、核验与判断形成闭环',
         [['C1','C2','C3','C4']],
         '学习方法要通过推理、风险匹配的证据核验和决策使用；单独会学不能替代查证。'),
   _spec('C.regulation','计划调节与压力后回到行动承接判断',
         [['C5','C6']],
         '只在已有场景内评价从判断回到行动，不把心理或全部智力外推。') ]},
 'D':{
  'core':['D1','D2','D5'], 'support':['D3','D4','D6'],
  'critical':['D1','D2','D3','D5','D6'],
  'checks':[
   _spec('D.delivery','专业、问题处置与可靠交付同时成立',
         [['D1','D2','D5']],
         '专业过程、排查处置和实际履约形成交付链；管理高分不能替代本人专业或收尾。'),
   _spec('D.coordination','沟通、组织和独立办事共同支持',
         [['D3','D4','D6']],
         '表达、资源重组和实际办事是不同环节，职位和人数不能自动代替内容。') ]},
 'E':{
  'core':['E1','E2','E3','E4','E5','E6'], 'support':[],
  'critical':['E1','E3','E4','E6'],
  'checks':[
   _spec('E.income','收入覆盖与经常收款履约',
         [[_criterion('E1',50),'E6']],
         '收入覆盖50在既有函数中为收入等于必要开支；来源75/100另看实际履约，不强制副业。'),
   _spec('E.capacity','本人资产与即时现金形成两层缓冲',
         [[_criterion('E2',50),_criterion('E3',50)]],
         '资产50对应一必要开支年，现金50对应三必要开支月；这是声明的基础容量门槛，不是人口财富排名。'),
   _spec('E.debt','偿付负担不过度挤压收入',
         [['E4']],
         '低偿付负担只支持这个条件，不能单独推出整个财务很强。'),
   _spec('E.surplus','实际收入留存得到观察',
         [[_criterion('E5',0,strict=True)]],
         '必须有同期间实际总消费，才能判断实际结余；必要开支不能代替，未知不当失败。') ]},
 'F':{
  'core':['F1','F2','F3','F4'], 'support':['F5','F6'],
  'critical':['F3','F4','F6'],
  'checks':[
   _spec('F.backstop','可调用资金与居住退路相互托底',
         [[_criterion('F1',50),'F2']],
         '资金容量与使用权是不同资源，家庭资金不提前加入本人资产。'),
   _spec('F.people','现场人手与协作渠道可实际承接',
         [['F3','F4']],
         '钱或住房不会自动变成现场照护；付费帮助只有渠道落实后才算可用人手。'),
   _spec('F.enable','工具环境与责任约束允许调用',
         [['F5','F6']],
         '可接触的工具与当前责任约束分别判断，不凭少社交或有无房产替代。') ]}
}

STATE_LABELS = {
 'multi_strength':'主要条件协同成立',
 'strength_with_constraint':'有优势组合，也有明确制约',
 'single_strength':'单项突出，组合尚未成立',
 'pending':'已知部分可用，联合结论待补',
 'constrained':'存在明确条件短板',
 'partial':'部分条件可用，尚不足下整体强结论'
}


def _lookup(axes):
    if not isinstance(axes,list) or [axis.get('id') for axis in axes] != list('ABCDEF'):
        raise ValueError('Joint interpretation needs all six A-F axes')
    lookup={}
    for axis in axes:
        if [item.get('id') for item in axis.get('items',[])] != [axis['id']+str(n) for n in range(1,7)]:
            raise ValueError('Keep all six ordered items in every axis')
        for item in axis['items']:
            score=item.get('score')
            if score is not None and (type(score) not in (int,float) or not math.isfinite(score) or not 0<=score<=100):
                raise ValueError('Item scores must be finite 0-100 or unknown')
            bounds=item.get('score_range',[score,score] if score is not None else [0,100])
            if not isinstance(bounds,(list,tuple)) or len(bounds)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=100 for v in bounds) or bounds[0]>bounds[1]:
                raise ValueError('Item ranges must be ordered 0-100 bounds')
            if score is not None and not bounds[0]<=score<=bounds[1]:
                raise ValueError('Item ranges must contain the existing point rating')
            lookup[item['id']]=item
    return lookup


def _criterion_result(item, criterion):
    if item.get('score') is None:
        return 'unknown'
    low,high=item.get('score_range',[item['score'],item['score']])
    cutoff=criterion['minimum'];strict=criterion.get('strict',False)
    passes=lambda value:value>cutoff if strict else value>=cutoff
    if passes(low):
        return 'met'
    if not passes(high):
        return 'limited'
    return 'unknown'


def _check(spec, items):
    path_results=[];path_details=[]
    for path in spec['paths']:
        values=[_criterion_result(items[c['id']],c) for c in path]
        result='limited' if 'limited' in values else 'unknown' if 'unknown' in values else 'met'
        path_results.append(result)
        path_details.append({'criteria':[{'item_id':c['id'],'operator':'>' if c.get('strict') else '>=',
                                         'threshold':c['minimum'],'result':value} for c,value in zip(path,values)],
                             'result':result})
    result='met' if 'met' in path_results else 'unknown' if 'unknown' in path_results else 'limited'
    identifiers=list(dict.fromkeys(c['id'] for path in spec['paths'] for c in path))
    terms=[]
    for path in spec['paths']:
        terms.append(' 且 '.join(c['id']+(' > ' if c.get('strict') else ' ≥ ')+str(c['minimum']) for c in path))
    condition='；或：'.join(terms)
    observed=[{'id':identifier,'name':items[identifier].get('name',identifier),'score':items[identifier].get('score'),
               'score_range':deepcopy(items[identifier].get('score_range')),
               'scope':items[identifier].get('coverage',{}).get('scope','只覆盖原报告已述内容')} for identifier in identifiers]
    if result=='met':
        passed=[str(i+1) for i,value in enumerate(path_results) if value=='met']
        reason='现有材料支持路径'+('/'.join(passed))+'的联合条件。'+spec['meaning']
    elif result=='unknown':
        reason='决定联合结论的条件有缺失或候选范围跨档；保留未决，不把材料不足判为失败。'+spec['meaning']
    else:
        reason='已有表现未满足这条声明的组合条件；其他单项高分不能自动抵消。'+spec['meaning']
    return {'id':spec['id'],'label':spec['label'],'item_ids':identifiers,
            'operator':'any_path_all_conditions','observed':observed,'condition':condition,
            'result':result,'reason':reason,'paths':path_details,'essential':spec['essential']}


def _assessment(axes, context=None, baseline_axes=None):
    items=_lookup(axes);result_axes=[]
    # Regional E1 is a wage coordinate, not the original expense-coverage item.
    # Local A1 prominence likewise does not replace the declared height preference.
    # Reuse the actual-condition items for conjunctions; show the coordinates aside.
    if baseline_axes is not None:
        baseline=_lookup(baseline_axes)
        for identifier in ['A1']+['E'+str(n) for n in range(1,7)]:
            items[identifier]=baseline[identifier]
    for axis in axes:
        axis_id=axis['id'];rules=SPECS[axis_id]
        axis_specs=deepcopy(rules['checks'])
        checks=[_check(spec,items) for spec in axis_specs]
        strengths=[check['label']+'：'+check['reason'] for check in checks if check['result']=='met']
        unknowns=[];bottlenecks=[]
        for item in (items[axis_id+str(n)] for n in range(1,7)):
            identifier=item['id'];score=item.get('score')
            if score is None:
                unknowns.append(identifier+' '+item.get('name',identifier)+'尚无代表分；保留原始缺口，不当低能力。')
            elif score<=50:
                suffix='这是本项已有表现/条件的局限，不能被不相关高分抹掉。'
                if axis_id=='A' and identifier=='A1':
                    suffix='这只是所选高个偏好的局限；其他形象路径仍可成立，身高不是共同硬门槛。'
                elif axis_id=='B' and identifier in ('B2','B3'):
                    suffix='只描述已选运动任务，不外推全面身体能力。'
                elif axis_id=='E' and identifier in ('E1','E2','E3','E5'):
                    suffix='这是已声明容量/比值节点的条件提示，不是人口财富等级或理财能力判断。'
                bottlenecks.append(identifier+' '+item.get('name',identifier)+' 当前'+str(score)+'：'+suffix)
        for check in checks:
            if check['result']=='unknown':
                unresolved=[obs['id'] for obs in check['observed'] if obs['score'] is None or
                            any(c['item_id']==obs['id'] and c['result']=='unknown' for path in check['paths'] for c in path['criteria'])]
                unknowns.append(check['label']+'中的 '+('/'.join(dict.fromkeys(unresolved)))+' 条件未决。')
        essential=[c for c in checks if c['essential']]
        has_met=any(c['result']=='met' for c in essential)
        has_unknown=any(c['result']=='unknown' for c in essential)
        has_limited=any(c['result']=='limited' for c in essential)
        critical_low=any(items[i].get('score') is not None and items[i]['score']<=50 for i in rules['critical'])
        if has_limited and (has_met or any(items[i].get('score') is not None and items[i]['score']>=75 for i in rules['core'])):
            state='strength_with_constraint' if critical_low else 'single_strength'
        elif has_limited:
            state='constrained'
        elif has_unknown:
            state='pending'
        elif all(c['result']=='met' for c in essential):
            state='multi_strength'
        else:
            state='partial'
        label=STATE_LABELS[state]
        if axis_id=='F' and state=='strength_with_constraint' and next(c for c in checks if c['id']=='F.backstop')['result']=='met':
            label='托底组合成立，现场人手另有缺口'
        elif axis_id=='E' and state=='pending':
            label='已知财务底盘可用，整体强结论待补'
        elif axis_id=='B' and state=='strength_with_constraint':
            activity=next(c for c in checks if c['id']=='B.activity')['result']
            label='活动底盘可用，恢复支持仍有欠账' if activity=='met' else '已见活动优势，动作适配待补且恢复欠账'
        result_axes.append({'id':axis_id,'name':axis.get('name',axis_id),'state':label,'state_code':state,
                            'core_items':list(rules['core']),'support_items':list(rules['support']),
                            'checks':checks,'strengths':strengths,'bottlenecks':bottlenecks,
                            'unknowns':list(dict.fromkeys(unknowns)),
                            'contextual_references':[],
                            'comparison_basis':('本人原始实际财务口径；当地工资坐标另列，不纳入联合条件。' if axis_id=='E' and baseline_axes is not None else
                                                '沿用全局所选高个偏好；地区身高突出坐标另列，不等于审美或吸引力。' if axis_id=='A' and baseline_axes is not None else
                                                '原报告的内容档与容量节点。'),
                            'coverage_note':'只解释原报告已观察内容之间的组合；原coverage、来源、日期和未测场景仍有效。同分不证明全部能力或人口位置相同。'})
    chains=[
     _spec('thinking_to_delivery','认知→问题解决→可靠交付',
           [['C1','C2','C3','C4','D1','D2','D5']],
           '把方法理解、证据链、判断和实际交付连起来，不能用组织头衔替代其中的薄弱环节。'),
     _spec('economic_to_backstop','本人缓冲→家庭/居住托底',
           [[_criterion('E1',50),_criterion('E2',50),_criterion('E3',50),'E4','E6',_criterion('F1',50),'F2']],
           '只能支持已知的基础抗冲击条件，不证明实际持续结余或永远财务安全。'),
     _spec('judgment_to_action','调节→沟通组织→独立办事',
           [['C5','C6','D3','D4','D6','F4','F5']],
           '判断经调节与协作转成行动；工作与个人项目适用范围仍分别保留。') ]
    assessed=[_check(spec,items) for spec in chains]
    constraints=[]
    critical=['B5','B6','C3','C5','D5','E1','E3','E4','F3','F4','F6']
    labels={'B5':'恢复感→持续投入','B6':'清醒精力→任务持续','C3':'证据核验→决策可信度',
            'C5':'计划调节→行动推进','D5':'履约→可信交付','E1':'收入覆盖→日常自主',
            'E3':'即时流动性→过渡缓冲','E4':'偿付负担→可用现金流','F3':'现场人手→照护执行',
            'F4':'可调用协作→任务扩展','F6':'责任约束→可支配选择'}
    for identifier in critical:
        score=items[identifier].get('score')
        if score is not None and score<=50:
            label=labels[identifier]
            constraints.append(identifier+' '+label+'：原项已有'+str(score)+'的条件/表现，其他强项不能直接替代。')
    unknowns=[]
    for axis in result_axes:unknowns.extend(axis['unknowns'])
    context=context if isinstance(context,dict) else {}
    if context.get('target_language_status') not in ('verified','not_required'):
        unknowns.append('目标工作语言、资格与当地资源适配尚未核实；仅迁居/跨语言场景待核，不判语言能力低，也不扣通用思考或专业分。')
    return {'version':VERSION,'rule_origin':RULE_ORIGIN,'axes':result_axes,
            'overall':{'established_chains':assessed,'constraints':constraints,'unknowns':list(dict.fromkeys(unknowns))},
            'policy':{'changes_scores':False,'unknown_is_failure':False,'threshold_basis':'既有内容档/容量函数节点的项目联合规则，非各国人口标准。',
                      'compensation':'仅声明的替代路径允许补足；恢复、查证、可靠交付、现场照护等相关条件不能用不相关高分取消。',
                      'no_new_total':'本层不再生成一个貌似客观的新总分，解释主要条件共同成立与制约。'}}


def _number(value):
    return value if type(value) in (int,float) and math.isfinite(value) else None


def _interval(value):
    if _number(value) is not None:
        return [value,value]
    if isinstance(value,(list,tuple)) and len(value)==2 and all(_number(v) is not None for v in value) and value[0]<=value[1]:
        return list(value)
    return None


def _regional_references(region):
    """Descriptive coordinates, deliberately excluded from conjunction states."""
    review=region['review'];items=_lookup(review['axes'])
    income=review.get('income') or {}
    inputs=(items['E1'].get('calculation') or {}).get('inputs') or {}
    own=_interval(income.get('own_annual_cny',inputs.get('own_gross_annual_cny')))
    reference=_number(income.get('reference_annual_cny',inputs.get('reference_gross_annual_cny')))
    ratios=[v/reference for v in own] if own is not None and reference is not None and reference>0 else None
    ratio=sum(ratios)/2 if ratios is not None else None
    income_result=('unknown' if ratios is None or ratios[0]<1<=ratios[1] else 'met' if ratios[0]>=1 else 'limited')
    income_check={
        'id':'E.local_income','label':'本人名义收入相对所选当地工资坐标','item_ids':['E1'],
        'operator':'reference_ratio','observed':{'own_annual_cny':sum(own)/2 if own is not None else None,
            'own_annual_cny_range':own,'reference_annual_cny':reference,'ratio':ratio,
            'ratio_range':ratios,'regional_score':items['E1'].get('score')},
        'condition':'本人税前年收入 ÷ 所选当地税前工资参照 ≥ 1；只表示不低于这一工资坐标。',
        'result':income_result,
        'reason':('当前名义收入不低于所选工资参照。' if income_result=='met' else
                  '当前名义收入低于所选工资参照。' if income_result=='limited' else
                  '工资参照缺失或收入范围跨过所选工资参照，保留未决。')+
                 '这不是当地可获得的工资、当地生活成本或可支撑月数；不改本人现实收入覆盖、现金容量或财务联合状态。',
        'source':deepcopy(income.get('source'))}
    height=review.get('height') or {}
    own_height=_number(height.get('height_cm'))
    reference_height=_number(height.get('reference_cm',region.get('height_reference_cm')))
    delta=own_height-reference_height if own_height is not None and reference_height is not None else None
    height_result='unknown' if delta is None else 'met' if delta>=0 else 'limited'
    height_check={
        'id':'A.local_stature','label':'相对地区所选均高的身高突出坐标','item_ids':['A1'],
        'operator':'reference_difference','observed':{'height_cm':own_height,'reference_cm':reference_height,
            'delta_cm':delta,'regional_score':items['A1'].get('score')},
        'condition':'本人身高 − 所选地区均高 ≥ 0；只表示不低于该参照均高。',
        'result':height_result,
        'reason':('身高不低于所选均高。' if height_result=='met' else
                  '身高低于所选均高。' if height_result=='limited' else '身高或对应参照缺失。')+
                 '厘米差与突出坐标不等于整体外形、当地审美或吸引力；仍需面部、身形和呈现共同支持，不替换全局所选高个偏好。',
        'source':deepcopy(height.get('source',region.get('height_source')))}
    return {'A':[height_check],'E':[income_check]}


def calculate_joint(report):
    """Return an immutable-input, idempotent joint interpretation of a report."""
    if not isinstance(report,dict):
        raise ValueError('A calculated character report is required')
    result=deepcopy(report)
    result['joint_assessment']=_assessment(result.get('axes'),result.get('joint_context'))
    for region in result.get('regions',[]):
        review=region.get('review')
        if isinstance(review,dict) and isinstance(review.get('axes'),list):
            review['joint_assessment']=_assessment(review['axes'],region.get('joint_context',result.get('joint_context')),result['axes'])
            references=_regional_references(region)
            for axis in review['joint_assessment']['axes']:
                axis['contextual_references']=references.get(axis['id'],[])
            review['joint_assessment']['region_note']='联合条件沿用本人原始形象偏好和现实财务口径；地区身高与工资坐标另列，不混作当地审美、工作报价或生活容量。原地区分数保留。'
    return result
