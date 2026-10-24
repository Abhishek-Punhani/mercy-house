import unittest
from mercy.town.factory import build


class CasebookTests(unittest.TestCase):
    def test_review_only_acquired_content_without_proof_metadata(self):
        world=build('last_witness',7)
        denied=world.step('review_records',{'records':['r1']})
        self.assertIn('error',denied)
        found=world.step('search',{'surface':'floor'})['findings']
        received=world.step('review_records',{'records':[r['record_id'] for r in found]})['records']
        self.assertEqual(received,found)
        self.assertTrue(all('propositions' not in r and 'source' not in r for r in received))

    def test_notes_cannot_certify_a_guessed_accusation(self):
        world=build('last_witness',7)
        note=world.step('record_note',{'summary':'A hypothesis to test.','hypotheses':[{'statement':'Savitri killed Mira.','status':'open','sources':[]}]})
        world.step('submit_report',{'findings':[{'actor':'savitri','predicate':'killed','object':'mira','sources':[note['record_id']]}]})
        self.assertEqual(world.result['score'],0.)
        self.assertEqual(world.result['supported_findings'],[])

    def test_fake_citations_and_long_notes_are_rejected(self):
        world=build('last_witness',7)
        for args in [{'summary':'x','hypotheses':[{'statement':'Hypothesis','status':'open','sources':['made-up']}]},{'summary':'x'*1201}]:
            result=world.step('record_note',args)
            self.assertIn('error',result)
        self.assertEqual(world.receipts,{})
