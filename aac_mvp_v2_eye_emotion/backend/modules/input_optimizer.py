class InputOptimizer:
    def __init__(self):
        self.stats = {}
    def update_and_choose(self, m):
        method = m.get('method','touch')
        st = self.stats.setdefault(method, {'selections':0,'errors':0,'time_sum':0,'samples':0})
        st['selections'] += int(m.get('selections',0))
        st['errors'] += int(m.get('errors',0))
        st['time_sum'] += float(m.get('avg_time_ms',0))
        st['samples'] += 1
        best, best_score = method, 1e18
        for k,v in self.stats.items():
            sel = max(v['selections'],1)
            acc = 1.0 - (v['errors']/sel)
            avg_time = (v['time_sum']/max(v['samples'],1)) if v['samples'] else 9e9
            score = avg_time / max(acc, 0.1)
            if score < best_score:
                best_score, best = score, k
        return best
