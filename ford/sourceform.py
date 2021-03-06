#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  sourceform.py
#  
#  Copyright 2014 Christopher MacMackin <cmacmackin@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

from __future__ import print_function

import sys
import re
import os.path
import copy
#Python 2 or 3:
if (sys.version_info[0]>2):
    from urllib.parse import quote
else:
    from urllib import quote

import toposort
from pygments import highlight
from pygments.lexers import FortranLexer
from pygments.formatters import HtmlFormatter

import ford.reader
import ford.utils

VAR_TYPE_STRING = "^integer|real|double\s*precision|character|complex|logical|type|class|procedure"
VARKIND_RE = re.compile("\((.*)\)|\*\s*(\d+|\(.*\))")
KIND_RE = re.compile("kind\s*=\s*",re.IGNORECASE)
LEN_RE = re.compile("len\s*=\s*",re.IGNORECASE)
ATTRIBSPLIT_RE = re.compile(",\s*(\w.*?)::\s*(.*)\s*")
ATTRIBSPLIT2_RE = re.compile("\s*(::)?\s*(.*)\s*")
ASSIGN_RE = re.compile("(\w+\s*(?:\([^=]*\)))\s*=(?!>)(?:\s*([^\s]+))?")
POINT_RE = re.compile("(\w+\s*(?:\([^=>]*\)))\s*=>(?:\s*([^\s]+))?")
EXTENDS_RE = re.compile("extends\s*\(\s*([^()\s]+)\s*\)")
DOUBLE_PREC_RE = re.compile("double\s+precision",re.IGNORECASE)
QUOTES_RE = re.compile("\"([^\"]|\"\")*\"|'([^']|'')*'",re.IGNORECASE)
PARA_CAPTURE_RE = re.compile("<p>.*?</p>",re.IGNORECASE|re.DOTALL)
COMMA_RE = re.compile(",(?!\s)")
NBSP_RE = re.compile(" (?= )|(?<= ) ")
DIM_RE = re.compile("^\w+\s*(\(.*\))\s*$")

INTRINSICS = ['abort','abs','abstract','access','achar','acos','acosh','adjustl',
              'adjustr','aimag','aint','alarm','all','allocatable','allocate',
              'allocated','and','anint','any','asin','asinh','assign','associate',
              'associated','asynchronous','atan','atan2','atanh','atomic_add',
              'atomic_and','atomic_cas','atomic_define','atomic_fetch_add',
              'atomic_fetch_and','atomic_fetch_or','atomic_fetch_xor','atomic_or',
              'atomic_ref','atomic_xor','backtrace','backspace','bessel_j0',
              'bessel_j1','bessel_jn','bessel_y0','bessel_y1','bessel_yn','bge',
              'bgt','bind','bit_size','ble','block','block data','blt','btest',
              'c_associated','c_f_pointer','c_f_procpointer','c_funloc','c_loc',
              'c_sizeof','cabs','call','case','case default','cdabs','ceiling',
              'char','character','chdir','chmod','class','close','cmplx',
              'codimension','co_broadcast','co_max','co_min','co_reduce','co_sum',
              'command_argument_count','common','compiler_options',
              'compiler_version','complex','conjg','contains','contiguous',
              'continue','cos','cosh','count','cpu_time','critical','cshift',
              'cycle','data','ctime','dabs','date_and_time','dble','dcmplx',
              'deallocate','deferred','digits','dim','dimension','do',
              'do concurrent','do while','dlog','dlog10','dmax1','dmin1',
              'dot_product','double precision','dprod','dreal','dshiftl','dshiftr',
              'dsqrt','dtime','elemental','else','else if','elseif','elsewhere',
              'end','end associate','end block','end block data','end critical',
              'end do','end enum','end forall','end function','end if',
              'end interface','end module','end program','end select',
              'end submodule','end subroutine','end type','end where','endfile',
              'endif','entry','enum','enumerator','eoshift','epsilon',
              'equivalence','erf','erfc','erfc_scaled','etime','error stop',
              'execute_command_line','exit','exp','exponent','extends',
              'extends_type_of','external','fget','fgetc','final','findloc',
              'fdate','floor','flush','fnum','forall','format','fput','fputc',
              'fraction','function','free','fseek','fstat','ftell','gamma',
              'generic','gerror','getarg','get_command','get_command_argument',
              'getcwd','getenv','get_environment_variable','go to','goto','getgid',
              'getlog','getpid','getuid','gmtime','hostnm','huge','hypot','iabs',
              'iachar','iall','iand','iany','iargc','ibclr','ibits','ibset','ichar',
              'idate','ieee_class','ieee_copy_sign','ieee_get_flag',
              'ieee_get_halting_mode','ieee_get_rounding_mode','ieee_get_status',
              'ieee_get_underflow_mode','ieee_is_finite','ieee_is_nan',
              'ieee_is_negative','ieee_is_normal','ieee_logb','ieee_next_after',
              'ieee_rem','ieee_rint','ieee_scalb','ieee_selected_real_kind',
              'ieee_set_flag','ieee_set_halting_mode','ieee_set_rounding_mode',
              'ieee_set_status','ieee_support_datatype','ieee_support_denormal',
              'ieee_support_divide','ieee_support_flag','ieee_support_halting',
              'ieee_support_inf','ieee_support_io','ieee_support_nan',
              'ieee_support_rounding','ieee_support_sqrt','ieee_support_standard',
              'ieee_support_underflow_control','ieee_unordered','ieee_value',
              'ieor','ierrno','if','imag','image_index','implicit',
              'implicit none','import','include','index','inquire','int','integer',
              'intent','interface','intrinsic','int2','int8','ior','iparity',
              'irand','is','is_contiguous','is_iostat_end','is_iostat_eor',
              'isatty','ishft','ishftc','isnan','itime','kill','kind','lbound',
              'lcobound','leadz','len','len_trim','lge','lgt','link','lle','llt',
              'lock','lnblnk','loc','log','log_gamma','log10','logical','long',
              'lshift','lstat','ltime','malloc','maskl','maskr','matmul','max',
              'max0','maxexponent','maxloc','maxval','mclock','mclock8','merge',
              'merge_bits','min','min0','minexponent','minloc','minval','mod',
              'module','module procedure','modulo','move_alloc','mvbits','namelist',
              'nearest','new_line','nint','non_overridable','none','nopass','norm2',
              'not','null','nullify','num_images','only','open','or','operator',
              'optional','pack','parameter','parity','pass','pause','pointer',
              'perror','popcnt','poppar','precision','present','print','private',
              'procedure','product','program','protected','public','pure','radix',
              'ran','rand','random_number','random_seed','range','rank','read',
              'real','recursive','rename','repeat','reshape','result','return',
              'rewind','rewrite','rrspacing','rshift','same_type_as','save',
              'scale','scan','secnds','second','select','select case','select type',
              'selected_char_kind','selected_int_kind','selected_real_kind',
              'sequence','set_exponent','shape','shifta','shiftl','shiftr','sign',
              'signal','sin','sinh','size','sizeof','sleep','spacing','spread',
              'sqrt','srand','stat','stop','storage_size','submodule','subroutine',
              'sum','sync all','sync images','sync memory','symlnk','system',
              'system_clock','tan','tanh','target','then','this_image','time',
              'time8','tiny','trailz','transfer','transpose','trim','ttynam',
              'type','type_as','ubound','ucobound','umask','unlock','unlink',
              'unpack','use','value','verify','volatile','wait','where','while',
              'write','xor','zabs']

base_url = ''

class FortranBase(object):
    """
    An object containing the data common to all of the classes used to represent
    Fortran data.
    """
    POINTS_TO_RE = re.compile("\s*=>\s*",re.IGNORECASE)
    SPLIT_RE = re.compile("\s*,\s*",re.IGNORECASE)
    SRC_CAPTURE_STR = r"^[ \t]*([\w(),*: \t]+?[ \t]+)?{0}([\w(),*: \t]+?)?[ \t]+{1}[ \t\n,(].*?end[ \t]*{0}[ \t]+{1}[ \t]*?(!.*?)?$"
    
    #~ this regex is not working for the LINK and DOUBLE_LINK types
    
    base_url = ''
    
    def __init__(self,source,first_line,parent=None,inherited_permission=None,
                 strings=[]):
        self.visible = False
        if (inherited_permission!=None):
            self.permission = inherited_permission.lower()
        else:
            self.permission = None
        self.strings = strings
        self.parent = parent
        if self.parent:
            self.parobj = self.parent.obj
            self.display = self.parent.display
            self.settings = self.parent.settings
        else:
            self.parobj = None
            self.display = None
            self.settings = None
        self.obj = type(self).__name__[7:].lower()
        if self.obj == 'subroutine' or self.obj == 'function' or self.obj == 'submoduleprocedure':
            self.obj = 'proc'
        self._initialize(first_line)
        del self.strings
        self.doc = []
        line = source.__next__()
        while line[0:2] == "!" + self.settings['docmark']:
            self.doc.append(line[2:])
            line = source.__next__()
        source.pass_back(line)
        self.hierarchy = []
        cur = self.parent
        while cur:
            self.hierarchy.append(cur)
            cur = cur.parent
        self.hierarchy.reverse()

    def get_dir(self):
        if ( type(self) in [FortranSubroutine,FortranFunction] and
             type(self.parent) is FortranInterface and 
             not self.parent.generic ):
            return 'interface'
        elif type(self) is FortranSubmodule:
            return 'module'
        elif ( type(self) in [FortranSourceFile,FortranProgram,FortranModule]
               or ( type(self) in [FortranType,FortranInterface,FortranFunction,
                                   FortranSubroutine, FortranSubmoduleProcedure]
                    and type(self.parent) in [FortranSourceFile,FortranProgram,
                                              FortranModule, FortranSubmodule] ) ):
            return self.obj
        else:
            return None
            
    def get_url(self):
        outstr = "{0}/{1}/{2}.html"
        loc = self.get_dir()
        if loc:
            return outstr.format(self.base_url,loc,quote(self.ident))
        elif isinstance(self,FortranBoundProcedure):
            return self.parent.get_url() + '#' + self.anchor
        else:
            return None
    
    @property
    def ident(self):
        if ( type(self) in [FortranSubroutine,FortranFunction] and
             type(self.parent) == FortranInterface and 
             not self.parent.generic ):
            return namelist.get_name(self.parent)
        else:
            return namelist.get_name(self)

    @property
    def anchor(self):
        return self.obj + '-' + quote(self.ident)
        
    def __str__(self):
        outstr = "<a href='{0}'>{1}</a>"
        url = self.get_url()
        if url:
            return outstr.format(url,self.name)
        elif self.name:
            return self.name
        else:
            return ''

    def __lt__(self,other):
        '''
        Compare two Fortran objects. Needed to make toposort work.
        '''
        return (self.ident < other.ident)
    
    def markdown(self,md,project):
        """
        Process the documentation with Markdown to produce HTML.
        """
        if len(self.doc) > 0:
            if len(self.doc) == 1 and ':' in self.doc[0]:
                words = self.doc[0].split(':')[0].strip()
                if words.lower() not in ['author','date','license','version','category','summary','deprecated','display','graph']:
                    self.doc.insert(0,'')
                self.doc.append('')
            self.doc = '\n'.join(self.doc)
            self.doc = md.convert(self.doc)
            self.meta = md.Meta
            md.reset()
        else:
            if self.settings['warn'].lower() == 'true' and self.obj != 'sourcefile':
                #TODO: Add ability to print line number where this item is in file
                print('Warning: Undocumented {} {} in file {}'.format(self.obj, self.name, self.hierarchy[0].name))
            self.doc = ""
            self.meta = {}

        if self.parent:
            self.display = self.parent.display

        for key in self.meta:
            if key == 'display':
                tmp = [ item.lower() for item in self.meta[key] ]
                if type(self) == FortranSourceFile:
                    while 'none' in tmp:
                        tmp.remove('none')
                
                if len(tmp) == 0:
                    pass
                elif 'none' in tmp:
                    self.display = []
                elif 'public' not in tmp and 'private' not in tmp and 'protected' not in tmp:
                    pass
                else:
                    self.display = tmp
            elif len(self.meta[key]) == 1:
                self.meta[key] = self.meta[key][0]
            elif key == 'summary':
                self.meta[key] = '\n'.join(self.meta[key])
            
        self.doc = ford.utils.sub_macros(ford.utils.sub_notes(self.doc),self.base_url)
    
        if 'summary' in self.meta:
            self.meta['summary'] = md.convert(self.meta['summary'])
            self.meta['summary'] = ford.utils.sub_macros(ford.utils.sub_notes(self.meta['summary']),self.base_url)
        elif PARA_CAPTURE_RE.search(self.doc):
            self.meta['summary'] = PARA_CAPTURE_RE.search(self.doc).group()
        if 'graph' not in self.meta:
            self.meta['graph'] = self.settings['graph']
        else:
            self.meta['graph'] = self.meta['graph'].lower()

        if self.obj == 'proc' or self.obj == 'type' or self.obj == 'program':
            if 'source' not in self.meta:
                self.meta['source'] = self.settings['source'].lower()
            else:
                self.meta['source'] = self.meta['source'].lower()
            if self.meta['source'] == 'true':
                if self.obj == 'proc':
                    obj = self.proctype.lower()
                else:
                    obj = self.obj
                regex = re.compile(self.SRC_CAPTURE_STR.format(obj,self.name), re.IGNORECASE|re.DOTALL|re.MULTILINE)
                match = regex.search(self.hierarchy[0].raw_src)
                if match:
                    self.src = highlight(match.group(),FortranLexer(),HtmlFormatter())
                else:
                    self.src = ''
                    if self.settings['warn'].lower() == 'true':
                        print('Warning: Could not extract source code for {} {} in file {}'.format(self.obj, self.name, self.hierarchy[0].name))
                
        def sort_items(items,args=False):
            if self.settings['sort'].lower() == 'src': return
            def alpha(i):
                return i.name
            def permission(i):
                if args:
                    if i.intent == 'in': return 'b'
                    if i.intent == 'inout': return 'c'
                    if i.intent == 'out': return 'd'
                    if i.intent == '': return 'e'
                if i.permission == 'public': return 'b'
                if i.permission == 'protected': return 'c'
                if i.permission == 'private': return 'd'
                return 'a'
            def permission_alpha(i):
                return permission(i) + '-' + i.name
            def itype(i):
                if i.obj == 'variable':
                    retstr = i.vartype
                    if retstr == 'class': retstr = 'type'
                    if i.kind: retstr = retstr + '-' + str(i.kind)
                    if i.strlen: retstr = retstr + '-' + str(i.strlen)
                    if i.proto:
                        retstr = retstr + '-' + i.proto[0]
                    return retstr
                elif i.obj == 'proc':
                    if i.proctype != 'Function':
                        return i.proctype.lower()
                    else:
                        return i.proctype.lower() + '-' + itype(i.retvar)
                else:
                    return i.obj
            def itype_alpha(i):
                return itype(i) + '-' + i.name
            
            if self.settings['sort'].lower() == 'alpha':
                items.sort(key=alpha)
            elif self.settings['sort'].lower() == 'permission':
                items.sort(key=permission)
            elif self.settings['sort'].lower() == 'permission-alpha':
                items.sort(key=permission_alpha)
            elif self.settings['sort'].lower() == 'type':
                items.sort(key=itype)
            elif self.settings['sort'].lower() == 'type-alpha':
                items.sort(key=itype_alpha)
        
        md_list = []
        if hasattr(self,'variables'):
            md_list.extend(self.variables)
            sort_items(self.variables)
        if hasattr(self,'types'):
            md_list.extend(self.types)
            sort_items(self.types)
        if hasattr(self,'modules'):
            md_list.extend(self.modules)
            sort_items(self.modules)
        if hasattr(self,'submodules'):
            md_list.extend(self.submodules)
            sort_items(self.submodules)
        if hasattr(self,'subroutines'):
            md_list.extend(self.subroutines)
            sort_items(self.subroutines)
        if hasattr(self,'modprocedures'):
            md_list.extend(self.modprocedures)
            sort_items(self.modprocedures)
        if hasattr(self,'functions'):
            md_list.extend(self.functions)
            sort_items(self.functions)
        if hasattr(self,'interfaces'):
            md_list.extend(self.interfaces)
            sort_items(self.interfaces)
        if hasattr(self,'absinterfaces'):
            md_list.extend(self.absinterfaces)
            sort_items(self.absinterfaces)
        if hasattr(self,'programs'):
            md_list.extend(self.programs)
            sort_items(self.programs)
        if hasattr(self,'boundprocs'):
            md_list.extend(self.boundprocs)
            sort_items(self.boundprocs)
        if hasattr(self,'args'):
            md_list.extend(self.args)
            #sort_items(self.args,args=True)
        if hasattr(self,'retvar') and self.retvar: md_list.append(self.retvar)
        if hasattr(self,'procedure'): md_list.append(self.procedure)
        
        for item in md_list:
            if isinstance(item, FortranBase): item.markdown(md,project)

        return
    
    
    def make_links(self,project):
        """
        Process intra-site links to documentation of other parts of the program.
        """
        self.doc = ford.utils.sub_links(self.doc,project)
        if 'summary' in self.meta:
            self.meta['summary'] = ford.utils.sub_links(self.meta['summary'],project)
        recurse_list = []
        
        if hasattr(self,'variables'): recurse_list.extend(self.variables)
        if hasattr(self,'types'): recurse_list.extend(self.types)
        if hasattr(self,'modules'): recurse_list.extend(self.modules)
        if hasattr(self,'submodules'): recurse_list.extend(self.submodules)
        if hasattr(self,'subroutines'): recurse_list.extend(self.subroutines)
        if hasattr(self,'functions'): recurse_list.extend(self.functions)
        if hasattr(self,'interfaces'): recurse_list.extend(self.interfaces)
        if hasattr(self,'absinterfaces'): recurse_list.extend(self.absinterfaces)
        if hasattr(self,'programs'): recurse_list.extend(self.programs)
        if hasattr(self,'boundprocs'): recurse_list.extend(self.boundprocs)
        # if hasattr(self,'finalprocs'): recurse_list.extend(self.finalprocs)
        # if hasattr(self,'constructor') and self.constructor: recurse_list.append(self.constructor)
        if hasattr(self,'args'): recurse_list.extend(self.args)
        if hasattr(self,'bindings'): recurse_list.extend(self.bindings)
        if hasattr(self,'retvar') and self.retvar: recurse_list.append(self.retvar)
        if hasattr(self,'procedure'): recurse_list.append(self.procedure)
        
        for item in recurse_list:
            if isinstance(item, FortranBase): item.make_links(project)


class FortranContainer(FortranBase):
    """
    A class on which any classes requiring further parsing are based.
    """
    ATTRIB_RE = re.compile("^(asynchronous|allocatable|bind\s*\(.*\)|data|dimension|external|intent\s*\(\s*\w+\s*\)|optional|parameter|pointer|private|protected|public|save|target|value|volatile)(?:\s+|\s*::\s*)((/|\(|\w).*?)\s*$",re.IGNORECASE)
    END_RE = re.compile("^end\s*(?:(module|submodule|subroutine|function|procedure|program|type|interface)(?:\s+(\w+))?)?$",re.IGNORECASE)
    MODPROC_RE = re.compile("^(module\s+)?procedure\s*(?:::|\s)\s*(\w.*)$",re.IGNORECASE)
    MODULE_RE = re.compile("^module(?:\s+(\w+))?$",re.IGNORECASE)
    SUBMODULE_RE = re.compile("^submodule\s*\(\s*(\w+)\s*(?::\s*(\w+))?\s*\)\s*(?:::|\s)\s*(\w+)$",re.IGNORECASE)
    PROGRAM_RE = re.compile("^program(?:\s+(\w+))?$",re.IGNORECASE)
    SUBROUTINE_RE = re.compile("^\s*(?:(.+?)\s+)?subroutine\s+(\w+)\s*(\([^()]*\))?(?:\s*bind\s*\(\s*(.*)\s*\))?$",re.IGNORECASE)
    FUNCTION_RE = re.compile("^(?:(.+?)\s+)?function\s+(\w+)\s*(\([^()]*\))?(?=(?:.*result\s*\(\s*(\w+)\s*\))?)(?=(?:.*bind\s*\(\s*(.*)\s*\))?).*$",re.IGNORECASE)
    TYPE_RE = re.compile("^type(?:\s+|\s*(,.*)?::\s*)((?!(?:is))\w+)\s*(\([^()]*\))?\s*$",re.IGNORECASE)
    INTERFACE_RE = re.compile("^(abstract\s+)?interface(?:\s+(\S.+))?$",re.IGNORECASE)
    #~ ABS_INTERFACE_RE = re.compile("^abstract\s+interface(?:\s+(\S.+))?$",re.IGNORECASE)
    BOUNDPROC_RE = re.compile("^(generic|procedure)\s*(\([^()]*\))?\s*(.*)\s*::\s*(\w.*)",re.IGNORECASE)
    FINAL_RE = re.compile("^final\s*::\s*(\w.*)",re.IGNORECASE)
    USE_RE = re.compile("^use(?:\s*,\s*(?:non_)?intrinsic\s*::\s*|\s+)(\w+)\s*($|,.*)",re.IGNORECASE)
    CALL_RE = re.compile("(?:^|(?<=[^a-zA-Z0-9_%]))\w+(?=\s*\(\s*(?:.*?)\s*\))",re.IGNORECASE)
    SUBCALL_RE = re.compile("^(?:if\s*\(.*\)\s*)?call\s+(\w+)\s*(?:\(\s*(.*?)\s*\))?$",re.IGNORECASE)
    SUBCALL_NOPAREN_RE = re.compile("^(?:if\s*\(.*\)\s*)?call\s+(\w+)\s*$",re.IGNORECASE)
    
    VARIABLE_STRING = "^(integer|real|double\s*precision|character|complex|logical|type(?!\s+is)|class(?!\s+is|\s+default)|procedure{})\s*((?:\(|\s\w|[:,*]).*)$"
    
    #TODO: Add the ability to recognize function calls
        
    def __init__(self,source,first_line,parent=None,inherited_permission=None,
                 strings=[]):
        
        if type(self) != FortranSourceFile:
            FortranBase.__init__(self,source,first_line,parent,inherited_permission,
                             strings)
        incontains = False
        if type(self) is FortranSubmodule:
            permission = "private"
        else:
            permission = "public"
        
        typestr = ''
        for vtype in self.settings['extra_vartypes']:
            typestr = typestr + '|' + vtype
        self.VARIABLE_RE = re.compile(self.VARIABLE_STRING.format(typestr),re.IGNORECASE)
        
        for line in source:
            if line[0:2] == "!" + self.settings['docmark']: 
                self.doc.append(line[2:])
                continue

            # Temporarily replace all strings to make the parsing simpler
            self.strings = []
            search_from = 0
            while QUOTES_RE.search(line[search_from:]):
                self.strings.append(QUOTES_RE.search(line[search_from:]).group())
                line = line[0:search_from] + QUOTES_RE.sub("\"{}\"".format(len(self.strings)-1),line[search_from:],count=1)
                search_from += QUOTES_RE.search(line[search_from:]).end(0)

            # Check the various possibilities for what is on this line
            if self.settings['lower'].lower() == 'true': line = line.lower()
            if line.lower() == "contains":
                if not incontains and type(self) in _can_have_contains:
                    incontains = True
                    if isinstance(self,FortranType): permission = "public"
                elif incontains:
                    raise Exception("Multiple CONTAINS statements present in scope")
                else:
                    raise Exception("CONTAINS statement in {}".format(type(self).__name__[7:].upper()))
            elif line.lower() == "public": permission = "public"
            elif line.lower() == "private": permission = "private"
            elif line.lower() == "protected": permission = "protected"
            elif line.lower() == "sequence":
                if type(self) == FortranType: self.sequence = True
            elif self.ATTRIB_RE.match(line):
                match = self.ATTRIB_RE.match(line)
                attr = match.group(1).lower().replace(" ", "")
                if len(attr) >= 4 and attr[0:4].lower() == 'bind':
                    attr = attr.replace(",",", ")
                if hasattr(self,'attr_dict'):
                    if attr == 'data':
                        pass
                    elif attr == 'external':
                        names = [decl.strip() for decl in ford.utils.paren_split(',',match.group(2))]
                        self.variables = [var for var in self.variables if var.name.lower() not in [name.lower() for name in names]]
                        self.externals.extend(names)
                    elif attr == 'dimension' or attr == 'allocatable' or attr == 'pointer':
                        names = ford.utils.paren_split(',',match.group(2))
                        for name in names:
                            name = name.strip().lower()
                            i = name.index('(')
                            n = name[:i]
                            sh = name[i:]
                            if n in self.attr_dict:
                                self.attr_dict[n].append(attr+sh)
                            else:
                                self.attr_dict[n] = [attr+sh]
                    else:
                        names = ford.utils.paren_split(',',match.group(2))
                        search_from = 0
                        while QUOTES_RE.search(attr[search_from:]):
                            num = int(QUOTES_RE.search(attr[search_from:]).group()[1:-1])
                            attr = attr[0:search_from] + QUOTES_RE.sub(self.strings[num],attr[search_from:],count=1)
                            search_from += QUOTES_RE.search(attr[search_from:]).end(0)
                        for name in names:
                            name = name.strip().lower()
                            if name in self.attr_dict:
                                self.attr_dict[name].append(attr)
                            else:
                                self.attr_dict[name] = [attr]
                else:
                    raise Exception("Found {} statement in {}".format(attr.upper(),type(self).__name__[7:].upper()))
            elif self.END_RE.match(line):
                if isinstance(self,FortranSourceFile):
                    raise Exception("END statement outside of any nesting")
                self._cleanup()
                return
            elif self.MODPROC_RE.match(line) and (self.MODPROC_RE.match(line).group(1) or type(self) is FortranInterface):
                if hasattr(self,'modprocs'):
                    # Module procedure in an INTERFACE
                    self.modprocs.extend(get_mod_procs(source,
                                         self.MODPROC_RE.match(line),self))
                elif hasattr(self,'modprocedures'):
                    # Module procedure implementing an interface in a SUBMODULE
                    self.modprocedures.append(FortranSubmoduleProcedure(source,
                                              self.MODPROC_RE.match(line),self,
                                              permission))
                else:
                    raise Exception("Found module procedure in {}".format(type(self).__name__[7:].upper()))
            elif self.MODULE_RE.match(line):
                if hasattr(self,'modules'):
                    self.modules.append(FortranModule(source,
                                        self.MODULE_RE.match(line),self))
                else:
                    raise Exception("Found MODULE in {}".format(type(self).__name__[7:].upper()))
            elif self.SUBMODULE_RE.match(line):
                if hasattr(self,'submodules'):
                    self.submodules.append(FortranSubmodule(source,
                                           self.SUBMODULE_RE.match(line),self))
                else:
                    raise Exception("Found SUBMODULE in {}".format(type(self).__name__[7:].upper()))
            elif self.PROGRAM_RE.match(line):
                if hasattr(self,'programs'):
                    self.programs.append(FortranProgram(source,
                                         self.PROGRAM_RE.match(line),self))
                else:
                    raise Exception("Found PROGRAM in {}".format(type(self).__name__[7:].upper()))
                if len(self.programs) > 1:
                    raise Exception("Multiple PROGRAM units in same source file.")
            elif self.SUBROUTINE_RE.match(line):
                if isinstance(self,FortranCodeUnit) and not incontains: continue
                if hasattr(self,'subroutines'):
                    self.subroutines.append(FortranSubroutine(source,
                                            self.SUBROUTINE_RE.match(line),self,
                                            permission))
                else:
                    raise Exception("Found SUBROUTINE in {}".format(type(self).__name__[7:].upper()))
            elif self.FUNCTION_RE.match(line):
                if isinstance(self,FortranCodeUnit) and not incontains: continue
                if hasattr(self,'functions'):
                    self.functions.append(FortranFunction(source,
                                          self.FUNCTION_RE.match(line),self,
                                          permission))
                else:
                    raise Exception("Found FUNCTION in {}".format(type(self).__name__[7:].upper()))
            elif self.TYPE_RE.match(line):
                if hasattr(self,'types'):
                    self.types.append(FortranType(source,self.TYPE_RE.match(line),
                                      self,permission))
                else:
                    raise Exception("Found derived TYPE in {}".format(type(self).__name__[7:].upper()))
            elif self.INTERFACE_RE.match(line):
                if hasattr(self,'interfaces'):
                    intr = FortranInterface(source,self.INTERFACE_RE.match(line),
                                            self,permission)
                    if intr.abstract:
                        self.absinterfaces.extend(intr.contents)
                    elif intr.generic:
                        self.interfaces.append(intr)
                    else:
                        self.interfaces.extend(intr.contents)
                else:
                    raise Exception("Found INTERFACE in {}".format(type(self).__name__[7:].upper()))
            elif self.BOUNDPROC_RE.match(line) and incontains:
                if hasattr(self,'boundprocs'):
                    match = self.BOUNDPROC_RE.match(line)
                    split = match.group(4).split(',')
                    split.reverse()
                    if match.group(1).lower() == 'generic' or len(split) == 1:
                        self.boundprocs.append(FortranBoundProcedure(source,
                                               self.BOUNDPROC_RE.match(line),self,
                                               permission))
                    else:
                        for bind in split:
                            pseudo_line = line[:match.start(4)] + bind
                            self.boundprocs.append(FortranBoundProcedure(source,
                                                   self.BOUNDPROC_RE.match(pseudo_line),
                                                   self,permission))
                else:
                    raise Exception("Found type-bound procedure in {}".format(type(self).__name__[7:].upper()))
            elif self.FINAL_RE.match(line) and incontains:
                if hasattr(self,'finalprocs'):
                    procedures = self.FINAL_RE.match(line).group(1).strip()
                    self.finalprocs.extend(self.SPLIT_RE.split(procedures))
                else:
                    raise Exception("Found finalization procedure in {}".format(type(self).__name__[7:].upper()))
            elif self.VARIABLE_RE.match(line):
                if hasattr(self,'variables'):
                    variables, externals = line_to_variables(source,line,permission,self)
                    if externals:
                        self.externals.extend(externals)
                    else:
                        self.variables.extend(variables)
                else:
                    raise Exception("Found variable in {}".format(type(self).__name__[7:].upper()))
            elif self.USE_RE.match(line):
                if hasattr(self,'uses'): 
                    self.uses.append(self.USE_RE.match(line).groups())
                else:
                    raise Exception("Found USE statemnt in {}".format(type(self).__name__[7:].upper()))
            elif self.SUBCALL_NOPAREN_RE.search(line):
                if hasattr(self,'calls'):
                    callvals = self.SUBCALL_NOPAREN_RE.findall(line)
                    for val in callvals:
                        if val.lower() not in self.calls and val.lower() not in INTRINSICS:
                            self.calls.append(val.lower())
                else:
                    raise Exception("Found procedure call in {}".format(type(self).__name__[7:].upper()))
            elif self.CALL_RE.search(line):
                if hasattr(self,'calls'):
                    callvals = self.CALL_RE.findall(line)
                    for val in callvals:
                        if val.lower() not in [var.name.lower() for var in self.variables] and val.lower() not in self.calls and val.lower() not in INTRINSICS:
                            self.calls.append(val.lower())
                else:
                    raise Exception("Found procedure call in {}".format(type(self).__name__[7:].upper()))
            elif self.CALL_RE.match(line):
                # Need this to catch any subroutines called without argument lists
                if hasattr(self,'calls'):
                    callval = self.CALL_RE.match(line).group(1)
                    if callval.lower() not in self.calls and callval.lower() not in INTRINSICS: 
                        self.calls.append(callval.lower())
                else:
                    raise ("Found procedure call in {}".format(type(self).__name__[7:].upper()))
            

        if not isinstance(self,FortranSourceFile):
            raise Exception("File ended while still nested.")
    
    def _cleanup(self):
        return
        
             
    
class FortranCodeUnit(FortranContainer):
    """
    A class on which programs, modules, functions, and subroutines are based.
    """
    def correlate(self,project):
        # Add procedures, interfaces and types from parent to our lists
        if hasattr(self.parent,'all_procs'): self.all_procs.update(self.parent.all_procs)
        self.all_absinterfaces = getattr(self.parent,'all_absinterfaces',{})
        for ai in self.absinterfaces:
            self.all_absinterfaces[ai.name.lower()] = ai
        self.all_types = getattr(self.parent,'all_types',{})
        for dt in self.types:
            self.all_types[dt.name] = dt
        self.all_vars = getattr(self.parent,'all_vars',{})
        # Remove those host-associated variables made inaccessible by local external functions
        for name in [external.lower() for external in self.externals if external.lower() in [var.lower() for var in self.all_vars]]:
            del self.all_vars[[var for var in self.all_vars if var.lower()==name][0]]
        for var in self.variables:
            self.all_vars[var.name] = var
        
        if type(getattr(self,'ancestor','')) not in [str, type(None)]:
            self.ancestor.descendants.append(self)
            self.all_procs.update(self.ancestor.all_procs)
            self.all_absinterfaces.update(self.ancestor.all_absinterfaces)
            self.all_types.update(self.ancestor.all_types)
        elif type(getattr(self,'ancestor_mod','')) not in [str, type(None)]:
            self.ancestor_mod.descendants.append(self)
            self.all_procs.update(self.ancestor_mod.all_procs)
            self.all_absinterfaces.update(self.ancestor_mod.all_absinterfaces)
            self.all_types.update(self.ancestor_mod.all_types)
        
        if isinstance(self,FortranSubmodule):
            for proc in self.functions + self.subroutines:
                if proc.module and proc.name.lower() in self.all_procs:
                    intr = self.all_procs[proc.name.lower()]
                    # FIXME: Don't think these logical tests are necessary anymore
                    if intr.proctype.lower() == 'interface' and not intr.generic and not intr.abstract and intr.procedure.module == True:
                        proc.module = intr
                        intr.procedure.module = proc
        
        if hasattr(self,'modprocedures'):
            tmplist = []
            for proc in self.modprocedures:
                if proc.name.lower() in self.all_procs:
                    intr = self.all_procs[proc.name.lower()]
                    # Don't think I need these checks...
                    if intr.proctype.lower() =='interface' and not intr.generic and not intr.abstract and intr.procedure.module == True:
                        proc.attribs = intr.procedure.attribs
                        proc.args = intr.procedure.args
                        proc.retvar = getattr(intr.procedure,'retvar',None)
                        proc.proctype = intr.procedure.proctype
                        proc.module = intr
                        intr.procedure.module = proc

        typelist = {}
        for dtype in self.types:
            if  dtype.extends and dtype.extends.lower() in self.all_types:
                dtype.extends = self.all_types[dtype.extends.lower()]
                typelist[dtype] = set([dtype.extends])
            else:
                typelist[dtype] = set([])
        typeorder = toposort.toposort_flatten(typelist)

        # Add procedures and types from USED modules to our lists
        for mod, extra in self.uses:
            if type(mod) is str: continue
            procs, absints, types, variables = mod.get_used_entities(extra)
            if self.obj == 'module':
                self.pub_procs.update(procs)
                self.pub_absints.update(absints)
                self.pub_types.update(types)
                self.pub_vars.update(variables)
            self.all_procs.update(procs)
            self.all_absinterfaces.update(absints)
            self.all_types.update(types)
            self.all_vars.update(variables)
        self.uses = [m[0] for m in self.uses]
        
        # Match up called procedures
        if hasattr(self,'calls'):
            tmplst = []
            for call in self.calls:
                argname = False
                for a in getattr(self,'args',[]):
                    # Consider allowing procedures passed as arguments to be included in callgraphs
                    argname = argname or call == a.name
                if hasattr(self,'retvar'):
                    argname = argname or call == self.retvar.name
                if call.lower() not in [name.lower() for name in self.all_vars] and (call.lower() not in [name.lower() for name in self.all_types] and call.lower() not in [arg.name.lower() for arg in getattr(self.parent,'args',[])] or call in self.all_procs) and not argname: tmplst.append(call)
            self.calls = tmplst
            fileprocs = {}
            if self.parobj == 'sourcefile':
                for proc in self.parent.subroutines + self.parent.functions:
                    fileprocs[proc.name.lower()] = proc
            for i in range(len(self.calls)):
                if self.calls[i].lower() in self.all_procs:
                    self.calls[i] = self.all_procs[self.calls[i].lower()]
                elif self.calls[i].lower() in fileprocs:
                    self.calls[i] = fileprocs[self.calls[i].lower()]

        if self.obj == 'submodule':
            self.ancestry = []
            item = self
            while item.ancestor:
                item = item.ancestor
                self.ancestry.insert(0,item)
            self.ancestry.insert(0,item.ancestor_mod)

        # Recurse
        for dtype in typeorder:
            if dtype in self.types: dtype.correlate(project)
        for func in self.functions:
            func.correlate(project)
        for subrtn in self.subroutines:
            subrtn.correlate(project)
        for interface in self.interfaces:
            interface.correlate(project)
        for absint in self.absinterfaces:
            absint.correlate(project)
        for var in self.variables:
            var.correlate(project)
        if hasattr(self,'modprocedures'):
            for mp in self.modprocedures:
                mp.correlate(project)
        if hasattr(self,'args') and not getattr(self,'mp',False):
            for arg in self.args:
                arg.correlate(project)
        if hasattr(self,'retvar') and not getattr(self,'mp',False):
            self.retvar.correlate(project)
        
        # Separate module subroutines/functions from normal ones
        if self.obj == 'submodule':
            self.modfunctions = [func for func in self.functions if func.module]
            self.functions = [func for func in self.functions if not func.module]
            self.modsubroutines = [sub for sub in self.subroutines if sub.module]
            self.subroutines = [sub for sub in self.subroutines if not sub.module]


    def process_attribs(self):
        for item in self.functions + self.subroutines + self.types + self.interfaces + self.absinterfaces:
            if item.name.lower() in self.attr_dict:
                if 'public' in self.attr_dict[item.name.lower()]:
                    item.permission = 'public'
                elif 'private' in self.attr_dict[item.name.lower()]:
                    item.permission = 'private'
                elif attr[0:4] == 'bind':
                    if hasattr(item,'bindC'):
                        item.bindC = attr[5:-1]
                    elif getattr(item,'procedure',None):
                        item.procedure.bindC = attr[5:-1]
                    else:
                        item.attribs.append(attr[5:-1])
        for var in self.variables:
            for attr in self.attr_dict.get(var.name.lower(),[]):
                if attr == 'public' or attr == 'private' or attr == 'protected':
                    var.permission = attr
                elif attr[0:6] == 'intent':
                    var.intent = attr[7:-1]
                elif DIM_RE.match(attr) and ('dimension' in attr or 'pointer' in attr or 'allocatable' in attr):
                    i = attr.index('(')
                    var.attribs.append(attr[0:i])
                    var.dimension = attr[i:]
                else:
                    var.attribs.append(attr)
        del self.attr_dict


    def prune(self):
        """
        Remove anything which shouldn't be displayed.
        """
        self.functions = [obj for obj in self.functions if obj.permission in self.display]
        self.subroutines = [obj for obj in self.subroutines if obj.permission in self.display]
        self.types = [obj for obj in self.types if obj.permission in self.display]
        self.interfaces = [obj for obj in self.interfaces if obj.permission in self.display]
        self.absinterfaces = [obj for obj in self.absinterfaces if obj.permission in self.display]
        self.variables = [obj for obj in self.variables if obj.permission in self.display]
        if hasattr(self,'modprocedures'):
            self.modprocedures = [obj for obj in self.modprocedures if obj.permission in self.display]
        if hasattr(self,'modsubroutines'):
            self.modsubroutines = [obj for obj in self.modsubroutines if obj.permission in self.display]
        if hasattr(self,'modfunctions'):
            self.modfunctions = [obj for obj in self.modfunctions if obj.permission in self.display]

        # Recurse
        for obj in self.absinterfaces:
            obj.visible = True
        for obj in self.functions + self.subroutines + self.types + self.interfaces + getattr(self,'modprocedures',[]) + getattr(self,'modfunctions',[]) + getattr(self,'modsubroutines',[]):
            obj.visible = True
        for obj in self.functions + self.subroutines + self.types + getattr(self,'modprocedures',[]) + getattr(self,'modfunctions',[]) + getattr(self,'modsubroutines',[]):
            obj.prune()

        
class FortranSourceFile(FortranContainer):
    """
    An object representing individual files containing Fortran code. A project
    will consist of a list of these objects. In turn, SourceFile objects will
    contains lists of all of that file's contents
    """
    def __init__(self,filepath,settings,preprocess=False):
        self.path = filepath.strip()
        self.name = os.path.basename(self.path)
        self.settings = settings
        self.parent = None
        self.modules = []
        self.submodules = []
        self.functions = []
        self.subroutines = []
        self.programs = []
        self.doc = []
        self.hierarchy = []
        self.obj = 'sourcefile'
        self.display = settings['display']
                
        source = ford.reader.FortranReader(self.path,settings['docmark'],
                    settings['predocmark'],settings['docmark_alt'],
                    settings['predocmark_alt'],preprocess,
                    settings['macro'])
        
        FortranContainer.__init__(self,source,"")
        readobj = open(self.path,'r')
        self.raw_src = readobj.read()
        #~ self.src = highlight(self.src,FortranLexer(),HtmlFormatter(linenos=True))
        # TODO: Get line-numbers working in such a way that it will look right with Bootstrap CSS
        self.src = highlight(self.raw_src,FortranLexer(),HtmlFormatter())



class FortranModule(FortranCodeUnit):
    """
    An object representing individual modules within your source code. These
    objects contains lists of all of the module's contents, as well as its 
    dependencies.
    """
    ONLY_RE = re.compile('^\s*,\s*only\s*:\s*(?=[^,])',re.IGNORECASE)
    RENAME_RE = re.compile('(\w+)\s*=>\s*(\w+)',re.IGNORECASE)
    
    def _initialize(self,line):
        self.name = line.group(1)
        # TODO: Add the ability to parse ONLY directives and procedure renaming
        self.uses = []
        self.variables = []
        self.externals = []
        self.public_list = []
        self.private_list = []
        self.protected_list = []
        self.external_list = []
        self.volatile_list = []
        self.async_list = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.absinterfaces = []
        self.types = []
        self.descendants = []
        self.visible = True
        self.attr_dict = dict()

    def _cleanup(self):
        # Create list of all local procedures. Ones coming from other modules
        # will be added later, during correlation.
        self.all_procs = {}
        for p in self.functions + self.subroutines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface
        self.process_attribs()
        self.pub_procs = {}
        for p, proc in self.all_procs.items():
            if proc.permission == "public":
                self.pub_procs[p] = proc
        self.pub_vars = {}
        for var in self.variables:
            if var.permission == "public" or var.permission == "protected":
                self.pub_vars[var.name] = var
        self.pub_types = {}
        for dt in self.types:
            if dt.permission == "public":
                self.pub_types[dt.name] = dt
        self.pub_absints = {}
        for ai in self.absinterfaces:
            if ai.permission == "public":
                self.pub_absints[ai.name] = ai

        
    def get_used_entities(self,use_specs):
        """
        Returns the entities which are imported by a use statement. These
        are contained in dicts.
        """
        if len(use_specs.strip()) == 0:
            return (self.pub_procs, self.pub_absints, self.pub_types, self.pub_vars)
        only = bool(self.ONLY_RE.match(use_specs))
        use_specs = self.ONLY_RE.sub('',use_specs)
        ulist = self.SPLIT_RE.split(use_specs)
        ulist[-1] = ulist[-1].strip()
        uspecs = {}
        for item in ulist:
            match = self.RENAME_RE.search(item)
            if match:
                uspecs[match.group(1)] = match.group(2)
            else:
                uspecs[item] = item
        ret_procs = {}
        ret_absints = {}
        ret_types = {}
        ret_vars = {}
        for name, obj in self.pub_procs.items():
            if only:
                if name in uspecs: ret_procs[uspecs[name]] = obj
            else:
                if name in uspecs: 
                    ret_procs[uspecs[name]] = obj
                else:
                    ret_procs[name] = obj
        for name, obj in self.pub_absints.items():
            if only:
                if name in uspecs: ret_absints[uspecs[name]] = obj
            else:
                if name in uspecs: 
                    ret_absints[uspecs[name]] = obj
                else:
                    ret_absints[name] = obj
        for name, obj in self.pub_types.items():
            if only:
                if name in uspecs: ret_types[uspecs[name]] = obj
            else:
                if name in uspecs: 
                    ret_types[uspecs[name]] = obj
                else:
                    ret_types[name] = obj
        for name, obj in self.pub_vars.items():
            if only:
                if name in uspecs: ret_vars[uspecs[name]] = obj
            else:
                if name in uspecs: 
                    ret_vars[uspecs[name]] = obj
                else:
                    ret_vars[name] = obj
        return (ret_procs,ret_absints,ret_types,ret_vars)


class FortranSubmodule(FortranModule):
    def _initialize(self,line):
        FortranModule._initialize(self,line)
        self.name = line.group(3)
        self.ancestor = line.group(2)
        self.ancestor_mod = line.group(1)
        self.modprocedures = []
        del self.public_list
        del self.private_list
        del self.protected_list

    def _cleanup(self):
        # Create list of all local procedures. Ones coming from other modules
        # will be added later, during correlation.
        self.process_attribs()
        self.all_procs = {}
        for p in self.functions + self.subroutines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface
    
    
class FortranSubroutine(FortranCodeUnit):
    """
    An object representing a Fortran subroutine and holding all of said 
    subroutine's contents.
    """
    def _initialize(self,line):
        self.proctype = 'Subroutine'
        self.name = line.group(2)
        attribstr = line.group(1)
        self.module = False
        self.mp = False
        if not attribstr: attribstr = ""
        self.attribs = []
        if attribstr.find("impure") >= 0:
            self.attribs.append("impure")
            attribstr = attribstr.replace("impure","",1)
        if attribstr.find("pure") >= 0:
            self.attribs.append("pure")
            attribstr = attribstr.replace("pure","",1)
        if attribstr.find("elemental") >= 0:
            self.attribs.append("elemental")
            attribstr = attribstr.replace("elemental","",1)
        if attribstr.find("non_recursive") >= 0:
            self.attribs.append("non_recursive")
            attribstr = attribstr.replace("non_recursive","",1)
        if attribstr.find("recursive") >= 0:
            self.attribs.append("recursive")
            attribstr = attribstr.replace("recursive","",1)
        if attribstr.find("module") >= 0:
            self.module = True
            attribstr = attribstr.replace("module","",1)
        attribstr = re.sub(" ","",attribstr)
        #~ self.name = line.group(2)
        self.args = []
        if line.group(3):
            if self.SPLIT_RE.split(line.group(3)[1:-1]):
                for arg in self.SPLIT_RE.split(line.group(3)[1:-1]):
                    if arg != '': self.args.append(arg.strip())
        self.bindC = line.group(4)
        self.variables = []
        self.externals = []
        self.uses = []
        self.calls = []
        self.optional_list = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.absinterfaces = []
        self.types = []
        self.external_list = []
        self.volatile_list = []
        self.async_list = []
        self.attr_dict = dict()

    def set_permission(self, value):
        self._permission = value

    def get_permission(self):
        if type(self.parent) == FortranInterface and not self.parent.generic:
            return self.parent.permission
        else:
            return self._permission

    permission = property(get_permission, set_permission)
    
    def _cleanup(self):
        self.all_procs = {}
        for p in self.functions + self.subroutines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface
        for i in range(len(self.args)):
            for var in self.variables:
                if self.args[i].lower() == var.name.lower():
                    self.args[i] = var
                    self.variables.remove(var)
                    break
            if type(self.args[i]) == str:
                for intr in self.interfaces:
                    if not intr.generic and intr.procedure.name.lower() == self.args[i].lower():
                        self.args[i] = intr.procedure
                        self.args[i].parent = self
                        self.args[i].parobj = self.obj
                        self.args[i].permission = None
                        self.interfaces.remove(intr)
                        break
            if type(self.args[i]) == str:
                if self.args[i][0].lower() in 'ijklmn':
                    vartype = 'integer'
                else:
                    vartype = 'real'
                self.args[i] = FortranVariable(self.args[i],vartype,self)
        self.process_attribs()
    
class FortranFunction(FortranCodeUnit):
    """
    An object representing a Fortran function and holding all of said function's
    contents.
    """
    def _initialize(self,line):
        self.proctype = 'Function'
        self.name = line.group(2)
        attribstr = line.group(1)
        self.module = False
        self.mp = False
        if not attribstr: attribstr = ""
        self.attribs = []
        if attribstr.find("impure") >= 0:
            self.attribs.append("impure")
            attribstr = attribstr.replace("impure","",1)
        if attribstr.find("pure") >= 0:
            self.attribs.append("pure")
            attribstr = attribstr.replace("pure","",1)
        if attribstr.find("elemental") >= 0:
            self.attribs.append("elemental")
            attribstr = attribstr.replace("elemental","",1)
        if attribstr.find("non_recursive") >= 0:
            self.attribs.append("non_recursive")
            attribstr = attribstr.replace("non_recursive","",1)
        if attribstr.find("recursive") >= 0:
            self.attribs.append("recursive")
            attribstr = attribstr.replace("recursive","",1)
        if attribstr.find("module") >= 0:
            self.module = True
            attribstr = attribstr.replace("module","",1)
        attribstr = re.sub(" ","",attribstr)
        if line.group(4):
            self.retvar = line.group(4)
        else:
            self.retvar = self.name
            
        typestr = ''
        for vtype in self.settings['extra_vartypes']:
            typestr = typestr + '|' + vtype
        var_type_re = re.compile(VAR_TYPE_STRING + typestr,re.IGNORECASE)
        if var_type_re.search(attribstr):
            rettype, retkind, retlen, retproto, rest =  parse_type(attribstr,self.strings,self.settings)
            self.retvar = FortranVariable(self.retvar,rettype,self.parent,
                                          kind=retkind,strlen=retlen,
                                          proto=retproto)
        self.args = [] # Set this in the correlation step
        
        for arg in self.SPLIT_RE.split(line.group(3)[1:-1]):
            # FIXME: This is to avoid a problem whereby sometimes an empty argument list will appear to contain the argument ''. I didn't know why it would do this (especially since sometimes it works fine) and just put this in as a quick fix. However, at some point I should try to figure out the actual root of the problem.
            if arg != '': self.args.append(arg.strip())
        try:
            self.bindC = ford.utils.get_parens(line.group(5),-1)[0:-1]
        except:
            self.bindC = line.group(5)
        if self.bindC:
            search_from = 0
            while QUOTES_RE.search(self.bindC[search_from:]):
                num = int(QUOTES_RE.search(self.bindC[search_from:]).group()[1:-1])
                self.bindC = self.bindC[0:search_from] + QUOTES_RE.sub(self.parent.strings[num],self.bindC[search_from:],count=1)
                search_from += QUOTES_RE.search(self.bindC[search_from:]).end(0)
        self.variables = []
        self.externals = []
        self.uses = []
        self.calls = []
        self.optional_list = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.absinterfaces = []
        self.types = []
        self.external_list = []
        self.volatile_list = []
        self.async_list = []
        self.attr_dict = dict()

    def set_permission(self, value):
        self._permission = value

    def get_permission(self):
        if type(self.parent) == FortranInterface and not self.parent.generic:
            return self.parent.permission
        else:
            return self._permission

    permission = property(get_permission, set_permission)
    
    def _cleanup(self):
        self.all_procs = {}
        for p in self.functions + self.subroutines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface
        for i in range(len(self.args)):
            for var in self.variables:
                if self.args[i].lower() == var.name.lower():
                    self.args[i] = var
                    self.variables.remove(var)
                    break
            if type(self.args[i]) == str:
                for intr in self.interfaces:
                    for proc in intr.subroutines + intr.functions:
                        if proc.name.lower() == self.args[i].lower():
                            self.args[i] = proc
                            if proc.proctype == 'Subroutine': intr.subroutines.remove(proc)
                            else: intr.functions.remove(proc)
                            if len(intr.subroutines + intr.functions) < 1:
                                self.interfaces.remove(intr)
                            self.args[i].parent = self
                            break
            if type(self.args[i]) == str:
                if self.args[i][0].lower() in 'ijklmn':
                    vartype = 'integer'
                else:
                    vartype = 'real'
                self.args[i] = FortranVariable(self.args[i],vartype,self)
        if type(self.retvar) != FortranVariable:
            for var in self.variables:
                if var.name.lower() == self.retvar.lower():
                    self.retvar = var
                    self.variables.remove(var)
                    break
            # TODO:Add support for implicitely typed retval
        self.process_attribs()


class FortranSubmoduleProcedure(FortranCodeUnit):
    """
    An object representing a the implementation of a Module Function or
    Module Subroutine in a sumbmodule.
    """
    def _initialize(self,line):
        self.proctype = 'Module Procedure'
        self.name = line.group(2)
        self.variables = []
        self.externals = []
        self.uses = []
        self.calls = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.absinterfaces = []
        self.types = []
        self.external_list = []
        self.volatile_list = []
        self.async_list = []
        self.attr_dict = dict()
        self.mp = True

    def _cleanup(self):
        self.process_attribs()
        self.all_procs = {}
        for p in self.functions + self.subroutines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface


class FortranProgram(FortranCodeUnit):
    """
    An object representing the main Fortran program.
    """
    def _initialize(self,line):
        self.name = line.group(1)
        self.variables = []
        self.externals = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.types = []
        self.uses = []
        self.calls = []
        self.absinterfaces = []
        self.external_list = []
        self.volatile_list = []
        self.async_list = []
        self.attr_dict = dict()
    
    def _cleanup(self):
        self.all_procs = {}
        for p in self.functions + self.subroutines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface
        self.process_attribs()
    
    
class FortranType(FortranContainer):
    """
    An object representing a Fortran derived type and holding all of said type's
    components and type-bound procedures. It also contains information on the
    type's inheritance.
    """
    def _initialize(self,line):
        self.name = line.group(2)
        self.extends = None
        self.attributes = []
        if line.group(1):
            attribstr = line.group(1)[1:].strip()
            attriblist = self.SPLIT_RE.split(attribstr.strip())
            for attrib in attriblist:
                if EXTENDS_RE.search(attrib):
                    self.extends = EXTENDS_RE.search(attrib).group(1)
                elif attrib.strip().lower() == "public":
                    self.permission = "public"
                elif attrib.strip().lower() == "private":
                    self.permission = "private"
                elif attrib.strip().lower() == "external":
                    self.attributes.append("external")
                else:
                    self.attributes.append(attrib.strip())
        if line.group(3):
            paramstr = line.group(3).strip()
            self.parameters = self.SPLIT_RE.split(paramstr)
        else:
            self.parameters = []
        self.sequence = False
        self.variables = []
        self.boundprocs = []
        self.finalprocs = []
        self.constructor = None
        
        
    def _cleanup(self):
        # Match parameters with variables
        for i in range(len(self.parameters)):
            for var in self.variables:
                if self.parameters[i].lower() == var.name.lower():
                    self.parameters[i] = var
                    self.variables.remove(var)
                    break

        
    def correlate(self,project):
        self.all_absinterfaces = self.parent.all_absinterfaces
        self.all_types = self.parent.all_types
        self.all_procs = self.parent.all_procs
        self.all_boundprocs = copy.copy(self.boundprocs)
        # Get type of extension
        if self.extends and type(self.extends) is not str:
            for bp in self.extends.all_boundprocs:
                deferred = False
                for attr in bp.attribs:
                    if attr.lower() == 'deferred': deferred = True
                present = False
                for b in self.boundprocs:
                    if bp.name.lower() == b.name.lower(): present = True
                if not deferred or not present: self.all_boundprocs.append(bp)

        # Match variables as needed (recurse)
        #~ for i in range(len(self.variables)-1,-1,-1):
            #~ self.variables[i].correlate(project)
        for v in self.variables:
            v.correlate(project)
        # Match boundprocs with procedures
        # FIXME: This is not at all modular because must process non-generic bound procs first--could there be a better way to do it
        for proc in self.boundprocs:
            if not proc.generic: proc.correlate(project)
        for proc in self.boundprocs:
            if proc.generic: proc.correlate(project)
        # Match finalprocs
        for i in range(len(self.finalprocs)):
            if self.finalprocs[i].lower() in self.all_procs:
                self.finalprocs[i] = self.all_procs[self.finalprocs[i].lower()]
        # Find a constructor, if one exists
        if self.name.lower() in self.all_procs:
            self.constructor = self.all_procs[self.name.lower()]
        
    def prune(self):
        """
        Remove anything which shouldn't be displayed.
        """
        self.boundprocs = [ obj for obj in self.boundprocs if obj.permission in self.display ]
        self.variables = [ obj for obj in self.variables if obj.permission in self.display ]
        for obj in self.boundprocs + self.variables:
            obj.visible = True

        
    
class FortranInterface(FortranContainer):
    """
    An object representing a Fortran interface.
    """
    def _initialize(self,line):
        self.proctype = 'Interface'
        self.name = line.group(2)
        self.subroutines = []
        self.functions = []
        self.modprocs = []
        self.generic = bool(self.name)
        self.abstract = bool(line.group(1))
        if self.generic and self.abstract:
            raise Exception("Generic interface {} can not be abstract".format(self.name))

    def correlate(self,project):
        self.all_absinterfaces = self.parent.all_absinterfaces
        self.all_types = self.parent.all_types
        self.all_procs = self.parent.all_procs
        if self.generic:
            for modproc in self.modprocs:
                if modproc.name.lower() in self.all_procs:
                    modproc.procedure = self.all_procs[modproc.name.lower()]
            for subrtn in self.subroutines:
                subrtn.correlate(project)
            for func in self.functions:
                func.correlate(project)
        else:
            self.procedure.correlate(project)

    def _cleanup(self):
        if len(self.subroutines + self.functions + self.modprocs) < 1 and self.generic:
            raise Exception("Generic interface block found with no contents: {}".format(self.name))
        if self.abstract:
            contents = []
            for proc in (self.subroutines + self.functions):
                proc.visible = True
                item = copy.copy(self)
                item.procedure = proc
                item.procedure.parent = item
                del item.functions
                del item.modprocs
                del item.subroutines
                item.name = proc.name
                item.permission = proc.permission
                contents.append(item)
            self.contents = contents
        elif not self.generic:
            contents = []
            for proc in (self.functions + self.subroutines):
                proc.visible = True
                item = copy.copy(self)
                item.procedure = proc
                item.procedure.parent = item
                del item.functions
                del item.modprocs
                del item.subroutines
                item.name = proc.name
                item.permission = proc.permission
                contents.append(item)
            self.contents = contents


    
class FortranVariable(FortranBase):
    """
    An object representing a variable within Fortran.
    """
    def __init__(self,name,vartype,parent,attribs=[],intent="",
                 optional=False,permission="public",parameter=False,kind=None,
                 strlen=None,proto=None,doc=[],points=False,initial=None):
        self.name = name
        self.vartype = vartype.lower()
        self.parent = parent
        if self.parent:
            self.parobj = self.parent.obj
            self.settings = self.parent.settings
        else:
            self.parobj = None
            self.settings = None
        self.obj = type(self).__name__[7:].lower()
        self.attribs = attribs
        self.intent = intent
        self.optional = optional
        self.kind = kind
        self.strlen = strlen
        self.proto = proto
        self.doc = doc
        self.permission = permission
        self.points = points
        self.parameter = parameter
        self.doc = []
        self.initial = initial
        self.dimension = ''
        self.meta = {}
        self.visible = False
        
        indexlist = []
        indexparen = self.name.find('(')
        if indexparen > 0:
            indexlist.append(indexparen)
        indexbrack = self.name.find('[')
        if indexbrack > 0:
            indexlist.append(indexbrack)
        indexstar = self.name.find('*')
        if indexstar > 0:
            indexlist.append(indexstar)
            
        if len(indexlist) > 0:
            self.dimension = self.name[min(indexlist):]
            self.name = self.name[0:min(indexlist)]
        
        self.hierarchy = []
        cur = self.parent
        while cur:
            self.hierarchy.append(cur)
            cur = cur.parent
        self.hierarchy.reverse()


    def correlate(self,project):
        if (self.vartype == "type" or self.vartype == "class") and self.proto and self.proto[0] != '*':
            if self.proto[0].lower() in [name.lower() for name in self.parent.all_types]:
                self.proto[0] = self.parent.all_types[[name for name in self.parent.all_types if name.lower()==self.proto[0].lower()][0]]
        elif self.vartype == "procedure" and self.proto and self.proto[0] != '*':
            if self.proto[0].lower() in self.parent.all_procs:
                self.proto[0] = self.parent.all_procs[self.proto[0].lower()]
            elif self.proto[0].lower() in self.parent.all_absinterfaces:
                self.proto[0] = self.parent.all_absinterfaces[self.proto[0].lower()]



class FortranBoundProcedure(FortranBase):
    """
    An object representing a type-bound procedure, possibly overloaded.
    """
    def _initialize(self,line):
        attribstr = line.group(3)
        self.attribs = []
        if attribstr:
            tmp_attribs = ford.utils.paren_split(",",attribstr[1:])
            for i in range(len(tmp_attribs)):
                tmp_attribs[i] = tmp_attribs[i].strip()
                if tmp_attribs[i].lower() == "public": self.permission = "public"
                elif tmp_attribs[i].lower() == "private": self.permission = "private"
                else: self.attribs.append(tmp_attribs[i])
        rest = line.group(4)
        split = self.POINTS_TO_RE.split(rest)
        self.name = split[0].strip()
        self.generic = (line.group(1).lower() == "generic")
        self.proto = line.group(2)
        if self.proto:
            self.proto = self.proto[1:-1]
        self.bindings = []
        if len(split) > 1:
            binds = self.SPLIT_RE.split(split[1])
            for bind in binds:
                self.bindings.append(bind.strip())
        else:
            self.bindings.append(self.name)
        if line.group(2):
            self.prototype = line.group(2)[1:-1]
        else:
            self.prototype = None

    def correlate(self,project):
        self.all_procs = self.parent.all_procs
        self.protomatch = False
        if self.proto:
            if self.proto.lower() in self.all_procs:
                self.proto = self.all_procs[self.proto.lower()]
                self.protomatch = True
            elif self.proto.lower() in self.parent.all_absinterfaces:
                self.proto = self.parent.all_absinterfaces[self.proto.lower()]
                self.protomatch = True
        self.matched = []
        if self.generic:
            for i in range(len(self.bindings)):
                for proc in self.parent.all_boundprocs:
                    if proc.name and proc.name.lower() == self.bindings[i].lower():
                        self.bindings[i] = proc
                        self.matched.append(True)
                        break
                else:
                    self.matched.append(False)
        else:
            for i in range(len(self.bindings)):
                if self.bindings[i].lower() in self.all_procs:
                    self.bindings[i] = self.all_procs[self.bindings[i].lower()]
                    self.matched.append(True)
                else:
                    self.matched.append(False)


class FortranModuleProcedure(FortranBase):
    """
    An object representing a module procedure in an interface. Not to be
    confused with type of module procedure which is the implementation of
    a module function or module subroutine in a submodule.
    """
    def __init__(self,name,parent=None,inherited_permission=None):
        if (inherited_permission!=None):
            self.permission = inherited_permission.lower()
        else:
            self.permission = None
        self.parent = parent
        if self.parent:
            self.parobj = self.parent.obj
            self.settings = self.parent.settings
        else:
            self.parobj = None
            self.settings = None
        self.obj = 'moduleprocedure'
        self.name = name
        self.procedure = None
        self.doc = []
        self.hierarchy = []
        cur = self.parent
        while cur:
            self.hierarchy.append(cur)
            cur = cur.parent
        self.hierarchy.reverse()
                

_can_have_contains = [FortranModule,FortranProgram,FortranFunction,
                      FortranSubroutine,FortranType,FortranSubmodule]
        
def line_to_variables(source, line, inherit_permission, parent):
    """
    Returns a list of variables declared in the provided line of code. The
    line of code should be provided as a string.
    """
    vartype, kind, strlen, proto, rest = parse_type(line,parent.strings,parent.settings)
    attribs = []
    intent = ""
    optional = False
    permission = inherit_permission
    parameter = False
    
    EXTERNAL_RE = re.compile("external")
    attribmatch = ATTRIBSPLIT_RE.match(rest)
    if attribmatch:
        attribstr = attribmatch.group(1).strip()
        if EXTERNAL_RE.match(attribstr):  # We have external functions, not variables.
            return [], [name.strip() for name in ford.utils.paren_split(",",attribmatch.group(2))]
        declarestr = attribmatch.group(2).strip()
        tmp_attribs = ford.utils.paren_split(",",attribstr)
        for i in range(len(tmp_attribs)):
            tmp_attribs[i] = tmp_attribs[i].strip()
            if tmp_attribs[i].lower() == "public": permission = "public"
            elif tmp_attribs[i].lower() == "private": permission = "private"
            elif tmp_attribs[i].lower() == "protected": permission = "protected"
            elif tmp_attribs[i].lower() == "optional": optional = True
            elif tmp_attribs[i].lower() == "parameter": parameter = True
            elif tmp_attribs[i].lower().replace(' ','') == "intent(in)":
                intent = 'in'
            elif tmp_attribs[i].lower().replace(' ','') == "intent(out)":
                intent = 'out'
            elif tmp_attribs[i].lower().replace(' ','') == "intent(inout)":
                intent = 'inout'
            else: attribs.append(tmp_attribs[i])
    else:
        declarestr = ATTRIBSPLIT2_RE.match(rest).group(2)
    declarations = ford.utils.paren_split(",",declarestr)

    varlist = []
    for dec in declarations:
        dec = re.sub(" ","",dec)
        split = ford.utils.paren_split('=',dec)
        if len(split) > 1:
            if split[1][0] == '>':
                name = split[0]
                initial = split[1][1:]
                points = True
            else:
                name = split[0]
                initial = split[1]
                points = False
        else:
            name = dec.strip()
            initial = None
            points = False
            
        if initial and vartype == "character":
            initial = COMMA_RE.sub(', ',initial)
            search_from = 0
            while QUOTES_RE.search(initial[search_from:]):
                num = int(QUOTES_RE.search(initial[search_from:]).group()[1:-1])
                string = NBSP_RE.sub('&nbsp;',parent.strings[num])
                initial = initial[0:search_from] + QUOTES_RE.sub(string,initial[search_from:],count=1)
                search_from += QUOTES_RE.search(initial[search_from:]).end(0)
        
        if proto:
            varlist.append(FortranVariable(name,vartype,parent,copy.copy(attribs),intent,
                           optional,permission,parameter,kind,strlen,list(proto),
                           [],points,initial))
        else:
            varlist.append(FortranVariable(name,vartype,parent,copy.copy(attribs),intent,
                           optional,permission,parameter,kind,strlen,proto,
                           [],points,initial))
        
    doc = []
    docline = source.__next__()
    while docline[0:2] == "!" + parent.settings['docmark']:
        doc.append(docline[2:])
        docline = source.__next__()
    source.pass_back(docline)
    varlist[-1].doc = doc
    return varlist, []
    
    

def parse_type(string,capture_strings,settings):
    """
    Gets variable type, kind, length, and/or derived-type attributes from a 
    variable declaration.
    """
    typestr = ''
    for vtype in settings['extra_vartypes']:
        typestr = typestr + '|' + vtype
    var_type_re = re.compile(VAR_TYPE_STRING + typestr,re.IGNORECASE)
    match = var_type_re.match(string)
    if not match: raise Exception("Invalid variable declaration: {}".format(string))
    
    vartype = match.group().lower()
    if DOUBLE_PREC_RE.match(vartype): vartype = "double precision"
    rest = string[match.end():].strip()
    kindstr = ford.utils.get_parens(rest)
    rest = rest[len(kindstr):].strip()

    # FIXME: This won't work for old-fashioned REAL*8 type notations
    if len(kindstr) < 3 and vartype != "type" and vartype != "class":
        return (vartype, None, None, None, rest)
    match = VARKIND_RE.search(kindstr)
    if match:
        if match.group(1):
            star = False
            args = match.group(1).strip()
        else:
            star = True
            args = match.group(2).strip()

        args = re.sub("\s","",args)
        if vartype == "type" or vartype == "class" or vartype == "procedure":
            PROTO_RE = re.compile("(\*|\w+)\s*(?:\((.*)\))?")
            try:
                proto = list(PROTO_RE.match(args).groups())
                if not proto[1]: proto[1] = ''
            except:
                raise Exception("Bad type, class, or procedure prototype specification: {}".format(args))
            return (vartype, None, None, proto, rest)
        elif vartype == "character":
            if star:
                return (vartype, None, args[1], None, rest)
            else:
                kind = None
                length = None
                if KIND_RE.search(args):
                    kind = KIND_RE.sub("",args)
                    try:
                        match = QUOTES_RE.search(kind)
                        num = int(match.group()[1:-1])
                        kind = QUOTES_RE.sub(captured_strings[num],kind)
                    except:
                        pass
                elif LEN_RE.search(args):
                    length = LEN_RE.sub("",args)
                else:
                    length = args
                return (vartype, kind, length, None, rest)
        else: 
            kind = KIND_RE.sub("",args)
            return (vartype, kind, None, None, rest)

    raise Exception("Bad declaration of variable type {}: {}".format(vartype,string))


def set_base_url(url):
    FortranBase.base_url = url

def get_mod_procs(source,line,parent):
    inherit_permission = parent.permission
    retlist = []
    SPLIT_RE = re.compile("\s*,\s*",re.IGNORECASE)
    splitlist = SPLIT_RE.split(line.group(2))
    if splitlist and len(splitlist) > 0:
        for item in splitlist:
            retlist.append(FortranModuleProcedure(item,parent,inherit_permission))
    else:
        retlist.append(FortranModuleProcedure(line.group(1),parent,inherit_permission))
    
    doc = []
    docline = source.__next__()
    while docline[0:2] == "!" + parent.settings['docmark']:
        doc.append(docline[2:])
        docline = source.__next__()
    source.pass_back(docline)
    retlist[-1].doc = doc
    
    return retlist


class NameSelector(object):
    """
    Object which tracks what names have been provided for different
    entities in Fortran code. It will provide an identifier which is
    guaranteed to be unique. This identifier can then me used as a
    filename for the documentation of that entity.
    """
    def __init__(self):
        self._items = {}
        self._counts = {}
                       
    
    def get_name(self,item):
        """
        Return the name for this item registered with this NameSelector.
        If no name has previously been registered, then generate a new
        one.
        """
        if not isinstance(item,ford.sourceform.FortranBase):
            raise Exception('{} is not of a type derived from FortranBase'.format(str(item)))
        
        if item in self._items:
            return self._items[item]
        else:
            if item.get_dir() not in self._counts:
                self._counts[item.get_dir()] = {}
            if item.name in self._counts[item.get_dir()]:
                num = self._counts[item.get_dir()][item.name] + 1
            else:
                num = 1
            self._counts[item.get_dir()][item.name] = num
            name = item.name.lower().replace('/','SLASH')
            if num > 1:
                name = name + '~' + str(num)
            self._items[item] = name
            return name
            
namelist = NameSelector()

