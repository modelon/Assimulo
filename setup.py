#!/usr/bin/env python 
# -*- coding: utf-8 -*-
from distutils.core import setup, Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize
import numpy as N
import logging as L
import sys as S
import os as O
import shutil as SH

#L.basicConfig(format='%(levelname)s:%(message)s')

incdirs = ''
libdirs = ''
SLUdir = ""
BLASdir = ""
BLASname = 'blas'
BLASname_t = ""
debug = False

if S.platform == 'win32':
    incdirs = ''
    libdirs = ''
elif S.platform == 'win64':
    incdirs = ''
    libdirs = ''
else:
    incdirs = '/usr/local/include'
    libdirs = '/usr/local/lib'
    


copy_args=S.argv[1:]

for x in S.argv[1:]:
    if not x.find('--sundials-home'):
        incdirs = O.path.join(x[16:],'include')
        libdirs = O.path.join(x[16:],'lib')
        copy_args.remove(x)
    if not x.find('--prefix'):
        copy_args[copy_args.index(x)] = x.replace('/',O.sep)
    if not x.find('--superlu-home'):
        SLUdir = x[15:]
        copy_args.remove(x)
    if not x.find('--blas-home'):
        BLASdir = x[12:]
        copy_args.remove(x)
    if not x.find('--blas-name'):
        BLASname_t = x[12:]
        copy_args.remove(x)
    if not x.find('--debug'):
        debug = x[8:]
        if x[8:].upper() == "TRUE":
            debug = True
        copy_args.remove(x)
    if not x.find('--log'):
        level = x[6:]
        try:
            num_level = getattr(L, level.upper())
        except AttributeError:
            L.warning("No log-level defined for: "+level)
            num_level = 30
        L.basicConfig(level=num_level)
        copy_args.remove(x)
        
def pre_processing():
    def create_dir(d):
        try:
            O.mkdir(d) #Create the build directory
        except:
            pass #Directory already exists
    create_dir(O.path.join("build"))
    create_dir(O.path.join("build","assimulo"))
    create_dir(O.path.join(O.path.join("build","assimulo"),"lib"))
    create_dir(O.path.join(O.path.join("build","assimulo"),"solvers"))
    create_dir(O.path.join(O.path.join("build","assimulo"),"examples"))
    
    fileSrc     = O.listdir("src")
    fileLib     = O.listdir(O.path.join("src","lib"))
    fileSolvers = O.listdir(O.path.join("src","solvers"))
    fileExamples= O.listdir("examples")
    
    curdir = O.path.dirname(O.path.abspath(__file__))
    
    desSrc = O.path.join(curdir,O.path.join("build","assimulo"))
    desLib = O.path.join(curdir,O.path.join(O.path.join("build","assimulo"),"lib"))
    desSolvers = O.path.join(curdir,O.path.join("build","assimulo"),"solvers")
    desExamples = O.path.join(curdir,O.path.join("build","assimulo"),"examples")

    for f in fileSrc:
        if not O.path.isdir(O.path.join("src",f)):
            SH.copy2(O.path.join("src",f), desSrc)
    for f in fileLib:
        if not O.path.isdir(O.path.join(O.path.join("src","lib"),f)):
            SH.copy2(O.path.join(O.path.join("src","lib"),f), desLib)
    for f in fileSolvers:
        if not O.path.isdir(O.path.join(O.path.join("src","solvers"),f)):
            SH.copy2(O.path.join(O.path.join("src","solvers"),f), desSolvers)
    for f in fileExamples:
        if not O.path.isdir(O.path.join("examples",f)):
            SH.copy2(O.path.join("examples",f), desExamples)

def check_extensions():
    
    #Cythonize main modules
    ext_list = cythonize(["assimulo"+O.path.sep+"*.pyx"], include_path=[".","assimulo"],include_dirs=[N.get_include()],pyrex_gdb=debug)
    
    #Cythonize Euler
    ext_list = ext_list + cythonize(["assimulo"+O.path.sep+"solvers"+O.path.sep+"euler.pyx"], include_path=[".","assimulo"],include_dirs=[N.get_include()],pyrex_gdb=debug)
    
    for i in ext_list:
        i.include_dirs = [N.get_include()]
        
        #Debug
        if debug:
            i.extra_compile_args = ["-g","-fno-strict-aliasing"]
            i.extra_link_args = ["-g"]
        else:
            i.extra_compile_args = ["-O2", "-fno-strict-aliasing"]
            
    #If Sundials
    if O.path.exists(O.path.join(O.path.join(incdirs,'cvodes'), 'cvodes.h')):
        ext_list = ext_list + cythonize(["assimulo"+O.path.sep+"solvers"+O.path.sep+"sundials.pyx"], include_path=[".","assimulo","assimulo"+O.sep+"lib"],include_dirs=[N.get_include()],pyrex_gdb=debug)
        ext_list[-1].include_dirs = [N.get_include(), "assimulo","assimulo"+O.sep+"lib", incdirs]
        ext_list[-1].library_dirs = [libdirs]
        ext_list[-1].extra_link_args = ["-lsundials_cvodes", "-lsundials_nvecserial", "-lsundials_idas"]
        if debug:
            ext_list[-1].extra_compile_args = ["-g", "-fno-strict-aliasing"]
        else:
            ext_list[-1].extra_compile_args = ["-O2", "-fno-strict-aliasing"]
    
    #Sundials found
    if O.path.exists(O.path.join(O.path.join(incdirs,'cvodes'), 'cvodes.h')):
        cordir = O.path.join(O.path.join('assimulo','lib'),'sundials_core.pyx')
        cordir_KINSOL_wSLU = O.path.join(O.path.join('assimulo','lib'),'sundials_kinsol_core_wSLU.pyx')
        cordir_KINSOL = O.path.join(O.path.join('assimulo','lib'),'sundials_kinsol_core.pyx')
    
        cordir_KINSOL_jmod_wSLU = O.path.join(O.path.join('assimulo','lib'),'kinsol_jmod_wSLU.c')
        cordir_KINSOL_jmod = O.path.join(O.path.join('assimulo','lib'),'kinsol_jmod.c')
    
        cordir_kinpinv = O.path.join(O.path.join('assimulo','lib'),'kinpinv.c')
        cordir_kinslug = O.path.join(O.path.join('assimulo','lib'),'kinslug.c')
        cordir_reg_routines = O.path.join(O.path.join('assimulo','lib'),'reg_routines.c')

        
        wSLU = check_wSLU()
        if wSLU:
            ext_list = ext_list + [Extension('assimulo.lib.sundials_kinsol_core_wSLU',
                          [cordir_KINSOL_wSLU,cordir_KINSOL_jmod_wSLU,cordir_kinpinv,cordir_kinslug,cordir_reg_routines],
                          include_dirs=[incdirs, N.get_include(),SLUincdir],
                          library_dirs=[libdirs,SLUlibdir,BLASdir],
                          libraries=['sundials_kinsol','sundials_nvecserial','superlu_4.1',BLASname])]
        else:
            ext_list = ext_list + [Extension('assimulo.lib.sundials_kinsol_core',
                          [cordir_KINSOL,cordir_KINSOL_jmod,cordir_kinpinv],
                          include_dirs=[incdirs, N.get_include()],
                          library_dirs=[libdirs],
                          libraries=['sundials_kinsol','sundials_nvecserial'])]
        
    return ext_list

def check_wSLU():
    wSLU = True
    
    global BLASname, BLASname_t
    
    if SLUdir != "":    
        SLUincdir = O.path.join(SLUdir,'SRC')
        SLUlibdir = O.path.join(SLUdir,'lib')
        if not O.path.exists(O.path.join(SLUincdir,'supermatrix.h')):
            wSLU = False
            L.warning("Could not find SuperLU, disabling support. View more information using --log=DEBUG")
            L.debug("Could not find SuperLU at the given path.")
            L.debug("usage: --superlu-home=path")
            L.debug("KINSOL will not be compiled with support for SUperLU.")
            
        L.debug("SLUinc: "+SLUincdir)
        L.debug("SLUlib: "+SLUlibdir)

    else:
        L.warning("No path to SuperLU supplied, disabling support. View more information using --log=DEBUG")
        L.debug("No path to SuperLU supplied, KINSOL will not be compiled with support for SUperLU.")
        L.debug("usage: --superlu-home=path")
        L.debug("Note: the path required is to the folder where the folders 'SRC' and 'lib' are found.")
        wSLU = False
        
    if BLASname_t != "":
        if BLASname_t.startswith("lib"):
            BLASname = BLASname_t[3:]
        else:
            BLASname = BLASname_t
            BLASname_t = "lib"+BLASname_t
    else:
        BLASname_t = "lib" + BLASname
           
    if BLASdir == "":
        L.warning("No path to BLAS supplied, disabling support. View more information using --log=DEBUG")
        L.debug("No path to BLAS supplied, KINSOL will not be compiled with support for SUperLU.")
        L.debug("usage: --blas-home=path")
        L.debug("Note: the path required is to where the static library lib"+BLASname+" is found")
        wSLU = False
    else:
        if not O.path.exists(O.path.join(BLASdir,BLASname_t+'.a')):
            L.warning("Could not find BLAS, disabling support. View more information using --log=DEBUG")
            L.debug("Could not find BLAS at the given path.")
            L.debug("usage: --blas-home=path")
            L.debug("KINSOL will not be compiled with support for SUperLU.")
            wSLU = False
            
        L.debug("BLAS: "+BLASdir+"/"+BLASname_t)
    
    return wSLU

pre_processing()
O.chdir("build") #Change dir
      
ext_list = check_extensions()
      
setup(name='Assimulo',
      version='trunk',
      description='A package for solving ordinary differential equations and differential algebraic equations.',
      author='Claus Führer and Christian Andersson',
      author_email='claus@maths.lth.se chria@kth.se',
      url='http://wwww.jmodelica.org/assimulo',
      package_dir = {'assimulo':'assimulo'},
      packages=['assimulo', 'assimulo.lib','assimulo.solvers','assimulo.examples'],
      cmdclass = {'build_ext': build_ext},
      ext_modules = ext_list,
      script_args=copy_args)

O.chdir("..") #Change back to dir
