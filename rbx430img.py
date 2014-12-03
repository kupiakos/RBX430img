#!/usr/bin/env python
# rbx430img.py - Convert given images into the uint16 array format for the
#                RBX430-1 development board.
# 
################################################################################
# The MIT License (MIT)
#
# Copyright (c) 2014 Kevin Haroldsen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
################################################################################

# This code is designed to work in both Python 2.7 and Python 3.

from __future__ import print_function
try:
    range = xrange
except:
    pass

import argparse
import sys
from itertools import product, chain
from pprint import pprint
import math
from PIL import Image

class DefaultHelpParser(argparse.ArgumentParser):
    def error(self, message):
        print('error:', message, file=sys.stderr)
        self.print_help()
        sys.exit(2)

# v for lambdas is a number from 0-255.
# they need to return numbers 0-31.
mappingfuncs = {
    'squareroot': (lambda v : int(round((math.sqrt(v + 1) - 1) * 2.05))),
    # gives more accurate results than linear.
    'round': (lambda v : int(round((v / 8.225806451612904)))),
    'linear': (lambda v: v // 8),
    'bwround': (lambda v: int(round(v / 256.0)) * 31),
    'bwnonzero': (lambda v: 31 if v else 0),
    }

scalingmethods = {
    'nearest': Image.NEAREST,
    'bilinear': Image.BILINEAR,
    'bicubic': Image.BICUBIC,
    'antialias': Image.ANTIALIAS
    }

def loadwidth(s):
    w = int(s)
    if w % 3 != 0 or w < 0 or w >= 160:
        raise argparse.ArgumentTypeError(
            'Width must be a multiple of 3 from 3-159!')
    return w

def loadheight(s):
    h = int(s)
    if h < 0 or h > 160:
        raise argparse.ArgumentTypeError('Height must be from 1-160!')
    return h

def loadimage(imgfile):
    im = Image.open(imgfile)
    im = im.convert('RGBA')
    white = Image.new('RGBA', im.size, (255,255,255))
    im = Image.alpha_composite(white, im)
    im = im.convert('RGB')
    return im

def calcheight(im, w):
    h = int(round((float(im.size[1]) / im.size[0]) * w))
    if h > 160:
        raise ValueError('The calculated new height (' +
                         str(h) + ') is larger than 160!')
    return h

def scaleimage(im, w, h, method):
    im = im.resize((w, h), method)
    im = im.convert('L')
    im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im = im.point(lambda i : 255 - i)
    return im

def map5bit(im, mapfunc):
    raw = im.load()
    data = [mapfunc(raw[x,y]) 
            for y,x in product(range(im.size[1]), range(im.size[0]))]
    data = [(data[i+2] << 11) | (data[i+1] << 6) | (data[i])
            for i in range(0, len(data), 3)]
    return data

def compress(data):
    new = []
    cur = -1
    cnt = 0
    for i in chain(data, (-1,)):
        if cur == i and cnt < 0xff:
            cnt += 1
        else:
            if cnt == 1:
                new.append(cur)
            elif cnt > 1: # if cnt == 0, on first
                if cur == 0:
                    new.append((cnt << 8) | 0x00ff)
                elif cur == 0xffdf: # full
                    new.append((cnt << 8) | 0x00fe)
                else:
                    new.append((cnt << 8) | 0x00f0)
                    new.append(cur)
            cur = i
            cnt = 1
    return new

def outputdata(data, w, h, oneline=True):
    if oneline:
        print('{%d,%d,' % (w, h) +
              ','.join('0x' + hex(i)[2:].zfill(4) for i in data) + 
              '};')
    else:
        print('{%d, %d,' % (w, h))
        print(',\n'.join(
            ('\t' + ','.join('0x' + hex(j)[2:].zfill(4)
                           for j in data[i:min(i+9, len(data))]))
            for i in range(0, len(data), 9)
            ))
        print('};')
              

def main():
    ap = DefaultHelpParser(
        description='Converts any LCD image to an ' +
        'RXB430_lcd-compatible C array.',
        epilog='This code is open-sourced under the MIT license! ' +
        'Feel free to donate.')

    ap.add_argument('imagefile',
                    help='The image to load. ' +
                    'Most image formats are supported.')
    ap.add_argument('width',
        type=loadwidth,
        help='The destination width of the image. ' +
                    'It must be a multiple of 3 from 3-159.')
    ap.add_argument('height',
        type=loadheight,
        nargs='?',
        default=0,
        help='The destination height of the image. It must be from 1-159. ' +
            'If it is not specified, it will be calculated from the ' +
            'given width and the aspect ratio of the image will be conserved.')
    
    ap.add_argument('-f', '--format',
        choices=('oneline','pretty'),
        dest='format',
        nargs=1,
        default=('oneline',),
        metavar='FMT',
        help='The output format of the data. It may be oneline or pretty. ' +
            'The default is oneline.')
    ap.add_argument('-m', '--map',
        choices=('squareroot', 'round', 'linear', 'bwround', 'bwnonzero'),
        dest='mappingfunc',
        nargs=1,
        default=('squareroot',),
        metavar='FUNC',
        help='The function used to downscale the pixels to 5-bit grayscale. ' +
            'It may be squareroot, round, linear, bwround, or bwnonzero. '
            'The default is squareroot.')
    ap.add_argument('-s', '--scale',
        choices=('nearest', 'bilinear', 'bicubic', 'antialias'),
        dest='scale',
        nargs=1,
        default=('antialias',),
        metavar='METHOD',
        help='The method used to scale the given image down or up. ' +
            'It may be nearest, bilinear, bicubic, or antialias. ' +
            'The default is antialias and is recommended.')
    ap.add_argument('--nocompress',
        dest='compress',
        action='store_false',
        help='Do not compress the image; leave the pixels as-is. ' +
                    'Easier for debugging.')
    args = ap.parse_args()
    
    im = loadimage(args.imagefile)
    
    w = args.width
    h = args.height
    if h == 0:
        h = calcheight(im, w)
    
    print('Converting', args.imagefile, 'to size', '%sx%s' % (w, h),
          file=sys.stderr)
    im = scaleimage(im, w, h, scalingmethods[args.scale[0]])
    data = map5bit(im, mappingfuncs[args.mappingfunc[0]])
    if args.compress:
        data = compress(data)
    print('The image uses', len(data) + 2, 'words of space.', file=sys.stderr)
    outputdata(data, w, h, args.format[0] == 'oneline')
    

if __name__ == '__main__':
    main()
