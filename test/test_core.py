import os
import sys
import pytest

sys.path.insert(0,os.getcwd())

from LSparser.command import CommandCore


def teardown_function():
    #每个测试函数后执行
    CommandCore.cores.clear()
    CommandCore.last=None

def test_name():
    assert CommandCore.getLast().name==CommandCore.default
    assert CommandCore.last==CommandCore.default
    with CommandCore("admin") as core:
        assert core.name=="admin"
        assert CommandCore.last=="admin"
        with CommandCore("extra"):
            assert CommandCore.last=="extra"
        assert CommandCore.last=="admin"
    assert CommandCore.last==CommandCore.default
    for n in [CommandCore.default,"admin","extra"]:
        assert n in CommandCore.cores
    assert CommandCore.getCore("extra").name=="extra"
    assert CommandCore.getCore().name==CommandCore.default
    with pytest.raises(KeyError):
        CommandCore.getCore("void")

def test_dup():
    CommandCore.getLast()
    with pytest.raises(ValueError):
        CommandCore(CommandCore.default) # 创建重名指令中枢
    # print(err.value) # 指令管理器已存在

def test_prefix():
    core=CommandCore.getLast()
    assert "." in core.commandPrefix
    assert "。" in core.commandPrefix
    assert "-" in core.commandPrefix
    assert core.isMatchPrefix("!test")
    assert not core.isMatchPrefix("test")
    assert not core.isMatchPrefix("")