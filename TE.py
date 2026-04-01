import math
T=int(input())
for _ in range(T):
    n,k=map(int,input().split())
    best=1
    for i in range(1,int(math.isqrt(n))+1):
        if n%i==0:
            if i<=k:
                best=max(best,i)
            if n//i<=k:
                best=max(best,n//i)
    print(n//best)            