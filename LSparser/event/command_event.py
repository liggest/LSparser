from ..command import CommandCore

class CommandEvents:
    """
        指令事件相关操作
    """

    @staticmethod
    def getEventName(name):
        """
            指令事件名统一为 cmd-指令名
        """
        return f"cmd-{name}"

    Error="error" # error子事件（报错回调）的名称

    def __init__(self,name,core:CommandCore):
        """
            name 为指令名\n
            core 为指令所在的中枢对象
        """
        self.name=name
        self.core=core
        self.EM=self.core.EM
        self.eventName=CommandEvents.getEventName(self.name)

    def onExecute(self,*callbacks):
        """
            添加执行回调
        """
        self.EM.add(self.eventName,*callbacks)
        print(f"为 {self.name} 指令添加了执行回调")
    
    def onError(self,*callbacks):
        """
            添加报错回调
        """
        self.EM.addSub(self.eventName,CommandEvents.Error,*callbacks)
        print(f"为 {self.name} 指令添加了报错回调")
    
    def merge(self,otherName):
        """
            将其他名称的指令对应的事件纳入当前指令的事件中
        """
        otherEventName=CommandEvents.getEventName(otherName)
        if otherEventName in self.EM.events:
            print(f"将 {otherName} 指令的回调纳入 {self.name} 指令")
            self.EM.merge(self.eventName,otherEventName)

    def send(self,name,pr=None,*args,**kw):
        """
            触发回调
        """
        if not pr is None:
            result=[]
            for r in self.EM.sendGen(name,*args,**kw):
                pr.output.append(r)
                result.append(r)
            return result
        return self.EM.send(name,*args,**kw)

    async def asyncSend(self,name,pr=None,*args,**kw):
        """
            异步触发回调
        """
        if not pr is None:
            result=[]
            async for r in self.EM.asyncSendGen(name,*args,**kw):
                pr.output.append(r)
                result.append(r)
            return result
        return await self.EM.asyncSend(name,*args,**kw)

    def sendExecute(self,pr=None,*args,**kw):
        """
            触发执行回调\n
                pr 解析结果对象，不为 None 则回调结果会传入其 output 中
        """
        return self.send(self.eventName,pr,*args,**kw)

    async def asyncSendExecute(self,pr=None,*args,**kw):
        """
            异步触发执行回调\n
                pr 解析结果对象，不为 None 则回调结果会传入其 output 中
        """
        return await self.asyncSend(self.eventName,pr,*args,**kw)

    def sendSub(self,name,subName,pr=None,*args,**kw):
        """
            触发子事件回调
        """
        if not pr is None:
            result=[]
            for r in self.EM.sendSubGen(name,subName,*args,**kw):
                pr.output.append(r)
                result.append(r)
            return result
        return self.EM.sendSub(name,subName,*args,**kw)

    async def asyncSendSub(self,name,subName,pr=None,*args,**kw):
        """
            异步触发子事件回调
        """
        if not pr is None:
            result=[]
            async for r in self.EM.asyncSendSubGen(name,subName,*args,**kw):
                pr.output.append(r)
                result.append(r)
            return result
        return await self.EM.asyncSend(name,*args,**kw)

    def sendError(self,pr=None,*args,**kw):
        """
            触发报错回调\n
                pr 解析结果对象，不为 None 则回调结果会传入其 output 中
        """
        return self.sendSub(self.eventName,CommandEvents.Error,pr,*args,**kw)

    async def asyncSendError(self,pr=None,*args,**kw):
        """
            异步触发报错回调\n
                pr 解析结果对象，不为 None 则回调结果会传入其 output 中
        """
        return await self.asyncSendSub(self.eventName,CommandEvents.Error,pr,*args,**kw)

# 这个在py3.9以下用不了……
# 只能使用 event.py 中的替代方案
class CommandEventsWrapper:
    """
        给指令添加事件用的装饰器
    """

    def __init__(self,name,coreName=None):
        """
            name 指令名\n
            coreName 指令中枢名，默认为 None
        """
        core=CommandCore.getCore(coreName)
        cmd=core.cmds.get(name)
        if cmd:
            self.events=cmd.events
        else:
            self.events=CommandEvents(name,core)
    
    def __call__(self,func):
        """
            等同于添加执行回调
        """
        return self.execute(func)

    def execute(self,func):
        """
            添加执行回调
        """
        self.events.onExecute(func)
        return func

    def error(self,func):
        """
            添加报错回调
        """
        self.events.onError(func)
        return func