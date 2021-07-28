"""
    若干种字符串相似度
"""

import math

def getStrVector(tarstr,cdict,clen=None):
    """
        将字符串向量化，向量的每一项对应字符集中一种字符的频数，字符集、每种字符在向量中对应的下标由cdict提供
    """
    if not clen:
        clen=len(cdict.keys())
    vec=[0]*clen
    for c in tarstr:
        vec[cdict[c]]+=1
        #vec[cdict[c]]=1
    return vec

def cosSimilarity(str1,str2):
    """
        余弦相似度，将字符串向量化后计算
    """
    cdict={}
    currentidx=0
    for c in str1+str2:
        idx=cdict.get(c,None)
        if idx is None:
            cdict[c]=currentidx
            currentidx+=1
    vec1=getStrVector(str1,cdict,clen=currentidx)
    vec2=getStrVector(str2,cdict,clen=currentidx)
    dot=0
    sum1=0
    sum2=0
    for i in range(len(vec1)):
        sum1+=vec1[i]**2
        sum2+=vec2[i]**2
        dot+=vec1[i]*vec2[i]
    if dot==0:
        return 0.0
    return dot/( math.sqrt(sum1)*math.sqrt(sum2) )

def IoU(str1,str2):
    """
        交并比，将字符串转化为字符集合进行计算
    """
    set1=set(str1)
    set2=set(str2)
    ul=len(set1.union(set2))
    if ul==0:
        return 0.0
    return len(set1.intersection(set2))/ul

def diceSimilarity(str1,str2):
    """
        dice相似度，IoU的变种
    """
    set1=set(str1)
    set2=set(str2)
    ul=len(set1)+len(set2)
    if ul==0:
        return 0.0
    return 2*len(set1.intersection(set2))/ul

def editSimilarity(str1,str2):
    """
        编辑相似度，由编辑距离转化而来
    """
    len1=len(str1)
    len2=len(str2)
    lev=levenshtein(str1,str2,len1,len2)
    return 1-lev/max(len1,len2)

def levenshtein(str1,str2,len1=None,len2=None):
    """
        编辑距离，返回从一个字符串变成另一个，需要的最少编辑（插入、删除、替换字符）次数
    """
    if not len1:
        len1=len(str1)
    if not len2:
        len2=len(str2)
    #if len1==0:
    #    return len2
    #if len2==0:
    #    return len1
    dislist=[ [i for i in range(len2+1)] ]
    for i in range(1,len1+1):
        dislist.append( [0]*(len2+1) )
        dislist[i][0]=i
    for i in range(1,len1+1):
        for j in range(1,len2+1):
            temp=0
            if str1[i-1]==str2[j-1]:
                temp=0
            else:
                temp=1
            dislist[i][j]=min(dislist[i-1][j-1]+temp,dislist[i][j-1]+1,dislist[i-1][j]+1)
    #for d in dislist:
    #    print(d)
    return dislist[len1][len2]
    
def hammingSimilarity(str1,str2):
    """
        汉明相似度，表示相同长度字符串，对应位置上字符相同的程度
    """
    len1=len(str1)
    len2=len(str2)
    if len1!=len2:
        return 0.0
    if len1==0:
        return 1.0
    same=0
    for i in range(len1):
        if str1[i]==str2[i]:
            same+=1
    return same/len1
    


if __name__ == "__main__":
    #print( cosSimilarity("apple","app") )
    #print( cosSimilarity("abcd","dcba") )
    #print( cosSimilarity("非空","") )
    
    #print( IoU("aa","bb"),diceSimilarity("aa","bb") )
    #print( IoU("aa","ab"),diceSimilarity("aa","ab") )
    #print( IoU("aa",""),diceSimilarity("aa","") )
    #print( IoU("abcd","dcba"),diceSimilarity("abcd","dcba") )
    #print( IoU("abcd","aacbcdc"),diceSimilarity("abcd","aacbcdc") )
    #print( IoU("app","apple"),diceSimilarity("app","apple") )

    #print( editSimilarity("apple","app") )
    #print( editSimilarity("一二三四五","12345") )
    #print( editSimilarity("abcd","dcba") )
    #print( editSimilarity("非空","") )
    #print( editSimilarity("拥有效果","效果的") )
    #print( editSimilarity("效果的","拥有效果") )
    #print( editSimilarity("abcd","baaccd") )
    #print( editSimilarity("一样","一样") )

    #print( hammingSimilarity("一样","一样") )
    #print( hammingSimilarity("吃肉大过年的","大过年的吃肉") )
    #print( hammingSimilarity("一三一四二","二四一四三") )
    #print( hammingSimilarity("","") )

    print("全完了")
