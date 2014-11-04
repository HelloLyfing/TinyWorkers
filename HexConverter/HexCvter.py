# coding:utf-8

# 62进制 => 10进制: 'a' => 0, '9' => 61
Hex62Chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

class HexCvter(object):
    """Hex Converter"""

    @staticmethod
    def _10to62(decimal):
        """给定一个10进制的数字，返回与其值相等的62进制的数值编码"""
        rest = int(decimal)
        ret = []
        while rest > 0:
            remainder = (rest - rest / 62 * 62)
            ret.insert(0, Hex62Chars[remainder])
            rest = rest / 62
        return ''.join(ret)

    @staticmethod
    def _62to10(code62):
        """给定一个62进制的数值编码，返回与其值相等的10进制的数字"""
        codelen = len(code62)
        ret = 0
        for i in xrange(codelen):
            index = Hex62Chars.find(code62[i])
            ret += index * 62 ** (codelen - 1 - i)
        return ret

    @staticmethod
    def _62incr(code62 = None, size = 10):
        """对62进制的数值进行+1操作
        size定义了输出的长度(不足用a补齐，62进制中a代表0)
        例如: code62 = 'mA1', size = 10, 则返回 'aaaaaaamA2'
        """
        if not code62: code62 = Hex62Chars[0]

        codelist = []
        for char in code62:
            if char not in Hex62Chars:
                raise Exception('Hex62-Code62-Invalid code:%s' %code62)
            codelist.append(char)

        # 1. +1 操作
        pt = 1
        index = Hex62Chars.find(codelist[-pt]) + 1
        if index <= 61:
            codelist[-pt] = Hex62Chars[index]
        while index > 61:
            # +1后发生了进位，当前位补零
            codelist[-pt] = Hex62Chars[0]
            pt += 1
            # 遇到了需要添加一位的情况('999' => 'baaa')
            if  pt > len(codelist):
                codelist = [Hex62Chars[0] for x in xrange(pt)]
                codelist[0] = Hex62Chars[1]
                break
            index = Hex62Chars.find(codelist[-pt]) + 1
            if index <= 61:
                codelist[-pt] = Hex62Chars[index]
                break

        # size超出范围
        if len(codelist) > size:
            raise Exception('Hex62-Incr-OVERFLOW max-size[%s]' %size)
        
        # 2. 补足位数(size)
        while len(codelist) < size:
            codelist.insert(0, Hex62Chars[0])

        return ''.join(codelist)

if __name__ == '__main__':
    import time
    decimal_src = int(time.time())
    hex62 = HexCvter._10to62(decimal_src)
    decimal_new = HexCvter._62to10(hex62)
    logfmt = 'd_src:[%s](base10) = hex62:[%s](base62) = d_new:[%s](base10) \n' 
    print logfmt %(decimal_src, hex62, decimal_new)
    
    # use _62incr to generate UniqueID-Code
    # the code-length, outputsize is up to you
    unique_id1 = HexCvter._62incr(None, size = 10)
    unique_id2 = HexCvter._62incr(unique_id1, size = 10)
    logfmt = 'UniqueIDGenerator > id1:[%s] id2:[%s] max-possible-comb(6chars):[%s]' 
    print logfmt %(unique_id1, unique_id2, 62 ** 6)