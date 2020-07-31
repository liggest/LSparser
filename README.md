# LSparser
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

  默认地，`commandPrefix=[".","。","-","!","！","/"]`
- command/指令名：指令名称
- params/参数：提供给指令的参数
- short option/短选项：默认以`"-"`为前缀的选项，可以有至多一个选项值
- long option/长选项：默认以`"--"`为前缀的选项，可以有多个选项值

一些规则：
- 指令名、参数、选项、选项值之间通过`" "`分隔
- 需要事先设定哪些选项可被解析，以及这些选项后是否有选项值
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
    c.opt("-s1",2,"短选项s1").opt("-s2",1,"s2").opt("--l",1,"还有长选项l")
```
可以为指令添加别名、指令前缀
```Python
    c.names("cmd1")
    c.types("$","￥")
```
添加回调函数
```Python
    def cmdfunc(cp):
        #cp为CommandParser对象
        print(cp.command) #解析结果以字典的形式存储
        return "随便返回些什么"
    c.callback(cmdfunc)
```
另一种添加回调函数的方法
```Python
    @cmdCallback("cmd")
    def cmdfunc1(cp):
        #另一个回调函数
        return "随便返回些什么"
```
解析指令
```Python
    cmd=".cmd param1 param2 -s1 -s2 s2val --l lval1 lval2 lval3"
    cp=CommandParser()
    result=cp.tryParse(cmd) #result为各回调函数执行结果的列表
```

进阶地，指令解析后的复杂情况
```Python
    if result:
        #解析成功，执行了回调函数，返回了函数结果
        pass
    elif cp.isCommand():
        #至少是指令
        if cp.isDefinedCommand():
            #用指令模板定义过
            if cp.isWrongType():
                #但是指令前缀和定义时不匹配
                #可以在这里处理错误
                pass
            else:
                #仅仅是没有回调函数可以执行
                #可以在这里处理指令
                pass
        else:
            #是未用指令模板定义的指令
            if cp['command']=="test": #判断指令名
                cp.opt("-ts1",1).opt("-opt",0).opt(["-j","--j"],2).parse()
                #根据指令名设定选项，再次解析
                #可以在这里处理指令
    else:
        #根本不是指令
        pass
```
额外功能，比较文本和各指令的相似度
```Python
    similist=cp.core.getCmdSimilarity("zmd",top=5)
```