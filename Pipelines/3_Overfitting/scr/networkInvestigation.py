import pandas as pd
import numpy as np
import networkx as nx
from scipy.optimize import curve_fit
import collections
import os 


th_begin = 0.03
th_delta = 0.0002
th_end = 0.015

# read df
df = pd.read_csv("CN_ig_0.015.ig", dtype={'SNP1': str, 'SNP2': str, 'ig': np.float16, 'mi': np.float16}, names = ['SNP1', 'SNP2', 'ig', 'mi'], header=None,delim_whitespace=True)

# generate graph
def generateGraph(edgelist):
    # return the G 
    G=nx.from_pandas_edgelist(edgelist, 'SNP1', 'SNP2', ['ig', 'mi'])
    return G

# graph analysis

def func(x, a, b):
    return a * x ** -b

def degreeDistribution(G):
    nodeDegree = [val for (node, val) in G.degree()]
    nodeDegree_counter = collections.Counter(nodeDegree)
    degree, degreeCount = zip(*nodeDegree_counter.items())
    total = sum(degreeCount)
    degreePct= tuple([c/total for c in degreeCount])
    node_degree_popt, node_degree_pcov = curve_fit(func, degree, degreePct)
    return node_degree_popt[0], node_degree_popt[1], max(nodeDegree)

def analysisGraph(G):
    c,lam, max_degree = degreeDistribution(G)
    return {'Node#': len(G), 'Edge#':G.number_of_edges(), 'Comp#': nx.number_connected_components(G), 'MaxDegree': max_degree,'L_coeff': lam}


    

print('ig','Node#','Edge#','Comp#','LargestHubSize','power_coeff','LC_Node#','LC_Edge#','LC_LargestHubSize','LC_power_coeff',sep='\t')

for th in np.arange(th_begin,th_end-th_delta,-th_delta):
    th = round(th,4)
    df_t = df.loc[df['ig'] >= th]
    G = generateGraph(df_t)
    arr_Component = sorted(nx.connected_components(G), key=len, reverse=True)
    Glc = G.subgraph(arr_Component[0])
    G_stat = analysisGraph(G)
    Glc_stat = analysisGraph(Glc)
    print(th, G_stat['Node#'], G_stat['Edge#'], G_stat['Comp#'], G_stat['MaxDegree'],G_stat['L_coeff'],Glc_stat['Node#'], Glc_stat['Edge#'], Glc_stat['MaxDegree'],Glc_stat['L_coeff'],sep='\t')
    #os.mkdir(str(th))
    #nx.write_edgelist(Gg,'subgraph'+str(th)+'.edgelist',data=False)

    '''
    nx.write_edgelist(G.subgraph(arr_Component[0]),'LC0_'+str(th)+'.edgelist',data=False)
    nx.write_edgelist(G.subgraph(arr_Component[1]),'LC1_'+str(th)+'.edgelist',data=False)
    nx.write_edgelist(G.subgraph(arr_Component[2]),'LC2_'+str(th)+'.edgelist',data=False)
    nx.write_edgelist(G.subgraph(arr_Component[3]),'LC3_'+str(th)+'.edgelist',data=False)
    nx.write_edgelist(G.subgraph(arr_Component[4]),'LC4_'+str(th)+'.edgelist',data=False)
    nx.write_edgelist(G.subgraph(arr_Component[5]),'LC5_'+str(th)+'.edgelist',data=False)
    nx.write_edgelist(G.subgraph(arr_Component[6]),'LC6_'+str(th)+'.edgelist',data=False)
    nx.write_edgelist(G.subgraph(arr_Component[7]),'LC7_'+str(th)+'.edgelist',data=False)
    nx.write_edgelist(G.subgraph(arr_Component[8]),'LC8_'+str(th)+'.edgelist',data=False)
    nx.write_edgelist(G.subgraph(arr_Component[9]),'LC9_'+str(th)+'.edgelist',data=False)
    nx.write_edgelist(G.subgraph(arr_Component[10]),'LC10_'+str(th)+'.edgelist',data=False)
    nx.write_edgelist(G.subgraph(arr_Component[11]),'LC11_'+str(th)+'.edgelist',data=False)
    '''





