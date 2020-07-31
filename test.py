from LSparser import * #引入库

#创建指令模板，提供帮助文本，并设定要被解析的选项
c=Command("cmd")
c.help("这是名为cmd的指令").opt("-s1",2,"短选项s1").opt("-s2",1,"s2").opt("--l",1,"还有长选项l")

#可以为指令添加别名、指令前缀
c.names("cmd1").types("$","￥")

#添加回调函数
def cmdfunc(cp):
    #cp为CommandParser对象
    print("一个回调函数")
    print(cp.command) #解析结果以字典的形式存储
    return "随便返回些什么"

c.callback(cmdfunc)

#另一种添加回调函数的方法
@cmdCallback("cmd")
def cmdfunc1(cp):
    print("另一个回调函数")
    return "随便返回些什么"

#解析指令
#cmd=".cmd param1 param2 -s1 -s2 s2val --l lval1 lval2 lval3"
cmd="$cmd param1 param2 -s1 -s2 s2val --l lval1 lval2 lval3"
cp=CommandParser()
#result=cp.tryParse(cmd)
result=cp.tryParse(cmd,commandPrefix+["$","￥"]) #result为各回调函数执行结果的列表

#进阶地，指令解析后的复杂情况
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

#额外功能，比较文本和各指令的相似度
similist=cp.core.getCmdSimilarity("zmd",top=5)
print(similist)