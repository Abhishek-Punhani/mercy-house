import unittest
from copy import deepcopy

from mercy.audit.review import clean_advisory, review
from mercy.town.factory import build
from mercy.town.reference import solve
from mercy.rl.skills import checkpoint, restore, propose


class PrivateReportReviewTests(unittest.TestCase):
    def test_truth_knowledge_cannot_replace_acquired_proof_and_snapshot_unchanged(self):
        w=build('lantern_room',7);snapshot=w.export_private();before=deepcopy(snapshot)
        result=review(snapshot,{'findings':[{'actor':w.case['culprit'],'predicate':'killed','object':'oren','sources':[]}]})
        self.assertEqual(result['programmatic_result']['score'],0.)
        self.assertTrue(result['private_unestablished_targets'])
        self.assertEqual(snapshot,before)

    def test_advisory_cannot_override_programmatic_reward(self):
        value=clean_advisory({'assessment':'A hypothetical review','issues':[],'limitations':[],'score':1,'success':True,'programmatic_result':{'score':1}})
        self.assertTrue(value['unscored'])
        for key in ('score','success','programmatic_result'):self.assertNotIn(key,value)

    def test_supported_reference_review_agrees_and_lists_real_sources(self):
        w=build('mercy_inquest',7);solve(w)
        report={'findings':[{**p,'sources':list(w.receipts)} for p in w.result['supported_findings']]}
        out=review(w.export_private(),report)
        self.assertEqual(out['programmatic_result']['score'],1.)
        self.assertEqual(out['private_unestablished_targets'],[])
        self.assertTrue(all(s['acquired'] for c in out['claim_reviews'] for s in c['sources']))

    def test_delegation_proposer_attributes_carriage_to_signer_not_payer(self):
        w,book=restore(checkpoint('delegation',141000))
        action={'tool':'search','args':{'surface':'visitors book','by':'kabir','supervise':True}}
        result=w.step(action['tool'],action['args']);book.observe(action,result)
        reports=[a for a in propose('delegation',book) if a['tool']=='submit_report']
        findings=[f for a in reports for f in a['args']['findings']]
        self.assertTrue(any(f['predicate']=='moved' and f['actor']=='nalin' for f in findings))
        self.assertFalse(any(f['predicate']=='moved' and f['actor']=='savitri' for f in findings))
