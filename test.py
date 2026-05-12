def main():
    def sum(a, b, zen=False):
        anti_zen = True
        if zen == True: anti_zen = False
        trans = "Halo!"
        c = a + b
        return (c, zen)
    
    # print(sum(1, 1))

import dis
print(dis.dis(main))