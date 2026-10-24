import unittest
from mercy.town.factory import build
from mercy.town.reference import Investigator
from mercy.town.agents import FixtureAgent
from mercy.town.world import Town


class CompositionalProofTests(unittest.TestCase):
    def documents(self):
        w=build('borrowed_signature',7)
        a=Investigator(w)
        a.act('search',surface='desk')
        a.go('hall','courtyard','square','das_house')
        a.act('search',surface='parlor table')
        a.act('search',surface='stove')
        return w,a

    def test_two_separate_comparisons_can_support_same_forgery(self):
        w,a=self.documents()
        paper=a.compare('folded note','household paper')
        handwriting=a.compare('folded note','signed shopping note')
        self.assertIn('matching torn edges',paper['observation'])
        self.assertIn('Letter strokes',handwriting['observation'])
        note=next(r for r in a.book.records.values() if r.get('label')=='folded note')
        w.step('submit_report',{'findings':[{'actor':'Savitri Das','predicate':'forged','object':note['object_id'],
                                             'sources':[paper['record_id'],handwriting['record_id']]}]})
        self.assertEqual(w.result['score'],1.)

    def test_paper_match_alone_cannot_identify_writer(self):
        w,a=self.documents();paper=a.compare('folded note','household paper')
        w.step('submit_report',{'findings':[{'actor':'savitri','predicate':'forged','object':'threat',
                                           'sources':[paper['record_id']]}]})
        self.assertEqual(w.result['score'],0.)

    def test_unique_observed_label_with_suffix_identifies_same_document(self):
        w,a=self.documents();a.compare('folded note','household paper','signed shopping note')
        w.step('submit_report',{'findings':[{'actor':'savitri','predicate':'forged','object':'folded note threatening Dev','sources':list(a.book.records)}]})
        self.assertEqual(w.result['score'],1.)

    def test_physical_match_is_symmetric_and_does_not_imply_murder(self):
        w=Town(7,FixtureAgent());w.simulate(4);w.arrive()
        floor=w.step('search',{'surface':'floor'})['findings']
        w.location='das_house';table=w.step('search',{'surface':'parlor table'})['findings']
        cuff=next(r for r in floor if r['label']=='torn cuff');coat=next(r for r in table if r['label']=='household shawl')
        compared=w.step('compare',{'records':[cuff['record_id'],coat['record_id']]})
        w.step('submit_report',{'findings':[{'actor':cuff['object_id'],'predicate':'matched','object':coat['object_id'],'sources':[compared['record_id']]}]})
        self.assertTrue(any(p['predicate']=='matched' for p in w.result['supported_findings']))
        self.assertEqual(w.result['score'],0.)


if __name__=='__main__':unittest.main()
