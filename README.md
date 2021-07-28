# LSparser
[![pypi_badge](https://img.shields.io/pypi/v/LSparser?color=blue)](https://pypi.org/project/LSparser/)

一个基于Python的指令解析器（大概）

解析一定格式的指令，形如：
```
    .cmd param1 param2 -s1 -s2 s2val --l lval1 lval2 lval3
```
得到
```
    type: "."
    command: "cmd"
    params: ["param1", "param2"]
    s1: True
    s2: "s2val"
    l: ["lval1", "lval2", "lval3"]
```
### 安装
```
    pip install LSparser
```

### 指令格式
- type/指令前缀：一个字符，用于分辩文本是否为指令

  默认为`[".", "。", "-", "!", "！", "/"]`
- command/指令名：指令名称
- params/参数：提供给指令的参数
- short options/短选项：默认以`"-"`为前缀的选项，可以有至多一个选项值
- long options/长选项：默认以`"--"`为前缀的选项，可以有多个选项值

一些规则：
- 指令名、参数、选项、选项值之间通过`" "`分隔
- 可以事先设定哪些选项可被解析，以及这些选项后是否有选项值
- 没有附带选项值但出现在指令中的选项，其选项值当做`True`处理

### 使用方法
引入库
```Python
    from LSparser import *
```
创建指令模板，提供帮助文本，并设定要被解析的选项
```Python
    c=Command("cmd")
    c.help("这是名为cmd的指令")
    c.opt("-s1",OPT.Try,"短选项s1").opt("-s2",OPT.Must,"s2").opt("--l",OPT.Must,"还有长选项l")
```
可以为指令添加别名、指令前缀
```Python
    c.names("cmd1")
    c.types("$","￥")
```
添加回调函数
```Python
    @Events.onCmd("cmd")
    def cmdfunc(pr:ParseResult):
        # result 为 ParseResult 对象
        print("一个回调函数")
        print(pr) #解析结果储存在对象中
        return "返回值"
```
解析指令
```Python
    cmd=".cmd param1 param2 -s1 -s2 s2val --l lval1 lval2 lval3"
    cp=CommandParser()
    pr:ParseResult=cp.tryParse(cmd)
    print("args:",pr.args) #选项
    print("output: ",pr.output) #回调函数执行结果
    # => ["返回值","随便返回些什么"]
```

进阶地，指令解析后各种情况
- 未解析到指令：
```Python
    #根本不是指令
    @Events.onNotCmd
    def notCmd(pr:ParseResult,cp:CommandParser):
        pass
```
- 解析到未定义指令：
```Python
    @Events.onUndefinedCmd
    def cmdUndefined(pr:ParseResult,cp:CommandParser):
        if pr.command=="test": #判断指令名
            cp.opt("-ts1",OPT.Must).opt("-opt",OPT.Not).opt(["-j","--j"],OPT.Try)
            pr=cp.parse(pr)
            #根据指令名设定选项，再次解析
            #可以在这里处理指令
```
- 解析到指令，但指令前缀和定义不匹配：
```Python
    @Events.onWrongCmdType
    def wrongType(pr:ParseResult,cp:CommandParser):
        #可以在这里处理错误
        pass
```
额外地，可以比较文本和各指令间的相似度
```Python
    similist=cp.core.getCmdSimilarity("zmd",top=5)
```