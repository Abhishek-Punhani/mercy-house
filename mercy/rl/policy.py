"""A dependency-free linear softmax policy trained with episodic REINFORCE.

This module is public: it imports no world, character, verifier or training data.
"""
import json
import math
from pathlib import Path


class Selector:
    VERSION = 1

    def __init__(self, weights=None):
        self.weights = dict(weights or {})

    def probabilities(self, features):
        if not features:
            raise ValueError('At least one candidate is required')
        logits = [sum(self.weights.get(k, 0.) * v for k, v in row.items()) for row in features]
        peak = max(logits)
        values = [math.exp(x - peak) for x in logits]
        total = sum(values)
        return [v / total for v in values]

    def choose(self, features, rng, greedy=False):
        probabilities = self.probabilities(features)
        if greedy:
            # Random tie breaking avoids learning a candidate-order convention.
            peak = max(probabilities)
            chosen = rng.choice([i for i, p in enumerate(probabilities) if abs(p - peak) < 1e-12])
        else:
            point = rng.random()
            chosen = len(probabilities) - 1
            for i, p in enumerate(probabilities):
                point -= p
                if point <= 0:
                    chosen = i
                    break
        return chosen, probabilities

    @staticmethod
    def log_gradient(features, chosen, probabilities):
        gradient = dict(features[chosen])
        for p, row in zip(probabilities, features):
            for key, value in row.items():
                gradient[key] = gradient.get(key, 0.) - p * value
        return gradient

    def update(self, episodes, baseline, learning_rate=.08, entropy_coefficient=0.):
        """One on-policy batch update; baseline was fixed before this batch.

        Each episode is (trajectory, terminal_return). A trajectory stores the
        public feature rows, sampled index and probabilities at decision time.
        No hidden state, expert action labels or verifier internals are inputs.
        """
        if not episodes:
            raise ValueError('An update requires episodes')
        gradient = {}
        for trajectory, reward in episodes:
            advantage = reward - baseline
            for features, chosen, probabilities in trajectory:
                for key, value in self.log_gradient(features, chosen, probabilities).items():
                    gradient[key] = gradient.get(key, 0.) + advantage * value / len(episodes)
                if entropy_coefficient:
                    mean_log=sum(p*math.log(max(p,1e-300)) for p in probabilities)
                    for p,row in zip(probabilities,features):
                        scale=entropy_coefficient*p*(mean_log-math.log(max(p,1e-300)))/len(episodes)
                        for key,value in row.items():gradient[key]=gradient.get(key,0.)+scale*value
        norm = math.sqrt(sum(v * v for v in gradient.values()))
        scale = min(1., 5. / max(norm, 1e-12))
        for key, value in gradient.items():
            self.weights[key] = self.weights.get(key, 0.) + learning_rate * scale * value
        return norm

    def save(self, path, metadata=None):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'version': self.VERSION, 'feature_version': 2,
                                    'algorithm': 'episodic_reinforce_linear_softmax',
                                    'weights': self.weights, 'metadata': metadata or {}},
                                   indent=2, sort_keys=True) + '\n')

    @classmethod
    def load(cls, path):
        path = Path(path)
        if path.stat().st_size > 2_000_000:
            raise ValueError('Selector checkpoint too large')
        data = json.loads(path.read_text())
        if data.get('version') != cls.VERSION or data.get('feature_version') not in (1, 2):
            raise ValueError('Unsupported selector checkpoint')
        weights = data.get('weights')
        if not isinstance(weights, dict) or len(weights) > 10000:
            raise ValueError('Invalid selector weights')
        for key, value in weights.items():
            if not isinstance(key, str) or len(key) > 200 or type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('Invalid selector coefficient')
        return cls(weights)
