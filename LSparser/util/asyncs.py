
import asyncio
import typing

def asSync(coro:typing.Coroutine):
    """
        同步执行协程
    """
    newLoop=False
    try:
        loop=asyncio.get_event_loop()
    except RuntimeError:
        loop=asyncio.new_event_loop()
        newLoop=True
    result=loop.run_until_complete(coro)
    if newLoop:
        loop.close()
    return result

def gatherAsSync(*coros):
    newLoop=False
    try:
        loop=asyncio.get_event_loop()
    except RuntimeError:
        loop=asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        newLoop=True
    result=loop.run_until_complete( asyncio.gather( *coros ) )
    if newLoop:
        asyncio.set_event_loop(None)
        loop.close()
    return result

def callAllGen(callList,*args,**kw):
    """
        生成器，执行列表中所有回调，逐一返回结果
    """
    _,_,asyncs,asyncIdx=splitCorosWithIdx(callList)
    aLen=0
    aIdx=0
    if asyncs:
        aResults=gatherAsSync( *[coro(*args,**kw) for coro in asyncs] )
        aLen=len(aResults)
    for i,func in enumerate(callList):
        if aIdx<aLen and i==asyncIdx[aIdx]:
            yield aResults[aIdx]
            aIdx+=1
        else:
            yield func(*args,**kw)

async def asyncCallAllGen(callList,*args,**kw):
    """
        异步生成器，执行列表中所有回调，逐一返回结果
    """
    _,_,asyncs,asyncIdx=splitCorosWithIdx(callList)
    aLen=0
    aIdx=0
    tasks=[]
    if asyncs:
        for coro in asyncs:
            tasks.append( asyncio.create_task(coro(*args,**kw)) )
        aLen=len(tasks)
    for i,func in enumerate(callList):
        if aIdx<aLen and i==asyncIdx[aIdx]:
            yield await tasks[aIdx]
            aIdx+=1
        else:
            yield func(*args,**kw)

def splitCoros(funclist):
    syncs=[]
    asyncs=[]
    for func in funclist:
        if asyncio.iscoroutinefunction(func):
            asyncs.append(func)
        else:
            syncs.append(func)
    return syncs,asyncs

def splitCorosAsIdx(funclist):
    syncs=[]
    asyncs=[]
    for idx,func in enumerate(funclist):
        if asyncio.iscoroutinefunction(func):
            asyncs.append(idx)
        else:
            syncs.append(idx)
    return syncs,asyncs
    
def splitCorosWithIdx(funclist):
    syncs=[]
    syncIdx=[]
    asyncs=[]
    asyncIdx=[]
    for idx,func in enumerate(funclist):
        if asyncio.iscoroutinefunction(func):
            asyncs.append(func)
            asyncIdx.append(idx)
        else:
            syncs.append(func)
            syncIdx.append(idx)
    return syncs,syncIdx,asyncs,asyncIdx

async def emptyAsyncGen():
    return
    yield