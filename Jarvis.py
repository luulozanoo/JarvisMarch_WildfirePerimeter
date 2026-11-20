#!/usr/bin/env python
# coding: utf-8




def angulo(u, v):
    c = (u[0]*v[0] + u[1]*v[1]) / (sqrt(u[0]**2 + u[1]**2) * sqrt(v[0]**2 + v[1]**2))
    return acos(max(-1, min(1, c)))

def minimoAngular(p, actual, d):
    mejor = None
    mejor_ang = None
    mejor_dist = None
    for q in p:
        if q == actual:
            continue
        v = (q[0]-actual[0], q[1]-actual[1])
        ang = angulo(d, v)
        dist = v[0]**2 + v[1]**2
        if mejor is None or ang < mejor_ang or (ang == mejor_ang and dist > mejor_dist):
            mejor, mejor_ang, mejor_dist = q, ang, dist
    return mejor

def Ymin(p):
    p_select=p[0]
    
    for i in range(len(p)):
        if (p[i][1]==p_select[1] and p[i][0]<p_select[0]) or p[i][1]<p_select[1]:
            p_select=p[i]

    return p_select



def Jarvis(S):
    minimo = Ymin(S)
    envolvente = [minimo]
    i = 1
    while True:
        if i == 1:
            d = (1, 0)
        else:
            d = (envolvente[i-1][0]-envolvente[i-2][0], envolvente[i-1][1]-envolvente[i-2][1])
        minimo_angular = minimoAngular(S, E[i-1], d)
        if minimo_angular == minimo:
            break
        envolvente.append(minimo_angular)
        i += 1
    return envolvente
    

