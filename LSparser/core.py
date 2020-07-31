"""
    指令模板管理
"""

from .strSimilarity import editSimilarity
from . import command

class CommandCore:
    """
        指令模板管理类\n
        一般会自动创建一个对象，可以通过CommandCore.getLast()得到\n
        也可以手动创建对象，所有CommandCore对象都会存储在CommandCore.corelist中
    """
    corelist=[]

    @staticmethod
    def getLast():
        """
            得到最后创建的CommandCore对象
        """
        if len(CommandCore.corelist)==0:
            CommandCore()
        return CommandCore.corelist[-1]

    def __init__(self):
        self.cmds={}
        self.cmdlist=[]
        self.isRefreshed=False
        self.spareFuncs={} #记录因为装饰器的缘故，比指令模板还先添加的那些回调函数

        CommandCore.corelist.append(self)

    def __getitem__(self,key):
        return self.cmds[key] #如果key不存在会报错，只能用来得到已经存在的指令模板

    def __str__(self):
        if not self.isRefreshed:
            self.refresh()
        cmdstr='\n'.join(self.cmdlist)
        return f"当前记录了{len(self.cmdlist)}个指令名\n{cmdstr}"

    __repr__=__str__

    def addCommand(self,cmd,name=None):
        if name is None:
            name=cmd.name
        if self.cmds.get(name,None):
            raise Exception("尝试注册已经存在的指令")
        self.cmds[name]=cmd
        funcs=self.spareFuncs.get(name,None)
        if funcs:
            cmd.callback(*funcs)
            del self.spareFuncs[name]
        self.isRefreshed=False #因为添加了新指令，所以可能需要调用refresh方法

    def refresh(self,force=False):
        """
            刷新指令列表\n
            如果要使用排序好的指令列表，则需要调用此函数
        """
        self.cmdlist=list(self.cmds.keys())
        self.cmdlist.sort()
        self.isRefreshed=True
    
    def addFunc(self,cmdname,func):
        cmd=self.cmds.get(cmdname,None)
        if cmd:
            cmd.callback(func)
        else:
            sparelist=self.spareFuncs.get(cmdname,None)
            if sparelist:
                sparelist.append(func)
            else:
                sparelist=[]
                sparelist.append(func)
                self.spareFuncs[cmdname]=sparelist

    def getCmdSimilarity(self,text,top=-1,getScore=False,scoreFunc=editSimilarity):
        """
            比较给定文本和列表中指令的相似度\n
                text 给定的文本 如：test、.test（指令前缀不会纳入比较）\n
                top 返回列表的长度 默认为-1 若为正，则只返回若干个结果\n
                getScore 是否返回相似度 默认为False 若为True，则返回结果中包含相似度\n
                scoreFunc 相似度比较函数 默认使用strSimilarity.editSimilarity\n
            返回 一个列表，内含指令，按和给定文本的相似度从大到小排列
        """
        if not self.isRefreshed:
            self.refresh()
        perfix=""
        if command.isMatchPrefix(text):
            perfix=text[0]
            text=text[1:]
        similist=[]
        for cn in self.cmdlist:
            score=scoreFunc(text,cn)
            similist.append( (score,cn) )
        similist.sort(reverse=True)
        if getScore:
            resultlist=similist
        else:
            resultlist=[ sl[1] for sl in similist ]
        if top>0:
            resultlist=resultlist[:top]
        return resultlist
        

if __name__ == "__main__":
    CommandCore()
    CommandCore()
    CommandCore()
    print(CommandCore.corelist)