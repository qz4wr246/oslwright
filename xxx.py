import re
from app.core.common import Version


def checkver(version: str, req_ver: str) -> bool:
    """ """
    reg = r"^\s*([><=]=?)?\s*([^\s,;]+)(\s*[,;]+\s*([><]=?)([\w.-]+))?$"

    m = re.match(reg, req_ver)
    if m is None:
        return False

    ope1 = m.group(1)
    ver1 = m.group(2)
    ope2 = m.group(4)
    ver2 = m.group(5)

    result = False
    if not ver1:
        return False

    if not ope1 and ver1 and ope2 is None:
        return True if ver1 == version else False
    else:
        if ope1 == "=" or ope1 == "==":
            result = True if ver1 == version else False
        elif ope1 == "<=":
            result = True if Version(version) <= Version(ver1) else False
        elif ope1 == ">=":
            result = True if Version(version) >= Version(ver1) else False
        elif ope1 == "<":
            result = True if Version(version) < Version(ver1) else False
        elif ope1 == ">":
            result = True if Version(version) > Version(ver1) else False

    if ope2 and ver2:
        if ope2 == "=" or ope2 == "==":
            result &= True if ver2 == version else False
        elif ope2 == "<=":
            result &= True if Version(version) <= Version(ver2) else False
        elif ope2 == ">=":
            result &= True if Version(version) >= Version(ver2) else False
        elif ope2 == "<":
            result &= True if Version(version) < Version(ver2) else False
        elif ope2 == ">":
            result &= True if Version(version) > Version(ver2) else False

    return result


result = checkver("1.3", ">=1.2")
print(f"res={result}")
