"""
Some code to time various api calls

"""

from meerkat_api.resources import data
import time
import cProfile
ag = data.AggregateYear()
ag = data.AggregateCategory()

#print(ag.get(1,1))
def timeit(function, N, *pos):
    times = []
    for _ in range(N):
        t = time.time()
        function(*pos)
        times.append(time.time()-t)
    return sum(times)/N, times

print(timeit(ag.get,10,"front",1))

#|cProfile.run('ag.get(1,1)')
