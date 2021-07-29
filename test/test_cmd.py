import os
import sys
import pytest

sys.path.insert(0,os.getcwd())

from LSparser.command import CommandCore,OPT,Option
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
        def _(result,err):
            print(err)
            return err

        c=Command("error")
        pr=cp.tryParse("!error")
        assert len(pr.output)==1
        assert isinstance(pr.output[0],IndexError)

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

def test_parse():
    with CommandCore("main"):
        cp=CommandParser()
        Command("cmd")
        assert cp.tryParse(".cmd M W WmW").params == ["M","W","WmW"]
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
            assert pr.command=="uno"
            assert pr.type=="!"
            assert not "s" in pr
            pr.type="$"
            pr.parse()
            assert pr["s"]=="uno!"
        
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
