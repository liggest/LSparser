#coding:utf-8
"""
    解析指令
"""
#from .util import *
from . import CommandCore,BaseCommand,Command,Option,OPT,OptType
from ..event import EventNames

from enum import IntEnum

import asyncio
import typing

class CommandState(IntEnum):
    Unknown=-1          #未解析
    NotCommand=0        #不是指令
    Command=1           #是指令（但不一定用指令模板定义过）
    DefinedCommand=2    #是指令模板定义过的指令
    WrongType=3         #是指令模板定义过的指令（但解析时发现指令前缀不匹配）

class ParseResult:
    """
        指令解析结果
    """

    CommandState=CommandState

    @staticmethod
    def fromCmd(parser:"CommandParser",command:typing.Union[str,Command],
        params:list=(),args:typing.Dict[str,typing.Any]=None,
        type:str=None,raw=None):
        """
            从指令、参数、选项等反向构建解析结果对象\n
                parser 解析器\n
                command 指令对象或指令名，指令名如 `"cmd"`、`".cmd"`\n
                *params 参数\n
                **args 选项，无需选项前缀\n
                type 指令前缀，如 `"."`，默认为`None`\n
                raw 原始指令（传入 `tryParse` 时的指令），默认为`None`\n
        """
        return parser.buildResult(command,params,args,type,raw)

    def __init__(self,parser:"CommandParser"=None):
        self.command=""
        self.type=""
        self.params=[]
        self.args={}
        self.raw="" #完整的被解析字符串
        self.state=CommandState.Unknown #通过CommandState枚举记录指令解析状态
        self._cons=[]
        self._cmd:BaseCommand=None
        self.output=[]
        self._data=None #用来携带一些额外的数据
        self.parser=parser
        self._parent:ParseResult=None #预留，方便编写嵌套指令
        # if self.parser:
        #     self.data["parser"]=self.parser._data # 从 parser 中继承 _data 的引用

    def __contains__(self,key):
        return key in self.args

    def __getitem__(self,key):
        return self.args.get(key) #访问args的简易写法

    def __str__(self):
        result=f"{self.raw}\n"
        result+=f"type: {self.type or '未知'}\n"
        result+=f"command: {self.command or '未知'}\n"
        result+=f"params: {self.params}\n"
        if self.hasOpt:
            for k,v in self.args.items():
                result+=f"{k}: {v}\n"
        return result.strip() #基本输出的是 self 的内容，只不过格式漂亮一点

    def __repr__(self):
        return f"<ParseResult: {self.raw}>"

    def __bool__(self):
        return self.isCommand()

    @property
    def data(self):
        """
            可携带的一些额外数据
        """
        if not self._data:
            self._data={}
        return self._data

    @data.setter
    def data(self,val):
        self._data=val

    @property
    def dataArgs(self):
        """
            tryParse 方法中额外的 *args
        """
        return self.data.get("args",())

    @dataArgs.setter
    def dataArgs(self,val):
        if val:
            self.data["args"]=val

    @property
    def dataKW(self):
        """
            tryParse 方法中额外的 **kw
        """
        return self.data.get("kw",{})

    @dataKW.setter
    def dataKW(self,val):
        if val:
            self.data["kw"]=val

    @property
    def parserData(self):
        """
            解析器可能携带的一些额外数据
        """
        if self.parser:
            return self.parser.data

    def hasOpt(self):
        """
            指令是否有选项
        """
        if self._cmd:
            return len(self._cmd.Optset)!=0
        return False

    def isChecked(self):
        """
            指令是否已被初步检查（确定是否为指令、指令类型等）
        """
        return self.state != CommandState.Unknown

    def isCommand(self):
        """
            当前解析的内容是否是指令
        """
        return self.state.value > CommandState.NotCommand.value

    def isDefinedCommand(self):
        """
            当前解析的内容是否是指令模板定义过的指令
        """
        return self.state.value>=CommandState.DefinedCommand.value

    def isWrongType(self):
        """
            解析结果是否和指令模板定义的types不匹配
        """
        return self.state==CommandState.WrongType

    @property
    def paramStr(self):
        """
            得到用" "连接的指令参数（params）
        """
        return " ".join(self.params)

    @property
    def realCommand(self):
        """
            得到真正的指令名（而不是指令的别名）
        """
        if self._cmd:
            return self._cmd.name
        return self.command

    def getByType(self,arg,default=None,T=str):
        """
            得到解析后的指定选项，附加类型限制\n
                arg 选项的名称，不带选项前缀\n
                default 默认值，如果没得到选项则使用该值 默认为None\n
                T 要获得的类型，如果存在选项但不是指定类型的，也只返回默认值 默认为str
        """
        r=self.args.get(arg,default)
        if isinstance(r,T):
            return r
        return default

    def getToType(self,arg,default=None,T=str):
        """
            得到解析后的指定选项，附加类型限制\n
                arg 选项的名称，不带选项前缀\n
                default 默认值，如果没得到选项则使用该值 默认为None\n
                T 要获得的类型，如果存在选项但不是指定类型的，则尝试转换，转换失败时返回默认值 默认为str
        """
        r=self.args.get(arg,default)
        if isinstance(r,T):
            return r
        elif r:
            try:
                r=T(r)
                return r
            except:
                pass
        return default

    def splitHead(self,head):
        """
            若给定文本（head）在指令首部，则返回切除该文本后的字符串\n
            如解析到指令"rd"，传入"r"，则返回"d"
        """
        if self.command.startswith(head):
            return self.command[len(head):]
        return ""

    def opt(self,names,hasValue=OPT.Not):
        """
            在解析前为指令添加选项，常用于为没有用指令模板定义过的指令补充选项
        """
        self._cmd.opt(names,hasValue)
        return self

    def _checkParser(self):
        """
            检查解析器是否存在，无解析器则抛出异常
        """
        if not self.parser:
            raise ValueError("没找到解析器！可能本解析结果不是通过解析器产生的…")
        return self.parser
        
    def parse(self):
        """
            让解析器解析指令\n
            需要在为指令添加好所有选项后调用\n
        """
        parser=self._checkParser()
        return parser.parse(self)
    
    def execute(self):
        """
            手动让解析器执行指令\n
            不经过解析，直接调用与指令执行相关的回调，无法执行时抛出错误\n
            仅能触发指令的执行回调、报错回调、`onExecuteError` 等
        """
        parser=self._checkParser()
        return parser.execute(self)

    async def asyncExecute(self):
        """
            手动让解析器执行指令\n
            不经过解析，直接异步调用与指令执行相关的回调，无法执行时抛出错误\n
            仅能触发指令的执行回调、报错回调、`onExecuteError` 等
        """
        parser=self._checkParser()
        return await parser.asyncExecute(self)

class CommandParser:
    '''
        指令解析类\n
        例: .cmd param1 param2 -s1 -s2 s2val --l lval1 lval2 lval3\n
    '''
    def __init__(self,coreName=None):
        """
            coreName 指令中枢名称，默认为 None，即最后创建的中枢\n
        """
        self._data=None
        self.result=ParseResult(parser=self)
        self.core=CommandCore.getCore(coreName)
        self.core.tryRefresh() #如果都要解析了，core还需要刷新，那就刷新一下

    @property
    def data(self):
        if not self._data:
            self._data={}
        return self._data

    @data.setter
    def data(self,val):
        self._data=val

    def opt(self,names,hasValue=OPT.Not):
        """
            在解析前为指令添加选项，常用于为没有用指令模板定义过的指令补充选项
        """
        self.result.opt(names,hasValue)
        return self

    def getCommand(self,t) -> ParseResult:
        """
            判断指定文本是否为指令，并更新当前解析状态\n
                t 文本\n
        """
        result=ParseResult(parser=self)
        result.raw=t
        if not isinstance(t,str):
            t=str(t)
        if t=="":
            result.state=CommandState.NotCommand
            self.result=result
            return result
        if self.core.isMatchPrefix(t): #至少被识别为一个指令
            result._cons=t.strip().split()
            result.type=result._cons[0][0]
            result.command=result._cons[0][1:]
            if result.command=="": #不允许空指令
                result.state=CommandState.NotCommand
                self.result=result
                return result
            result.state=CommandState.Command
            cmd:BaseCommand=self.core.cmds.get(result.command)
            
            if cmd: #定义的指令
                result._cmd=cmd
                result.state=CommandState.DefinedCommand
                if not result.type in cmd.typelist:
                    result.state=CommandState.WrongType
            else: #未定义指令，给它一个临时的模板
                result._cmd=BaseCommand(result._cons[0],coreName=self.core.name)
        else: #不是一个指令
            result.state=CommandState.NotCommand
        self.result=result
        return result
    
    def parse(self,pr:ParseResult=None):
        """
            解析指令\n
            需要在为指令添加好所有选项后调用\n
                pr 供解析用的 ParseResult 对象
        """
        if pr is None:
            pr=self.result
        con=pr._cons[1:]
        if not pr.hasOpt():
            pr.params=con
            self.result=pr
            return pr
        while con:
            optType=Option.getOptType(con[0])
            if optType==OptType.Not:
                pr.params.append(con[0])
                con=con[1:]
            else:
                matched=False
                if optType==OptType.Long:
                    tarOpt:Option=pr._cmd.longOpts.get(con[0])
                    if tarOpt:
                        matched=True
                        optText=tarOpt.name
                        _,pr.args[optText],con=self.getLong(con,tarOpt.hasValue)
                else: #OptType.Short
                    tarOpt:Option=pr._cmd.shortOpts.get(con[0])
                    if tarOpt:
                        matched=True
                        optText=tarOpt.name
                        _,pr.args[optText],con=self.getShort(con,tarOpt.hasValue)
                if not matched:
                    pr.params.append(con[0])
                    con=con[1:]
        self.result=pr
        return pr

    def getLong(self,con,hasValue):
        """
            解析中得到一个长选项
        """
        arg=con[0]
        con=con[1:]
        if hasValue!=OPT.Not:
            val=[]
            while con and Option.getOptType(con[0])==OptType.Not:
                val.append(con[0])
                con=con[1:]
            if hasValue==OPT.Try and len(val)==0:
                val=True
        else:
            val=True
        return arg,val,con

    def getShort(self,con,hasValue):
        """
            解析中得到一个短选项
        """
        arg=con[0]
        con=con[1:]
        if hasValue==OPT.Not or (not con) or (hasValue==OPT.Try and Option.getOptType(con[0])!=OptType.Not ):
            val=True
        else:
            val=con[0]
            con=con[1:]
        return arg,val,con

    def recheckCmd(self,pr:ParseResult):
        """
            检查与解析结果对应的指令，对可能存在的问题抛出异常
        """
        cmd:Command=pr._cmd
        if not cmd:
            raise ValueError(f"{repr(pr)} 无对应指令")
        if not hasattr(cmd,"events"):
            raise ValueError(f"{repr(pr)} 可能对应未定义指令")
        return cmd

    def execute(self,pr:ParseResult):
        """
            执行解析结果对应的指令\n
            不经过解析，直接调用与指令执行相关的回调，无法执行时抛出错误\n
            仅能触发指令的执行回调、报错回调、`onExecuteError` 等
        """
        cmd:Command=self.recheckCmd(pr)
        try:
            cmd.events.sendExecute(pr,pr) #第二个 pr 会传入回调函数
            #第一个 pr 使得回调结果存入 output 中
        except Exception as err:
            cmdErrorHandle=cmd.events.sendError(pr,pr,err) #第二个 pr 和 err 会传入回调函数
            #第一个 pr 使得回调结果存入 output 中
            errorHandle=self.core.EM.send(EventNames.ExecuteError,pr,self,err)
            if not cmdErrorHandle and not any(errorHandle):
                raise err #没处理的话还是要抛出错误的
        return pr

    def tryParse(self,t,*args,**kw):
        """
            尝试解析给定文本\n
            解析指令、调用回调函数、返回解析结果对象\n
                t 文本或可以转换成文本的对象\n
                剩余参数将作为解析结果对象的额外数据\n
        """
        pr=self.getCommand(t)
        pr.dataArgs=args
        pr.dataKW=kw
        self.core.EM.send(EventNames.BeforeParse,pr,self)
        if pr and pr.state==CommandState.DefinedCommand: # 不能包括 WrongCommand
            pr=self.parse(pr)
            pr=self.execute(pr)
        elif not pr.isCommand():
        #各种事件
            self.core.EM.send(EventNames.NotCmd,pr,self)
        elif not pr.isDefinedCommand():
            self.core.EM.send(EventNames.UndefinedCmd,pr,self)
        elif pr.isWrongType():
            self.core.EM.send(EventNames.WrongCmdType,pr,self)
        self.core.EM.send(EventNames.AfterParse,pr,self)
        return pr

    async def asyncExecute(self,pr:ParseResult):
        """
            执行解析结果对应的指令\n
            不经过解析，直接异步调用与指令执行相关的回调，无法执行时抛出错误\n
            仅能触发指令的执行回调、报错回调、`onExecuteError` 等
        """
        cmd:Command=self.recheckCmd(pr)
        try:
            await cmd.events.asyncSendExecute(pr,pr) #第二个 pr 会传入回调函数
            #第一个 pr 使得回调结果存入 output 中
        except Exception as err:
            cmdErrTsk=asyncio.create_task( cmd.events.asyncSendError(pr,pr,err) ) #第二个 pr 和 err 会传入回调函数
            #第一个 pr 使得回调结果存入 output 中
            parserErrTsk=asyncio.create_task( self.core.EM.asyncSend(EventNames.ExecuteError,pr,self,err) )
            cmdErrorHandle=await cmdErrTsk
            errorHandle=await parserErrTsk #暂时不知道这样搞好不好
            if not cmdErrorHandle and not any(errorHandle):
                raise err #没处理的话还是要抛出错误的
        return pr

    async def asyncTryParse(self,t,*args,**kw):
        """
            尝试解析给定文本\n
            解析指令、异步调用回调函数、返回解析结果对象\n
                t 文本或可以转换成文本的对象\n
                剩余参数将作为解析结果对象的额外数据\n
        """
        pr=self.getCommand(t)
        pr.dataArgs=args
        pr.dataKW=kw
        await self.core.EM.asyncSend(EventNames.BeforeParse,pr,self)
        if pr and pr.state==CommandState.DefinedCommand: # 不能包括 WrongCommand
            pr=self.parse(pr)
            pr=await self.asyncExecute(pr)
        elif not pr.isCommand():
        #各种事件
            await self.core.EM.asyncSend(EventNames.NotCmd,pr,self)
        elif not pr.isDefinedCommand():
            await self.core.EM.asyncSend(EventNames.UndefinedCmd,pr,self)
        elif pr.isWrongType():
            await self.core.EM.asyncSend(EventNames.WrongCmdType,pr,self)
        await self.core.EM.asyncSend(EventNames.AfterParse,pr,self)
        return pr

    def buildResult(self,command:typing.Union[str,Command],
        params:list=(),args:typing.Dict[str,typing.Any]=None,
        type:str=None,raw=None):
        """
            从指令、参数、选项等反向构建解析结果对象
        """
        pr=ParseResult(self)
        pr.state=CommandState.NotCommand
        if isinstance(command,str):
            if self.core.isMatchPrefix(command):
                pr.type=command[0]
                pr.command=command[1:]
            else:
                pr.command=command
            _cmd=self.core.cmds.get(pr.command)
        elif isinstance(command,Command):
            _cmd=command
            pr.command=_cmd.name
        if not pr.type and type:
            pr.type=type
        if pr.command: #非空指令
            pr.state=CommandState.Command
            pr._cmd=_cmd
            pr.params=[*params]
            if args:
                pr.args=args
            if pr._cmd:
                pr.state=CommandState.DefinedCommand
                if not pr.type:
                    pr.type=pr._cmd.typelist[0]
                if not pr.type in pr._cmd.typelist:
                    pr.state=CommandState.WrongType
            else:
                if not pr.type:
                    pr.type=self.core.commandPrefix[0]
                pr._cmd=BaseCommand(f"{pr.type}{pr.command}",coreName=self.core.name)
        if raw:
            pr.raw=raw
            if not isinstance(raw,str):
                raw=str(raw)
            pr._cons=raw.strip().split()
        else:
            if pr.type or pr.command:
                pr._cons.append(f"{pr.type}{pr.command}")
            pr._cons+=[str(x) for x in pr.params]
            for k,v in pr.args.items():
                if v:
                    longk=f"{Option.longPrefix}{k}"
                    if longk in pr._cmd.longOpts:
                        k=longk #优先使用长选项
                    else:
                        k=f"{Option.shortPrefix}{k}"
                    pr._cons.append(k) 
                    if isinstance(v,(list,tuple)):
                        pr._cons+=[str(x) for x in v]
                    elif isinstance(v,str):
                        pr._cons.append(v)
                    elif not v is True:
                        pr._cons.append(str(v))
            pr.raw=" ".join(pr._cons)
        return pr

if __name__=="__main__":
    cp=CommandParser()
    #cmd="！login 1313123 -a -z -s 888 --c 12 13 -x"
    cmd=".cmd param1 param2 -s1 -s2 s2val --long lval1 lval2 lval3"
    #cmd=".send aaa -box2"
    if cp.getCommand(cmd):
        #print(cp.separateCommand("lo"))
        #print(cp.separateCommand("logi"))
        #cp.opt(["-z","-a"],2).opt("--c",1).parse()
        #cp.opt("-s1",2).opt("-s2",1).opt(["--l","--long"],1).parse()
        #cp.opt(["-box","-b"],0).opt("-user",0).opt(["-qq","-group"],0).parse()
        print(cp.result)
    else:
        print("不是命令")
            
            
        
        
