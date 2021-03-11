#!/usr/bin/env python3
from __future__ import with_statement
import sys
from PIL import Image
from huffnib import huffnibenc

WIDTHS_4BIT = True

def rgbasm_bytearray(s):
    """Produce db statements for a constant array in rgbasm"""
    s = ['  db ' + ','.join("%3d" % ch for ch in s[i:i + 16])
         for i in range(0, len(s), 16)]
    return '\n'.join(s)

def vwfcvt(filename, tileHt=8):
    im = Image.open(filename)
    pixels = im.load()
    (w, h) = im.size
    (xparentColor, sepColor) = im.getextrema()
    widths = bytearray()
    tiledata = bytearray()
    for yt in range(0, h, tileHt):
        for xt in range(0, w, 8):
            # step 1: find the glyph width
            tilew = 8
            for x in range(8):
                if pixels[x + xt, yt] == sepColor:
                    tilew = x
                    break
            # step 2: encode the pixels
            widths.append(tilew)
            for y in range(tileHt):
                rowdata = 0
                for x in range(8):
                    pxhere = pixels[x + xt, y + yt]
                    pxhere = 0 if pxhere in (xparentColor, sepColor) else 1
                    rowdata = (rowdata << 1) | pxhere
                tiledata.append(rowdata)
    return (widths, tiledata)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) > 1 and argv[1] == '--help':
        print("usage: %s font.png font.s" % argv[0])
        return
    if len(argv) != 3:
        print("wrong number of options; try %s --help" % argv[0], file=sys.stderr)
        sys.exit(1)
        
    (widths, tiledata) = vwfcvt(argv[1])

    # Compress
    if WIDTHS_4BIT:
        widths = bytes(
            hi << 4 | lo for hi, lo in zip(widths[0::2], widths[1::2])
        )
    cwidths = huffnibenc(widths)
    ctiledata = huffnibenc(tiledata)

    out = ["; Generated by vwfbuild",
           'section "vwfChrData", ROM0',
           'vwfChrData_huf::',
           rgbasm_bytearray(ctiledata),
           "vwfChrWidths_huf::",
           rgbasm_bytearray(cwidths),
           '']
    with open(argv[2], 'w') as outfp:
        outfp.write('\n'.join(out))

if __name__ == '__main__':
    if 'idlelib' in sys.modules:
        main(['vwfbuild', '../../common/tilesets/vwf7_cp144p.png',
              '../obj/gb/vwf7.z80'])
    else:
        main()
