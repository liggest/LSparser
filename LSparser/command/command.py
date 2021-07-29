"""
    创建指令模板
"""

from . import CommandCore
from ..event import CommandEvents

from enum import IntEnum

class OptVal(IntEnum):
    """
        用于Option的取值判定\n
            Not / N=0 无需值\\
            Must / M=1 需要值\\
            Try / T=2 尽可能有值\\
    """
    Not=0
    Must=1
    Try=2
    N=0
    M=1
    T=2

OPT=OptVal

class OptType(IntEnum):
    """
        用于Option的类型判定\n
            Not=0 非Opt\\
            Short=1 短\\
            Long=2 长\\
    """
    Not=0
    Short=1
    Long=2

class BaseCommand:
    """
        指令模板基类，包含一些指令模板的基本逻辑
    """
    def __init__(self,name,types:list=None,coreName=None):
        core=CommandCore.getCore(coreName)
        self.core=core
        if types is None:
            types=self.core.commandPrefix #使用中枢的默认前缀
        if self.core.isMatchPrefix(name):
            self.name=name[1:]
            self.typelist=[name[0]]
        else:
            self.name=name
            self.typelist=[]
            self.types(*types) #用 types 方法能更新中枢的潜在前缀
        if not self.name:
            raise ValueError("指令名不能为空")
        self.nameset=set()
        self.nameset.add(self.name)
        self.Optset=set()
        self.longOpts={}
        self.shortOpts={}

    def __str__(self):
        return f"Command - {self.name}\nOpts - {self.Optset}"

    def addLSOpt(self,name,opt,optType):
        """
            optType   
                OptType.Short：短\\
                OptType.Long：长
        """
        if optType==OptType.Short:
            opts=self.shortOpts
        elif optType==OptType.Long:
            opts=self.longOpts
        else:
            raise ValueError(f"{self.name} 指令的 {name} 选项的选项类型有误")
        if name in opts:
            raise ValueError(f"{self.name} 指令的 {name} 选项已存在")
        opts[name]=opt

    def types(self,*types):
        """
            为指令模板添加更多 type（指令前缀）\n
            支持链式调用
        """
        if self.typelist is self.core.commandPrefix:
            self.typelist=self.core.commandPrefix.copy()
        self.typelist+=types
        self.core.potentialPrefix.update(*types)
        return self
    
    def names(self,*names):
        """
            为指令模板添加更多名称（别名）\n
            支持链式调用
        """
        for n in names:
            self.nameset.add(n)
            # self.core.addCommand(self,name=n)
            # self.events.merge(n)
        return self

    def opt(self,names,hasValue=OptVal.Not):
        """
            为指令模板添加选项\n
                names 选项名，字符串/列表/元组，形如 "-a" 或 ["-a","-A","--aAa"]\n
                hasValue 取值判定\n
                    OPT.Not=0 不需要值\\
                    OPT.Must=1 需要值\\
                    OPT.Try=2 尽可能有值\n
            支持链式调用
        """
        Option(names,hasValue,None,self)
        return self
    

class Command(BaseCommand):
    """
        指令模板类
    """

    def __init__(self,name,types=None,coreName=None):
        """
            name 指令名，诸如 .test 或 test\n
            types 指令前缀列表。可用前缀会根据name决定，或默认使用指令中枢中的前缀\n
            coreName 要添加指令的CommandCore
        """

        super().__init__(name,types,coreName)
        
        self.help() #初始化时，默认不显示帮助，需要手动添加
        #添加到core
        self.core.addCommand(self)
        self.events:CommandEvents=CommandEvents(self.name,self.core)

    def __str__(self):
        return self.getHelp()

    __repr__=__str__

    def names(self,*names):
        """
            为指令模板添加更多名称（别名）\n
            支持链式调用
        """
        for n in names:
            self.nameset.add(n)
            self.core.addCommand(self,name=n) #将别名也添加到core
            self.events.merge(n) #如果定义了别名的事件，将它们划为指令的事件
        return self

    def opt(self,names,hasValue=OptVal.Not,help=None):
        """
            为指令模板添加选项\n
                names 选项名，字符串/列表/元组，形如 "-a" 或 ["-a","-A","--aAa"]\n
                hasValue 取值判定\n
                    OPT.Not=0 不需要值\\
                    OPT.Must=1 需要值\\
                    OPT.Try=2 尽可能有值\n
                help 选项的帮助文本\n
            支持链式调用
        """
        Option(names,hasValue,help,self)
        return self

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

    def help(self,front=None,back=None):
        """
            为指令模板添加帮助文本\n
                front 选项帮助前的帮助文本，输出时每行前会有两个空格\n
                back 选项帮助后的帮助文本\n
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

    def callback(self,*funcs):
        """
            为指令模板添加更多执行回调\n
            支持链式调用
        """
        self.events.onExecute(*funcs)
        return self

    onExecute=callback

    def onError(self,*funcs):
        """
            为指令模板添加更多报错回调\n
            支持链式调用
        """
        self.events.onError(*funcs)
        return self

class Option():
    """
        选项类\n
        选项前缀见 Option.shortPrefix 和 Option.longPrefix
    """
    shortPrefix="-"
    longPrefix="--"

    @staticmethod
    def getOptType(text):
        """
            返回OptType
        """
        if text.startswith(Option.longPrefix):
            return OptType.Long
        elif text.startswith(Option.shortPrefix):
            return OptType.Short
        else:
            return OptType.Not

    def __init__(self,names,hasValue=OptVal.Not,help=None,cmd:Command=None):
        """
            详见 Command.opt\n
                cmd 要添加选项的指令模板
        """
        if not names:
            raise ValueError("选项不能为空")
        if isinstance(names,str):
            names=[names]
        for i,n in enumerate(names):
            optType=Option.getOptType(n)
            if optType==OptType.Not:
                names[i]=Option.shortPrefix + n
                optType=OptType.Short
            if cmd:
                cmd.addLSOpt(names[i],self,optType)
            if i==0:
                self.name=names[0].lstrip(Option.longPrefix if optType==OptType.Long else Option.shortPrefix)
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
        if self.hasValue==OptVal.Not:
            mid=" True "
        elif self.hasValue==OptVal.Must:
            mid=" Text "
        else:
            mid=" True/Text "
        back=""
        if self.help:
            back=self.help
        return front+mid+back

    __repr__=__str__

if __name__ == "__main__":
    c=Command("test").opt("-v",0,"测试选项").opt(["--r","-e"],1,"选项选项").help("这是测试命令")
    print( CommandCore.getLast() )
    print(c)
    print(OptVal.Must)
    print(OptVal.Must.value)
    print(OptVal.Must==1) #True