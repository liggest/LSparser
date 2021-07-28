from LSparser import * #引入库

#创建指令模板，提供帮助文本，并设定要被解析的选项
c=Command("cmd")
c.help("这是名为cmd的指令").opt("-s1",OPT.Try,"短选项s1").opt("-s2",OPT.Must,"s2").opt("--l",OPT.Must,"还有长选项l")

#还可以为指令添加别名
c.names("cmd1")

#添加回调函数
@Events.onCmd("cmd")
def cmdfunc(pr:ParseResult):
    # result 为 ParseResult 对象
    print("一个回调函数")
    print(pr) #解析结果储存在对象中
    return "返回值"

def cmdfunc2(pr:ParseResult):
    print("另一个回调函数")
    return "随便返回些什么"
#另一种添加回调函数的方法
c.onExecute(cmdfunc2)

#指令解析后的各种情况

#根本不是指令
@Events.onNotCmd
def notCmd(pr:ParseResult,cp:CommandParser):
    pass

#是未用指令模板定义的指令
@Events.onUndefinedCmd
def cmdUndefined(pr:ParseResult,cp:CommandParser):
    if pr.command=="test": #判断指令名
        pr.opt("-ts1",OPT.Must).opt("-opt",OPT.Not).opt(["-j","--j"],OPT.Try)
        pr=cp.parse(pr)
        print(pr)
        #根据指令名设定选项，再次解析
        #可以在这里处理指令

#解析到指令，但指令前缀和定义时不匹配
@Events.onWrongCmdType
def wrongType(pr:ParseResult,cp:CommandParser):
    #可以在这里处理错误
    pass

#解析指令
cmd=".cmd param1 param2 -s1 -s2 s2val --l lval1 lval2 lval3"
# cmd=".test --j"
cp=CommandParser()
pr:ParseResult=cp.tryParse(cmd)
print("args:",pr.args) #选项
# => {'s1': True, 's2': 's2val', 'l': ['lval1', 'lval2', 'lval3']}
print("output:",pr.output) #回调函数执行结果
# => ["返回值","随便返回些什么"]

#额外功能，比较文本和各指令的相似度
similist=cp.core.getCmdSimilarity("zmd",top=5)
print(similist)