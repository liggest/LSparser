"""
事件管理
"""

class EventLists(list):

    @property
    def subs(self):
        if self._subs is None:
            self._subs={}
        return self._subs

    def __init__(self,*args,**kw):
        self._subs=None
        super().__init__(*args,**kw)

    def __setattr__(self,name,value):
        if isinstance(value,(list,tuple)):
            self.subs[name]=EventLists(value)
        else:
            super().__setattr__(name,value)

    def __getattr__(self,name):
        subList=self.subs.get(name)
        if subList:
            return subList
        else:
            raise AttributeError

    def __delattr__(self, name):
        if name in self.subs:
            del self.subs[name]
        else:
            super().__delattr__(name)

    def __str__(self):
        return f"{super().__str__()}\nsubs:{self._subs}"

    def __bool__(self):
        return bool(len(self) or self._subs) #若列表或subs中有值，就为true

    def hasSub(self,name):
        return self._subs and name in self.subs #subs不为空且name在其中

    def addSub(self,name,*callbacks):
        subList=getattr(self,name,None)
        if subList:
            subList+=callbacks
        else:
            subList=callbacks
        setattr(self,name,subList)

    def sendSub(self,name,*args,**kw):
        subList=getattr(self,name,None)
        if subList:
            return EventManager.callAll(subList,*args,**kw)
        print(f"子事件 {name} 不存在！")
        return []

    def removeSub(self,name,*callbacks):
        subList=getattr(self,name,None)
        if subList:
            for func in callbacks:
                try:
                    subList.remove(func)
                except:
                    print(f"子事件 {name} 中没有找到回调",func)
        else:
            print(f"子事件 {name} 不存在！")
    
    def removeSubAll(self,name):
        if name in self.subs:
            self.subs.pop(name)
        else:
            print(f"子事件 {name} 不存在！")

    def merge(self,other):
        if isinstance(other,(list,tuple)):
            self+=other
            if isinstance(other,EventLists):
                for k,v in other.subs.items():
                    self.addSub(k,*v)
        else:
            raise ValueError(f"无法将 {other} 纳入")

class EventManager:
    
    @staticmethod
    def callAll(callList,*args,**kw):
        results=[]
        for func in callList:
            rtmp=func(*args,**kw)
            results.append(rtmp)
        return results
    
    def __init__(self):
        self.events={}

    def add(self,name,*callbacks):
        callList=self.events.get(name)
        if callList:
            callList+=callbacks
        else:
            callList=callbacks # EventLists(callbacks)
        self.events[name]=callList
    
    def send(self,name,*args,**kw):
        callList=self.events.get(name)
        if callList:
            return EventManager.callAll(callList,*args,**kw)
        # print(f"事件 {name} 不存在！")
        return []
    
    def remove(self,name,*callbacks):
        callList=self.events.get(name)
        if callList:
            for func in callbacks:
                try:
                    callList.remove(func)
                except:
                    print(f"事件 {name} 中没有找到回调",func)
        else:
            print(f"事件 {name} 不存在！")
    
    def removeAll(self,name):
        if name in self.events:
            self.events.pop(name)
        else:
            print(f"事件 {name} 不存在！")

    def mergeLists(self,one,other):
        if not one:
            return other
        if isinstance(one,EventLists):
            one.merge(other)
        elif isinstance(other,EventLists):
            one=EventLists(one)
            one.merge(other)
        else:
            one+=other
        return one

    def merge(self,name,otherName):
        callList=self.events.get(name)
        otherList=self.events.get(otherName)
        if otherList:
            callList=self.mergeLists(callList,otherList)
            self.events[name]=callList
            self.removeAll(otherName)

    def hasSub(self,name,subName):
        callList=self.events.get(name)
        return callList and isinstance(callList,EventLists) and callList.hasSub(subName)

    def addSub(self,name,subName,*callbacks):
        callList=self.events.get(name)
        if callList:
            if not isinstance(callList,EventLists):
                callList=EventLists(callList)
        else:
            callList=EventLists()
        self.events[name]=callList
        callList.addSub(subName,*callbacks)
    
    def sendSub(self,name,subName,*args,**kw):
        callList=self.events.get(name)
        if callList and isinstance(callList,EventLists):
            return callList.sendSub(subName,*args,**kw)
        # print(f"事件 {name} 的子事件 {subName} 不存在！")
        return []

    def removeSub(self,name,subName,*callbacks):
        callList=self.events.get(name)
        if callList and isinstance(callList,EventLists):
            callList.removeSub(subName,*callbacks)
        else:
            print(f"事件 {name} 的子事件 {subName} 不存在！")

    def removeSubAll(self,name,subName):
        callList=self.events.get(name)
        if callList and isinstance(callList,EventLists):
            callList.removeSubAll(subName)
        else:
            print(f"事件 {name} 的子事件 {subName} 不存在！")


if __name__ == "__main__":

    # class CallableName:
    #     def __init__(self,name):
    #         self.name=name
    #     def __call__(self):
    #         print(self)
    #     def __str__(self):
    #         return self.name
    #     __repr__=__str__
    # Name=CallableName

    # A=Name("A");B=Name("B");C=Name("C");D=Name("D")
    # E=Name("E");F=Name("F");G=Name("G");H=Name("H")
    # I=Name("I");J=Name("J");K=Name("K");L=Name("L")
    # M=Name("M");N=Name("N");O=Name("O");P=Name("P")
    # Q=Name("Q");R=Name("R");S=Name("S");T=Name("T")
    # U=Name("U");V=Name("V");W=Name("W");X=Name("X")
    # Y=Name("Y");Z=Name("Z")

    # a=EventLists([A,B,C])
    # a.addSub("def",D,E,F)
    # print(a)
    # a+=[G,H,I]
    # print(a)
    # a.sendSub("h")
    # a.sendSub("def")
    # a.removeSub("def",E)
    # print(a)

    # em=EventManager()
    # em.addSub("b","jkl",J,K,L)
    # print(em.events["b"])
    # a.addSub("jkl",M)
    # print(a)
    # em.events["b"].merge(a)
    # print(em.events["b"])
    # em.removeSubAll("b","def")
    # print(em.events["b"])

    # c=EventLists()
    # print(c)
    # c.addSub("n",N)
    # print(bool(c))
    pass


            

