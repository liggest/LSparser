"""
    辅助查看、生成指令的帮助信息
"""
from . import CommandCore,Command,Option
from ..util import indent

import os
from io import StringIO

class CommandHelper:
    """
        帮助管理器
    """
    
    lineLimit=10
    
    # HintNotFound="是没见过的帮助呢"
    NotFound=""
    
    defaultFile="general.txt"
    defaultHidden="__hidden.txt"

    def __init__(self,root="./help",core=None):
        """
            root 帮助文本文件所在的根目录\n
            core 可以为指令中枢对象，也可以为其名称，默认为 None，即最后创建的中枢\n
        """
        if isinstance(core,CommandCore):
            self.core=core
        else:
            self.core=CommandCore.getCore(core)
        self.rootPath=root

    def getHelp(self,target:list=[],page=1):
        """
            按页查看指令的帮助信息\n
                target 目标指令，可以为字符串或列表，内容为指令名或包含其下的选项名\n
                page 页数，从 1 开始，默认为 1\n
                    每页行数由 cls.lineLimit 确定
        """
        cmd,target=self.tryFindCmd(target) # 检查、更新target，并尝试寻找指令模板
        filePath=self.getHelpFilePath(target) 
        if filePath: # 如果找到了文件，直接使用文件内容
            content=self.NotFound
            with open(filePath,"r",encoding="utf-8") as f:
                content=self.getPageContent(f,page)
            return content
        helpText=self.getHelpInCmd(cmd,target) # 否则去指令对象中找
        if helpText:
            return self.getPageContent(StringIO(helpText),page)
        return self.NotFound

    def tryFindCmd(self,target:list):
        """
            检查 target 并尝试得到指令模板
        """
        if isinstance(target,str): # str -> list
            target=target.split()
        cmd:Command=None
        if target:
            if self.core.isMatchPrefix(target[0]): #除去指令前缀
                target[0]=target[0][1:]
            cmd=self.core.cmds.get(target[0])
            if cmd:
                target[0]=cmd.name #真正的指令名
        return cmd,target

    def getPageContent(self,lines,page=1):
        """
            得到指定页的内容
        """
        page=max(page,1)
        currentPage=1
        lineNum=0
        pageContent=None
        current=[]
        last=[]
        for line in lines:
            current.append(line)
            lineNum+=1
            if lineNum==self.lineLimit: #该翻页了
                if currentPage==page:
                    pageContent=current
                currentPage+=1
                last=current
                current=[]
                lineNum=0
        totalPage=currentPage #总页数
        if totalPage>1 and len(current)<=self.lineLimit//2: #最后一页行数太少
            for line in current: #最后一页合并到倒数第二页
                last.append(line)
            totalPage-=1
            current=last
        if not pageContent:
            pageContent=current
        if pageContent and not pageContent[-1].endswith("\n"): #加入换行，让页码能显示在正确的位置
            pageContent[-1]+="\n"
        page=min(totalPage,page)
        if totalPage>1:
            pageContent.append(f"==={page}/{totalPage}===") #添加页码
        return "".join(pageContent)

    def getHelpFilePath(self,target:list):
        """
            尝试得到指令帮助文本文件的路径
        """
        path=os.path.join(self.rootPath,*target)
        filePath=path+".txt" # 先找 name.txt
        if not os.path.exists(filePath):
            filePath=os.path.join(path,self.defaultFile) # 再找 name/general.txt
            if not os.path.exists(filePath):
                return None
        return filePath

    def getHelpInCmd(self,cmd:Command,target):
        """
            尝试从指令模板中得到帮助信息
        """
        if not (cmd and cmd.showHelp and target):
            return None
        if len(target)==1:
            return cmd.getHelp()
        else: #得到给定选项的帮助
            opts=[]
            for n in target[1:]:
                opt=cmd.shortOpts.get(n) or cmd.longOpts.get(n)
                if opt:
                    opts.append(opt)
            if opts:
                result=cmd.headHelp
                optHelp=indent(Option.sortOpts(*opts),fn=str)
                result+=f"\n{optHelp}"
                return result
        return None

    def generateHelp(self,target:list=[]):
        """
            生成指令的帮助文本文件\n
                target 目标指令，可以为字符串或列表，内容为指令名或包含其下的选项名\n
        """
        cmd,target=self.tryFindCmd(target) # 检查、更新target，并尝试寻找指令模板
        helpText=self.getHelpInCmd(cmd,target) # 去指令对象中找帮助文本
        if helpText:
            filePath=self.getHelpFilePath(target) #优先覆盖已存在的
            if not filePath:
                filePath=os.path.join(self.rootPath,*target,self.defaultFile) #默认是 name/general.txt
            dir=os.path.dirname(filePath)
            self.ensureDir(dir)
            with open(filePath,"w",encoding="utf-8") as f:
                f.write(helpText)
            print("生成了帮助文本：",filePath)

    def generateMainHelp(self,startText="",endText=""): # 生成根目录的帮助文本，简单列出所有的指令
        """
            生成根目录的帮助文本文件，即简单的指令列表\n
                startText 在指令列表前附加额外内容\n
                endText 在指令列表后附加额外内容\n
        """
        self.ensureDir(self.rootPath)
        helps={}
        hiddens=self.getHidden(self.rootPath)
        for n in os.listdir(self.rootPath):
            name,_=os.path.splitext(n)
            if name in helps or (hiddens and name in hiddens) or n==self.defaultFile or n==self.defaultHidden:
                # hiddens 中的名称全部忽略
                # defaultFile 和 defaultHidden 也忽略
                continue
            filePath=os.path.join(self.rootPath,n) #非目录直接拿文件
            if os.path.isdir(filePath):
                filePath=os.path.join(filePath,self.defaultFile) #拿目录里的 general.txt
            if os.path.exists(filePath):
                helps[name]="  ".join(self.getFileShort(filePath))
        for cn in self.core.cmdlist:
            cmd:Command=self.core.cmds[cn]
            if cmd.name in helps or (hiddens and cmd.name in hiddens):
                # hiddens 中的名称全部忽略
                continue
            if cmd.showHelp: # 只添加显示帮助信息的指令
                helps[cmd.name]=self.getCmdShort(cmd)
        content=""
        for n,v in helps.items():
            if not self.core.isMatchPrefix(v): # 对于一些不以指令名开头的，加上指令名
                cmd=self.core.cmds.get(n)
                if cmd:
                    v=f"{cmd.typelist[0]}{n}  {v}"
                else:
                    # v=f"{self.core.commandPrefix[0]}{n}  {v}" # 对于尚未定义的指令，可能指令前缀会出错
                    v=f"{n}  {v}" # 先不添加指令前缀
            content+=f"{v}\n"
        if startText:
            content=f"{startText}\n{content}"
        if endText:
            content=f"{content}{endText}"
        mainPath=os.path.join(self.rootPath,self.defaultFile)
        with open(mainPath,"w",encoding="utf-8") as f:
            f.write(content)
        print("生成了主要帮助文本：",mainPath)
                

    def getFileShort(self,path,lineLimit=2):
        """
            得到帮助文本文件的前几行，作为指令简介
        """
        lines=[]
        count=0
        with open(path,"r",encoding="utf-8") as f:
            for line in f:
                lines.append(line.strip())
                count+=1
                if count==lineLimit:
                    break
        return lines

    def getCmdShort(self,cmd:Command):
        """
            从指令模板得到指令简介
        """
        if cmd.shortHelp:
            return f"{cmd.headHelp}  {cmd.shortHelp}"
        else:
            return cmd.headHelp

    def getHidden(self,dirPath):
        """
            得到目录中标记隐藏指令的文件
        """
        hiddenPath=os.path.join(dirPath,self.defaultHidden)
        if not os.path.exists(hiddenPath):
            return None
        hiddens=set()
        with open(hiddenPath,"r",encoding="utf-8") as f:
            for line in f:
                hiddens.add(line.strip())
        return hiddens
    
    def ensureDir(self,dir):
        """
            保证目录存在
        """
        if not os.path.exists(dir):
            os.makedirs(dir,exist_ok=True)

        


                

            


            

        


