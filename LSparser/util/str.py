import typing

def indent(texts:typing.Union[str,typing.Iterable],num=2,char=" ",fn:typing.Callable[...,str]=None):
    prefix=char*num
    if isinstance(texts,str):
        texts=texts.split("\n")
    if fn:
        return "\n".join([ f"{prefix}{fn(t)}" for t in texts ])
    else:
        return "\n".join([ f"{prefix}{t}" for t in texts ])