"""
    Command Parser with Long/Short options/arguments\n
    使用command.Command类创建指令模板，为模板添加长短选项（Options）、回调函数、别名、帮助信息等\n
    使用parser.CommandParser类创建对象，根据情况调用tryParse或parse解析指令
"""

from .command import Command,CommandParser,OPT,ParseResult
from .event import Events
#这样就可以 from LSParser import *