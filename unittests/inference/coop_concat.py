class A:
    def doA(self):
        return

class C(A):
    def doC(self):
        return

class B(C):
    def doB(self):
        return

class A2:
    def doA2(self):
        return

class C2(A2):
    def doC2(self):
        return

class B2(C2):
    def doB2(self):
        return

def concat(separator, frm, to):
    to.append(separator)
    for cur in frm:
        to.append(cur)

sep = C()
sep.doC()
frmlst = [B()]
frmlst[0].doB()
tolst = [A()]
tolst[0].doA()

# sep2 = C()
# sep2.doC()
# frmlst2 = [B2()]
# frmlst2[0].doB2()
# tolst2 = [A()]
# tolst2[0].doA()

sep2 = C2()
sep2.doC2()
frmlst2 = [B2()]
frmlst2[0].doB2()
tolst2 = [A2()]
tolst2[0].doA2()

sep3 = A()
sep3.doA()
frmlst3 = [A()]
frmlst3[0].doA()
tolst3 = [A()]
tolst3[0].doA()

concat(sep, frmlst, tolst)

concat(sep2, frmlst2, tolst2)

concat(sep3, frmlst3, tolst3)