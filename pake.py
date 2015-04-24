#!/usr/bin/env python2
# encoding: utf-8
# Thomas Nagy, 2005-2010; Arne Babenhauserheide

"""Waffle iron - creates waffles :)

- http://draketo.de/proj/waffles/

TODO: Differenciate sourcetree and packages: sourcetree as dir in wafdir, packages in subdir packages. 
"""

__license__ = """
This license only applies to the waffle part of the code,
which ends with
### Waffle Finished ###

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

3. The name of the author may not be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

import os, sys, optparse, getpass, re, binascii
if sys.hexversion<0x204000f: raise ImportError("Waffle requires Python >= 2.4")
try:
	from hashlib import md5
except:
	from md5 import md5 # for python < 2.5

if 'PSYCOWAF' in os.environ:
	try:import psyco;psyco.full()
	except:pass

VERSION="0.1"
REVISION="a7cd1977effc8779a75a4f6863dcac31"
INSTALL=''
cwd = os.getcwd()
join = os.path.join
HOME = os.path.expanduser('~')

WAF='waffle' #: the default name of the executable
WAFFLE='waffle' #: the default name of the dir with the sources (prepended with s when unpacked)
WAFFLE_MAKER='waffle_maker.py'

def parse_cmdline_args():
	"""@return: opts, args; opts are parsed"""
	# parse commandline arguments.
	parser = optparse.OptionParser()
	parser.add_option("-o", "--filename", 
			  help="Set the output filename", default="waffle.py", metavar="OUTPUT_FILE")
	parser.add_option("-p", "--package", action="append", dest="packages",
		  help="Package folder to include (can be used multiple times)", metavar="PACKAGE_FOLDER")
	parser.add_option("-m", "--module", action="append", dest="modules", 
			  help="Python module to include (can be used multiple times)", metavar="module_to_include.py")
	parser.add_option("-s", "--script", 
			  help="Execute this script", default="run.py", metavar="script_to_run.py")
	parser.add_option("--unpack-only", action="store_true", 
			  help="only unpack the tar.bz2 data, but don't execute anything.", default=False)
	opts, args = parser.parse_args()
	if opts.modules is None:
		opts.modules = []
	if opts.packages is None:
		opts.packages = []
			      
	return opts, args

def b(x):
	return x

if sys.hexversion>0x300000f:
	WAF='waffle3'
	def b(x):
		return x.encode()

def err(m):
	print(('\033[91mError: %s\033[0m' % m))
	sys.exit(1)

def get_waffle_data():
	f = open(sys.argv[0],'r')
	c = "corrupted waf (%d)"
	while True:
		line = f.readline()
		if not line: err("no data")
		if line.startswith('#==>'):
			txt = f.readline()
			if not txt: err("wrong data: data-line missing")
			if not f.readline().startswith('#<=='): err("wrong data: closing line missing")
			return txt

def unpack_wafdir(txt, zip_type="bz2"):
	"""@param txt: The compressed data"""
	if not txt: err(c % 3)
	if sys.hexversion>0x300000f:
		txt = binascii.a2b_base64(eval("b'" + txt[1:-1] + r"\n'"))
	else: 
		txt = binascii.a2b_base64(txt[1:])

	# select the target folder
	import shutil, tarfile

	s = '.%s-%s-%s'
	if sys.platform == 'win32': s = s[1:]

	## Firstoff we we select some possible folders, to be tested one after the other (with the appropriate precautions).
	## For the sake of readability we first note the different options here.
	#: The home folder as the best option (if the user has a writeable home)
	dirhome = join(HOME, s % (WAF, VERSION, REVISION))
	# the scripts dir
	name = sys.argv[0]
	base = os.path.dirname(os.path.abspath(name))
	#: As second option use the folder where the script resides (if writeable by us - and not yet taken, which could be, if another user started the script). 
	dirbase = join(base, s % (WAF, VERSION, REVISION), getpass.getuser())
	#: tmp as last resort
	dirtmp = join("/tmp", getpass.getuser(), "%s-%s-%s" % (WAF, VERSION, REVISION))

	def prepare_dir(d):
		"""create the needed folder"""
		os.makedirs(join(d, WAFFLE))

	def check_base(d):
		"""Check the dir in which the script resides.

		Only use the dir, if it belongs to us. If we can’t trust the scripts dir, we’re fragged anyway (someone could just tamper directly with the script itself - or rather: could compromise anything we run)."""
		prepare_dir(d)
		return d

	def check_tmp(d):
		"""Check the tmp dir - always remove the dir before startup.

		This kills the caching advantage, but is necessary for security reasons (else someone could create a compromised dir in tmp and chmod it to us)."""
		# last resort: tmp
		if os.path.exists(d):
			try: shutil.rmtree(d)
			except OSError: err("Can't remove the previously existing version in /tmp - executing would endanger your system")
			try: 
				prepare_dir(d)
				return d
			except OSError: err("Cannot unpack waf lib into %s\nMove waf into a writeable directory" % dir)

	## Now check them. 
	# first check: home
	try:
		d = dirhome
		prepare_dir(d)
	except OSError:
		# second check: base
		if base.startswith(HOME) or sys.platform == 'win32':
			try:
				d = check_base(dirbase)
			except OSError:
				d = check_tmp(dirtmp)
		else: d = check_tmp(dirtmp)

	## Now unpack the tar.bz2 stream into the chosen dir. 
	os.chdir(d)
	if zip_type == 'bz2': 
		tmp = 't.tbz2'
	elif zip_type == 'gz':
		tmp = 't.gz'
	t = open(tmp,'wb')
	t.write(txt)
	t.close()

	try:
		t = tarfile.open(tmp)
	# watch out for python versions without bzip2
	except:
		try: 
			os.system('bunzip2 t.bz2')
			t = tarfile.open('t')
		except:
			# if it doesn’t work, go back and remove the garbage we created.
			try: 
				os.unlink(tmp)
			except OSError: pass
			os.chdir(cwd)
			try: shutil.rmtree(d)
			except OSError: pass
			err("Waf cannot be unpacked, check that bzip2 support is present")

	for x in t:
		t.extract(x)
	t.close()
	os.unlink(tmp)


	#if sys.hexversion>0x300000f:
		#sys.path = [join(d, WAFFLE)] + sys.path
		#import py3kfixes
		#py3kfixes.fixdir(d)

	os.chdir(cwd)
	return join(d, WAFFLE)


def make_waffle(base_script="waffle_maker.py", packages=[], modules=[], folder=WAFFLE, executable="run.py", target="waffle.py", zip_type="bz2"):
	"""Create a waf-like waffle from the base_script (make_waffle.py), the folder and a python executable (appended to the end of the waf-light part)."""
	print("-> preparing waffle")
	mw = 'tmp-waf-'+VERSION

	import tarfile, re, shutil

	if zip_type not in ['bz2', 'gz']:
		zip_type = 'bz2'

	# copy all modules and packages into the build folder
	if not os.path.isdir(folder):
		os.makedirs(folder)
	
	for i in modules + packages:
		if i.endswith(os.path.sep): 
			i = i[:-1]
		if os.path.isdir(i) and not os.path.isdir(join(folder, i.split(os.path.sep)[-1])):
			shutil.copytree(i, join(folder, i.split(os.path.sep)[-1]))
		elif os.path.isfile(i): 
			shutil.copy(i, folder)

	#open a file as tar.[extension] for writing
	tar = tarfile.open('%s.tar.%s' % (mw, zip_type), "w:%s" % zip_type)
	tarFiles=[]

	def all_files_in(folder): 
		"""Get all paths of files inside the folder."""
		filepaths = []
		walked = [i for i in os.walk(folder)]
		for base, dirs, files in walked:
		    filepaths.extend([os.path.join(base, f) for f in files])
		return filepaths
		
	files = [f for f in all_files_in(folder) if not f.endswith(".pyc") and not f.endswith(".pyo") and not "/." in f]

	for x in files:
		tar.add(x)
	tar.close()

	# first get the basic script which sets up the path
	f = open(base_script, 'r')
	code1 = f.read()
	f.close()
	# make sure it doesn't do anything.
	code1.replace("__name__ == '__main__':", "__name__ == '__main__' and False:")
	# then append the code from the executable 
	if executable is not None:
		f = open(executable, 'r')
		code1 += f.read()
		f.close()

	# now store the revision unique number in waf
	#compute_revision()
	#reg = re.compile('^REVISION=(.*)', re.M)
	#code1 = reg.sub(r'REVISION="%s"' % REVISION, code1)

	prefix = ''
	#if Build.bld:
	#	prefix = Build.bld.env['PREFIX'] or ''

	reg = re.compile('^INSTALL=(.*)', re.M)
	code1 = reg.sub(r'INSTALL=%r' % prefix, code1)
	#change the tarfile extension in the waf script
	reg = re.compile('bz2', re.M)
	code1 = reg.sub(zip_type, code1)

	f = open('%s.tar.%s' % (mw, zip_type), 'rb')
	cnt = f.read()
	f.close()

	# the REVISION value is the md5 sum of the binary blob (facilitate audits)
	m = md5()
	m.update(cnt)
	REVISION = m.hexdigest()
	reg = re.compile('^REVISION=(.*)', re.M)
	code1 = reg.sub(r'REVISION="%s"' % REVISION, code1)
	f = open(target, 'w')
	f.write(code1)
	f.write('#==>\n')
	data = str(binascii.b2a_base64(cnt))
	if sys.hexversion>0x300000f:
		data = data[2:-3] + '\n'
	f.write("#"+data)
	f.write('#<==\n')
	f.close()

	# on windows we want a bat file for starting.
	if sys.platform == 'win32':
		f = open(target + '.bat', 'wb')
		f.write('@python -x %~dp0'+target+' %* & exit /b\n')
		f.close()

	# Now make the script executable
	if sys.platform != 'win32':
		# octal prefix changed in 3.x from 0xxx to 0oxxx. 
		if sys.hexversion>0x300000f:
			os.chmod(target, eval("0o755"))
		else:
			os.chmod(target, eval("0755"))

	# and get rid of the temporary files
	os.unlink('%s.tar.%s' % (mw, zip_type))
	shutil.rmtree(WAFFLE)
	

def test(d):
	try: 
	      os.stat(d)
	      return os.path.abspath(d)
	except OSError: pass

def find_lib():
	"""Find the folder with the modules and packages.

	@return: path to to folder."""
	name = sys.argv[0]
	base = os.path.dirname(os.path.abspath(name))

	#devs use $WAFDIR
	w=test(os.environ.get('WAFDIR', ''))
	if w: return w

	#waffle_maker.py is executed in place.
	if name.endswith(WAFFLE_MAKER):
		w = test(join(base, WAFFLE))
		# if we don’t yet have a waffle dir, just create it.
		if not w:
			os.makedirs(join(base, WAFFLE))
			w = test(join(base, WAFFLE))
		if w: return w
		err("waffle.py requires " + WAFFLE + " -> export WAFDIR=/folder")

	d = "/lib/%s-%s-%s/" % (WAF, VERSION, REVISION)
	for i in [INSTALL,'/usr','/usr/local','/opt']:
		w = test(i+d)
		if w: return w

	# first check if we can use HOME/s,
	# if not, check for s (allowed?)
	# then for /tmp/s (delete it, if it already exists,
	# else it could be used to smuggle in malicious code)
	# and finally give up. 
	
	#waf-local
	s = '.%s-%s-%s'
	if sys.platform == 'win32': s = s[1:]
	# in home
	d = join(HOME, s % (WAF, VERSION, REVISION), WAFFLE)
	w = test(d)
	if w: return w

	# in base
	if base.startswith(HOME):
		d = join(base, s % (WAF, VERSION, REVISION), WAFFLE)
		w = test(d)
		if w: return w
	# if we get here, we didn't find it.
	return None


wafdir = find_lib()
if wafdir is None: # no existing found
	txt = get_waffle_data() # from this file
	if txt is None and __name__ == "__main__": # no waffle data in file
		opts, args = parse_cmdline_args()
		make_waffle(packages=opts.packages, modules=opts.modules, executable=opts.script)
	else: 
		wafdir = unpack_wafdir(txt)
	
elif sys.argv[0].endswith(WAFFLE_MAKER) and __name__ == "__main__": # the build script called
	opts, args = parse_cmdline_args()
	if opts.filename.endswith(WAFFLE_MAKER):
		err("Creating a script whose name ends with " + WAFFLE_MAKER + " would confuse the build script. If you really want to name your script *" + WAFFLE_MAKER + " you need to adapt the WAFFLE_MAKER constant in " + WAFFLE_MAKER + " and rename " + WAFFLE_MAKER + " to that name.")
	make_waffle(packages=opts.packages, modules=opts.modules, executable=opts.script, target=opts.filename)
	# since we’re running the waffle_maker, we can stop here. 
	exit(0)

if wafdir is not None: 
	sys.path = [wafdir] + [join(wafdir, d) for d in os.listdir(wafdir)] + sys.path


## If called with --unpack-only, no further code is executed.
if "--unpack-only" in sys.argv:
	print(sys.argv[0], "unpacked to", wafdir)
	exit(0)

### Waffle Finished ###

#!/usr/bin/env python

import fsutils
import ui
import targets
import variables
import configurations
import pake.parser
import command_line


def parse_source_tree():
    for filename in fsutils.pake_files:
        pake.parser.parse(filename)

    configuration = configurations.get_selected_configuration()
    variables.export_special_variables(configuration)


def _build_some_targets_if_requested():
    if command_line.args.target:
        for target in command_line.args.target:
            targets.build(target)
        return True
    elif command_line.args.all:
        targets.build_all()
        return True


def main():
    parse_source_tree()

    configuration = configurations.get_selected_configuration()
    if configuration.name != "__default":
        ui.bigstep("configuration", str(configurations.get_selected_configuration()))

    if not _build_some_targets_if_requested():
        ui.info("no target selected\n")

        ui.info(ui.BOLD + "targets:" + ui.RESET)
        for target in targets.targets.values():
            ui.info("  " + str(target))

        ui.info(ui.BOLD + "\nconfigurations:" + ui.RESET)
        for configuration in configurations.configurations:
            ui.info("  " + str(configuration))

        ui.info("\nsee --help for more\n")

if __name__ == '__main__':
    main()
#==>
#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
#<==
