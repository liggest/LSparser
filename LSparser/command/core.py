"""
    指令管理中枢
"""

from ..util.str_similarity import editSimilarity

class CommandCore:
    """
        指令管理中枢\n
        一般会自动创建对象\n
        - CommandCore.getLast() 得到最后创建的指令中枢\n
        - CommandCore.getCore(name) 得到指定名字的指令中枢\n
        也可指定一个名字，手动创建，所有 CommandCore 对象都会存储在 CommandCore.cores 中\n
        配合 with 语句可一定程度上控制指令中枢的生效范围\n
        例如：
        ```python
            with CommandCore(name="admin"):
                pass
        ```
    """
    # corelist=[]
    cores={}
    default="default"
    last=None

    defaultPrefix=(".","。","-","!","！","/")

    @classmethod
    def getLast(cls) -> "CommandCore":
        """
            得到最后创建的指令中枢对象
        """
        if cls.cores:
            if not cls.last:
                cls.last=cls.default
        else:
            CommandCore(name=cls.default)
        return cls.cores[cls.last]

    @classmethod
    def addCore(cls,core,name):
        if name in cls.cores:
            raise ValueError(f"指令管理器 {name} 已存在")
        cls.cores[name]=core
        cls.last=name

    @classmethod
    def getCore(cls,name=None) -> "CommandCore":
        """
            得到指定名字的指令中枢对象\n
            未提供 name 时，同 CommandCore.getLast()\n
                name 指令中枢名
        """
        if name:
            return cls.cores[name] #name 不存在则报错
        else:
            return cls.getLast()

    @property
    def cmdlist(self):
        """
            排序后的指令列表
        """
        self.tryRefresh()
        return self._cmdlist

    def __init__(self,name=None):
        """
            name 中枢名称\n
        """
        self.cmds={}
        self._cmdlist=[]
        self.isRefreshed=False

        from ..event.event_manager import EventManager
        #因为event中也用到CommandCore，所以这里的import出现在奇怪的地方
        self.EM:EventManager=EventManager()

        name=name or CommandCore.default
        self.name=name
        self.oldLast=CommandCore.last

        self.commandPrefix=[*CommandCore.defaultPrefix] #作为中枢内指令的默认前缀
        self.potentialPrefix=set(self.commandPrefix)  #作为中枢内指令可能拥有的潜在前缀，一般认为其包含 commandPrefix

        CommandCore.addCore(self,name)

    def __getitem__(self,key):
        return self.cmds[key] #如果key不存在会报错，只能用来得到已经存在的指令模板

    def __str__(self):
        cmdstr='\n'.join(self.cmdlist)
        return f"指令中枢 {self.name}\n当前记录了{len(self.cmdlist)}个指令名\n{cmdstr}"

    __repr__=__str__

    def __enter__(self):
        CommandCore.last=self.name
        return self

    def __exit__(self,etype,eval,etb):
        CommandCore.last=self.oldLast
        self.tryRefresh()

    def addCommand(self,cmd,name=None):
        if name is None:
            name=cmd.name
        if self.cmds.get(name):
            raise ValueError(f"尝试注册已经存在的指令 {name}")
        self.cmds[name]=cmd
        self.isRefreshed=False #因为添加了新指令，所以可能需要调用refresh方法

    def refresh(self):
        """
            刷新指令列表，并排序\n
        """
        self._cmdlist=list(self.cmds.keys())
        self._cmdlist.sort()
        self.isRefreshed=True
    
    def tryRefresh(self):
        """
            若未刷新，则刷新
        """
        if not self.isRefreshed:
            self.refresh()

    def isMatchPrefix(self,text):
        """
            判断文本是否和前缀列表中的前缀匹配\n
                text 文本\n
            前缀列表见指令中枢对象的 commandPrefix 属性
        """
        temp=text.lstrip()
        if temp=="":
            return False
        # return temp[0] in self.commandPrefix
        return temp[0] in self.potentialPrefix # 只要命中潜在前缀，都算作是指令


    def getCmdSimilarity(self,text,top=-1,getScore=False,scoreFunc=editSimilarity):
        """
            比较给定文本和列表中指令的相似度\n
                text 文本 如："test"、".test"（指令前缀不会纳入比较）\n
                top 返回列表的长度 默认为-1 若为正，则只返回若干个结果\n
                getScore 是否返回相似度得分 默认为False 若为True，则返回结果中包含相似度\n
                scoreFunc 相似度比较函数 editSimilarity 更多详见 LSparser.util.str_similarity\n
            返回 指令名列表，按和给定文本的相似度降序排列
        """
        perfix=""
        if self.isMatchPrefix(text):
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
    print(CommandCore.last)
    CommandCore.getLast()
    print(CommandCore.last)
    CommandCore(name="extra")
    print(CommandCore.last)
    with CommandCore(name="admin"):
        print(CommandCore.last)
    print(CommandCore.last)
    print(CommandCore.cores)