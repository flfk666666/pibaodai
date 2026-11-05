"""Transparent 36-item project weighting and six-axis regional scenarios."""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import importlib.util
import math
from pathlib import Path

VERSION='weighted-character-v0.4'

def _number(value,low=None,high=None):
    if type(value) not in (int,float) or not math.isfinite(value):
        raise ValueError('Use finite numeric values, not booleans')
    if low is not None and value<low or high is not None and value>high:
        raise ValueError('Value outside declared bounds')
    return float(value)

def _round(value):
    return int(Decimal(str(value)).quantize(Decimal('1'),rounding=ROUND_HALF_UP))

def piecewise_score(value,points):
    value=_number(value)
    if len(points)<2 or any(points[i][0]>=points[i+1][0] for i in range(len(points)-1)):
        raise ValueError('Provide strictly increasing published reference points')
    if value<=points[0][0]:return float(points[0][1])
    for (x1,y1),(x2,y2) in zip(points,points[1:]):
        if value<=x2:return y1+(y2-y1)*(value-x1)/(x2-x1)
    return float(points[-1][1])

def height_preference_score(height):
    return piecewise_score(height,[(160,0),(165,20),(170,40),(175,60),(180,80),(185,100)])

def swim_score(distance):
    return piecewise_score(distance,[(0,0),(25,20),(50,40),(200,60),(800,80),(1609,100)])

def family_capacity_score(years):
    return piecewise_score(years,[(0,0),(.25,20),(.5,40),(1,60),(2,80),(3,100)])

def family_support_score(amount,reference_annual,access_score):
    _number(amount,0);_number(reference_annual,.001);_number(access_score,0,100)
    return 0 if amount==0 else .5*family_capacity_score(amount/reference_annual)+.5*access_score

def asset_year_score(years):
    years=_number(years)
    if years<0:return 0
    return next(score for cutoff,score in [(0.25,20),(1,40),(3,60),(10,80),(math.inf,100)] if years<cutoff)

def cash_month_score(months):
    months=_number(months,0)
    if months==0:return 0
    return next(score for cutoff,score in [(1,20),(3,40),(6,60),(12,80),(math.inf,100)] if months<cutoff)

def _summary(rows):
    known=sum(weight for weight,score,low,high in rows if score is not None)
    numerator=sum(weight*score for weight,score,low,high in rows if score is not None)
    lower=sum(weight*low for weight,score,low,high in rows)/100
    upper=sum(weight*high for weight,score,low,high in rows)/100
    exact=numerator/known if known else None
    return {'score':_round(exact) if exact is not None else None,
            'score_exact':exact,'weighted_numerator':numerator,'coverage_pct':round(known,4),
            'known_weight':round(known,4),'lower':round(lower,4),'upper':round(upper,4),
            'score_low':math.floor(lower+1e-8),'score_high':math.ceil(upper-1e-8),
            'partial':known<100-1e-7 or abs(upper-lower)>1e-7}

def _summarize_axes(axes):
    if not isinstance(axes,list) or len(axes)!=6 or [axis.get('id') for axis in axes]!=list('ABCDEF'):
        raise ValueError('Provide all six axes in A-F order')
    if abs(sum(_number(axis.get('axis_weight'),.001,100) for axis in axes)-100)>1e-7:
        raise ValueError('The six positive axis weights must sum to 100')
    global_rows=[]
    for axis in axes:
        items=axis.get('items')
        if not isinstance(items,list) or len(items)!=6 or [item.get('id') for item in items]!=[axis['id']+str(i) for i in range(1,7)]:
            raise ValueError('Each axis needs all six ordered items; no item may disappear')
        if abs(sum(_number(item.get('weight'),.001,100) for item in items)-100)>1e-7:
            raise ValueError('Six positive item weights must sum to 100')
        rows=[];terms=[]
        for item in items:
            score=item.get('score')
            if score is not None:score=_number(score,0,100)
            if not isinstance(item.get('reason'),str) or not item['reason'].strip():
                raise ValueError('Every item needs its evidence or missing-data reason')
            bounds=item.get('score_range',[score,score] if score is not None else [0,100])
            if not isinstance(bounds,(list,tuple)) or len(bounds)!=2:
                raise ValueError('Use [low, high] for a declared score range')
            low,high=(_number(value,0,100) for value in bounds)
            if low>high or score is not None and not low<=score<=high:
                raise ValueError('Score ranges must contain the representative score')
            weight=item['weight'];global_weight=axis['axis_weight']*weight/100
            item['global_weight']=round(global_weight,6)
            item['weighted_contribution']=round(global_weight*score/100,4) if score is not None else None
            rows.append((weight,score,low,high));global_rows.append((global_weight,score,low,high))
            if score is not None:terms.append(f'{score:g}×{weight:g}')
        axis.update(_summary(rows))
        axis.update(scored_items=sum(row[1] is not None for row in rows),total_weighted_items=6,
                    delta_from_60=axis['score']-60 if axis['score'] is not None else None,
                    range_label='缺项/粗估范围',formula='('+' + '.join(terms)+f") ÷ {axis['known_weight']:g}")
    overall=_summary(global_rows)
    for axis in axes:
        contribution=sum(item['global_weight']*item['score'] for item in axis['items'] if item['score'] is not None)
        axis['normalized_contribution']=round(contribution/overall['known_weight'],4) if overall['known_weight'] else None
    overall['formula']='Σ(子项分×主轴权重×子项权重/100) ÷ 已知全局权重；未知保留原权重范围'
    overall['known_items']=sum(row[1] is not None for row in global_rows)
    overall['total_items']=36
    return axes,overall

def _override(axes,identifier,score,reason,bounds=None):
    item=next(item for axis in axes for item in axis['items'] if item['id']==identifier)
    item.update(score=score,reason=reason,anchor='地区情境：'+reason)
    item.pop('score_range',None)
    item.pop('next_anchor',None)
    if bounds is not None:item['score_range']=bounds

def _regional_review(base_axes,facts,group):
    settings=group.get('character_settings',{})
    cases=[]
    for income in group.get('income_rows',[]):
        annual=income.get('annual_cny')
        if annual is None:continue
        _number(annual,.001)
        axes=deepcopy(base_axes)
        height=facts.get('height_cm')
        height_ref=settings.get('height_reference_cm')
        if height is not None and height_ref is not None:
            points=max(0,min(100,60+3*(height-height_ref)))
            interval=facts.get('height_range_cm',[height,height])
            bounds=[max(0,min(100,60+3*(value-height_ref))) for value in interval]
            _override(axes,'A1',points,f"身高{height:g}cm与{settings.get('height_reference_label','明示样本')}均高{height_ref:g}cm相差{height-height_ref:.1f}cm；项目相对优势曲线60+3×厘米差并封顶100，非颜值百分位",bounds)
        elif settings.get('height_sensitivity_low') is not None:
            base=next(i for a in axes for i in a['items'] if i['id']=='A1')['score']
            _override(axes,'A1',base,settings.get('height_reason','沿用全局偏好曲线，另列强参照敏感性'),[settings['height_sensitivity_low'],base])
        elif height is not None:
            base=next(i for a in axes for i in a['items'] if i['id']=='A1')['score']
            _override(axes,'A1',base,'未取得当地适用身高参照；沿用全局偏好曲线，不能视为已完成当地相对身高比较')
        if 'communication_score' in settings:
            value=settings['communication_score']
            _override(axes,'D3',value,settings.get('communication_reason','目标工作语言情境；未知不直接给零'),settings.get('communication_range',[value,value] if value is not None else [0,100]))
        own=facts.get('self_annual_cny')
        if own is not None:
            ratio=own/annual
            points=0 if own==0 else max(0,min(100,60+20*math.log2(ratio)))
            _override(axes,'E1',points,f"本人与{income.get('label','该参照')}人民币年化比{ratio:.2f}倍，按60+20×log₂比值计算；不是人口分位")
        elif group.get('strict_comparison'):
            _override(axes,'E1',None,'没有本人同口径税前年化原值，不能将全局生活覆盖分冒充地区工资分')
        assets=facts.get('net_assets_snapshot_cny')
        if assets is not None:
            years=assets/annual
            interval=facts.get('net_assets_snapshot_range_cny',[assets,assets])
            _override(axes,'E2',asset_year_score(years),f"按已授权沿用的{facts.get('asset_snapshot_date','历史')}资产快照，折该工资参照{years:.2f}年；不是本日重新盯市或当地财富分位",[asset_year_score(v/annual) for v in interval])
        elif group.get('strict_comparison'):
            _override(axes,'E2',None,'没有可沿用的本人净资产原值，地区工资等价资产容量留空')
        cash_low,cash_high=facts.get('cash_low_cny'),facts.get('cash_high_cny')
        if cash_low is not None and cash_high is not None:
            low,high=cash_low/(annual/12),cash_high/(annual/12)
            midpoint=(cash_low+cash_high)/2/(annual/12)
            _override(axes,'E3',cash_month_score(midpoint),f"已记录可用现金范围折该参照{low:.2f}–{high:.2f}个工资等价月；以资金区间中点作代表，范围两端分别评分；不是当地实际可生活月数",[cash_month_score(low),cash_month_score(high)])
        elif group.get('strict_comparison'):
            _override(axes,'E3',None,'可用现金原值区间未完整提供，地区工资等价现金月数留空')
        support=facts.get('family_support_cny')
        available=facts.get('family_availability_score')
        if support==0:
            _override(axes,'F1',0,'已明确没有可给本人的家庭支持；不因条件描述明确而奖励分数')
        elif support is not None and available is not None:
            years=support/annual;capacity=family_capacity_score(years)
            value=family_support_score(support,annual,available)
            amounts=facts.get('family_support_range_cny',[support,support]);conditions=facts.get('family_availability_range',[available,available])
            bounds=[family_support_score(amount,annual,condition) for amount,condition in zip(amounts,conditions)]
            _override(axes,'F1',value,f"潜在家庭支援折该工资参照{years:.2f}年，容量档{capacity}；与可调用条件档{available}各50%。未到账且不并本人资产",bounds)
        elif support is not None:
            amounts=facts.get('family_support_range_cny',[support,support])
            _override(axes,'F1',None,'潜在家庭支援容量按当地工资参照重算；可调用条件未知，保留另一半权重范围',[.5*family_capacity_score(amounts[0]/annual),.5*family_capacity_score(amounts[1]/annual)+50])
        elif available is not None:
            conditions=facts.get('family_availability_range',[available,available])
            _override(axes,'F1',None,'可调用条件已知、潜在支持容量未知；保留容量的一半原权重范围',[.5*conditions[0],.5*conditions[1]+50])
        elif group.get('strict_comparison'):
            _override(axes,'F1',None,'家庭支援容量与调用条件均未提供；不沿用或默认全局分冒充地区容量')
        for identifier,key in [('F2','housing_score'),('F3','care_score'),('F4','network_score')]:
            if key in settings:
                _override(axes,identifier,settings[key],settings.get(key+'_reason','按已提供的地域可调用性；未知不按0'),settings.get(key+'_range'))
        axes,overall=_summarize_axes(axes)
        cases.append({'label':income.get('label','参照情境'),'axes':axes,'overall':overall})
    if not cases:return None
    selected=min(cases,key=lambda case:case['overall']['score_exact'] if case['overall']['score_exact'] is not None else 101)
    original={item['id']:item for axis in base_axes for item in axis['items']}
    review=deepcopy(group.get('character_summary',{}))
    review.update(selected['overall'])
    review['selected_case_lower']=selected['overall']['lower']
    review['selected_case_upper']=selected['overall']['upper']
    review['lower']=min(case['overall']['lower'] for case in cases)
    review['upper']=max(case['overall']['upper'] for case in cases)
    review['score_low']=min(case['overall']['score_low'] for case in cases)
    review['score_high']=max(case['overall']['score_high'] for case in cases)
    review['selected_case']=selected['label']
    review['case_scores']=[{'label':case['label'],**case['overall']} for case in cases]
    review['axes']=[]
    for axis in selected['axes']:
        changed=[]
        for item in axis['items']:
            before=original[item['id']]
            if item['score']!=before['score'] or item['reason']!=before['reason']:
                changed.append({'id':item['id'],'name':item.get('name',item['id']),'base_score':before['score'],'regional_score':item['score'],
                                'weight':item['weight'],'global_weight':item['global_weight'],'reason':item['reason']})
        other_axes=[case['axes'][list('ABCDEF').index(axis['id'])] for case in cases]
        review['axes'].append({'id':axis['id'],'name':axis.get('name',axis['id']),'weight':axis['axis_weight'],
                               'score':axis['score'],'score_low':min(a['score_low'] for a in other_axes),'score_high':max(a['score_high'] for a in other_axes),
                               'coverage_pct':axis['coverage_pct'],'reason':settings.get('axis_reasons',{}).get(axis['id'],'沿用同一项目规则；不因国家自动增减能力'),
                               'normalized_contribution':axis['normalized_contribution'],
                               'changed_items':changed})
        if axis['id']=='A' and facts.get('height_cm') is not None:
            item=axis['items'][0]
            height=_number(facts['height_cm'])
            reference=settings.get('height_reference_cm')
            delta=height-_number(reference) if reference is not None else None
            raw=60+3*delta if delta is not None else None
            known=axis['known_weight']
            numerator=sum(i['weight']*i['score'] for i in axis['items'] if i['score'] is not None)
            review['axes'][-1]['height_comparison']={
                'status':'referenced' if reference is not None else 'fallback',
                'height_cm':height,'reference_cm':reference,
                'delta_cm':round(delta,3) if delta is not None else None,
                'score':item['score'],'uncapped_score':round(raw,3) if raw is not None else None,
                'capped':raw is not None and (raw>=100 or raw<=0),
                'reference_label':settings.get('height_reference_label','未取得当地适用参照'),
                'source_url':settings.get('height_reference_source_url'),
                'population_source_url':settings.get('height_population_source_url'),
                'method_note':settings.get('height_reference_method'),
                'within_axis_weight':item['weight'],
                'effective_known_axis_weight':round(item['weight']/known*100,4) if known else None,
                'appearance_contribution':round(item['score']*item['weight']/known,4) if known and item['score'] is not None else None,
                'appearance_unrounded':round(numerator/known,4) if known else None,
                'formula':'clip(60 + 3 × (本人身高cm − 参照均高cm), 0, 100)',
                'scope_note':'厘米差不是个人百分位；身高项目分不等于整个外形分。封顶相同不表示相对优势相同。'}
    return review

def calculate_report(report):
    if not isinstance(report,dict) or report.get('rating_type')!='weighted_character' or report.get('version') not in {VERSION,'weighted-character-v0.5'}:
        raise ValueError('Use an explicitly supported weighted-character version')
    if report.get('population_percentile') is not None:
        raise ValueError('Project character scores do not produce population percentiles')
    result=deepcopy(report)
    if result['version']=='weighted-character-v0.5':
        protocol_spec=importlib.util.spec_from_file_location('character_rule_contract',Path(__file__).with_name('rule_contract.py'))
        protocol=importlib.util.module_from_spec(protocol_spec);protocol_spec.loader.exec_module(protocol)
        result=protocol.validate_and_attach(result)
    result['axes'],result['overall']=_summarize_axes(result.get('axes'))
    benchmarks=result.get('benchmarks')
    if isinstance(benchmarks,dict) and benchmarks.get('version')=='regional-income-v0.3':
        spec=importlib.util.spec_from_file_location('weighted_regional_income',Path(__file__).with_name('regional_income.py'))
        regional=importlib.util.module_from_spec(spec);spec.loader.exec_module(regional)
        result['benchmarks']=regional.calculate_benchmarks(benchmarks)
        for group in result['benchmarks'].get('groups',[]):
            if result['version']=='weighted-character-v0.5':group['strict_comparison']=True
            review=_regional_review(result['axes'],result.get('assessment_facts',{}),group)
            if review is not None:group['character_review']=review
            if result['version']=='weighted-character-v0.5':
                group['comparison_mode']='coordinate_current_life'
                group['scenario_note']='当前生活换参照：保留实际工作语言与现有资源，不假装已经搬到当地。工资、资产和现金只是名义坐标，不是当地可获工资或生活费。'
                group['relocation_review']=review
                settings=deepcopy(group.get('character_settings',{}))
                for key in ('communication_score','communication_range','communication_reason','housing_score','housing_score_reason',
                            'care_score','care_score_reason','network_score','network_score_reason'):
                    settings.pop(key,None)
                settings.setdefault('axis_reasons',{}).update({
                    'D':'当前生活换参照，沿用已有专业、中文沟通和交付材料；当地语言适配仅在另列迁居情景中讨论。',
                    'F':'当前生活换参照，保留已知住房、照护和协作事实；仅家庭支援容量换当地工资等价坐标。当地可调用性另列情景。'})
                comparison={**deepcopy(group),'character_settings':settings,'character_summary':{
                    **group.get('character_summary',{}),'verdict':'换参照看优势，迁居条件另算',
                    'summary':'这组六维使用当前事实和统一规则；相对身高与经济/支持容量用所选地区参照。没有因为切换国家就擅自扣工作语言、现有住房或人脉。',
                    'bottlenecks':['工资等价资产/现金容量不等于目标地生活成本或当地财富百分位。','当地求职语言、支持网络和实际报价仍需在迁居情景中核对。']}}
                group['character_review']=_regional_review(result['axes'],result.get('assessment_facts',{}),comparison)
                group['regional_rule_status']={
                    'A':'身高已取当地参照，其余沿用统一形象偏好' if settings.get('height_reference_cm') is not None else '身高当地参照未完成，其余沿用统一形象偏好',
                    'B':'沿用同一任务/功能规则，不称当地人群排名','C':'沿用同一行为锚点，不称当地人群排名',
                    'D':'当前生活事实；当地语言在迁居情景另评',
                    'E':'名义工资等价坐标；年龄和统计定义逐条标记',
                    'F':'当前资源事实；家庭支援容量换坐标，异地调用另评'}
    return result
