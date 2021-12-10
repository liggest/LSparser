import os
import sys
import pytest

sys.path.insert(0,os.getcwd())

from LSparser.command import CommandCore,OPT,Option,CommandHelper,OptType,ParserCore
from LSparser import Events,Command,CommandParser,ParseResult

def teardown_function():
    #每个测试函数后执行
    CommandCore.cores.pop("main")
    CommandCore.last=None

def test_basic():
    with CommandCore("main") as core:
        c=Command("test")
        assert c.name=="test"
        assert c.core.name==core.name
        assert c.typelist==core.commandPrefix
        assert c.name in c.core.cmds
        c.names("tes","est")
        assert "tes" in c.nameset
        assert "est" in c.nameset
        with pytest.raises(ValueError):
            c.names("test")
        with pytest.raises(ValueError):
            Command("test")
        with pytest.raises(ValueError):
            Command("")
        c=Command("cmd").opt("-s1",OPT.Try).opt("-s2",OPT.Must).opt("--l",OPT.Must)
        assert "-s1" in c.shortOpts
        assert "-s2" in c.shortOpts
        assert "--l" in c.longOpts
        assert OPT.M==OPT.Must
        assert c.shortOpts["-s1"].hasValue==OPT.T
        assert c.longOpts["--l"] in c.Optset
        c=Command("!solo")
        assert len(c.typelist)==1 and "!" in c.typelist
        assert not core.isMatchPrefix("$multi")
        c=Command("multi",types=["。","$"])
        assert len(c.typelist)==2 and "。" in c.typelist and "$" in c.typelist
        assert core.isMatchPrefix("$multi")

def test_opt():
    with CommandCore("main"):
        with pytest.raises(ValueError):
            Option([])
        with pytest.raises(ValueError):
            Option("")
        assert Option.getOptType("--s") == OptType.Long
        assert Option.getOptType("-!d") == OptType.Short
        assert Option.getOptType("not") == OptType.Not
        assert Option(["-s","--c","-!d"]).name=="s"
        assert Option(["--c","-!d","-s"]).name=="c"
        assert Option("-e",OPT.M).hasValue==OPT.Must
        assert "-ads" in Option("ads").names

def test_event():
    with CommandCore("main") as core:
        cp=CommandParser()

        def p(result:ParseResult):
            print(result)
            return "success"
        Command("test").onExecute(p)
        pr=cp.tryParse(".test")
        assert pr.isChecked()
        assert pr.isCommand()
        assert pr.isDefinedCommand()
        assert not pr.isWrongType()
        assert not pr.hasOpt()
        assert pr.command=="test"
        assert not pr.params
        assert pr.paramStr==""
        assert pr.output[0] == "success"

        Command("deco")
        @Events.onCmd("deco")
        def _(result):
            return "deco"
        assert cp.tryParse(".deco").output[0] == "deco"

        @Events.onCmd("duck")
        def _(result):
            return result.command

        @Events.onCmd("duk")
        def _(result):
            return result.command

        c=Command("duck").names("dack","duk","daaa")
        assert len(core.EM.events[c.events.eventName])==2
        assert not core.EM.events.get("cmd-duk")
        out=cp.tryParse(".duk").output
        assert out[0]=="duk" and out[1]=="duk"

        @Events.onCmd("lag")
        def _(result):
            return result.command
        c=Command("lag").names("laag","lagg","log")
        assert len(core.EM.events[c.events.eventName])==1
        @Events.onCmd("laag")
        def _(result):
            return result.command
        assert len(core.EM.events[c.events.eventName])==2
        assert not core.EM.events.get("cmd-laag")
        @Events.onCmd("lag")
        def _(result):
            return result.command
        assert len(core.EM.events[c.events.eventName])==3
        assert cp.tryParse(".log").realCommand == "lag"
        
        @Events.onCmd("error")
        def _(result):
            return [][5]
        
        @Events.onCmd.error("error")
        def _(result,err:Exception):
            assert str(err)=="list index out of range"
            return err

        c=Command("error")
        pr=cp.tryParse("!error")
        assert len(pr.output)==1
        assert isinstance(pr.output[0],IndexError)

        @Events.onCmd("no-error")
        def _(result):
            return [][5]
        
        c=Command("no-error")
        with pytest.raises(IndexError):
            pr=cp.tryParse("!no-error")

        @Events.onCmd.error("before")
        def beforeError(result):
            return result.command
        @Events.onCmd("before")
        def _(result):
            return result.command
        @Events.onCmd.error("bf")
        def bfError(result):
            return result.command
        c=Command("before").names("bf")
        assert core.EM.hasSub(c.events.eventName,"error")
        assert len(core.EM.events[c.events.eventName])==1
        assert len(core.EM.events[c.events.eventName].subs["error"])==2
        @Events.onCmd.error("bf")
        def _(result):
            return result.command
        assert len(core.EM.events[c.events.eventName].subs["error"])==3

        @Events.onCmd("bf")
        def _(result):
            return result.command
        assert len(core.EM.events[c.events.eventName])==2

        @Events.onCmd.error("af")
        def _(result):
            return result.command
        @Events.onCmd("af")
        def _(result):
            return result.command
        c=Command("after").names("af")
        assert core.EM.hasSub(c.events.eventName,"error")
        assert len(core.EM.events[c.events.eventName])==1
        assert len(core.EM.events[c.events.eventName].subs["error"])==1

        outputLen=0
        @Events.onCmd("ultra-error")
        @Events.onCmd("ultra-error")
        @Events.onCmd("ultra-error")
        def onUltra(result):
            nonlocal outputLen
            # print(result.output)
            assert len(result.output)==outputLen
            outputLen+=1
            return result.command
        
        @Events.onCmd("ultra-error")
        def _(result):
            return [][5]
        
        Events.onCmd("ultra-error")(onUltra)
        Events.onCmd("ultra-error")(onUltra)
        Events.onCmd("ultra-error")(onUltra)

        @Events.onCmd.error("ultra-error")
        @Events.onCmd.error("ultra-error")
        @Events.onCmd.error("ultra-error")
        def _(result,err):
            nonlocal outputLen
            # print(result.output)
            assert len(result.output)==outputLen
            outputLen+=1
            return err

        c=Command("ultra-error")
        assert len(core.EM.events[c.events.eventName])==7
        assert len(core.EM.events[c.events.eventName].subs["error"])==3
        pr=cp.tryParse("!ultra-error")
        assert len(pr.output)==outputLen==6
        assert pr.output[0]==pr.command
        assert isinstance(pr.output[-1],IndexError)


def test_parse():
    with CommandCore("main"):
        cp=CommandParser()
        Command("cmd")
        assert cp.tryParse(".cmd M W WmW").params == ["M","W","WmW"]
        assert cp.tryParse("""
            .cmd M W
            WmW
            MwM wMw mWm
        """).params == ["M","W","\n","WmW","\n","MwM","wMw","mWm"]
        assert cp.tryParse("""
            .cmd M W
            WmW
            MwM wMw mWm
        """).paramStr=="M W\nWmW\nMwM wMw mWm"
        assert cp.tryParse(".cmd -r -s W --t").paramStr == "-r -s W --t"
        Command("shortN").opt("-s",OPT.Not)
        assert not cp.tryParse(".shortN").args
        assert not cp.tryParse(".shortN --s").args
        assert not cp.tryParse(".shortN -t").args
        assert cp.tryParse(".shortN -s").args["s"]
        assert cp.tryParse(".shortN -s abc").args["s"] is True
        Command("shortM").opt("-s",OPT.Must).opt("-t")
        assert cp.tryParse(".shortM -s").args["s"] #只有选项，没提供值，故为True
        assert cp.tryParse(".shortM -s abc").args["s"] == "abc"
        assert cp.tryParse(".shortM -s abc -s cde fg -s h").args["s"] == "h" #后面的覆盖前面的
        pr=cp.tryParse(".shortM -s -t")
        assert pr.args["s"] == "-t" and not pr.args.get("t") #-s必须有值
        assert pr.getByType("s") == "-t"
        assert cp.tryParse(".shortM -t -s").args["t"]
        Command("shortT").opt("-s",OPT.Try).opt("-t")
        assert cp.tryParse(".shortT -s").args["s"] #只有选项，没提供值，故为True
        pr=cp.tryParse(".shortT -s -t")
        assert pr.args["s"] is True and pr.args["t"] is True #因为有-t 故 -s 放弃值，只为True
        assert pr.getByType("s",T=bool) is True
        assert pr.getByType("t","Not str!") == "Not str!"
        assert pr.getByType("NO","NO!!!") == "NO!!!"
        assert pr.splitHead("sho") == "rtT"
        assert pr.splitHead("ssh") == ""
        Command("longN").opt("--s",OPT.Not)
        assert not cp.tryParse(".longN -s").args
        assert cp.tryParse(".longN --s").args["s"] is True
        Command("longM").opt("--s",OPT.Must).opt("-t",OPT.Must)
        assert cp.tryParse(".longM --s").args["s"] == [] #没提供值的时候是空列表
        assert cp.tryParse(".longM --s a b c").args["s"] == ["a","b","c"]
        assert cp.tryParse(".longM --s a b -t c").args["s"] == ["a","b"]
        assert cp.tryParse(".longM --s -t c").args["s"] == [] #被 -t 挡住的时候会是空列表
        assert not cp.tryParse(".longM -t --s c").args.get("s")
        Command("longT").opt("--s",OPT.Try).opt("-t")
        assert cp.tryParse(".longT --s").args["s"] is True #没提供值的时候是True
        assert cp.tryParse(".longT --s a b c").args["s"] == ["a","b","c"]
        assert cp.tryParse(".longT --s -t c").args["s"] is True #被 -t 挡住的时候会是True

def test_parse_events():
    with CommandCore("main") as core:
        cp=CommandParser()

        beforeTimes=0
        afterTimes=0
        @Events.onBeforeParse
        def before(pr:ParseResult,cp:CommandParser):
            nonlocal beforeTimes
            pr.data["brain"]="void"
            assert pr.parser==cp
            assert pr.isChecked()
            beforeTimes+=1

        @Events.onAfterParse
        def after(pr:ParseResult,cp:CommandParser):
            nonlocal afterTimes
            assert pr.data["brain"]=="void"
            assert pr.parser==cp
            afterTimes+=1

        @Events.onNotCmd()
        def notCmd(pr:ParseResult,cp:CommandParser):
            assert not pr.raw or pr.raw=="hh" or (not pr.command and pr.type=="。")

        @Events.onUndefinedCmd("main")
        def undefined(pr:ParseResult,cp:CommandParser):
            assert pr.command=="nono"
            pr.opt("-s").opt("--l",OPT.M).opt("-c",OPT.T).parse()
            assert pr["s"] is True
            assert pr["l"]==["yes","yes"]
            assert pr["c"]=="wow"
            assert pr.paramStr=="!"

        @Events.onWrongCmdType
        def wrong(pr:ParseResult,cp:CommandParser):
            assert pr.isDefinedCommand()
            assert pr.command=="uno"
            assert pr.type=="!"
            assert not "s" in pr
            pr.type="$"
            pr.parse()
            assert pr["s"]=="uno!"

        @Events.onCmd("uno")
        def noExecute(_):
            raise RuntimeError("此回调不该被执行")

        Command("cmd").opt("-s").opt("-c",OPT.M)
        Command("uno",types=["$","#"]).opt("-s",OPT.M)

        cp.tryParse("hh")
        cp.tryParse("")
        cp.tryParse("。")

        cp.tryParse(".cmd -s -c md")
        cp.tryParse(".nono -s --l yes yes -c wow !")
        cp.tryParse("!uno -s uno!")
        assert beforeTimes==6
        assert afterTimes==6

        @Events.onExecuteError
        def onError(pr:ParseResult, cp:CommandParser, err:Exception) -> bool:
            assert isinstance(err,IndexError)
        
        @Events.onCmd("raise")
        @Events.onCmd("error")
        def error(pr:ParseResult):
            [][863]
        
        Command("error")
        with pytest.raises(IndexError):
            cp.tryParse(".error")
        
        @Events.onCmd.error("error")
        def errorError(pr:ParseResult,err:Exception):
            assert isinstance(err,IndexError)
        
        assert cp.tryParse(".error").output==[None]

        Command("raise")
        with pytest.raises(IndexError):
            cp.tryParse(".raise")

        @Events.onExecuteError
        def handleError(pr:ParseResult, cp:CommandParser, err:Exception) -> bool:
            assert isinstance(err,IndexError)
            return True
        
        assert cp.tryParse(".raise").output==[]
              
class StringContaier:
    extra="more than a string!"

    def __init__(self,s):
        self.s=s

    def __str__(self) -> str:
        return self.s

def test_data():

    with CommandCore("main"):
        cp=CommandParser()
        cp.data["one"]="shot"
        Command("cmd")

        @Events.onBeforeParse
        def before(pr:ParseResult, cp:CommandParser):
            assert pr.parserData["one"]=="shot"
            assert not "two" in pr.data
        
        @Events.onCmd("cmd")
        def cmd(pr:ParseResult):
            assert pr.raw.extra=="more than a string!"
            pr.data["two"]="kick"
        
        @Events.onAfterParse
        def after(pr:ParseResult, cp:CommandParser):
            assert pr.parserData["one"]=="shot"
            assert pr.data["two"]=="kick"

        cp.tryParse( StringContaier(".cmd dmc") )

        Command("extra")
        @Events.onBeforeParse
        def _(pr:ParseResult, cp:CommandParser):
            ex1,ex2=pr.dataArgs
            kw=pr.dataKW
            ex3=kw["ex3"]
            ex4=kw["ex4"]
            assert ex1==42
            assert ex2=="TTT"
            assert ex3==...
            assert ex4==(True,False)

        @Events.onCmd("extra")
        def _(pr:ParseResult):
            pr.data["two"]="kick"
            return pr.dataArgs,pr.dataKW

        out=cp.tryParse(".extra",42,"TTT",ex3=...,ex4=(True,False)).output[0]
        assert out[0]==(42,"TTT")
        assert out[1]=={"ex3":...,"ex4":(True,False)}

def test_help():
    with CommandCore("main"):
        c=Command("cmd").names("CMD","Command")\
            .opt(["-s","--straight"],OPT.Must,"val  Straight!")\
            .opt(["-t","--tight"],OPT.Try,"[val]  Tight!")\
            .opt(["--l","--long"],OPT.Not," Long!")\
            .help("这是cmd",
            """
                cmd具有强大的功能
                其中之一便是显示帮助
                非常多的帮助
            """,
            ".cmd C M D",
            ".cmd -s smile",
            ".cmd -t T?",
            ".cmd --l"
            )
        assert c.frontHelp=="这是cmd\ncmd具有强大的功能\n其中之一便是显示帮助\n非常多的帮助"
        assert c.backHelp==".cmd C M D\n.cmd -s smile\n.cmd -t T?\n.cmd --l"
        helper=CommandHelper()
        # helper=CommandHelper("./help/default")
        assert helper.getHelp([".cmd"]).strip() == c.getHelp()
        # print(c.getHelp())
        # helper.lineLimit=2
        # print(helper.getHelp([".cmd"],1))
        # print(helper.getHelp([".cmd"],2))
        # print(helper.getHelp([".cmd"],10))
        # print(helper.getHelp([".cmd"],-5))
        # helper.generateHelp([".cmd"])
        # helper.generateMainHelp(startText="指令详情\n",endText="\n========")
        # print(helper.getHelp([".cmd","--l","-t","-s"]))


def test_execute():
    with CommandCore("main"):
        cp=CommandParser()
        Command("cmd").opt("-s",OPT.M).opt("-t",OPT.T).opt("-f",OPT.N).opt(["-c","--c"],OPT.M)

        @Events.onCmd("cmd")
        def cmdExecute(pr:ParseResult):
            assert pr["s"]
            assert pr["t"]
            if pr.data.get("exe"):
                return "from execute"
            return "from parse"
        pr=cp.tryParse(".cmd -s mile -t ea QwQ QwQ")
        assert pr["t"]=="ea"
        assert pr.paramStr=="QwQ QwQ"
        assert pr.output==["from parse"]
        assert not pr["f"]
        assert isinstance(pr.raw,str)

        pr=ParseResult.fromCmd(cp,"!cmd",params=["QAQ","QAQ"],args={"s":"our","t":True,"f":True},
            type=None,raw=StringContaier("exe cmd"))
        pr.data["exe"]=True
        pr=pr.execute()
        assert pr["t"]==True
        assert pr.paramStr=="QAQ QAQ"
        assert pr.output==["from execute"]
        assert pr["f"]
        assert isinstance(pr.raw,StringContaier)
        assert pr._cons==["exe","cmd"]
        assert pr.type=="!"

        pr=ParseResult.fromCmd(cp,"cmd",params=["Cost","tosC"],
            args={"s":"our","t":("A","Z"),"c":[386,"<>",True]},type="!")
        pr.data["exe"]=True
        pr=pr.execute()
        assert pr["t"]==("A","Z") # 通过字符串解析的话 t 是没法取到这个值的
        assert pr.paramStr=="Cost tosC"
        assert pr.raw=="!cmd Cost tosC -s our -t A Z --c 386 <> True"
        assert pr.type=="!"


def test_iter():
    with CommandCore("main"):
        cp=CommandParser()
        Command("cmd").opt("-s1",OPT.N).opt("-s2",OPT.M).opt("--l",OPT.M)
        
        cmdList=[".cmd","p1","p2 p3","-s1","-s2","sval","--l","lval1","lval2"]
        pr=cp.tryParse(cmdList)
        assert pr.params==["p1","p2 p3"]
        assert pr["s1"]
        assert pr["s2"]=="sval"
        assert pr["l"]==["lval1","lval2"]

class CustomParserCore(ParserCore):

    @staticmethod
    def tokenizeStr(t: str):
        current=""
        for c in t:
            if c==" " or c=="\n":
                continue
            current+=c
            if len(current)==2:
                yield current
                current=""
        if current:
            yield current

def test_custom():
    with CommandCore("main"):
        cp=CommandParser()
        cp._parserCore=CustomParserCore
        Command("c").names("c-").opt("-s",OPT.N).opt("-t",OPT.Try)
        pr=cp.tryParse(".c-s-tahefg")
        assert pr.type=="."
        assert pr.command=="c"
        assert pr["s"]
        assert pr["t"]=="ah"
        assert pr.params==["ef","g"]