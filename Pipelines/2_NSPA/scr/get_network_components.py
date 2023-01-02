import pandas as pd
import networkx as nx
import sys


# generate graph
def generateGraph(edgelist):
    # return the G 
    G=nx.from_pandas_edgelist(edgelist, 'SNP1', 'SNP2', ['ig', 'mi'])
    return G

if __name__ == "__main__":
    # read edgelist
    df_edgelist=pd.read_csv(sys.argv[1],sep='\t')
    th_comp_size=int(sys.argv[2])
    G = generateGraph(df_edgelist)
    arr_Component = sorted(nx.connected_components(G), key=len, reverse=True)

    # prepare component size distribution
    comp_size = [len(c) for c in arr_Component]
    rank = [int(r) for r in range(len(comp_size))]
    df_componentSize = pd.DataFrame({'rank': rank, 'size': comp_size})
    df_componentSize.to_csv('components_size.csv', index=False)


    for i in range(len(arr_Component)):
        #print(i, len(arr_Component[i]))
        if (len(arr_Component[i]) < th_comp_size):
            break
        nx.write_edgelist(G.subgraph(arr_Component[i]),'LC'+str(i)+'.edgelist',data=['ig', 'mi'],delimiter=',')
        # write nodelist
        pd.DataFrame({'SNP': list(arr_Component[i])}).to_csv('LC'+str(i)+'.nodelist', index=False, header=False)
