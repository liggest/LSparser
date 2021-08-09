import os
import sys
import pytest
import asyncio

sys.path.insert(0,os.getcwd())

# from LSparser.command import CommandCore,OPT,Option,CommandHelper,OptType
from LSparser import Events,Command,CommandCore,CommandParser,OPT,ParseResult

def teardown_function():
    #每个测试函数后执行
    CommandCore.cores.pop("main")
    CommandCore.last=None

async def parse_main():
    with CommandCore("main") as core:
        cp=CommandParser()

        c=Command("single")
        c.opt("-s1",OPT.Try).opt("-s2",OPT.Must).opt("--s3",OPT.Must)

        @Events.onCmd("single")
        async def _(pr:ParseResult):
            assert not pr.dataArgs
            assert pr.dataKW["X"]==5 and pr.dataKW["Y"]==3

        await cp.asyncTryParse(".single only one -s1 + -s2 + --s3 - - + ",X=5,Y=3)

        inOrder=[]
        outOrder=[]
        @Events.onCmd("task1")
        @Events.onCmd("task2")
        @Events.onCmd("task3")
        async def _(pr:ParseResult):
            inOrder.append(pr.command)
            await asyncio.sleep(int(pr.command[-1])/100)
            outOrder.append(pr.command)
        Command("task1")
        Command("task2")
        Command("task3")

        await asyncio.gather( 
            cp.asyncTryParse(".task2"),
            cp.asyncTryParse(".task1"),
            cp.asyncTryParse(".task3")
        )
        assert inOrder==["task2","task1","task3"]
        assert outOrder==["task1","task2","task3"]

        sleepTick=0
        @Events.onCmd("taskM")
        @Events.onCmd("taskM")
        @Events.onCmd("taskM")
        @Events.onCmd("taskM")
        @Events.onCmd("taskM")
        @Events.onCmd("taskM")
        async def _(pr:ParseResult):
            nonlocal sleepTick
            local=sleepTick
            sleepTick+=1
            await asyncio.sleep(sleepTick/20)
            assert len(pr.output)==local
            return len(pr.output)

        Command("taskM")
        pr=await cp.asyncTryParse(".taskM")
        assert len(pr.output)==sleepTick==6
        assert pr.output==[0,1,2,3,4,5]
        
        actual=[]
        Command("mix")
        @Events.onCmd("mix")
        async def ac(pr:ParseResult):
            actual.append("a")
            return "a"
        @Events.onCmd("mix")
        def sc(pr:ParseResult):
            actual.append("s")
            return "s"

        Events.onCmd("mix")(ac)
        Events.onCmd("mix")(ac)
        Events.onCmd("mix")(sc)

        pr=await cp.asyncTryParse(".mix")
        assert actual==["a","a","a","s","s"]
        assert pr.output==["a","s","a","a","s"]

        Command("error")
        
        @Events.onCmd("error")
        async def _(pr:ParseResult):
            pr.notAttribute

        @Events.onCmd.error("error")
        async def aErr(pr:ParseResult, err:Exception):
            assert isinstance(err,AttributeError)
            assert not pr.output
            return "solved"

        @Events.onCmd.error("error")
        def sErr(pr:ParseResult, err:Exception):
            assert isinstance(err,AttributeError)
            assert len(pr.output)==1
            return "solved"

        Events.onCmd.error("error")(aErr) #异步先执行，结果开始传入outpu时已执行结束，故output长都是0

        @Events.onExecuteError
        async def _(pr:ParseResult, cp:CommandParser, err:Exception):
            assert not pr.output
            while not pr.output:
                await asyncio.sleep(0)
            assert pr.output

        await cp.asyncTryParse("!error")

def test_parse():
    asyncio.run(parse_main())

def test_sync():
    with CommandCore("main") as core:
        cp=CommandParser()
        
        actual=[]
        Command("mix")
        @Events.onCmd("mix")
        async def ac(pr:ParseResult):
            actual.append("a")
            return "a"
        @Events.onCmd("mix")
        def sc(pr:ParseResult):
            actual.append("s")
            return "s"

        Events.onCmd("mix")(ac)
        Events.onCmd("mix")(ac)
        Events.onCmd("mix")(sc)
        pr=cp.tryParse(".mix")
        assert actual==["a","a","a","s","s"]
        assert pr.output==["a","s","a","a","s"]