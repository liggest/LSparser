"""
事件管理
"""

from ..util.asyncs import callAllGen,asyncCallAllGen,emptyAsyncGen

class EventLists(list):

    @staticmethod
    def mergeLists(one,other):
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

    def add(self,*callbacks):
        self+=callbacks

    def send(self,*args,**kw):
        return [*self.sendGen(*args,**kw)]

    def sendGen(self,*args,**kw):
        return callAllGen(self,*args,**kw)

    async def asyncSend(self,*args,**kw):
        return [r async for r in self.asyncSendGen(*args,**kw)]

    def asyncSendGen(self,*args,**kw):
        # async for r in asyncCallAllGen(self,*args,**kw):
        #     yield r
        return asyncCallAllGen(self,*args,**kw)

    def removes(self,*callbacks):
        for func in callbacks:
            try:
                self.remove(func)
            except:
                print(f"没有找到回调",func)
    
    def merge(self,other):
        if isinstance(other,(list,tuple)):
            self+=other
            if isinstance(other,EventLists):
                for k,v in other.subs.items():
                    self.addSub(k,*v)
        else:
            raise ValueError(f"无法将 {other} 纳入")

    def hasSub(self,name):
        return self._subs and name in self._subs #subs不为空且name在其中

    def getSub(self,name):
        return getattr(self,name,None)

    def addSub(self,name,*callbacks):
        subList=self.getSub(name)
        if subList:
            subList+=callbacks
        else:
            subList=[*callbacks]
        setattr(self,name,subList)

    def ensureSub(self,name):
        subList=self.getSub(name)
        if subList:
            return subList
        setattr(self,name,[])
        return self.getSub(name)

    ensure=ensureSub

    def sendSub(self,name,*args,**kw):
        return [*self.sendSubGen(name,*args,**kw)]

    def sendSubGen(self,name,*args,**kw):
        subList=self.getSub(name)
        if subList:
            yield from callAllGen(subList,*args,**kw)
        else:
            print(f"子事件 {name} 不存在！")

    async def asyncSendSub(self,name,*args,**kw):
        return [r async for r in self.asyncSendSubGen(name,*args,**kw)]

    def asyncSendSubGen(self,name,*args,**kw):
        subList=self.getSub(name)
        if subList:
            # async for r in asyncCallAllGen(subList,*args,**kw):
            #     yield r
            return asyncCallAllGen(subList,*args,**kw)
        else:
            print(f"子事件 {name} 不存在！")
        # async for r in emptyAsyncGen():
        #     yield r
        return emptyAsyncGen()

    def removeSub(self,name,*callbacks):
        subList:list=self.getSub(name)
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

EL=EventLists

class EventManager:
    
    # @classmethod
    # def callAll(cls,callList,*args,**kw):
        # return [*callAllGen(callList,*args,**kw)]
        # results=[]
        # for func in callList:
        #     rtmp=func(*args,**kw)
        #     results.append(rtmp)
        # return results
    
    def __init__(self):
        self.events={}

    def get(self,name):
        return self.events.get(name)

    def add(self,name,*callbacks):
        callList=self.get(name)
        if callList:
            EL.add(callList,*callbacks)
            # callList+=callbacks
        else:
            callList=[*callbacks] # EventLists(callbacks)
        self.events[name]=callList
    
    def ensure(self,name):
        callList=self.get(name)
        if callList:
            return callList
        callList=EventLists([])
        self.events[name]=callList
        return callList

    def send(self,name,*args,**kw):
        # callList=self.events.get(name)
        # if callList:
        #     return EventManager.callAll(callList,*args,**kw)
        # # print(f"事件 {name} 不存在！")
        # return []
        return [*self.sendGen(name,*args,**kw)]

    def sendGen(self,name,*args,**kw):
        callList=self.get(name)
        if callList:
            return EL.sendGen(callList,*args,**kw)
            # yield from callAllGen(callList,*args,**kw)
        return ()
    
    async def asyncSend(self,name,*args,**kw):
        return [r async for r in self.asyncSendGen(name,*args,**kw)]

    def asyncSendGen(self,name,*args,**kw):
        callList=self.get(name)
        if callList:
            return EL.asyncSendGen(callList,*args,**kw)
            # async for r in asyncCallAllGen(callList,*args,**kw):
            #     yield r
        # async for r in emptyAsyncGen():
        #     yield r
        return emptyAsyncGen()

    def remove(self,name,*callbacks):
        callList:list=self.get(name)
        if callList:
            print(f"尝试移除事件 {name} 的一些回调…")
            EL.removes(callList,*callbacks)
            # for func in callbacks:
            #     try:
            #         callList.remove(func)
            #     except:
            #         print(f"事件 {name} 中没有找到回调",func)
        else:
            print(f"事件 {name} 不存在！")
    
    def removeAll(self,name):
        if name in self.events:
            self.events.pop(name)
        else:
            print(f"事件 {name} 不存在！")

    def merge(self,name,otherName):
        callList=self.get(name)
        otherList=self.get(otherName)
        if otherList:
            callList=EL.mergeLists(callList,otherList)
            self.events[name]=callList
            self.removeAll(otherName)

    def hasSub(self,name,subName):
        callList=self.get(name)
        return callList and isinstance(callList,EventLists) and callList.hasSub(subName)

    def addSub(self,name,subName,*callbacks):
        callList=self.get(name)
        if callList:
            if not isinstance(callList,EventLists):
                callList=EventLists(callList)
        else:
            callList=EventLists()
        callList.addSub(subName,*callbacks)
        self.events[name]=callList
        

    def sendSub(self,name,subName,*args,**kw):
        # callList=self.get(name)
        # if callList and isinstance(callList,EventLists):
        #     return callList.sendSub(subName,*args,**kw)
        # # print(f"事件 {name} 的子事件 {subName} 不存在！")
        # return []
        return [*self.sendSubGen(name,subName,*args,**kw)]

    def sendSubGen(self,name,subName,*args,**kw):
        callList=self.get(name)
        if callList and isinstance(callList,EventLists):
            return callList.sendSubGen(subName,*args,**kw)
        return ()

    async def asyncSendSub(self,name,subName,*args,**kw):
        return [r async for r in self.asyncSendSubGen(name,subName,*args,**kw)]
    
    def asyncSendSubGen(self,name,subName,*args,**kw):
        callList=self.get(name)
        if callList and isinstance(callList,EventLists):
            # async for r in callList.asyncSendSubGen(subName,*args,**kw):
            #     yield r
            return callList.asyncSendSubGen(subName,*args,**kw)
        # async for r in emptyAsyncGen():
        #     yield r
        return emptyAsyncGen()

    def removeSub(self,name,subName,*callbacks):
        callList=self.get(name)
        if callList and isinstance(callList,EventLists):
            callList.removeSub(subName,*callbacks)
        else:
            print(f"事件 {name} 的子事件 {subName} 不存在！")

    def removeSubAll(self,name,subName):
        callList=self.get(name)
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


            

