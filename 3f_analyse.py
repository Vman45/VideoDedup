#!/usr/bin/env python3

import sys
import os
import subprocess
#import fnmatch
import shutil
#from os.path import join, getsize
#import hashlib
#import sqlite3
#import psycopg2
#from plog import plog
#import codecs
import time
#import datetime
from PIL import Image
import numpy
import gmpy2

#Declarations
debug = 1
copyright = 1
maxdiff = 20
hdmaxdiff = 200
threshold = 1
thresholduw = 2
ctrlref = True
fake = False
env = 'prd'
pid = str(time.time())
foutput = ''
unwanted = []
srclst = []
imglst = []
logfile = 'log/3analyse.' + pid + '.log'
tmp = '/tmp/'
cptsrc = 0
txtgreen = '\033[0;32m'
txterr = '\033[0;33m'
txtnocolor = '\033[0m'
lstfmt = ['.MP4','.AVI','.MOV','.M4V','.VOB','.MPG','.MPEG','.MKV','.WMV','.ASF','.FLV','.RM','.OGM','.M2TS','.RMVB']

#log messages to log file and to screen
def log(s='', threshold=1):
    flog.write(s + '\n')
    if debug >= threshold:
        print(s)

def duration(d, dat=True):
    h = int(d // 3600)
    m = int((d - 3600*h) // 60)
    s = d - 3600*h - 60*m
    if d > 3600: r = '{:02d}'.format(h) + ' h ' + '{:02d}'.format(m)
    elif d > 60: r = '{:02d}'.format(m) + ' mn ' + '{:02.0f}'.format(s)
    else: r = '{:02.3f}'.format(s) + ' s'
    if dat:
        r = txtgreen + time.asctime(time.localtime(time.time())) + txtnocolor + ' ' + r
    return r

#Give the name of a file by removing the forder reference
def ShortName(fullname):
    k = len(fullname) - 1
    while (fullname[k] != '/') and (k > 0): 
      k = k - 1
    if k == 0:
      r = fullname
    else:
      r = fullname[k+1:]
    return r

def MidName(line):
    try:
      pend = len(line) - 1
      while line[pend] != '/': pend = pend - 1
      pbeg = pend - 1
      while line[pbeg] != '/': pbeg = pbeg - 1
      r = line[pbeg+1:]
    except:
      r = line
      log('Error : MidName(' + line + ')')
      halt
    return r 

#Give the name of a file by removing the forder reference
def PathName(fullname):
    k = len(fullname) - 1
    while fullname[k] != '/': k = k - 1
    return str(fullname[:k])

def source(line):
    #Identify the source video file of this image
    k = len(line) - 1
    while line[k] != "/": k = k - 1
    return foldervideo + line[len(folderimg):k]

def newimage(line):
  result = ''
  pend = len(line) - 1
  while line[pend] != '/': pend = pend - 1
#  pbeg = pend - 1
#  while line[pbeg] != '/': pbeg = pbeg - 1
#    log('pbeg=' + str(pbeg) + ', pend=' + str(pend) + ', line[pbeg+1:pend]=' + line[pbeg+1:pend])
  for img in imglst:
    if img[0] == line[:pend]:
      result = img[1] + line[pend:]
#  log('newimage(' + line + ')=' + result, 2)
  return result
  
#Replace / in path to create an image file with reference to source path
def SlashToSpace(fullname, start):
    s = ''
    for k in range(start, len(fullname)):
        if fullname[k] == '/':
            s = s + ' '
        else:
            s = s + fullname[k]
    return s

def sortoccurence(elem):
    return elem[0]

def sortsources(elem):
    return elem[1][0] + elem[1][1]

def calcfp(file, quality, display=False):
  result = -1
  if os.path.exists(file):
    tmpfile = tmp + ShortName(file)
    if os.path.splitext(file)[1] == '.jpg':
      if quality == 1:
          s = 'convert "' + file + '"[160x160] -modulate 100,0 -blur 3x99 -normalize -equalize -resize 16x16 -threshold 50% "' + tmpfile +'"'
      if quality == 2:
          s = 'convert "' + file + '"[160x160] -modulate 100,0 -blur 3x99 -normalize -equalize -resize 28x16 -threshold 50% "' + tmpfile +'"'
      if quality == 3:
          s = 'convert "' + file + '"[160x160] -modulate 100,0 -blur 3x99 -normalize -equalize -resize 57x32 -threshold 50% "' + tmpfile +'"'
      log('Fingerprint : ' + s, 3)
      p=subprocess.Popen(s, stdout=subprocess.PIPE, shell=True)
      (output, err) = p.communicate()
      if err == None:
        im = Image.open(tmpfile)
        img = numpy.asarray(im)
        key = '0b'
        for i in range(img.shape[0]):
            for j in range(img.shape[1]):
                if (img[i,j] < 128):
                    key = key + '0'
                else:
                    key = key +'1'
        result = int(key,2)
        if display:
            print('quality = ' + str(quality))
            print(result)
            for i in range(img.shape[0]):
                s = ''
                for j in range(img.shape[1]):
                    if (img[i,j] < 128):
                        s = s + '.'
                    else:
                        s = s +'X'
                print(s)
  return result

def loadunwanted(folder):
    global unwanted
    global uwpair

    if not(os.path.isdir(folder)):
      os.mkdir(folder, mode=0o777)

    uwpair = []
    log(duration(time.perf_counter() - perf) + ' - Loading list of images to exclude from search from ' + folder, 1)
    for file in os.listdir(folder):
        if (os.path.splitext(file)[1] == '.jpg'):
            if (os.path.exists(folder + 'unwantedimages.fp')) and (os.path.getmtime(folder + 'unwantedimages.fp') < os.path.getatime(folder + file)):
                log('Rebuilt unwantedimages.fp due to recent files added.', 2)
                log(file + ' : ', 2)
                log(str(os.path.getatime    (folder + file)) + ' - ' + str(time.localtime(os.path.getatime(folder + file))), 2)
                log(str(os.path.getmtime    (folder + file)) + ' - ' + str(time.localtime(os.path.getmtime(folder + file))), 2)
                log(str(os.path.getctime    (folder + file)) + ' - ' + str(time.localtime(os.path.getctime(folder + file))), 2)
                log('unwantedimages.fp : ' + str(os.path.getmtime(folder + 'unwantedimages.fp')) + ' - ' + str(time.localtime(os.path.getmtime(folder + \
                  'unwantedimages.fp'))), 2)
                log('---', 2)
                os.remove(folder + 'unwantedimages.fp')
        if (os.path.splitext(file)[1] == '.txt'):
            f = open(folder + file, 'r')
            tmplist = []
            for line in f:
                if line[:5] == 'pair=':
                    tmplist.append(line[5:-1])
            f.close
            uwpair.append(tmplist)

    if os.path.exists(folder + 'unwantedimages.fp'):
        f = open(folder + 'unwantedimages.fp', 'r')
        for key in f:
            unwanted.append(int(key[:-1]))
        f.close

    else:
        log(duration(time.perf_counter() - perf) + ' - Cache unwantedimages.fp to rebuild. Around 5 files per second.')
        for file in os.listdir(folder):
            if (os.path.splitext(file)[1] == '.jpg'):
                key = calcfp(folder + file,1)
                if key in unwanted:
                    log(str(key) + ' : Other image with same key. Remove file from unwanted.', 1)
                    log(str(key) + ' : Other image with same key. Remove ' + folder + file, 4)
                    os.remove(folder + file)
                else:
                    unwanted.append(key)
                    log(str(key) + ' added in unwanted.', 2)

        f = open(folder + 'unwantedimages.fp', 'w')
        for key in unwanted:
            f.write(str(key) + '\n')
        f.close

    log(duration(time.perf_counter() - perf) + ' - ' + str(len(unwanted)) + ' unwanted images fingerprinted and ' + str(len(uwpair)) + ' unwanted pairs of sources.')

def LoadSources(folderv):
    global cptsrc
    global srclst

    if os.path.isdir(folderv):
        if folderv[-1] != "/":
          folderv = folderv + "/"
        for file in os.listdir(folderv):
            ext = os.path.splitext(file)[1]
            if os.path.isdir(folderv+file):
                LoadSources(folderv+file)
            elif ext.upper() in lstfmt:
                cptsrc = cptsrc + 1
                srclst.append([file, folderv])
    if folderv == foldervideo:
      log(duration(time.perf_counter() - perf) + ' - ' + str(len(srclst)) + ' loaded sources files.')

def LoadImages(folder):
    global imglst

#    print('LoadImages(' + folder + ')')
    for entry in os.scandir(folder):
      if entry.is_dir():
        ext = os.path.splitext(entry)[1]
        if ext.upper() in lstfmt:
          imglst.append([entry.name, entry.path])
#          print(imglst[len(imglst)-1])
        else:
          LoadImages(entry.path)
    if folder == folderimg:
      log(duration(time.perf_counter() - perf) + ' - ' + str(len(imglst)) + ' loaded images folders.')
                    
def helpprt():
    log('This program is free software: you can redistribute it and/or modify', copyright)
    log('it under the terms of the GNU General Public License as published by', copyright)
    log('the Free Software Foundation, either version 3 of the License, or', copyright)
    log('(at your option) any later version.', copyright)
    log('', copyright)
    log('This program is distributed in the hope that it will be useful,', copyright)
    log('but WITHOUT ANY WARRANTY; without even the implied warranty of', copyright)
    log('MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the', copyright)
    log('GNU General Public License for more details.', copyright)
    log('', copyright)
    log('You should have received a copy of the GNU General Public License', copyright)
    log('along with this program.  If not, see <http://www.gnu.org/licenses/>.', copyright)
    log('', copyright)
    log('SYNTAX : 3analyse foldersrc folderimg findimagedupesresult [options]', copyright)
    log('-v=n           verbosity', copyright)
    log('-t=n           minimum number of similar images to declare a pair of source as duplicate.', copyright)
    log('-tu=n          similarity of images vs unwanted to declare as unwanted.', copyright)
    log('-maxdiff=n     restrict results of findimagedupesresult on similarity < maxdiff', copyright)
    log('-hdmaxdiff=n   recalculate high def 57x32 similarity to filter final resultset.', copyright)
    log('-out=file      output a new findimagedupesresult file without unwanted images to speed up next runs.', copyright)
    log('-outhd=file    cache file that keep HDdistance between 2 images.', copyright)
    log('-ctrlref=False Will accept multiple occurence of a source in different sets. Risk of erasing both elements. Performance and storage hit.', copyright)
    log('-fake          Will not copy source and image files in analyse folder.', copyright)
    log('', 0)

    
#main
perf = time.perf_counter()
flog = open(logfile,'w')

log('************************************************************************************')
#read arguments and conform them
log('Video DeDup : find video duplicates')
log('Copyright (C) 2018  Pierre Crette')
log('')

print(sys.argv)

if len(sys.argv)<3:
    log('SYNTAX ERROR:')
    helpprt
    exit()

else:
    foldervideo = os.path.normpath(sys.argv[1])
    if foldervideo[-1] != "/": foldervideo = foldervideo + "/"
    folderimgraw = os.path.normpath(sys.argv[2])
    if folderimgraw[-1] != "/":
        folderimg = folderimgraw + "/db/"
        folderana = folderimgraw + "/ana-" + env + "-not-saved/"
        foutputhd = folderimgraw + "/hddb.fp"
    else:
        folderimg = folderimgraw + "db/"
        folderana = folderimgraw + "ana-" + env + "-not-saved/"
        foutputhd = folderimgraw + "hddb.fp"
    fresultset = os.path.normpath(sys.argv[3])
    if not(os.path.exists(folderana)):
        os.mkdir(folderana, mode=0o777)
    for i in sys.argv[3:]:
        if i[:3] == '-v=': debug  = int(i[3:])
        if i[:3] == '-t=': threshold  = int(i[3:])
        if i[:4] == '-tu=': thresholduw = int(i[4:])
        if i[:9] == '-maxdiff=' : maxdiff = int(i[9:])
        if i[:11] == '-hdmaxdiff=' : hdmaxdiff = int(i[11:])
        if i[:5] == '-out=': foutput = i[5:]
        if i[:7] == '-hdout=': foutputhd = i[7:]
        if i[:9] == '-ctrlref=': ctrlref = not(i[9:] == 'False')
        if i == '-fake': fake = True
        if i == '-nc': copyright = 12

    helpprt
    log('debug mode :' + str(debug), 2)
    log('  0 : silent', 2)
    log('  1 : normal', 2)
    log('  2 : verbose and analyse folder not created', 2)
    log('  3 : maximum verbose and analyse folder not created', 2)
    log('folderimg = ' + folderimg, 2)
    log('folderana = ' + folderana, 2)
    log('fresultset = ' + fresultset, 2)
    log('', 2)

    
    sshell = sys.argv[0] + ' ' + sys.argv[1] + ' ' + sys.argv[2] + ' ' + sys.argv[3] + ' -v=' + str(debug) + ' -t=' + str(threshold) 
    sshell = sshell + ' -tu=' + str(thresholduw) + ' -maxdiff=' + str(maxdiff) + ' -hdmaxdiff=' + str(hdmaxdiff) + ' -ctrlref=' + str(ctrlref)
    sshell = sshell + ' -out=' + foutput + ' -hdout=' + foutputhd
    if fake:
      sshell = sshell + ' -fake'
    log(txtgreen + sshell + txtnocolor, 1)
    log('', 0)
    log (txtgreen + 'Consider double if at least ' + str(threshold) + ' pair of images are similar in the set.' + txtnocolor, 0)
    log('', 0)

    perf = time.perf_counter()

    loadunwanted(folderimg + 'unwanted/')
    
    log(duration(time.perf_counter() - perf) + ' - Load current folder of each source...',0)
    LoadSources(foldervideo)
    LoadImages(folderimg)
    srclst = sorted(srclst, key=sortoccurence)

    prev = ''
    for i in range(len(srclst)):
      if srclst[i][0] == prev:
        log(duration(time.perf_counter() - perf) + ' - File ' + srclst[i][1] + srclst[i][0] + ' is referenced 2 times.')
        log(duration(time.perf_counter() - perf) + ' - ... renaming to ' + srclst[i][1] + str(i) + srclst[i][0])
        os.rename(srclst[i][1] + srclst[i][0], srclst[i][1] + str(i) + srclst[i][0])
      prev = srclst[i][0]

    #Step 1: parse fresultset and create memory map
    resultsetvideo = []
    setvideo = []
    setimg = []
    setprt = []
    setkey = []
    nblines = 0
    nbline = 0
    nbstill = 0
    nbunwant = 0
    nbuwpair = 0
    testdiff = True
    t1 = 0
    t2 = 0

    log(duration(time.perf_counter() - perf) + ' - Counting lines in resultset file.' , 1)

    f = open(fresultset, 'r')
    for line in f:
        nblines = nblines + 1
    f.close

    log(duration(time.perf_counter() - perf) + ' - Count number of lines in ' + fresultset + ' done : {:_}'.format(nblines), 1)

    f = open(fresultset, 'r')
    
    for line in f:
        if (nbline % 1000000 == 0) or (nbline == 100000) or (nbline == 10000) or (nbline == 1000):
            log(duration(time.perf_counter() - perf) + ' - Loading file and first checks, line {:_}'.format(nbline) + '/{:_}'.format(nblines) + ' - t1=' + duration(t1, False) + ', t2=' + duration(t2, False), 1)
        nbline = nbline + 1
        line = line[:-1]

        if line[:5] == 'BEGIN':
            if line[7:18] != 'Similarity=':
                log(txterr + 'ERROR : ' + txtnocolor + 'No similarity data in ' + fresultset)
                log(line)
                exit()
            similarity = int(line[18:]) 
            testdiff = (similarity <= maxdiff)
            #Initiate a new set of doubles files
            setvideo = []        # list of unique video file of the set.
            setimg = []          # list of .jpg in result file
            setprt = []          # same as setimg with / replaced by spaces
            setkey = []          # list of keys of images 

        if testdiff and (line == 'END'):
            #Close the set
            #If the set contains at least 'threshold' source video files
            if len(setvideo) > 1:
                #Seek if the set is already known
                slgn = str(round(100*nbline/nblines)) + '% ' + txtgreen + str(len(resultsetvideo)) + txtnocolor + ' : '

                perf1 = time.perf_counter()
                setvideo = sorted(setvideo)
                if setvideo in uwpair:
                    nbuwpair = nbuwpair + 1
                else:
                    resultsetvideo.append([1, setvideo, setimg, setprt, setkey, similarity])
#                    log(slgn + 'New ' + str(setvideo), 4)
                t1 = t1 + time.perf_counter() - perf1
            
            else:
                nbstill = nbstill + 1

        if testdiff and (line[:5] == 'file='):
            line = line[5:]
#            if (line[:17] == '/zpool/NAS_pierre'):
#                line = '/home/pierre/NAS_pierre' + line[17:]
#
#            if line[:len(folderimg)] != folderimg:
#                log(txterr)
#                log('CONFIGURATION ERROR, Mismatch image folder :')
#                log(folderimg + ' and resultset :')
#                log(line)
#                log('Either change your parameters,')
#                log('Or if multiple computer give different names to same folder, open 2analyse.py and update string replacement @Plateform specific.')
#                log(txtnocolor)

            src = ShortName(source(line))

            #Action on 1 image file of a set of doubles
            setimg.append(MidName(line))
            s = '/'
            for j in range(len(folderimg),len(line)):
                if line[j] == '/':
                    s = s + ' '
                else:
                    s = s + line[j]
            setprt.append(s)

            #This source video file is already in set ? Case of a still or repeted image in the movie
            new = True
            for d in setvideo:
                if d == src: new = False
            if new:
                setvideo.append(src)

        if testdiff and (line[:4] == 'key='):
            key = int(line[4:])
            setkey.append(key)
            # discard unwanted images
            perf2 = time.perf_counter()
            if key in unwanted:
                testdiff = False
                nbunwant = nbunwant + 1
            # discard images close to unwanted
            if testdiff and (thresholduw > 0):
                for uwkey in unwanted:
                  if gmpy2.hamdist(key,uwkey) <= thresholduw:
                    testdiff = False
                  
#                i = 0
#                while i < len(unwanted):
#                  dist = gmpy2.hamdist(key,unwanted[i])
#                  i = i + 1
#                  if dist <= thresholduw :
#                    testdiff = False
#                    i = 9999999
            
#                  log('Near unwanted copied from ' + setimg[len(setimg)-1][5:] + ' to ' + folderana + 'mindist' + str(mindist) + '/')
#                  shutil.copy2(setimg[len(setimg)-1][5:], folderana + 'mindist' + str(mindist) + '/')
            t2 = t2 + time.perf_counter() - perf2

    f.close
    worksize = len(resultsetvideo)
    log(duration(time.perf_counter() - perf) + ' - STEP1 done. {:_}'.format(worksize) + ' dupes found. {:_}'.format(nbstill) + \
         ' stills rejected and {:_}'.format(nbunwant) + ' unwanted images, {:_}'.format(nbuwpair) + ' unwanted pairs.', 1)
    log('     ' + duration(t1) + ' - t1 = Uwanted pairs controls and removal.')
    log('     ' + duration(t2) + ' - t2 = Uwanted images/keys controls and removal.')
    
    if foutput != '':
      f = open(foutput, 'w')
      for r in resultsetvideo:
          if (len(r[2]) != 2) or (len(r[4]) != 2):
            log('ERROR, more than 2 images in the set :')
            print(r)
#          log(r[2][0],4)
          f.write('BEGIN. Similarity=' + str(r[5]) + '\n')
          f.write('file=' + r[2][0] + '\n')
          f.write('key=' + str(r[4][0]) + '\n')
          f.write('file=' + r[2][1] + '\n')
          f.write('key=' + str(r[4][1]) + '\n')
          f.write('END' + '\n')        
      f.close
      log(duration(time.perf_counter() - perf) + ' - Output file written to disk : ' + foutput)

    #Step 2: clean files in multiple duplicates
    log('****************************************', 1)
    log('* STEP 2 : HD COMPARE TO NARROW FILTER *', 1)
    log('****************************************', 1)
    if worksize > 1000000:
      log(txtgreen + sshell + txtnocolor, 1)
#    resultsetvideo.append([1, setvideo, setimg, setprt])

    #Sort by 1st source then group and count same duplicate sets.
    resultsetvideo = sorted(resultsetvideo, key=sortsources)
    log(duration(time.perf_counter() - perf) + ' - Sorted {:_}'.format(len(resultsetvideo)) + ' elements.', 0)
    rsv = []
    prev = ['','']

    for i in range(len(resultsetvideo)):
        if prev[1] != resultsetvideo[i][1]:
            prev = resultsetvideo[i]
            rsv.append(prev)
        else:
            rsv[len(rsv)-1][0] = rsv[len(rsv)-1][0] + 1
            for j in range(len(resultsetvideo[i][2])):
                rsv[len(rsv)-1][2].append(resultsetvideo[i][2][j])
                rsv[len(rsv)-1][3].append(resultsetvideo[i][3][j])
        # Remove duplicate source images
        tmprs = sorted(resultsetvideo[i][2])
        resultsetvideo[i][2] = []
        previ = ''
        for j in range(len(tmprs)):
            if (previ != tmprs[j]):
                previ = tmprs[j]
                resultsetvideo[i][2].append(previ)

    log(duration(time.perf_counter() - perf) + ' - Grouped by source files from {:_}'.format(len(resultsetvideo)) + ' to {:_}'.format(len(rsv)) + ' unique dupes.', 0)

    rsv = sorted(rsv, key=sortoccurence, reverse=True)
    named= []
    resultsetvideo = []
    log('Check occurence >= ' + str(threshold), 2)
    rejthr = 0
    rejref = 0
    rejdel = 0
    rejimg = 0

    for i in range(len(rsv)):
      
        log('rsv[' + str(i) + '] : occurences = ' + str(rsv[i][0]), 4)
        keep = (rsv[i][0] >= threshold)
        if not(keep):
            rejthr = rejthr + 1
        if keep and ctrlref:
            for j in range(len(rsv[i][1])):
                if rsv[i][1][j] in named:
                    log('Rejected cause ' + rsv[i][1][j] + ' previously referenced.', 2)
                    keep = False
            if not(keep):
                rejref = rejref + 1
        if keep:
            images = sorted(rsv[i][2])
            rsv[i][2] = []
            prev = ''
            for j in range(len(images)):
                if prev != images[j]:
                    rsv[i][2].append(images[j])
#                    print(str(j) + ' - ' + images[j])
                    prev = images[j]
            n = threshold
            prev = ''
            for j in range(len(rsv[i][2])):
                if prev == PathName(rsv[i][2][j]):
                    n = n + 1
                else:
                    if n < threshold:
                        log('Rejected cause nb images < ' + str(threshold) + ' for one source :', 2)
                        for k in range(min(6,len(rsv[i][2]))):
                          log(rsv[i][2][k], 2)
                        keep = False
                    prev = PathName(rsv[i][2][j])
                    n = 1
            if n < threshold:
               log('Rejected cause nb images < ' + str(threshold) + ' for one source :', 2)
#               for k in range(len(rsv[i][2])): log(rsv[i][2][k], 2)
               keep = False

            if not(keep):
                rejimg = rejimg + 1
        if keep:
            for j in range(len(rsv[i][1])):
                named.append(rsv[i][1][j])
            resultsetvideo.append(rsv[i])

    log(duration(time.perf_counter() - perf) + ' - Controls restricted list from {:_}'.format(len(rsv)) + ' to ' + txtgreen + \
     '{:_}'.format(len(resultsetvideo)) + ' dupes.' + txtnocolor, 0)
    log('{:_}'.format(rejthr) + ' + {:_}'.format(rejimg) + ' rejections due to common images < {:_}'.format(threshold) + ', {:_}'.format(rejref) + \
        ' previously references sources, {:_}'.format(rejdel) + ' moved or deleted sources.', 1)

    #Calculate HD distance to limit resultset
    hdcacheimg = []
    hdcachekey = []
    hdkey = -1
    if os.path.exists(foutputhd):
      f = open(foutputhd, 'r')
      for line in f:
        if line[:6] == 'hdkey=':
          hdkey = line[6:-1]
        if line[:5] == 'file=':
#          print('LoadHDcache line = ' + line[:-1])
#          print('LoadHDcache MidName = ' + MidName(line[:-1]))
          if len(line) > 22:
#          if not(hdfile in hdcacheimg):
            hdcacheimg.append(line[5:-1])
            hdcachekey.append(int(hdkey))
      f.close
      if worksize > 100000:
        log(duration(time.perf_counter() - perf) + ' - HD cache loaded with ' + str(len(hdcacheimg)) + ' elements.')
        
    t1 = 0
    t2 = 0
    t3 = 0
    perf3 = time.perf_counter()
#    hdrs.append([similarity, setimg, sethdkey])
#    resultsetvideo.append([1, setvideo, setimg, setprt])
    rsv = []
    for i in range(0, len(resultsetvideo)):
        perf1 = time.perf_counter()
        t3 = t3 + perf1 - perf3

        if (i % 10 == 0):
          print('')
          print(duration(time.perf_counter() - perf) + ' - ' + str(i), end='', flush=True)
        print('.', end='', flush=True)
        hdkey = []
        for j in range(0, len(resultsetvideo[i][2])):
#          print(resultsetvideo[i][2][j])
#          print(MidName(resultsetvideo[i][2][j]))
          hdk = -1
#          print('hdcacheimg[0] = ' + hdcacheimg[0])
#          print('resultsetvideo[i][2][j]) = ' + resultsetvideo[i][2][j])
#          exit()
          try:
            hdk = hdcachekey[hdcacheimg.index(resultsetvideo[i][2][j])]
#            print('found : ' + MidName(resultsetvideo[i][2][j]))
#            exit()
          except:
            imagefile = newimage(resultsetvideo[i][2][j])
            hdk = calcfp(imagefile,3)
#            log('hdk = calcfp(' + imagefile + ',3)=' + str(hdk))
            hdcacheimg.append(MidName(imagefile))
            hdcachekey.append(hdk)
#            print(hdkey[len(hdkey)-1])
#            exit()
              
          if hdk != -1:
            hdkey.append([source(resultsetvideo[i][2][j]), resultsetvideo[i][2][j], hdk])
        
        perf2 = time.perf_counter()
        t1 = t1 + perf2 - perf1
        hdbest = []
        for j in range(0, len(hdkey)):
            hddupe = []
            for k in range(j+1, len(hdkey)):
                if (hdkey[j][0] != hdkey[k][0]):
#                    log('gmpy2.hamdist(' + str(hdkey[j][2]) + ', ' + str(hdkey[k][2]) + ')')
                    hddupe.append([gmpy2.hamdist(int(hdkey[j][2]),int(hdkey[k][2])), k])
            hddupe = sorted(hddupe, key=sortoccurence)
            # distance, img1, img2
            if (hddupe != []):
#                print('i=' + str(i) + ', j=' + str(j))
#                print(hddupe[0][0])
#                print(hdkey[j][1])
#                print(hdkey[hddupe[0][1]][1])
                hdbest.append([hddupe[0][0], hdkey[j][1], hdkey[hddupe[0][1]][1]])
#                print('hdbest :')
#                print([hddupe[0][0], hdkey[j][1], hdkey[hddupe[0][1]][1]])
                
        perf3 = time.perf_counter()
        t2 = t2 + perf3 - perf2
        if (hdbest != []):
            hdbest = sorted(hdbest, key=sortoccurence)
            j = 0
            s = ''
#            print(str(len(hdbest)) + ' vs ' + str(j))
            while (j < len(hdbest)) and (hdbest[j][0] <= hdmaxdiff):
                s = s + str(hdbest[j][0]) + ', '
                j = j + 1
            if j < len(hdbest):
              s = s + str(hdbest[j][0])
            if (j < threshold):
                log('Resultset rejected after HD 57x32 control. Best distances = ' + s, 2)
                log(resultsetvideo[i][1][0], 2)
                log(resultsetvideo[i][1][1], 2)
            else:
                rsv.append(resultsetvideo[i])
            
    print('')
    log(duration(t1) + ' - T1 = HDkey computation or seek')
    log(duration(t2) + ' - T2 = HDkey comparison')
    log(duration(t3) + ' - T3 = other')

    # Store HD distances in a cache file for next run
    if foutputhd != '':
      f = open(foutputhd, 'w')
      for i in range(len(hdcacheimg)):
          f.write('hdkey=' + str(hdcachekey[i]) + '\n')
          f.write('file=' + hdcacheimg[i] + '\n')
      f.close
      
    print('')
    log(duration(time.perf_counter() - perf) + ' - Limit to max HD 57x32 distance done. From {:_}'.format(len(resultsetvideo)) + txtgreen + \
     ' to {:_}'.format(len(rsv)) + ' dupes.' + txtnocolor, 0)
    resultsetvideo = rsv

    #Step 3: create Analyse folder and copy all files in it
    log('*******************************************')
    log('*    STEP 3 : COPY FILES FOR ANALYSIS     *')
    log('*******************************************')
    if fake:
        log(txtgreen + 'Fake: Analyse folder not created.' + txtnocolor)
        for i in range(len(resultsetvideo)):
            log('resultsetvideo[' + str(i) + '] : occurences = ' + str(resultsetvideo[i][0]), 2)
            log('Sources :', 2)
            for j in range(len(resultsetvideo[i][1])): log(resultsetvideo[i][1][j], 2)
            log('Images :', 4)
            for j in range(len(resultsetvideo[i][2])): log(resultsetvideo[i][2][j], 4)
    else:
        if not(os.path.exists(folderana)):
            os.mkdir(folderana)
        for j in range(len(resultsetvideo)):
            ok = True
            fld = folderana + str(j) + '/'
            x = resultsetvideo[j]
            if x[0] >= threshold:
                if os.path.exists(fld):
                    shutil.rmtree(fld)
                os.mkdir(fld, mode=0o777)

                #x[1] are Video source files
                for d in enumerate(x[1]):
                    patd1 = ''
                    for srcelt in srclst:
                      if srcelt[0] == d[1]:
                        patd1 = srcelt[1] + d[1]
                        
                    log('Copy ' + patd1 + ' ' + fld + d[1])
                    if ok and os.path.exists(patd1):
#                        shutil.copy2(patd1, fld + SlashToSpace(patd1, len(foldervideo)))
                        shutil.copy2(patd1, fld + d[1])
                    else:
                        ok = False

                #x[2] are images files
                if ok:
                    f = open(fld + '/nb_match_' + str(x[0]) + '.' + str(j) + '.' + pid + '.txt','w')
                    f.write('To move in ' + folderimg + '/unwanted to remove this pair from future comparison :\n')
                    for d in enumerate(x[1]):
                        f.write('pair=' + d[1] + '\n')
                    f.write('#\n')
                    f.write('Similar images files :\n')
                    prev = ''
                    for d in enumerate(x[2]):
                        log('prev = ' + prev, 4)
                        log('d[1]    = ' + d[1], 4)
                        if d[1] != prev:
                            log('d <> prev', 4)
                            f.write(d[1] + '\n')
                            log(fld + SlashToSpace(d[1], len(folderimg)), 2)
                            if os.path.exists(d[1]):
                                shutil.copy2(d[1],fld + SlashToSpace(d[1], len(folderimg)))
                            else:
                                log(txterr + 'Not exist ' + d[1] + txtnocolor)
                        prev = d[1]
                    f.close
                else:
                    shutil.rmtree(fld)

log(duration(time.perf_counter() - perf) + ' - STEP3 done' , 1)
log('', 0)
log(txtgreen + sshell + txtnocolor, 1)
flog.close