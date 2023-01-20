# -*- encoding: utf-8 -*-

import os, sys
from os import path

SHIFT = 27
private_key = 'He was an old man who fished alone in a skiff in the Gulf Stream and he had gone eighty-four days now without taking a fish. In the first forty days a boy had been with him. But after forty days without a fish the boy’s parents had told him that the old man was now definitely and finally salao, which is the worst form of unlucky, and the boy had gone at their orders in another boat which caught three good fish the first week. It made the boy sad to see the old man come in each day with his skiff empty and he always went down to help him carry either the coiled lines or the gaff and harpoon and the sail that was furled around the mast. The sail was patched with flour sacks and, furled, it looked like the flag of permanent defeat.'

def encrypt(raw):
    ret = ''
    raw = raw+private_key
    for char in raw:
        ret += chr(ord(char) + SHIFT)
    return ret

def decrypt(raw):
    ret = ''
    for char in raw:
        ret += chr(ord(char) - SHIFT)
    ret = ret.replace(private_key,'')
    return ret

def createLicense(raw):
    f = open("license.txt", 'w', encoding="utf-8")
    encrypted = encrypt(raw)
    f.write(encrypted)
    f.close()
    print('create License done! \nexpired data: %s' %raw)

def chekcLicense():
    license = {'user': '', 'date': ''}
    license_path = os.path.join(os.path.dirname(sys.argv[0]),'static','license','license.txt')
    if path.exists(license_path):
        f = open(license_path, 'r', encoding="utf-8")
        line = f.readline()
        f.close()
        decryptd= decrypt(line)
        license['user'] = decryptd.split('_')[0]
        license['date'] = decryptd.split('_')[1]
    return license

if __name__ == "__main__":
    createLicense('master_20231231')