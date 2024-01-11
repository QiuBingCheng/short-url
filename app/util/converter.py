# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 19:18:00 2020

@author: Jerry
"""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def base62_encode(num, alphabet=ALPHABET):
    """10進制轉62進制"""
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    return ''.join(arr[::-1])


def base62_decode(string, alphabet=ALPHABET):
    """62進制轉10進制"""
    num = 0
    base = len(alphabet)
    string = string[::-1]

    for i, alpha in enumerate(string):
        num += pow(base, i)*ALPHABET.find(alpha)
    return num


def test_case():
    nums = [0, 15, 26, 100, 156, 2692, 42901]
    for n in nums:
        string = base62_encode(n, alphabet=ALPHABET)
        num = base62_decode(string, alphabet=ALPHABET)
        print(num, string)
        assert n == num
