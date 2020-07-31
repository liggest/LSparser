"""
    创建指令模板
"""

from .core import CommandCore
#from .util import *

import functools

commandPrefix=[".","。","-","!","！","/"]

def isMatchPrefix(text,prefix=commandPrefix):
    """
        判断文本是否和前缀列表中的前缀匹配\n
            text 文本\n
            prefix 前缀列表\n
    """
    temp=text.lstrip()
    if temp=="":
        return False
    return temp[0] in prefix

def cmdCallback(cmdname,core=CommandCore.getLast()):
    """
        装饰器 另一种为指令模板添加回调函数的方式\n
            cmdname 指令名\n
            core 指令所在的CommandCore对象
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        core.addFunc(cmdname,wrapper)
        return wrapper
    return decorator

class Command:
    """
        指令模板类
    """
    def __init__(self,name,types=commandPrefix,addToCore=True,core=CommandCore.getLast()):
        """
            name 指令名，诸如 .test 或 test\n
            types 指令前缀，根据name决定，或使用默认\n
            addToCore 该指令模板是否自动添加到CommandCore对象\n
            core 要添加指令的CommandCore对象
        """
        if isMatchPrefix(name):
            self.name=name[1:]
            self.typelist=[name[0]]
        else:
            self.name=name
            self.typelist=types
        if self.name=="":
            raise ValueError("指令不能为空")
        self.nameset=set()
        self.nameset.add(self.name)
        self.Optset=set()
        self.longOpts={}
        self.shortOpts={}
        self.callbacklist=[]
        self.help() #初始化时，默认不显示帮助，需要手动添加
        if addToCore: #添加到core
            self.core=core
            self.core.addCommand(self)

    def __str__(self):
        return self.getHelp()

    __repr__=__str__

    def addLSOpt(self,name,opt,opttype):
        """
            opttype 1：短 2：长
        """
        if opttype==1:
            self.shortOpts[name]=opt
        elif opttype==2:
            self.longOpts[name]=opt
        else:
            raise Exception("错误的opttype")

    def getHelp(self):
        """
            得到指令的完整帮助文本
        """
        result=""
        result+=self.typelist[0]+"/".join(self.nameset)+" "
        for o in self.Optset:
            result+="/".join(o.names)+" "
        if self.showHelp:
            result+="\n"
            front="\n".join( ["  "+h for h in self.frontHelp.split("\n")] )
            result+=f"{front}\n"
            for o in self.Optset:
                result+=f"  {str(o)}\n"
            result+=f"{self.backHelp}\n"
        return result[:-1]

    def types(self,*types):
        """
            为指令模板添加更多type（指令前缀）\n
            支持链式调用
        """
        if self.typelist is commandPrefix:
            self.typelist=commandPrefix.copy()
        self.typelist+=types
        return self

    def names(self,*names):
        """
            为指令模板添加更多名称（别名）\n
            支持链式调用
        """
        for n in names:
            self.core.addCommand(self,name=n)
            self.nameset.add(n)
        return self

    def help(self,front=None,back=None):
        """
            为指令模板添加帮助文本\n
                front 选项帮助前的帮助文本，输出时每行前会有两个空格\n
                back 选项帮助后的帮助问题\n
            两个参数均为None，则视为不显示帮助文本\n
            支持链式调用
        """
        if not (front or back):
            self.showHelp=False
            self.frontHelp=""
            self.backHelp=""
        else:
            self.showHelp=True
            if front:
                self.frontHelp=front
            if back:
                self.backHelp=back
        return self

    def opt(self,names,hasValue=0,help=None):
        """
            为指令模板添加选项\n
                names 选项名，字符串/列表/元组，形如"-a"或["-a","-A","--aAa"]\n
                hasValue 取值判定 0为不需要值 1为需要值 2为尽可能有值\n
                help 选项的帮助文本\n
            支持链式调用
        """
        Option(names,hasValue,help,self)
        return self

    def callback(self,*funcs):
        """
            为指令模板添加更多回调函数\n
            支持链式调用
        """
        self.callbacklist+=funcs
        print(f"为{'/'.join(self.nameset)}添加了回调函数")
        return self

class Option():
    """
        选项类
    """
    shortPrefix="-"
    longPrefix="--"

    @staticmethod
    def getOptType(text):
        """
            返回整数 0为非Opt，1为短，2为长
        """
        if text.startswith(Option.longPrefix):
            return 2
        elif text.startswith(Option.shortPrefix):
            return 1
        else:
            return 0

    def __init__(self,names,hasValue=0,help=None,cmd=None):
        """
            详见Command.opt\n
                cmd 要添加选项的指令模板
        """
        if isinstance(names,str):
            names=[names]
        for i,n in enumerate(names):
            opttype=Option.getOptType(n)
            if opttype==0:
                names[i]=Option.shortPrefix + n
                opttype=1
            if cmd:
                cmd.addLSOpt(n,self,opttype)
        self.names=names
        self.hasValue=hasValue
        self.help=help
        if cmd:
            cmd.Optset.add(self)

    def __str__(self):
        """
            -a/-b/--c True/Text 这里是帮助
        """
        front="/".join(self.names)
        if self.hasValue==0:
            mid=" True "
        elif self.hasValue==1:
            mid=" Text "
        else:
            mid=" True/Text "
        back=""
        if self.help:
            back=self.help
        return front+mid+back

    __repr__=__str__

    '''
    def isLongOrShort(self):
        """
            返回整数 0为短 1为长 2为短或长
        """
        hasShort=False
        hasLong=False
        for n in self.names:
            opttype=Option.getOptType(n)
            if opttype==2:
                hasLong=True
            elif opttype==1:
                hasShort=True
            if hasLong and hasShort:
                return 2
        if hasShort:
            return 0
        elif hasLong:
            return 1
        else:
            raise Exception("%s是无效的opt"%str(self))
    
    def isMatch(self,t):
        for n in self.names:
            if t.startswith(n):
                return True
        return False
    '''

if __name__ == "__main__":
    c=Command("test").opt("-v",0,"测试选项").opt(["--r","-e"],1,"选项选项").help("这是测试命令")
    print( CommandCore.getLast() )
    print(c)