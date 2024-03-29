#!/usr/bin/python3
# Warning: works only on unix-like systems, not windows where "python animaAnatomicalRegisterImage.py ..." has to be run

import argparse
import os
import sys
from subprocess import call
import shutil

if sys.version_info[0] > 2:
    import configparser as ConfParser
else:
    import ConfigParser as ConfParser

configFilePath = os.path.join(os.path.expanduser("~"), ".anima",  "config.txt")
if not os.path.exists(configFilePath):
    print('Please create a configuration file for Anima python scripts. Refer to the README')
    quit()

configParser = ConfParser.RawConfigParser()
configParser.read(configFilePath)

animaDir = configParser.get("anima-scripts", 'anima')

# Argument parsing
parser = argparse.ArgumentParser(
    description="Runs the registration of an image onto a current reference (to be used from build anatomical atlas).")
parser.add_argument('-d', '--ref-dir', type=str, required=True, help='Reference (working) folder')
parser.add_argument('-r', '--ref-image', type=str, required=True, help='Reference image')
parser.add_argument('-B', '--prefix-base', type=str, required=True, help='Prefix base')
parser.add_argument('-p', '--prefix', type=str, required=True, help='Prefix')
parser.add_argument('-e', '--files-extension', type=str, required=True, help='Input files extension')
parser.add_argument('-b', '--bch-order', type=int, default=2, help='BCH order when composing transformations in rigid unbiased (default: 2)')
parser.add_argument('-n', '--num-image', type=int, required=True, help='Image number')
parser.add_argument('-c', '--num-cores', type=int, default=40, help='Number of cores to run on')
parser.add_argument('--rigid', action='store_true', help="Unbiased atlas up to a rigid transformation")

args = parser.parse_args()
os.chdir(args.ref_dir)
basePrefBase = os.path.dirname(args.prefix_base)

animaPyramidalBMRegistration = os.path.join(animaDir,"animaPyramidalBMRegistration")
animaDenseSVFBMRegistration = os.path.join(animaDir,"animaDenseSVFBMRegistration")
animaTransformSerieXmlGenerator = os.path.join(animaDir,"animaTransformSerieXmlGenerator")
animaLinearTransformArithmetic = os.path.join(animaDir,"animaLinearTransformArithmetic")
animaLinearTransformToSVF = os.path.join(animaDir,"animaLinearTransformToSVF")
animaDenseTransformArithmetic = os.path.join(animaDir,"animaDenseTransformArithmetic")

filesExtension = args.files_extension

# Rigid / affine registration
command = [animaPyramidalBMRegistration,"-r",args.ref_image,"-m",os.path.join(args.prefix_base,args.prefix + "_" + str(args.num_image) + filesExtension),
           "-o",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_aff.nrrd"),
           "-O",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_aff_tr.txt"),
           "--out-rigid",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_aff_nr_tr.txt"),
           "--ot","2","-p","3","-l","0","-I","2","-T",str(args.num_cores),"--sym-reg","2"]
call(command)

# Non-Rigid registration

# For basic atlases
command = [animaDenseSVFBMRegistration,"-r",args.ref_image,"-m",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_aff.nrrd"),
           "-o",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_bal.nrrd"),
           "-O",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_bal_tr.nrrd"),
           "--tub","2","--es","3","--fs","2","-T",str(args.num_cores),"--sym-reg","2","--metric","1"]
call(command)

if args.rigid is True:
    shutil.move(os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_aff_nr_tr.txt"),
                os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_linear_tr.txt"))

    command = [animaLinearTransformArithmetic,"-i",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_linear_tr.txt"),
               "-M","-1","-c",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_aff_tr.txt"),
               "-o",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_linearaddon_tr.txt")]
    call(command)

    command = [animaLinearTransformToSVF,"-i",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_linearaddon_tr.txt"),
               "-o",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_linearaddon_tr.nrrd"),
               "-g",args.ref_image]
    call(command)

    command = [animaDenseTransformArithmetic,"-i",os.path.join(basePrefBase, "tempDir", args.prefix + "_" + str(args.num_image) + "_linearaddon_tr.nrrd"),
               "-c",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_bal_tr.nrrd"),
               "-b",str(args.bch_order),
               "-o",os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_nonlinear_tr.nrrd")]
    call(command)
else:
    shutil.move(os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_aff_tr.txt"),
                os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_linear_tr.txt"))
    shutil.move(os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_bal_tr.nrrd"),
                os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_nonlinear_tr.nrrd"))

if os.path.exists(os.path.join(os.getcwd(), "residualDir", args.prefix + "_" + str(args.num_image) + "_nonlinear_tr.nrrd")):
    os.remove(os.path.join(os.getcwd(), "residualDir", args.prefix + "_" + str(args.num_image) + "_nonlinear_tr.nrrd"))

os.symlink(os.path.join(os.getcwd(),"tempDir",args.prefix + "_" + str(args.num_image) + "_linear_tr.txt"),
           os.path.join(os.getcwd(), "residualDir", args.prefix + "_" + str(args.num_image) + "_linear_tr.txt"))

os.symlink(os.path.join(os.getcwd(),"tempDir",args.prefix + "_" + str(args.num_image) + "_nonlinear_tr.nrrd"),
           os.path.join(os.getcwd(), "residualDir", args.prefix + "_" + str(args.num_image) + "_nonlinear_tr.nrrd"))

if os.path.exists(os.path.join(os.getcwd(),"tempDir",args.prefix + "_" + str(args.num_image) + "_nonlinear_tr.nrrd")):
    open(os.path.join(basePrefBase,"residualDir",args.prefix + "_" + str(args.num_image) + "_flag"), 'a').close()

if os.path.exists(os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_bal_tr.nrrd")):
    os.remove(os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_bal_tr.nrrd"))

if os.path.exists(os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_linearaddon_tr.nrrd")):
    os.remove(os.path.join(basePrefBase,"tempDir",args.prefix + "_" + str(args.num_image) + "_linearaddon_tr.nrrd"))
