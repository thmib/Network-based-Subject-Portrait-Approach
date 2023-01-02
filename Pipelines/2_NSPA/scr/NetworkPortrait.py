# This file contains network-based subject portrait approach.
from collections import Counter
import pandas as pd
import numpy as np
import math
import random
import multiprocessing

def ModelDecomposition(d, f1, f2, l):
    #This function generats pair-wise modes for feature f1 and f2
    #Features:
    #   d: data 2 d list
    #   f1: feature1 index
    #   f2: feature1 index
    #   l: vector of labels
    
    v1 =  getFeatureValueVector(d, f1) # value vector for f1
    v2 =  getFeatureValueVector(d, f2)# value vector for f2
    
    app_round_balancing = 4 # rounding parameter

    s = ""

    f1_values = list(Counter(v1).keys())
    f2_values = list(Counter(v2).keys())
    
    df = pd.DataFrame({'f1': v1, 'f2': v2, 'labels': l})
    gb = df.groupby(['f1','f2','labels'])
    gb_size = gb.size()
    #print(gb_size.index)
    #print(gb_size.index[:][2])
    s = ""
    for i in gb_size.index:
        s = s + str(f1) +","+ str(int(i[0])) +","+ str(f2)+"," + str(int(i[1]))+","+ str(i[2])+"," + str(gb_size[i])+"\n"
    return s

def getFeatureValueVector(data, colIndex):
    # This function returns a data column.
    return [r[colIndex] for r in data]
    
def ComprehensiveNet(v1, v2, f1, f2, l, numOfPermutation):
    #This function generats comprehensive network
    #Features:
    #   v1: vector for f1
    #   v2: vector for f2
    #   f1: feature1 index
    #   f2: feature1 index
    #   l: vector of labels
    #   numOfPermutation: number of permutation
    #print(f1, f2, 1)
    #v1 =  getFeatureValueVector(d, f1) # value vector for f1
    #v2 =  getFeatureValueVector(d, f2)# value vector for f2

    app_round_balancing = 4 # rounding parameter


    #f1_values = list(Counter(v1).keys())
    #f2_values = list(Counter(v2).keys())

    f1_values = [0,1,2]
    f1_values_index = [[i for i, e in enumerate(v1) if e == f1_values[0]],[i for i, e in enumerate(v1) if e == f1_values[1]],[i for i, e in enumerate(v1) if e == f1_values[2]]]
    #print(f1_values_index)

    f2_values = [0,1,2]
    f2_values_index = [[i for i, e in enumerate(v2) if e == f2_values[0]],[i for i, e in enumerate(v2) if e == f2_values[1]],[i for i, e in enumerate(v2) if e == f2_values[2]]]
    #print(f2_values_index)

    l_values = [0,1]
    l_values_index = [[i for i in range(len(l)) if l[i] == 0], [i for i in range(len(l)) if l[i] == 1]]
    #print(l_values_index)


    #print(f1, f2, 2)
    #df = pd.DataFrame({'f1': v1, 'f2': v2, 'labels': l})
    
    # cal ig
    #gb = df.groupby(['f1','f2','labels'])
    #gb_size = gb.size()
    #print(gb_size.index)
    #print(gb_size.index[:][2])
    #print(gb_size)
    #print(f1_values)
    #print(f2_values)
    #print(f1, f2, 3)
    m_ctl = np.zeros(shape=(len(f1_values),len(f2_values)))
    m_case = np.zeros(shape=(len(f1_values),len(f2_values)))
    
    for i in range(0, 3):
        for j in range(0, 3):
            m_ctl[i][j] = len(set.intersection(set(f1_values_index[i]),set(f2_values_index[j]),set(l_values_index[0])))
            m_case[i][j] = len(set.intersection(set(f1_values_index[i]),set(f2_values_index[j]),set(l_values_index[1])))

    
    ratio = np.sum(m_case)/np.sum(m_ctl)
    m_ctl = m_ctl*ratio

    ig, mutual, main1, main2 = Fun_IG_ABC(m_ctl, m_case)
    # permutation
    #print(f1, f2, 4)

    #print(f1, f2, 5)
    ig = "{:.9f}".format(ig)
    mutual = "{:.9f}".format(mutual)
    return str(f1) + '\t' + str(f2) + '\t' + str(ig) + '\t' + str(mutual) + '\n'

def MainEffect(v1, v2, f1, f2, l, numOfPermutation):
    #This function generats comprehensive network
    #Features:
    #   v1: vector for f1
    #   v2: vector for f2
    #   f1: feature1 index
    #   f2: feature1 index
    #   l: vector of labels
    #   numOfPermutation: number of permutation
    #print(f1, f2, 1)
    #v1 =  getFeatureValueVector(d, f1) # value vector for f1
    #v2 =  getFeatureValueVector(d, f2)# value vector for f2

    app_round_balancing = 4 # rounding parameter


    #f1_values = list(Counter(v1).keys())
    #f2_values = list(Counter(v2).keys())

    f1_values = [0,1,2]
    f1_values_index = [[i for i, e in enumerate(v1) if e == f1_values[0]],[i for i, e in enumerate(v1) if e == f1_values[1]],[i for i, e in enumerate(v1) if e == f1_values[2]]]
    #print(f1_values_index)

    f2_values = [0,1,2]
    f2_values_index = [[i for i, e in enumerate(v2) if e == f2_values[0]],[i for i, e in enumerate(v2) if e == f2_values[1]],[i for i, e in enumerate(v2) if e == f2_values[2]]]
    #print(f2_values_index)

    l_values = [0,1]
    l_values_index = [[i for i in range(len(l)) if l[i] == 0], [i for i in range(len(l)) if l[i] == 1]]
    #print(l_values_index)


    #print(f1, f2, 2)
    #df = pd.DataFrame({'f1': v1, 'f2': v2, 'labels': l})
    
    # cal ig
    #gb = df.groupby(['f1','f2','labels'])
    #gb_size = gb.size()
    #print(gb_size.index)
    #print(gb_size.index[:][2])
    #print(gb_size)
    #print(f1_values)
    #print(f2_values)
    #print(f1, f2, 3)
    m_ctl = np.zeros(shape=(len(f1_values),len(f2_values)))
    m_case = np.zeros(shape=(len(f1_values),len(f2_values)))
    
    for i in range(0, 3):
        for j in range(0, 3):
            m_ctl[i][j] = len(set.intersection(set(f1_values_index[i]),set(f2_values_index[j]),set(l_values_index[0])))
            m_case[i][j] = len(set.intersection(set(f1_values_index[i]),set(f2_values_index[j]),set(l_values_index[1])))

    
    ratio = np.sum(m_case)/np.sum(m_ctl)
    m_ctl = m_ctl*ratio

    ig, mutual, main1, main2 = Fun_IG_ABC(m_ctl, m_case)
    # permutation
    #print(f1, f2, 4)

    #print(f1, f2, 5)
    ig = "{:.9f}".format(ig)
    mutual = "{:.9f}".format(mutual)
    main1 = "{:.9f}".format(main1)
    main2 = "{:.9f}".format(main2)
    return str(f1) + '\t' + str(f2) + '\t' + str(ig) + '\t' + str(mutual) + '\t' + str(main1) + '\t' + str(main2) + '\n'

#### Pair-wise information gain ####
#Ref: Hu, Ting, et al. "Characterizing genetic interactions in human disease association studies using statistical epistasis networks." BMC bioinformatics 12.1 (2011): 364.

def Fun_H_C(n_ctl, n_case):
    #n_ctl = sum(c=='control')
    #n_case = len(c) - n_ctl
    if(n_ctl==0 or n_case==0):
        return 0
    n_ctl_p = n_ctl/(n_ctl+n_case)
    n_case_p = n_case/(n_ctl+n_case)
    if(n_ctl_p==0 or n_case_p==0):
        return 0
    return n_ctl_p*math.log(1/n_ctl_p,2)+n_case_p*math.log(1/n_case_p,2)
    
def Fun_H_CA(arr_ctl, arr_case):
    s_ctl = sum(arr_ctl)
    s_case = sum(arr_case)
    s = sum([s_ctl, s_case])
    r = 0.0
    for i in range(0,len(arr_ctl)):
        if(arr_ctl[i] == 0 or arr_case[i] == 0):#encountered empty
            continue
        r += (arr_ctl[i]/s)*math.log(1/(arr_ctl[i]/(arr_ctl[i]+arr_case[i])),2)
    for i in range(0,len(arr_case)):
        if(arr_ctl[i] == 0 or arr_case[i] == 0):#encountered empty
            continue
        r += (arr_case[i]/s)*math.log(1/(arr_case[i]/(arr_ctl[i]+arr_case[i])),2)
    return r

def Fun_I_AC(arr_ctl, arr_case):
    return Fun_H_C(sum(arr_ctl),sum(arr_case)) - Fun_H_CA(arr_ctl, arr_case)

def Fun_IG_ABC(m_ctl, m_case):
    mutual = Fun_I_AC(m_ctl.flatten(),m_case.flatten())
    main_1 = Fun_I_AC(np.sum(m_ctl, axis=0),np.sum(m_case, axis=0))
    main_2 = Fun_I_AC(np.sum(m_ctl, axis=1),np.sum(m_case, axis=1))
    return mutual-main_1-main_2, mutual, main_1, main_2

def MakeSubjectNetDataset(d_m, l_m, d_n, l_n, e):
    #This function generats subject network dataset using delta degree as features.
    #Features:
    #   d_m: modeling data 2 d list
    #   l_m: labels of modeling data
    #   d_n: data to generate networks 2 d list
    #   l_n: labels of network data
    #   e: selected edges
    
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    data_pnFeatures = pool.map(subjectNet_parallel, [(d_m, l_m, subject, e) for subject in d_n])
    pool.close()
    #data_pnFeatures = [subjectNet(d_m, l_m, subject, e) for subject in d_n]
    return data_pnFeatures
    
def subjectNet_parallel(p):
    return subjectNet(p[0], p[1], p[2], p[3])

def subjectNet(d_m, l_m, arr_feature, e):
    #This function generats subject network dataset using delta degree as features.
    #Features:
    #   d_m: modeling data 2 d list
    #   l_m: labels of modeling data
    #   arr_feature: data to generate networks 2 d list
    #   e: selected edges
    #Returns:
    #   subjectNet feature
    
    # delta degree
    pn_features = [0] * len(arr_feature)
    for p in e:
        f1 = p[0] # feature index one
        f2 = p[1] # feature index two
        edgeProperity = deltaDegree(d_m, f1, arr_feature[f1], f2, arr_feature[f2], l_m)
        if edgeProperity == 0:
            # negative edge
            pn_features[f1] = pn_features[f1] + 1
            pn_features[f2] = pn_features[f2] + 1
        else:
            # positive edge
            pn_features[f1] = pn_features[f1] - 1
            pn_features[f2] = pn_features[f2] - 1
    return pn_features
    
def deltaDegree(d, f1, f1_value, f2, f2_value, l):
    #This function generats pair-wise modes for feature f1 and f2
    #Features:
    #   d: data 2 d list
    #   f1: feature1 index
    #   f1_value: value of feature1
    #   f2: feature1 index
    #   f2_value: value of feature2
    #   l: vector of labels
    #Return:
    #   return 1 means positive edge, otherwise 0 means negative edge

    v1 =  getFeatureValueVector(d, f1) # value vector for f1
    v2 =  getFeatureValueVector(d, f2)# value vector for f2

    app_round_balancing = 4 # rounding parameter

    s = ""

    f1_values = list(Counter(v1).keys())
    f2_values = list(Counter(v2).keys())

    df = pd.DataFrame({'f1': v1, 'f2': v2, 'labels': l})
    
    gb = df.groupby(['f1','f2','labels'])
    gb_size = gb.size()

    # get ratio
    ratio = (l==1).sum()/(l==0).sum()
    numOfControl = 0
    numOfCase = 0
    #print(gb_size)
    #print(f1_value, f2_value)
    if (f1_value, f2_value, 0) in gb_size.index:
        #print('enter')
        numOfControl = gb_size[(f1_value, f2_value, 0)]
    if (f1_value, f2_value, 1) in gb_size.index:
        #print('enter')
        numOfCase = gb_size[(f1_value, f2_value, 1)]

    numOfControl = numOfControl*ratio

    if numOfControl >= numOfCase:
        return 0 # negative
    else:
        return 1 # positive
    
