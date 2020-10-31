def getIdentityCode(obj) -> int:
        assert isinstance(obj, Person)
        assert type(obj) != Person
        assert type(obj) != SkilledPerson
        return obj.type

def getBasePacket(src: tuple, dest: tuple) -> dict:
    ret = {}
    ret['srcAddr'] = src[0]
    ret['srcPort'] = src[1]
    ret['destAddr'] = dest[0]
    ret['destPort'] = dest[1]
    return ret