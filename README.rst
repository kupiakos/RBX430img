============
RBX430img
============
RBX430img is a command-line program designed to convert images into the complex 5-bit grayscale format 
needed for the RBX430-1 development board to display using the ``lcd_wordImage`` function.
The program is known to work with ``.bmp``, ``.png``, and ``.jpg`` files. It will likely work with many others.

Requirements
===============
If you are using the TMCB lab computers at BYU, the requirements are already installed.

If you'd like to use RBX430img on your own computer, RBX430img requires 
Python 2.7 or 3 and PIL 1.1.3 (preferably through Pillow) to function.

- `Python Installation Page <https://www.python.org/downloads/>`_ 
  (If you're using Linux or Mac OS X, you probably already have Python installed)
- `Pillow Installation Page <http://pillow.readthedocs.org/en/latest/installation.html>`_

If you are using Windows, make sure you understand how to run ``python.exe``. 
The instructions are designed for UNIX but should work in Windows if you simply 
replace ``python`` with the correct executable.

Usage
===============

The syntax for the script is the following::

  rbx430img.py [-h] [-f FMT] [-m FUNC] [-s METHOD] [--nocompress] imagefile width [height]

Examples
---------

To convert a 120x160 image called ``flower.png`` into a 30x40 one-line word array using the default settings::

  $ python rbx430img.py flower.png 30 40

This sort of conversion will be the most common.

------

To convert a 900x643 image called ``orangutan.jpeg`` into a multi-line word array with a 
width of 120 and keeping the same aspect ratio::

  $ python rbx430img.py -f pretty orangutan.jpeg 120

-----

To convert an 200x200 image called ``life.bmp`` into a bitonal black-and-white 80x40 word array, 
using nearest-neighbor filtering::

  $ python rbx430img.py -s nearest -m bwround life.bmp 80 40

-----

To convert an 80x80 image called ``twilightsparkle.png`` into a multi-line word array and capture that data 
in a file ``image.txt``::

  $ python rbx430img.py -f pretty twilightsparkle.png 80 80 > image.txt

Arguments
------------------------

``imagefile``
  The filepath to the image to load and convert.

``width``
  The destination width (in pixels) of the converted image. 
  Because of the limitations of the RBX430-1 development board, this must be an integer divisible by 3 from 3-159. 
  
  For example, you can make an image 120 pixels wide, but not 121 or 122 pixels.

``height``
  The destination height (in pixels) of the converted image.
  It must be in the range 1-159 pixels. It does not suffer from the same limitation that width does.
  This argument is optional. If it is not specified, the image is scaled down to ``width`` while 
  keeping the aspect ratio of the original image. 

  For example, if you scale a 490x320 image and 
  specify a width of 120 but don't specify a height, the height will be 78 to try to keep the aspect ratio.

``-h`` or ``--help``
  Show the basic help-text explaining the arguments.

``-f FMT`` or ``--format FMT``
  Specify the format of the program's output. It may either be ``oneline`` or ``pretty``. The default is ``oneline``.

  If ``oneline`` is specified, the output word array will be on one line. This can be very convenient for copying.

  If ``pretty`` is specified, the output word array will span multiple lines, be tabbed, and only contain 6 words per line.
  This is better for a final file, because the code ends up looking nicer (albeit with more lines).

``-m FUNC`` or ``--map FUNC``
  Specify the function used to map pixels to their 5-bit grayscale counterparts. Here are the valid options:

  ``squareroot``
    This will try to map the pixels in the image to a square-root curve, making the pixels darker, 
    but still allowing for very light pixels. Because this most closely matches what the LCD screen actually projects, it is
    the default.
  
  ``round``
    This will downscale the pixels linearly, but rounding to the closest value instead of truncating. 
    It provides a bit more accuracy than ``linear``.

  ``linear``
    This will downscale the pixels with a linear 8:1 ratio. 
    Images will tend to appear faded unless they are primarily composed of dark colors.

  ``bwround``
    This will map the image to bitonal black and white so pixels below half-luminance will be white, 
    and pixels above half-luminance will be black.

  ``bwnonzero``
    This will map the image to bitonal black and white so any pixels not white will be black, and otherwise white.

``-s METHOD`` or ``--scale METHOD``
  Specify the resampling filter used to scale the image down or up. 
  If your source and destination image sizes are the same, this option is irrelevant.

  The available filters are ``nearest``, ``bilinear``, ``bicubic``, and ``antialias``. 
  ``antialias`` is the default, and is the highest quality for the RBX430-1.

``--nocompress``
  By default, identical contiguous pixels will be compressed in the image to save space. 
  These compressed images are faster and smaller, but if you'd like to not compress the image (for debugging or curiosity), 
  you can specify this option to never compress the image. The pixels will be untouched.

Using in your C code
---------------------

Once you've run the program with the desired arguments, you will be given a C array which can then be copied 
straight into your source code. You will want to define the array in your .c file first, with a possible declaration 
in a .h file. 

This can be done like so in your .c file::

  const uint16 image[] = {120,35,...,0x0000} // data generated by rbx430img.py

You can then show the image on-screen by using the ``lcd_wordImage`` function. 

Here's an example of how to show an image on the screen::

  #include "RBX430-1.h"
  #include "RBX430_lcd.h"
  
  const uint16 image = {3,4,0x07c0,0xffdf,0x07c0,0x07c0};
  
  int main()
  {
    lcd_init();
    lcd_volume(358);
    lcd_clear();
    lcd_wordImage(image, 81, 78, 1); // The x coordinate must be divisible by 3
    return 0;
  }

Notes and Tips
===================

- As specified in the ``lcd_wordImage`` documentation, the destination x coordinate and the 
  desired width of an image must be divisible by 3.
- The volume given to ``lcd_volume`` while developing this script was 358, and is recommended for good results.
- Make sure the LCD is initialized with ``lcd_init`` before trying to draw any images.
- You should really only deviate from the default settings (except for maybe ``-f pretty``) 
  unless you know what you are doing.
- Since loading large images can take noticable time, it may be best to run your program with 
  ``RBX430_init(_16MHZ)`` to get the CPU running as quickly as possible.

This program was written by Kevin Haroldsen, who is currently a freshman in Computer Science at BYU. 
It's open source under the MIT License, so feel free to modify it and provide fixes or really just do whatever you want. 
Just don't sue me, and keep the license.