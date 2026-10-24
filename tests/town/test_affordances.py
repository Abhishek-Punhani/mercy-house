import json
import unittest
from mercy.rl.affordances import augment
from mercy.rl.public import Notebook, features


class PublicAffordanceTests(unittest.TestCase):
    def test_only_visible_people_routes_and_features_are_added(self):
        book=Notebook({'now':{'place':{'id':'room'},'exits':[{'id':'hall'}],'searchable_features':['desk']},
                       'private_fake_field':{'journal':'HIDDEN_CANARY','killer':'not-public'}})
        book.people['room']=[{'id':'p1','name':'An observed person','occupation':'cook','appearance':'A person.'}]
        choices=augment(book,[])
        self.assertTrue(any(a['tool']=='go' and a['args']['destination']=='hall' for a in choices))
        self.assertTrue(any(a['tool']=='ask' and a['args']['pid']=='p1' for a in choices))
        self.assertFalse(any(a['tool']=='submit_report' for a in choices))
        text=json.dumps(choices)
        self.assertNotIn('HIDDEN_CANARY',text)
        self.assertNotIn('not-public',text)

    def test_family_risk_features_follow_public_connection_not_person_id(self):
        book=Notebook({'now':{'place':{'id':'hall'}}})
        book.records['r1']={'record_id':'r1','person':'person_one','recollections':[{'text':'My brother delivered it.','basis':'personal_history'}]}
        first=features(book,{'tool':'search','args':{'surface':'book','by':'person_one'}},10,10)
        book.records['r1']['person']='different_person'
        second=features(book,{'tool':'search','args':{'surface':'book','by':'different_person'}},10,10)
        self.assertEqual(first,second)
        self.assertEqual(first['delegated_family_unsupervised'],1.)


if __name__=='__main__':unittest.main()
