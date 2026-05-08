import sys
print(sys.version_info.minor)

import dis
def main():
    a = 5
    if(a%2 == 0):
        print("1")
    while(a>0):
        print(a)
        a = a-1

print(dis.dis(main))