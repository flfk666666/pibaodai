"""Nominal-CNY income coordinates, not PPP, percentiles, or job-offer estimates."""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import math

VERSION = 'regional-income-v0.3'
FACTORS = {'year': 1, 'month': 12, 'week': 52}


def number(value, label, allow_zero=False):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (not allow_zero and value == 0):
        raise ValueError(f'{label} must be a finite {"nonnegative" if allow_zero else "positive"} number')
    return value


def cross_rates(eur_base):
    if not isinstance(eur_base, dict) or 'CNY' not in eur_base:
        raise ValueError('Provide the common EUR-base CNY observation')
    base = number(eur_base['CNY'], 'CNY per EUR')
    rates = {'EUR': base, 'CNY': 1.0}
    for currency, value in eur_base.items():
        rates[currency] = base / number(value, f'{currency} per EUR')
    return rates


def compare_income(self_annual_cny, reference_amount, currency, frequency, cny_per_unit):
    if frequency not in FACTORS:
        raise ValueError('Use a declared year, month, or week wage period')
    if currency not in cny_per_unit:
        raise ValueError(f'Missing explicit nominal FX for {currency}')
    rate = number(cny_per_unit[currency], 'CNY per one source-currency unit')
    factor = FACTORS[frequency]
    result = {'annual_factor': factor, 'cny_per_unit': rate, 'annual_cny': None, 'ratio': None, 'score': None}
    if reference_amount is None:
        return result
    reference = number(reference_amount, 'Reference wage')
    annual = number(reference * factor * rate, 'Converted annual wage')
    result['annual_cny'] = round(annual, 2)
    if self_annual_cny is None:
        return result
    own = number(self_annual_cny, 'Own annual CNY wage', allow_zero=True)
    ratio = own / annual
    score = 0.0 if not own else min(100.0, max(0.0, 60.0 + 20.0 * math.log2(ratio)))
    result.update(ratio=ratio, score=int(Decimal(str(score)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)))
    return result


def calculate_benchmarks(benchmarks):
    if not isinstance(benchmarks, dict) or benchmarks.get('version') != VERSION:
        raise ValueError('Use the explicit regional-income-v0.3 contract')
    result = deepcopy(benchmarks)
    fx = result.get('fx', {})
    if not fx.get('rate_date') or not isinstance(fx.get('cny_per_unit'), dict):
        raise ValueError('Provide a dated common FX snapshot')
    own = result.get('self_annual_cny')
    identifiers = set()
    for group in result.get('groups', []):
        ident = group.get('id')
        if not ident or ident in identifiers:
            raise ValueError('Regional IDs must be explicit and unique')
        identifiers.add(ident)
        scores, ratios = [], []
        for row in group.get('income_rows', []):
            row.update(compare_income(own, row.get('source_amount'), row.get('currency'), row.get('frequency'), fx['cny_per_unit']))
            if row['score'] is not None:
                scores.append(row['score'])
                ratios.append(row['ratio'])
        rating = group.setdefault('regional_score', {})
        low, high = (min(scores), max(scores)) if scores else (None, None)
        ratio_label = ('待补金额' if not ratios else f'{min(ratios):.2f}倍' if min(ratios) == max(ratios)
                       else f'{min(ratios):.2f}–{max(ratios):.2f}倍')
        rating.update(label='名义收入参考分', score=low if low == high else None,
                      score_low=low, score_high=high, ratio_label=ratio_label,
                      formula_label='60 + 20 × log₂(本人人民币年化 / 参照人民币年化)，截在0–100',
                      scope_note='量化的是当前收入的相对坐标；不是人口百分位、购买力或综合就业能力。')
    return result
