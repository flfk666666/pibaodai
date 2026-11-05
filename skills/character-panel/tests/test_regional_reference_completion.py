"""Public cohort-reference provenance and EU27 weighting checks."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
EU27={'AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','EL','HU','IE','IT','LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE'}

class ReferenceCompletionTests(unittest.TestCase):
    def data(self):
        p=ROOT/'references'/'regional-height-v051.json'
        self.assertTrue(p.exists(),'Korea and EU27 completed reference data missing')
        return json.loads(p.read_text(encoding='utf-8'))

    def test_korea_has_a_near_birth_cohort_primary_reference(self):
        data=self.data();self.assertEqual({'hz','cn','us','eu','sg','my','jp','kr'},set(data['country_references']))
        r=data['country_references']['kr']
        self.assertEqual(2019,r['year']);self.assertEqual(19,r['age'])
        self.assertEqual(175.5,r['mean_height_cm'])
        self.assertIn('ncdrisc.org/',r['source_url']);self.assertTrue(r['original_line'])

    def test_eu27_is_fully_covered_and_reproducible(self):
        r=self.data()['country_references']['eu'];rows=r['countries']
        self.assertEqual('complete',r['status']);self.assertFalse(r['is_official_eu_height_estimate'])
        self.assertEqual(EU27,{i['code'] for i in rows})
        self.assertEqual(27,len(rows))
        self.assertTrue(all(i['male_age19_population_2019']>0 and i['source_url'].startswith('https://') for i in rows))
        total=sum(i['male_age19_population_2019'] for i in rows)
        mean=sum(i['male_age19_population_2019']*i['mean_height_cm'] for i in rows)/total
        self.assertEqual(total,r['total_population_age19_male'])
        self.assertAlmostEqual(mean,r['raw_mean_height_cm'],places=8)
        self.assertEqual(round(mean,1),r['mean_height_cm'])

    def test_reference_and_scale_reading_protocols_are_present(self):
        r=self.data()
        self.assertTrue(r['cohort_note']);self.assertTrue(r['country_references']['eu']['population_source_url'])
        text=(ROOT/'references'/'score-reading-v051.md').read_text(encoding='utf-8')
        self.assertIn('满分100',text);self.assertIn('能力最多60',text)

    def test_korea_wage_rows_are_near_age_and_keep_mean_median_separate(self):
        data=json.loads((ROOT/'references'/'regional-income-kr-v051.json').read_text(encoding='utf-8'))
        rows=data['rows'];self.assertEqual(2,len(rows))
        self.assertEqual({3150000,2960000},{r['source_amount'] for r in rows})
        self.assertEqual({'mean','median'},{r['statistic'] for r in rows})
        for row in rows:
            self.assertEqual((25,29),(row['age_min'],row['age_max']))
            self.assertEqual('month',row['frequency']);self.assertEqual('gross_before_tax',row['tax_basis'])
            self.assertEqual(30,row['pdf_page_one_based'])

if __name__=='__main__':unittest.main()
