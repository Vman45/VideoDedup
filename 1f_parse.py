#!/usr/bin/env python3

import sys
import os
import subprocess
#import fnmatch
import shutil
#import glob
#from os.path import join, getsize
#import hashlib
#import sqlite3
#import psycopg2
#from pprint import pprint
import time
import random
from PIL import Image
import numpy
import multiprocessing

#Declarations
debug = 1
copyright = 0
cpttodo = 0
cptdone = 0
level = 0
fpsn=60.0
parallel = False
clean = False
moved = True
srclst = []
pid = str(time.time())
logfile = 'log/1parse.' + pid + '.log'
foldervideo= '.'
folderimg = '.'
txtgreen = '\033[0;32m'
txtred = '\033[0;31m'
txtnocolor = '\033[0m'

#log messages to log file and to screen
def log(s='', threshold=1):
    flog.write(s + '\n')
    if debug >= threshold: print(s)

def duration(d):
    h = d // 3600
    m = (d - 3600*h) // 60
    s = d - 3600*h - 60*m
    r = str(round(s,1)) + ' s'
    if (d < 2): r = str(round(s,3)) + ' s'
    if (d > 60): r = str(round(m)) + ' mn ' + str(round(s))
    if (d > 3600): r = str(round(h)) + ' h ' + str(round(m))
    return r
    
def sortoccurence(elem):
    return elem[0]
  
#Step1: remove images with no more source
def BoucleSupp(radical='', root=True):
    global srclst

    if radical != "":
        if radical[-1] != "/": radical = radical + "/"
    log ('BoucleSupp(' + radical + ')', 4)
    if root:
      log ('BoucleSupp(' + radical + ')', 1)
      log('srclist contains ' + str(len(srclst)) + ' elements', 1)
    if clean:
      srclst = sorted(srclst, key=sortoccurence)
        
    if os.path.isdir(folderimg + radical):
        for file in os.listdir(folderimg + radical):
          if os.path.isdir(folderimg + radical + file):
            ext = os.path.splitext(file)[1]
            if ext != '.jpg':
                log ('ext = ' + ext + ' -> ' + folderimg + radical + file, 12)
            if (ext.upper() == '.MP4') or (ext.upper() == '.AVI') or (ext.upper() == '.MOV') or (ext.upper() == '.M4V') \
                or (ext.upper() == '.VOB') or (ext.upper() == '.MPG') or (ext.upper() == '.MPEG') or (ext.upper() == '.MKV') \
                or (ext.upper() == '.WMV') or (ext.upper() == '.ASF') or (ext.upper() == '.FLV') \
                or (ext.upper() == '.RM') or (ext.upper() == '.OGM') or (ext.upper() == '.M2TS') or (ext.upper() == '.RMVB'):
                if not(os.path.exists(foldervideo + radical + file)):
                    if clean:
                      log('Moved ' + foldervideo + radical + file, 1)
                      found = False
                      for newsrc in srclst:
                        if newsrc[0] == file:
                          found = True
                          log(' to ' + newsrc[2] + file, 1)
                          try:
                            shutil.move(folderimg + radical + file, newsrc[2] + file)
                          except:
                            log(txtred + 'Error' + txtnocolor + ' moving image folder. Try to remove it.', 1)
                            shutil.rmtree(folderimg + radical + file)
                      if not(found):
                        log(txtred + 'Error' + txtnocolor + ' not found. The file was deleted. Removing the image folder.', 1)
                        shutil.rmtree(folderimg + radical + file)
#                    else:
#                      log ('Delete because source removed and not clean option: ' + folderimg + radical + file, 0)
#                      shutil.rmtree(folderimg + radical + file)
                else:
                  log('test ' + folderimg + radical + file + '/*.jpg', 2)
#                 log('test ' + glob.escape(folderimg + radical + file + '/*.jpg'), 1)
#                 log(file[66:68])
                  if not(os.path.exists(folderimg + radical + file + '/img00001.jpg')):
                      log ('Delete because no .jpg image : ' + folderimg + radical + file, 0)
                      shutil.rmtree(folderimg + radical + file)                  
            if os.path.isdir(folderimg + radical + file):
                BoucleSupp(radical + file, False)

#Count source to do
def BoucleCount(folderv='.', folderi='.', level=1):
    global cpttodo
    global srclst

    level = level + 1
    spacer = ''
    if debug>0: 
        for i in range(level): spacer=spacer+'  '
        log(spacer + '[ ' + folderv, 0)
    if os.path.isdir(folderv):
        if not(os.path.exists(folderi)):
            os.mkdir(folderi, mode=0o777)
        if folderv[-1] != "/": folderv = folderv + "/"
        if folderi[-1] != "/": folderi = folderi + "/"
        for file in os.listdir(folderv):
            ext = os.path.splitext(file)[1]
            if os.path.isdir(folderv+file):
                BoucleCount(folderv+file, folderi+file, level+1)
            elif (ext.upper() == '.MP4') or (ext.upper() == '.AVI') or (ext.upper() == '.MOV') or (ext.upper() == '.M4V') \
                or (ext.upper() == '.VOB') or (ext.upper() == '.MPG') or (ext.upper() == '.MPEG') or (ext.upper() == '.MKV') \
                or (ext.upper() == '.WMV') or (ext.upper() == '.ASF') or (ext.upper() == '.FLV') \
                or (ext.upper() == '.RM') or (ext.upper() == '.OGM') or (ext.upper() == '.M2TS') or (ext.upper() == '.RMVB'):
                cpttodo = cpttodo + 1
                srclst.append([file, folderv, folderi])
            elif not(ext.upper() == '.JPG' or ext.upper() == '.TXT' or ext.upper() == '.TXT~'):
                log (spacer + '  Not match : ' + folderv + file, 2)
    if debug>0: 
        spacer = ''
        for i in range(level): spacer=spacer+'  '
        log (spacer + '  ' + folderv + ' count = ' + str(cpttodo) + ' ]', 0)
    level = level - 1

#Generate fingerprint for all images of 1 source file and store them in a file
def CreateFingerprint(folder=''):
    perf = time.perf_counter()
    todo = True
    if folder[-1] != "/": folder = folder + "/"
    if not(os.path.isdir(folder)):
        log('CreateFingerprint cannot run before ffmpeg for ' + folder, 0)
        todo = False
#    if os.path.exists(folder[:-1] + '.run'):
#        log('CreateFingerprint cannot run until ffmpeg is finished for ' + folder, 0)
#        todo = False
    else:
        log('CreateFingerprint : does not exist ' + folder[:-1] + '.run', 4)
    
    if todo:
        #lock fingerprint    
        todo = not(os.path.exists(folder + 'fingerprint.fp'))

        if not(parallel):
            if os.path.exists(folder + 'fingerprint.run') or clean:
                #check if fingerprint.fp contains enough lines
                if os.path.exists(folder + 'fingerprint.fp'):
                    f = open(folder + 'fingerprint.fp', 'r')
                    i = 0
                    for line in f:
                        i = i + 1
                    i = i // 2
                    log('fingerprint.fp exists with ' + str(i) + ' lines', 2)
                    for file in os.listdir(folder):
                        if os.path.splitext(file)[1] == '.jpg':
                            i = i-1
                    log(str(-i) + ' more files than fingerprints in ' + folder,2)
                else:
                    i = -1
                
                if i < 0:
                    log('   --- fingerprint.fp exist but fingerprint.run flag or not enough files so remove fingerprints', 0)
                    if os.path.exists(folder + 'fingerprint.fp'):
                        os.remove(folder + 'fingerprint.fp')
                    todo = True
                if os.path.exists(folder + 'fingerprint.run'):
                    os.remove(folder + 'fingerprint.run')
            log('set ' + folder + 'fingerprint.run flag',2)
            if not(clean):
                f = open(folder + 'fingerprint.run','w')
                f.write(pid + '\n')
                f.close

        if parallel and todo:
            if os.path.exists(folder + 'fingerprint.run'):
              todo = False
              log('   --- fingerprint.run flag for ' + folder + ' Skip due to parallel mode ', 0)
            else:
              log('set ' + folder + 'fingerprint.run flag',2)
              f = open(folder + 'fingerprint.run','w')
              f.write(pid + '\n')
              f.close
              time.sleep(3)
#                if os.path.exists(folder[:-1] + '.run'):
#                    log('CreateFingerprint cannot run until ffmpeg is finished for ' + folder, 0)
#                    todo = False
              if not(os.path.exists(folder + 'fingerprint.run')):
                  todo = False
                  log('   -------------------------------------------------------------------', 0)
                  log('   --- Concurent run detected !', 0)
                  log('   --- fingerprint.run flag for ' + folder + ' Skip due to parallel mode ', 0)
                  log('   -------------------------------------------------------------------', 0)
              else:
                  with open(folder + 'fingerprint.run') as f:  
                      line = f.readline()
                      line = line[:-1]
                  log (line + ' =? ' + pid, 4)
                  if line != pid:
                      todo = False
                      log('   -------------------------------------------------------------------', 0)
                      log('   --- Concurent run detected !', 0)
                      log('   --- fingerprint.run flag for ' + folder + ' Skip due to parallel mode ', 0)
                      log('   -------------------------------------------------------------------', 0)
        
        if todo and not(clean):
          log ('CreateFingerprint folder=' + folder, 1)
          finput = []
          for file in os.listdir(folder):
              if os.path.splitext(file)[1].upper() == ".JPG":
                  log('CreateFingerprint : file = ' + file, 3)
                  finput.append([folder,file])
          pool = multiprocessing.Pool(3)
          fpram = pool.map(calcfp, finput)
          
          if not(os.path.exists(folder + 'fingerprint.fp')):
              fp = open(folder + 'fingerprint.fp','w')
              for i in range(len(fpram)):
                  fp.write('key=' + str(fpram[i][0]) + '\n')
                  fp.write('file=' + fpram[i][1] + '\n')
              fp.close

          log ('CreateFingerprint for ' + folder + ' perf = ' + txtgreen + duration(time.perf_counter() - perf) + txtnocolor, 0)
          if os.path.exists(folder + 'fingerprint.run'):
              try:
                  os.remove(folder + 'fingerprint.run')
              except:
                  log(txtred + 'ERROR in CreateFingerprint for ' + txtnocolor + folder, 0)

def calcfp(elt):
  folder = elt[0]
  file = elt[1]
  result = []
  if os.path.splitext(file)[1] == '.jpg':
    s = 'convert "' + folder + '/' + file + '"[160x160] -modulate 100,0 -blur 3x99 -normalize -equalize -resize 16x16 -threshold 50% "' + tmp + file +'"'
    p=subprocess.Popen(s, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    if err == None:
      im = Image.open(tmp + file)
      img = numpy.asarray(im)
      key = '0b'
      for i in range(img.shape[0]):
        for j in range(img.shape[1]):
          if (img[i,j] < 128):
            key = key + '0'
          else:
            key = key +'1'
      result = [int(key,2),folder+file]
  return result
    
#Generate jpg images files for one source video file
def OneFile(folderv, folderi, file):
    global cpttodo, cptdone
    
    #Initialization
    fvideo = folderv + file
    fimg = folderi + file + '/img%05d.jpg'
    log ('OneFile(' + folderv +', ' + folderi + ', ' + file + ')', 2)
    
    if debug>1:
      s = 'ffmpeg -i "' + fvideo + '" -vf fps=1/' + str(fpsn * (0.9 + random.random()/4)) + ' "' + fimg + '"'
    else:
      s = 'ffmpeg -loglevel fatal -i "' + fvideo + '" -vf fps=1/' + str(fpsn * (0.9 + random.random()/4)) + ' "' + fimg + '"'
    
    folderi2 = folderi + file
    log (folderi2, 3)
    
    # Controls
    todo = True
#    try:
    if os.path.exists(folderi2):
        line = 'fps=1/60'            
        if os.path.exists(folderi2 + '/param.txt'):
            with open(folderi2 + '/param.txt') as f:
                line = f.readline()
                line = line[:-1]
                log(line,5)
        if len(line) <= 6:
            log('   --- Param.txt inconsistent : ' + line, 1)
            line = 'fps=1/999'
        log('Test fps: ' + line[6:] + ' <= ? ' + str(fpsn), 3)
        if float(line[6:]) <= fpsn:
            todo = False
            log ('   --- ffmpeg done ' + folderi2, 2)
        else:
            log (folderi2 + ' ffmpeg done but upgrade from ' + line + ' to fps=1/' + str(fpsn), 1)
    else:
        if clean:
            log (folderi2 + ' does not exist. To do.', 2)
        else:
            log (folderi2 + ' does not exist. To do.', 1)

    #Cleanup based on startover mechanism
    if (clean):
#        log('CLEAN : ' + folderi2 + '/fingerprint.run', 0)
        if os.path.exists(folderi2 + '.run'):
            log(txtgreen + 'CLEAN due to lock : ' + folderi2 + txtnocolor, 0)
            os.remove(folderi2 + '.run')
            if os.path.exists(folderi2):
                shutil.rmtree(folderi2)
        if os.path.exists(folderi2):
            if os.path.exists(folderi2 + '/fingerprint.run'):
                log(txtgreen + 'CLEAN due to fingerprint.run : ' + folderi2 + txtnocolor, 0)
                shutil.rmtree(folderi2)
            elif not(os.path.exists(folderi2 + '/fingerprint.fp')):
                log(txtgreen + 'CLEAN due to fingerprint empty : ' + folderi2 + txtnocolor, 0)
                shutil.rmtree(folderi2)
            elif todo:
                log(txtgreen + 'CLEAN due to parameters: ' + folderi2 + txtnocolor, 0)
                shutil.rmtree(folderi2)
#    except:
#        todo = False
#        log(txtred + 'ERROR Onefile ' + txtnocolor + folderv, 0)
                    
    #Lock mechanism for startover procedure and parralel mode
    if todo:
        if not(parallel):
            if os.path.exists(folderi2 + '.run'):
                log('   --- Exist but .run flag so remove image folder', 0)
                if os.path.exists(folderi2): 
                    shutil.rmtree(folderi2)
                os.remove(folderi2 + '.run')
            log('set ' + folderi2 + '.run flag',2)
            f = open(folderi2 + '.run','w')
            f.write(pid + '\n')
            f.close
        if (parallel):
            if os.path.exists(folderi2 + '.run'):
                todo = False
                log('   --- .run flag for ' + folderv + file + ' Skip due to parallel mode ', 0)
            else:
                log('set ' + folderi2 + '.run flag',2)
                f = open(folderi2 + '.run','w')
                f.write(pid + '\n')
                f.close
                time.sleep(3)
                with open(folderi2 + '.run') as f:  
                    line = f.readline()
                    line = line[:-1]
                log (line + ' =? ' + pid, 4)
                if line != pid:
                    todo = False
                    log('   -------------------------------------------------------------------', 0)
                    log('   --- Concurent ffmpeg run detected !', 0)
                    log('   --- .run flag for ' + folderv + file + ' Skip due to parallel mode ', 0)
                    log('   -------------------------------------------------------------------', 0)
                
    # Execute
    ok = True
    if todo :
        if os.path.exists(folderi2):
            shutil.rmtree(folderi2)
        
        if not(clean):
            log ('Call ffmpeg with folderi = ' + folderi + ' file = ' + file, 2)

            if not(os.path.exists(folderi)):
                os.mkdir(folderi, mode=0o777)
            if not(os.path.exists(folderi + file + '/')): 
                os.mkdir(folderi + file + '/', mode=0o777)

            #Call ffmpeg
            log (txtgreen + s + txtnocolor, 0)
            t = time.time()
            p=subprocess.Popen(s, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()  
            #p_status = p.wait()
            dur = time.time() - t
            siz = os.path.getsize(fvideo)/1048576
            log(time.asctime(time.localtime(time.time())) + ' - Duration : ' + duration(dur) + ' for ' + str(round(siz,0)) + ' Mb ' + txtgreen + '@ ' + str(round(siz/dur*0.0864,2)) + ' Tb/day' + txtnocolor, 0)
            
            CreateFingerprint(folderi + file)
            
            #Create a file to store parameters
            f = open(folderi2 + '/param.txt','w')
            f.write('fps=1/' + str(fpsn) + '\n')
            f.close
                    
        if ok:
            os.remove(folderi2 + '.run')

#        except:
#            log('******************************************************************', 0)
#            log(txtred + 'ERROR: Try again later ' + folderi2 + txtnocolor, 0)
#            log('******************************************************************', 0)
#            log('', 0)
#            log('', 0)
#            log('', 0)
#            ok = False
        
    cptdone = cptdone + 1
    if clean:
        log(time.asctime(time.localtime(time.time())) + ' : ' + txtgreen + str(cptdone) + ' / ' + str(cpttodo) + ' done ...' + txtnocolor, 1)
    else:
        log(time.asctime(time.localtime(time.time())) + ' : ' + txtgreen + str(cptdone) + ' / ' + str(cpttodo) + ' done ...' + txtnocolor, 0)

# Parse a single folder to call OneFile for source video files and BoucleFichier recursively if it'a a subfolder
def BoucleFichiers(folderv='.', folderi='.', level=1):
    level = level + 1
    spacer = ''
    if debug>1: 
        for i in range(level): spacer=spacer+'  '
        log(spacer + '[ ' + folderv, 0)
    if os.path.isdir(folderv):
        if not(os.path.exists(folderi)):
            os.mkdir(folderi, mode=0o777)
        if folderv[-1] != "/": folderv = folderv + "/"
        if folderi[-1] != "/": folderi = folderi + "/"
        for file in os.listdir(folderv):
            ext = os.path.splitext(file)[1]
            if os.path.isdir(folderv+file):
                BoucleFichiers(folderv+file,folderi+file)
            elif (ext.upper() == '.MP4') or (ext.upper() == '.AVI') or (ext.upper() == '.MOV') or (ext.upper() == '.M4V') \
                or (ext.upper() == '.VOB') or (ext.upper() == '.MPG') or (ext.upper() == '.MPEG') or (ext.upper() == '.MKV') \
                or (ext.upper() == '.WMV') or (ext.upper() == '.ASF') or (ext.upper() == '.FLV') \
                or (ext.upper() == '.RM') or (ext.upper() == '.OGM') or (ext.upper() == '.M2TS') or (ext.upper() == '.RMVB'):
                OneFile(folderv,folderi,file)
            elif not(ext.upper() == '.JPG' or ext.upper() == '.TXT' or ext.upper() == '.TXT~'):
                log (spacer + '  Not match : ' + folderv + file, 0)
    else:
        log('folderv = ' + folderv, 0)
        OneFile(os.path.dirname(folderv)+"/",os.path.basename(folderv))
    if debug>1: 
        spacer = ''
        for i in range(level): spacer=spacer+'  '
        log (spacer + folderv +  ' ]', 0)
    level = level - 1

def helpprt():
    log('************************************************************************************', 0)
    log('Video DeDup : find video duplicates', 0)
    log('Copyright (C) 2018  Pierre Crette', 0)
    log('', 0)
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
    log('SYNTAX: 1parse folderSRC folderimg [-v] [-i] [-d] [-fnn] [-p]', copyright)
    log('-v=n   Verbose mode', copyright)
    log('-f=n fps: take 1 picture each n seconds. Default fps=1/60 ie 1 picture every 60 seconds.', copyright)
    log('-p   Parallel. Will not process if run flag is set', copyright)
    log('-c   Clean. Will not execute ffmpeg but will remove unfinished images: run.flag exist or incorrect fps.', copyright)
    log('-log=file   Log file', copyright)
    log('', copyright)
  

#main

#Step0: Read arguments and initialize variables
print ('')
#print (str(sys.argv))
flog = open(logfile,'w')
if len(sys.argv)<2:
    print('SYNTAX ERROR')
    helpprt
    sys.exit()
else:
    foldervideo = os.path.normpath(sys.argv[1])
    if foldervideo[-1] != "/": foldervideo = foldervideo + "/"
    if not(os.path.exists(foldervideo)):
        print(txtred + 'Error: ' + foldervideo + ' does not exists' + txtnocolor)
        sys.exit()

    folderimg = os.path.normpath(sys.argv[2])
    if folderimg[-1] != "/": folderimg = folderimg + "/"
    if not(os.path.exists(folderimg)):
        os.makedirs(folderimg)

#    s = '1parse.py ' + foldervideo + ' ' + folderimg
    for i in sys.argv[3:]:
#        s = s + ' ' + i
        if i[:3] == '-v=': debug = int(i[3:])
        if i[:3] == '-f=': fpsn = float(i[3:])
        if i[:2] == '-p': parallel = True
        if i[:2] == '-c': clean = True
        if i[:6] == '-moved': moved = True
#        if i[:5] == '-log=': logfile = i[5:]
        if i[:3] == '-nc': copyright = 12

    if not(os.path.exists('log')):
        os.makedirs('log')
    tmp = '/tmp/' + pid + '/'
    os.makedirs(tmp)

    helpprt
    log ('foldervideo : ' + foldervideo, 5)
    log ('folderimg : ' + folderimg, 5)
    log ('fps : ' + str(fpsn), 5)
    log ('nb args : ' + str(len(sys.argv)-1), 5)
    log ('abspath' + os.path.abspath(foldervideo + '..'), 5)
    log ('basename' + os.path.basename(foldervideo), 5)
    log ('dirname' + os.path.dirname(foldervideo), 5)
    log ('debug = ' + str(debug), 5)
    log ('clean = ' + str(clean), 5)
    log ('', 0)
    if (clean and parallel):
        log('SYNTAX ERROR : clean and parallel flag cannot be use on same time.', 0)
        exit()
    if clean:
        log(txtgreen + 'CLEAN MODE : ' + txtnocolor + 'Will remove unfinished work to start over. DO NOT launch other instances before it is finished.', 0)
    if parallel:
        log(txtgreen + 'PARALLEL MODE : ' + txtnocolor + 'You can use other instances on other terminals or other computer. NONE can be a Clean instance or you will have inconsistencies.', 0)
    
    #Step 1: Delete obsolete images
    log ('', 0)
    log ('************************************************************************************', 0)
    log (' ' + txtgreen + 'Step 1: ' + txtnocolor + 'Delete obsolete images for ' + foldervideo, 0)
    log ('************************************************************************************', 0)

    BoucleCount(foldervideo, folderimg, level)

    if not(parallel):
        BoucleSupp('')
    
    #Step 2: Create missing images
    log ('', 0)
    log ('************************************************************************************', 0)
    log (' ' + txtgreen + 'Step 2: ' + txtnocolor + 'Create missing images for ' + foldervideo, 0)
    log ('************************************************************************************', 0)

    BoucleFichiers(foldervideo, folderimg, level)
    
log('************************************************************************************', 0)
log('* 1parse ' + foldervideo + ' ' + folderimg + txtgreen + ' DONE: ' + str(cptdone) + ' / ' + str(cpttodo) + txtnocolor, 0)
log('************************************************************************************', 0)
log('', 0)
flog.close

