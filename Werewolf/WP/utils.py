# 判断Python版本
try:
    xrange(10)
except NameError:
    py2 = False
else:
    py2 = True
