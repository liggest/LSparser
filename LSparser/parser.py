#coding:utf-8
"""
    解析指令
"""
#from .util import *
from .command import *
from .core import CommandCore

from enum import Enum

class CommandState(Enum):
    NotCommand=0        #不是指令
    Command=1           #是指令（但不一定用指令模板定义过）
    DefinedCommand=2    #是指令模板定义过的指令
    WrongType=3         #是指令模板定义过的指令（但解析时发现指令前缀不匹配）

class CommandParser():
    '''
        指令解析类\n
        例: .cmd param1 param2 -s1 -s2 s2val --l lval1 lval2 lval3\n
        基本一个CommandParser对象只用来解析一行文本
    '''
    def __init__(self,core=CommandCore.getLast()):
        self.command={}
        self.cmdobj=None
        self.state=CommandState.NotCommand #通过CommandState枚举记录指令解析状态
        #self.isCmd=False
        #self.isDefinedCmd=False
        #self.shortspecial=[]
        #self.longspecial=[]
        #self.special=[]
        self.cons=[]
        self.raw="" #完整的被解析字符串
        self.core=core
        if not self.core.isRefreshed: #如果都要解析了，core还需要刷新，那就刷新一下
            self.core.refresh()

    def __getitem__(self,key):
        return self.command.get(key,None) #访问command字典的简易写法

    def __str__(self):
        result=self.raw+"\n"
        result+=f"type: {self.command.get('type','未知')}\n"
        result+=f"command: {self.command.get('command','未知')}\n"
        result+=f"params: {self.command.get('params','未知')}\n"
        if self.hasOpt:
            for k,v in self.command.items():
                if not k in ["params","command","type"]:
                    result+=f"{k}: {v}\n"
        return result[:-1] #基本输出的是command字典的内容，只不过格式漂亮一点

    __repr__=__str__
    
    def isCommand(self):
        """
            当前解析的内容是否是指令
        """
        return self.state!=CommandState.NotCommand

    def isDefinedCommand(self):
        """
            当前解析的内容是否是指令模板定义过的指令
        """
        return self.state.value>=CommandState.DefinedCommand.value

    def isWrongType(self):
        """
            解析后是否发现和指令模板定义的types不匹配
        """
        return self.state==CommandState.WrongType

    def hasOpt(self):
        """
            指令是否有选项
        """
        if self.cmdobj:
            return len(self.cmdobj.Optset)!=0
        return False

    def opt(self,names,hasValue=0):
        """
            在解析前为指令添加选项，常用于为未用指令模板定义过的指令补充选项
        """
        self.cmdobj.opt(names,hasValue)
        return self

    def getCommand(self,t):
        """
            判断指定文本是否为指令，并更新当前解析状态
        """
        if t=="":
            return False
        r=isMatchPrefix(t) #如果r为True，则至少被识别为一个指令
        if r:
            self.cons=t.strip().split()
            self.command["type"]=self.cons[0][0]
            self.command["command"]=self.cons[0][1:]
            self.raw=t
            if self.command["command"]=="":
                return False
            self.state=CommandState.Command
            cmdobj=self.core.cmds.get(self.command["command"],None)
            if cmdobj:
                self.cmdobj=cmdobj
                self.state=CommandState.DefinedCommand
                #self.isDefinedCmd=True
                if not isMatchPrefix(t,cmdobj.typelist):
                    self.state=CommandState.WrongType
                    #raise TypeError(f"{self.command['command']}指令不支持type '{self.command['type']}'")
            else:
                self.cmdobj=Command(self.cons[0],addToCore=False)
            #self.isCmd=True
        return r
    
    def separateCommand(self,cmd):
        """
            若给定文本在指令首部，则返回切除该文本后的字符串\n
            如解析到指令"rd"，传入"r"，则返回"d"
        """
        if self.command["command"].startswith(cmd):
            return self.command["command"][len(cmd):]
        return None
        
    def parse(self):
        """
            解析指令\n
            需要在为指令添加好所有选项后调用
        """
        self.command["params"]=[]
        con=self.cons[1:]
        if not self.hasOpt():
            self.command["params"]=con
            return
        while len(con)!=0:
            if not con[0].startswith(Option.shortPrefix):
                self.command["params"].append(con[0])
                con=con[1:]
            else:
                matched=False
                if con[0].startswith(Option.longPrefix):
                    tarOpt=self.cmdobj.longOpts.get(con[0],None)
                    if tarOpt:
                        matched=True
                        optText=con[0].lstrip("-")
                        con=con[1:]
                        if tarOpt.hasValue>0:
                            self.command[optText]=[]
                            while len(con)!=0 and not con[0].startswith("-"):
                                self.command[optText].append(con[0])
                                con=con[1:]
                            if tarOpt.hasValue==2 and len(self.command[optText])==0:
                                self.command[optText]=True
                        else:
                            self.command[optText]=True
                else:
                    tarOpt=self.cmdobj.shortOpts.get(con[0],None)
                    if tarOpt:
                        matched=True
                        optText=con[0].lstrip("-")
                        con=con[1:]
                        if tarOpt.hasValue==0 or len(con)==0 or (tarOpt.hasValue==2 and con[0].startswith("-") ):
                            self.command[optText]=True
                        else:
                            self.command[optText]=con[0]
                            con=con[1:]
                if not matched:
                    self.command["params"].append(con[0])
                    con=con[1:]

    def tryParse(self,t):
        """
            尝试解析给定文本\n
            如果是在指令模板中定义过的指令，则直接解析、调用回调函数、以列表的形式返回各个函数运行结果\n
            如果 没有为指令模板附加回调函数 或 指令没在指令模板中定义过 或 根本不是指令，则返回None
        """
        result=None
        r=self.getCommand(t)
        if r and self.state==CommandState.DefinedCommand:
            self.parse()
            if len(self.cmdobj.callbacklist)!=0:
                result=[]
                for c in self.cmdobj.callbacklist:
                    temp=c(self)
                    result.append( temp )
        return result
            

    def getByType(self,attr,default=None,T=str):
        """
            得到解析后的指定选项，附加类型限制\n
                attr 选项的名称，不带选项前缀（如"-"）\n
                default 默认值，如果没得到选项则使用该值 默认为None\n
                T 要获得的类型，如果存在选项但不是指定类型的，也只返回默认值 默认为str
        """
        r=self.command.get(attr,default)
        if isinstance(r,T):
            return r
        return default
    
    def refresh(self):
        """
            干脆重新创建一个CommandParser对象也是可以的
        """
        self.__init__()
    
    def getParams(self):
        """
            得到用" "连接的指令参数（params）
        """
        return " ".join(self.command["params"])

    def getRealCommand(self):
        """
            得到真正的指令名（而不是指令的别名）
        """
        return self.cmdobj.name

if __name__=="__main__":
    cp=CommandParser()
    #cmd="！login 1313123 -a -z -s 888 --c 12 13 -x"
    cmd=".cmd param1 param2 -s1 -s2 s2val --l lval1 lval2 lval3"
    #cmd=".send aaa -box2"
    if cp.getCommand(cmd):
        #print(cp.separateCommand("lo"))
        #print(cp.separateCommand("logi"))
        #cp.opt(["-z","-a"],2).opt("--c",1).parse()
        cp.opt("-s1",2).opt("-s2",1).opt("--l",1).parse()
        #cp.opt(["-box","-b"],0).opt("-user",0).opt(["-qq","-group"],0).parse()
        print(cp.command)
    else:
        print("不是命令")
            
            
        
        
