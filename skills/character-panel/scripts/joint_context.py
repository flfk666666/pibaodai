"""Ownership, liquidity and conditional living-buffer context, not a new rating."""
from copy import deepcopy
import math


def _value(value):
    if value is None:return None
    if type(value) not in (int,float) or not math.isfinite(value):
        raise ValueError('Use finite numeric context values')
    return float(value)


def _range(value):
    if value is None:return None
    values=[_value(x) for x in value] if isinstance(value,(list,tuple)) else [_value(value)]*2
    if len(values)!=2 or values[0] is None or values[1] is None or not 0<=values[0]<=values[1]:
        raise ValueError('Use an ordered nonnegative context interval')
    return values


def calculate_context(facts):
    facts=deepcopy(facts)
    total=_value(facts.get('cash_total_cny'))
    liquid=_range(facts.get('liquid_cash_cny'))
    expense=_value(facts.get('monthly_necessary_cny'))
    assets=_value(facts.get('personal_net_assets_cny'))
    support=_value(facts.get('family_support_cny'))
    if any(v is not None and v<0 for v in (total,support)) or expense is not None and expense<=0:
        raise ValueError('Cash/support must be nonnegative and expenses positive')
    if total is not None and liquid is not None and liquid[1]>total:
        raise ValueError('Liquid subset cannot exceed the stated cash total')
    restricted=[total-liquid[1],total-liquid[0]] if total is not None and liquid is not None else None
    layers={'cash_total_cny':total,'liquid_cash_cny':liquid,'restricted_cash_cny':restricted,
            'restricted_is_deduced':restricted is not None,
            'restricted_early_access':facts.get('restricted_cash_early_access'),
            'verified_earmarked_emergency_fund_cny':facts.get('earmarked_emergency_fund_cny'),
            'personal_net_assets_cny':assets,'asset_date':facts.get('asset_date'),
            'cash_already_in_assets':True,'family_support_cny':support,
            'family_available':facts.get('family_available'),
            'family_within_days':facts.get('family_support_within_days'),
            'family_in_personal_assets':False,
            'note':'Ownership, availability and purpose are distinct; no balance is added twice.'}
    buffer=[x/expense for x in liquid] if expense is not None and liquid is not None else None
    windows=[]
    for months in (3,6,12):
        needed=expense*months if expense is not None else None
        gap=[max(0,needed-liquid[1]),max(0,needed-liquid[0])] if needed is not None and liquid is not None else None
        margin=[liquid[0]-needed,liquid[1]-needed] if needed is not None and liquid is not None else None
        result='unknown' if margin is None else 'covered' if margin[0]>=0 else 'not_covered' if margin[1]<0 else 'conditional'
        early=facts.get('restricted_cash_early_access')
        all_status='verified_available' if early is True and total is not None else 'unresolved'
        windows.append({'months':months,'necessary_cost_cny':needed,'liquid_gap_cny':gap,
                        'liquid_surplus_cny':margin,'liquid_result':result,
                        'all_cash_access_status':all_status,
                        'all_cash_buffer_months_if_verified':total/expense if early is True and total is not None and expense is not None else None,
                        'label':'Diagnostic no-income window; not a universal recommended reserve target.'})
    scenario=None
    rent=_value(facts.get('monthly_rent_cny'))
    if facts.get('fallback_housing_available') is True and expense is not None and rent is not None and 0<=rent<expense:
        baseline=expense-rent
        scenario={'conditional':True,'necessary_baseline_cny':baseline,
                  'liquid_buffer_months':[x/baseline for x in liquid] if liquid is not None else None,
                  'assumptions':['current_rent_ceases','no_replacement_rent','other_costs_held_constant',
                                 'moving_and_exit_costs_excluded','income_not_transferred'],
                  'note':'A conditional housing-lever comparison, not a measured target-city budget.'}
    income=_range(facts.get('net_monthly_income_cny'))
    coverage=[x/expense for x in income] if income is not None and expense is not None else None
    return {'version':'joint-context-v0.7','funding_layers':layers,'monthly_necessary_cny':expense,
            'liquid_buffer_months':buffer,'income_necessary_coverage':coverage,
            'stress_windows':windows,'fallback_housing_scenario':scenario,
            'actual_spending_known':facts.get('actual_spending_known',False),
            'boundaries':['not_actual_savings_rate','not_foreign_cost_of_living',
                          'no_automatic_addition_of_family_support','no_current_revaluation_of_assets']}
