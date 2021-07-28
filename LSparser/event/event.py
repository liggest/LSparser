from ..command import CommandCore
from . import EventManager
from . import CommandEvents
# from .command_event import CommandEventsWrapper

import functools

class CommandEventsWrapper:
    """
        为指令添加回调\n
            cmdName 指令名\n
            coreName 指令中枢名，默认为 None，即是使用最后创建的中枢\n
        例：
        ```python
            @Events.onCmd("cmd")
            def cmdExecute(result):
                pass

            @Events.onCmd.error("cmd")
            def cmdError(result,err):
                pass
        ```
    """

    def __init__(self,cmdName,coreName=None):
        """
            cmdName 指令名\n
            coreName 指令中枢名，默认为 None，即是使用最后创建的中枢
        """
        core=CommandCore.getCore(coreName)
        cmd=core.cmds.get(cmdName)
        if cmd:
            self.events=cmd.events
        else:
            self.events=CommandEvents(cmdName,core)
    
    def __call__(self,func):
        """
            等同于添加执行回调\n
            回调函数：\n
                传入 ParseResult 对象\n
                可以有返回值
        """
        return self._onExecute(func)

    @classmethod
    def execute(cls,cmdName,coreName=None):
        """
            为指令添加执行回调\n
                cmdName 指令名\n
                coreName 指令中枢名，默认为 None，即是使用最后创建的中枢\n
            回调函数：\n
                传入 ParseResult 对象\n
                可以有返回值
        """
        return cls(cmdName,coreName)._onExecute

    @classmethod
    def error(cls,cmdName,coreName=None):
        """
            为指令添加报错回调\n
                cmdName 指令名\n
                coreName 指令中枢名，默认为 None，即是使用最后创建的中枢\n
            回调函数：\n
                传入 ParseResult 对象和 异常 对象\n
                可以有返回值
        """
        return cls(cmdName,coreName)._onError

    def _onExecute(self,func):
        """
            添加执行回调
        """
        self.events.onExecute(func)
        return func

    def _onError(self,func):
        """
            添加报错回调
        """
        self.events.onError(func)
        return func

def _nameOrFunc(func):
    @functools.wraps(func)
    def wrapper(cls,x=None):
        if x is None or isinstance(x,str):
            return func(cls,x)
        else:
            return func(cls,None)(x)
    return wrapper

class Events:
    """
        提供为各种事件注册回调的装饰器
    """

    @staticmethod
    def getEM(coreName=None) -> EventManager:
        """
            得到指令中枢的事件管理器\n
                coreName 指令中枢名，默认为 None，即是使用最后创建的中枢
        """
        return CommandCore.getCore(coreName).EM

    onCmd=CommandEventsWrapper

    # @staticmethod
    # def onCmd(cmdName,coreName=None) -> CommandEventsWrapper:
    #     return CommandEventsWrapper(cmdName,coreName)

    @classmethod
    def on(cls,name,coreName=None):
        """
            为指定名称的事件添加回调
                name 事件名\n
                coreName 指令中枢名，默认为 None，即是使用最后创建的中枢\n
        """
        def decorator(func):
            cls.getEM(coreName).add(name,func)
            return func
        return decorator

    @classmethod
    @_nameOrFunc
    def onNotCmd(cls,coreName=None):
        """
            解析得到非指令时的回调
                coreName 指令中枢名，默认为 None，即是使用最后创建的中枢\n
            回调函数：\n
                传入 ParseResult 对象和此次解析使用的 CommandParser 对象\n
                不使用返回值
        """
        return cls.on(EventNames.NotCmd,coreName)

    @classmethod
    @_nameOrFunc
    def onUndefinedCmd(cls,coreName=None):
        """
            解析得到未定义指令时的回调
                coreName 指令中枢名，默认为 None，即是使用最后创建的中枢\n
            回调函数：\n
                传入 ParseResult 对象和此次解析使用的 CommandParser 对象\n
                不使用返回值
        """
        return cls.on(EventNames.UndefinedCmd,coreName)

    @classmethod
    @_nameOrFunc
    def onWrongCmdType(cls,coreName=None):
        """
            解析得到指令，但指令类型（前缀）有误时的回调
                coreName 指令中枢名，默认为 None，即是使用最后创建的中枢\n
            回调函数：\n
                传入 ParseResult 对象和此次解析使用的 CommandParser 对象\n
                不使用返回值
        """
        return cls.on(EventNames.WrongCmdType,coreName)

cmdCallback=Events.onCmd

class EventNames:

    NotCmd="parser-NotCommand"
    UndefinedCmd="parser-UndefinedCmd"
    WrongCmdType="parser-WrongType"