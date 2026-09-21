#!/usr/bin/env python3
"""Batch convert code files -> A4 images (SVG+PNG) + one PDF per file.

Multi-language build (v2.2.0):
  - 49 languages, auto-detection by extension / basename / content sniff
  - Per-language keyword / comment / string / special-token rules
  - Faithful indentation: the file's actual leading whitespace / tabs are
    preserved (works for both brace-based and space-based languages)
"""
import os, sys, subprocess, json

# ===== CONFIG =====
FILES = ['disp_test.c']          # list of source file names (auto-detected language)
FONT_KEY = 'cascadia'            # cascadia | firacode | jetbrains | consolas | courier | sourcecode
FONT_SIZE = 14
LINE_HEIGHT_RATIO = 1.65
TAB_WIDTH = 4
MIN_FONT_SIZE = 7
WRAP_IDENT = 2

# Optional: full path to the node binary (defaults to "node" on PATH).
NODE_EXE = os.environ.get('NODE_EXE', 'node')

FONT_NAMES = {
    'cascadia':'Cascadia Code','firacode':'Fira Code','jetbrains':'JetBrains Mono',
    'consolas':'Consolas','courier':'Courier New','sourcecode':'Source Code Pro',
}

A4_W, A4_H = 794, 1123
HDR_H = 60; PAD_R = 36; PAD_T = 72; PAD_B = 28
CONTENT_H = A4_H - PAD_T - PAD_B
CHAR_RATIO = 0.60
WRAP_PUNCT = set(';,(){}[]')

CO = {'keyword':'#d63384','register':'#e8590c','macro':'#9c36b5',
      'number':'#2b8a3e','string':'#099268','comment':'#868e96',
      'var':'#1971c2','tag':'#0b7285','text':'#212529'}
BG='#ffffff'; HDR_BG='#f1f3f5'; HDR_BD='#dee2e6'
GT_BG='#f8f9fa'; GT_BD='#e9ecef'; LN_COLOR='#868e96'

# ---------------------------------------------------------------------------
# Language definitions
#   kw      : keyword set (pink)
#   sp      : special identifiers, e.g. MCU registers (orange)
#   hash    : 'comment' | 'macro' | None   (# handling)
#   slash   : // line comment
#   dash    : -- line comment
#   block   : (start, end) block comment tuple, or None
#   quotes  : quote chars for strings (excluding backtick)
#   backtick: template-literal / backtick string support
#   name    : display name
# ---------------------------------------------------------------------------
def S(*parts):
    s = set()
    for p in parts:
        if isinstance(p, (set, list, tuple, frozenset)):
            s |= set(p)
        else:
            s.add(p)
    return s

PY_KW = S('def','class','import','from','return','if','elif','else','for','while','break',
    'continue','in','is','not','and','or','None','True','False','with','as','try','except',
    'finally','raise','lambda','yield','pass','global','nonlocal','assert','del','async',
    'await','print','range','len','list','dict','set','tuple','str','int','float','bool',
    'super','enumerate','zip','map','filter','getattr','setattr','hasattr','type','isinstance',
    'open','exec','eval','property','staticmethod','classmethod','self','__init__','__name__')

C_KW = S('auto','break','case','char','const','continue','default','do','double','else','enum',
    'extern','float','for','goto','if','inline','int','long','register','return','short','signed',
    'sizeof','static','struct','switch','typedef','union','unsigned','void','volatile','while',
    'bit','sbit','xdata','idata','code','interrupt','data','pdata','using','reentrant',
    'u8','u16','u32','u64','uchar','uint','bool','boolean','true','false','NULL')
C_SP = S('P0','P1','P2','P3','P4','P5','P6','P7','RST','SCLK','IO','SCK','T0','T1','TF0','TF1','IE','IP','TMOD','TCON','SCON','PCON')

CXX_KW = S(C_KW, 'class','public','private','protected','new','delete','template','typename','this',
    'virtual','override','final','namespace','using','throw','try','catch','operator','constexpr',
    'const_cast','static_cast','dynamic_cast','reinterpret_cast','friend','explicit','mutable',
    'export','typeid','decltype','noexcept','nullptr','auto','concept','requires','std')

JAVA_KW = S('abstract','assert','boolean','break','byte','case','catch','char','class','const',
    'continue','default','do','double','else','enum','extends','final','finally','float','for',
    'goto','if','implements','import','instanceof','int','interface','long','native','new','package',
    'private','protected','public','return','short','static','strictfp','super','switch','synchronized',
    'this','throw','throws','transient','try','void','volatile','while','true','false','null','var',
    'record','sealed','permits','yield')

JS_KW = S('break','case','catch','class','const','continue','debugger','default','delete','do','else',
    'export','extends','false','finally','for','function','if','import','in','instanceof','new','null',
    'return','super','switch','this','throw','true','try','typeof','var','void','while','with','yield',
    'let','static','async','await','of','enum','interface','type','implements','public','private',
    'protected','readonly','as','from','namespace','declare','abstract','constructor','get','set',
    'keyof','infer','never','unknown','any','string','number','boolean','symbol','bigint','undefined')

GO_KW = S('break','case','chan','const','continue','default','defer','else','fallthrough','for','func',
    'go','goto','if','import','interface','map','package','range','return','select','struct','switch',
    'type','var','nil','true','false','string','int','byte','bool','any','rune','float64','uint')

RUST_KW = S('as','async','await','break','const','continue','crate','dyn','else','enum','extern','false',
    'fn','for','if','impl','in','let','loop','match','mod','move','mut','pub','ref','return','self','Self',
    'static','struct','super','true','trait','type','unsafe','use','where','while','macro_rules',
    'Some','None','Ok','Err','Result','Option','Vec','String','u8','u16','u32','u64','i8','i16','i32','i64',
    'f32','f64','bool','str','char','usize','isize','Box','Arc','Rc')

RUBY_KW = S('BEGIN','END','alias','begin','break','case','class','def','defined?','do','else','elsif',
    'end','ensure','false','for','if','in','module','next','nil','not','or','redo','rescue','retry',
    'return','self','super','then','true','undef','unless','until','when','while','yield','puts','require',
    'attr_accessor','attr_reader','attr_writer')

SH_KW = S('if','then','else','elif','fi','for','while','do','done','case','esac','in','function','return',
    'exit','export','local','echo','read','cd','source','select','until','break','continue','set','unset',
    'shift','let','eval','alias')

LUA_KW = S('and','break','do','else','elseif','end','false','for','function','goto','if','in','local',
    'nil','not','or','repeat','return','then','true','until','while','print','pairs','ipairs','require',
    'type','tostring','tonumber','table','string','math','ipairs')

SQL_KW = S('select','from','where','and','or','not','insert','into','values','update','set','delete',
    'create','table','drop','alter','index','view','database','join','inner','left','right','outer','on',
    'group','by','order','having','limit','distinct','union','all','as','count','sum','avg','min','max',
    'null','is','like','in','between','exists','primary','key','foreign','references','default','constraint',
    'unique','case','when','then','else','end','begin','commit','rollback','transaction','grant','revoke',
    'use','show','describe','with','returning','cast','coalesce')

PHP_KW = S('abstract','and','array','as','break','callable','case','catch','class','clone','const',
    'continue','declare','default','do','echo','else','elseif','empty','enddeclare','endfor','endforeach',
    'endif','endswitch','endwhile','eval','exit','extends','final','finally','for','foreach','function',
    'global','goto','if','implements','include','include_once','instanceof','insteadof','interface','isset',
    'list','namespace','new','or','print','private','protected','public','require','require_once','return',
    'static','switch','throw','trait','try','unset','use','var','while','xor','yield','true','false','null',
    'die','self','parent','static','function')

CS_KW = S('using','namespace','class','public','private','protected','internal','static','void','int',
    'string','bool','double','float','char','var','if','else','for','foreach','while','do','switch','case',
    'break','continue','return','new','null','true','false','this','base','interface','struct','enum',
    'delegate','event','async','await','try','catch','finally','throw','lock','get','set','abstract',
    'sealed','override','virtual','partial','readonly','const','typeof','nameof','object','dynamic','long',
    'short','byte','decimal','uint','ulong','sbyte')

JSON_KW = S('true','false','null')

# ===== Extended language keyword sets (v2.2.0) =====
TS_KW = S(JS_KW, 'satisfies','override','accessor','object','out','in')

KT_KW = S('package','import','class','interface','object','companion','enum','sealed','data','abstract',
    'open','final','override','inner','external','public','private','protected','internal','const','var',
    'val','fun','if','else','when','for','while','do','return','break','continue','throw','try','catch',
    'finally','is','in','as','typealias','constructor','init','this','super','by','get','set','field',
    'property','receiver','inline','noinline','crossinline','reified','suspend','operator','infix',
    'tailrec','lateinit','lazy','vararg','where','out','true','false','null','unit','let','run','apply',
    'also','with','require','check','assert','print','println','listOf','mapOf','setOf','arrayOf',
    'Int','Long','Float','Double','String','Boolean','Char','Byte','Short','Array','List','Map','Set')

SW_KW = S('import','func','var','let','class','struct','enum','protocol','extension','actor','typealias',
    'associatedtype','if','else','guard','for','while','repeat','switch','case','default','break','continue',
    'fallthrough','return','in','do','throw','throws','rethrows','try','catch','defer','init','deinit','self',
    'super','nil','true','false','public','private','internal','fileprivate','open','override','static','final',
    'lazy','weak','unowned','mutating','nonmutating','required','convenience','subscript','operator','where',
    'as','is','some','any','async','await','nonisolated','isolated','new','get','set','willSet','didSet',
    'Int','Double','Float','String','Bool','Character','Array','Dictionary','Set','Optional','Void','Any','print')

DART_KW = S('import','export','part','library','class','extends','implements','with','mixin','abstract',
    'enum','typedef','var','final','const','late','dynamic','void','null','bool','int','double','num','String',
    'List','Map','Set','if','else','for','while','do','switch','case','default','break','continue','return','try',
    'catch','finally','throw','rethrow','assert','as','is','in','new','this','super','true','false','required',
    'factory','get','set','async','await','yield','sync','print','main','static')

R_KW = S('function','if','else','for','while','repeat','break','next','return','TRUE','FALSE','NULL','NA',
    'NaN','Inf','library','require','source','install.packages','print','cat','sum','mean','median','length',
    'c','list','data.frame','data.table','set.seed','seq','rep','paste','paste0','nrow','ncol','apply','lapply',
    'sapply','vapply','tapply','aggregate','merge','subset','str','summary','head','tail','names','dim','sort',
    'unique','table','rownames','colnames','as.numeric','as.character','as.factor','factor','levels','ggplot',
    'aes','geom_point','geom_line','geom_bar','geom_histogram','labs','theme','mutate','filter','select','arrange',
    'summarise','summarize','group_by','ungroup','left_join','inner_join','full_join','anti_join')

PL_KW = S('my','our','local','state','sub','use','package','no','if','elsif','else','unless','while','until',
    'for','foreach','return','last','next','redo','continue','do','eval','die','warn','print','printf','sprintf',
    'split','join','push','pop','shift','unshift','splice','defined','undef','ref','bless','open','close','read',
    'write','chomp','chop','scalar','map','grep','sort','keys','values','exists','delete','each','wantarray',
    'require','import','format','BEGIN','END','CHECK','INIT','UNITCHECK','eq','ne','lt','gt','le','ge','cmp',
    'and','or','not','xor')

OBJC_KW = S('interface','implementation','end','property','synthesize','dynamic','selector','class',
    'protocol','optional','required','public','private','protected','package','try','catch','finally',
    'throw','autoreleasepool','synchronized','encode','compatibility_alias','self','super','nil','Nil',
    'YES','NO','true','false','id','instancetype','BOOL','Class','SEL','IMP','typeof','sizeof','static',
    'extern','const','inline','in','out','inout','byref','byval','oneway','return','if','else','for','while',
    'do','switch','case','default','break','continue','goto','void','int','char','float','double','long',
    'short','unsigned','signed','struct','union','enum','typedef','import','include','define','nonatomic',
    'strong','weak','copy','retain','assign','readonly','readwrite','getter','setter','atomic')

MAT_KW = S('function','end','if','elseif','else','for','while','switch','case','otherwise','break','continue',
    'return','global','persistent','try','catch','parfor','spmd','classdef','properties','methods','events',
    'enumeration','import','true','false','nan','inf','pi','zeros','ones','eye','rand','randn','randi','linspace',
    'logspace','plot','subplot','disp','fprintf','sprintf','num2str','size','length','sum','mean','median','max',
    'min','abs','sqrt','sin','cos','tan','exp','log','log10','floor','ceil','round','mod','rem','prod','cumsum',
    'diff','sort','reshape','transpose','find','ismember','unique','setdiff','intersect','figure','hold','grid',
    'xlabel','ylabel','title','legend','axis','close','clear','clc','whos','who','save','load','eval','feval')

SCALA_KW = S('abstract','case','catch','class','def','do','else','extends','false','final','finally','for',
    'forSome','if','implicit','import','lazy','match','new','null','object','override','package','private',
    'protected','return','sealed','super','this','throw','trait','true','try','type','val','var','while','with',
    'yield','given','using','extension','opaque','enum','export','then','transparent','inline','infix','open',
    'end','derives','Int','Long','Float','Double','Boolean','Char','String','Unit','Any','Nothing','Option',
    'Some','None','List','Seq','Map','Set','Array','Vector','print','println','main')

HS_KW = S('case','class','data','default','deriving','do','else','foreign','if','import','in','infix',
    'infixl','infixr','instance','let','module','newtype','of','then','type','where','pure','return','fmap',
    'map','filter','foldl','foldr','zip','concat','length','head','tail','take','drop','reverse','print',
    'putStrLn','putStr','read','show','Maybe','Just','Nothing','Either','Left','Right','IO','Integer','Int',
    'Float','Double','Bool','Char','String','True','False','undefined','otherwise')

JL_KW = S('function','end','if','elseif','else','for','while','do','try','catch','finally','return','break',
    'continue','module','import','export','using','struct','mutable','abstract','primitive','type','const',
    'global','local','let','quote','macro','begin','in','isa','where','true','false','nothing','missing',
    'Inf','NaN','pi','print','println','length','size','push','pop','map','filter','reduce','sum','mean',
    'zeros','ones','rand','sort','append','setindex','getindex','Dict','Vector','Matrix','String','Int',
    'Float64','Bool','Symbol','Base','Core','Main','time','printf','show','assert')

ZIG_KW = S('const','var','fn','pub','export','extern','comptime','inline','noinline','struct','enum','union',
    'error','opaque','type','anytype','if','else','switch','while','for','break','continue','return','defer',
    'errdefer','try','catch','unreachable','suspend','resume','null','true','false','undefined','usingnamespace',
    'test','async','await','nosuspend','align','callconv','linksection','threadlocal','volatile','and','or','not',
    'u8','u16','u32','u64','i8','i16','i32','i64','f16','f32','f64','usize','isize','bool','void','print','std')

GROOVY_KW = S('def','class','interface','trait','enum','if','else','for','while','do','switch','case','default',
    'break','continue','return','try','catch','finally','throw','new','this','super','true','false','null','void',
    'int','long','float','double','boolean','char','byte','short','in','as','import','package','static','public',
    'private','protected','abstract','final','synchronized','volatile','transient','native','assert','instanceof',
    'println','print','it','each','eachWithIndex','findAll','collect','inject','with','find','any','every',
    'property','field','constructor','String','Integer','Boolean','List','Map','Set','Range','DateTime','use')

PS_KW = S('function','param','if','elseif','else','for','foreach','while','do','until','switch','break',
    'continue','return','try','catch','finally','throw','trap','begin','process','end','filter','class','enum',
    'using','module','import','export','new','set','get','remove','write','read','out','where','select','sort',
    'group','measure','format','invoke','test','wait','start','stop','restart','join','split','replace','contains',
    'eq','ne','lt','gt','le','ge','like','notlike','match','notmatch','and','or','not','xor','is','isnot','as',
    'true','false','null','foreach','where','Get-Content','Set-Content','Add-Content','Remove-Item','Copy-Item',
    'Move-Item','New-Item','Write-Output','Write-Host','Write-Error','Write-Warning','Read-Host','Get-ChildItem',
    'Set-Variable','Get-Variable','Clear-Host','exit','throw')

BAT_KW = S('echo','set','if','else','for','in','do','goto','call','rem','exit','pause','shift','title','color',
    'cd','mkdir','md','rmdir','rd','del','erase','copy','xcopy','move','ren','rename','type','find','findstr',
    'start','taskkill','choice','prompt','pushd','popd','setlocal','endlocal','errorlevel','not','exist',
    'defined','equ','neq','lss','leq','gtr','geq','assoc','ftype','verify','ver','vol','label','attrib',
    'replace','sort','more','tree','path','date','time','cls','break','disableextensions','enableextensions',
    'enabledelayedexpansion','disabledelayedexpansion')

VB_KW = S('Dim','Sub','Function','End','If','Then','Else','ElseIf','Select','Case','For','Each','Next','While',
    'Wend','Do','Loop','Until','Exit','Return','Call','ByRef','ByVal','Option','Explicit','Private','Public',
    'Friend','Static','Const','ReDim','Preserve','Type','Enum','Property','Get','Set','Let','With','Event',
    'Implements','Module','Class','Interface','New','Nothing','True','False','And','Or','Not','Xor','Mod','Is',
    'Like','To','Step','As','Integer','Long','Single','Double','String','Boolean','Byte','Date','Variant',
    'Object','MsgBox','InputBox','Range','Cells','Rows','Columns','WorksheetFunction','Workbook','Worksheet',
    'Application','Resume','On','Error','GoTo','GoSub','Declare','Lib','Alias','Optional','ParamArray','Handles',
    'Inherits','MustInherit','NotInheritable','Overrides','Overloads','Overridable','NotOverridable','Shared',
    'Shadows','ReadOnly','WriteOnly','Default','MustOverride')

ARDUINO_KW = S(CXX_KW, 'setup','loop','pinMode','digitalWrite','digitalRead','analogRead','analogWrite',
    'delay','delayMicroseconds','millis','micros','Serial','begin','end','println','print','read','available',
    'HIGH','LOW','INPUT','OUTPUT','INPUT_PULLUP','LED_BUILTIN','A0','A1','A2','A3','A4','A5','D0','D1','D2',
    'D3','D4','D5','D6','D7','D8','D9','D10','D11','D12','D13','attachInterrupt','detachInterrupt','interrupts',
    'noInterrupts','random','randomSeed','map','constrain','abs','min','max','pow','sqrt','sin','cos','tan',
    'tone','noTone','pulseIn','shiftIn','shiftOut')

MAKE_KW = S('PHONY','define','endef','include','export','override','private','vpath','ifeq','ifneq','ifdef',
    'ifndef','else','endif','wildcard','patsubst','notdir','dir','strip','foreach','eval','value','call',
    'filter','filter-out','sort','word','wordlist','firstword','lastword','abspath','realpath','shell',
    'subst','suffix','basename','addsuffix','addprefix','join','error','warning','info','MAKE','PWD',
    'CURDIR','MAKEFILE_LIST','DEFAULT_GOAL','SILENT','PHONY')

DOCKER_KW = S('FROM','RUN','CMD','ENTRYPOINT','COPY','ADD','ENV','ARG','LABEL','EXPOSE','WORKDIR','USER',
    'VOLUME','ONBUILD','STOPSIGNAL','HEALTHCHECK','SHELL','MAINTAINER','AS')

INI_KW = S('true','false','null','none','yes','no','on','off','True','False','None','YES','NO','ON','OFF')

TEX_KW = S('documentclass','usepackage','begin','end','document','section','subsection','subsubsection',
    'paragraph','subparagraph','chapter','part','item','textbf','textit','underline','emph','texttt','textrm',
    'itemize','enumerate','equation','align','table','figure','includegraphics','label','ref','cite','nocite',
    'bibliographystyle','bibliography','input','include','newcommand','renewcommand','definecolor','textcolor',
    'pagestyle','thispagestyle','title','author','date','maketitle','centering','caption','hline','multicolumn',
    'multirow','rowcolor','toprule','midrule','bottomrule','textwidth','linewidth','columnsep','hspace','vspace',
    'hfill','vfill','newpage','clearpage','cleardoublepage','footnote','marginpar','raisebox','scalebox',
    'resizebox','rotatebox','fbox','parbox','minipage','verbatim','lstlisting','tabular','array','frac','sqrt',
    'sum','int','prod','lim','rightarrow','leftarrow','Leftrightarrow','alpha','beta','gamma','delta','epsilon',
    'theta','lambda','mu','pi','sigma','phi','omega','infty','partial','nabla','pm','times','cdot','leq','geq',
    'neq','approx','in','notin','subset','subseteq','cup','cap','forall','exists','text','color','url','href')

CMAKE_KW = S('cmake_minimum_required','project','add_executable','add_library','target_link_libraries',
    'target_include_directories','target_compile_definitions','target_compile_options','include_directories',
    'add_subdirectory','add_definitions','add_compile_options','set','unset','if','elseif','else','endif',
    'foreach','endforeach','while','endwhile','function','endfunction','macro','endmacro','message','option',
    'find_package','find_library','find_path','find_file','install','configure_file','file','execute_process',
    'string','list','math','return','break','continue','include','cmake_policy','enable_language',
    'set_property','get_property','get_target_property','set_target_properties','add_custom_command',
    'add_custom_target','add_dependencies','aux_source_directory','source_group','target_sources',
    'write_basic_package_version_file','export','import','INTERFACE','PUBLIC','PRIVATE','STATIC',
    'SHARED','MODULE','EXECUTABLE')

SOL_KW = S('pragma','solidity','contract','interface','library','abstract','is','public','private','internal',
    'external','constant','immutable','view','pure','payable','storage','memory','calldata','struct','enum',
    'mapping','address','bool','string','bytes','uint','int','function','modifier','event','emit','require',
    'revert','assert','if','else','for','while','do','return','new','delete','this','msg','tx','block','now',
    'gas','value','sender','keccak256','abi','encode','decode','call','transfer','send','balance','selfdestruct',
    'fallback','receive','constructor','indexed','anonymous','virtual','override','returns','using','for')

ERL_KW = S('case','of','end','if','when','else','fun','receive','after','try','catch','throw','exit','error',
    'spawn','send','register','whereis','length','element','hd','tl','append','reverse','map','filter','foldl',
    'foldr','list_to_tuple','tuple_to_list','integer_to_list','list_to_integer','atom_to_list','list_to_atom',
    'io','format','put','get','module','export','import','record','define','include','ifdef','ifndef','endif',
    'undef','is_pid','is_atom','is_integer','is_float','is_list','is_tuple','is_map','is_binary','is_boolean',
    'is_function','is_record','self','nodes','node')

EX_KW = S('def','defmodule','defp','defmacro','defmacrop','defguard','defguardp','if','else','elsif','unless',
    'case','cond','for','with','receive','after','try','rescue','catch','raise','throw','exit','true','false',
    'nil','and','or','not','in','when','fn','do','end','alias','import','require','use','module','struct',
    'quote','unquote','super','rem','div','length','Enum','List','Map','String','IO','Process','spawn','send',
    'pid','__MODULE__','__ENV__','__FILE__','__DIR__','__CALLER__','Atom','Tuple','Keyword','Agent','Task',
    'GenServer','Supervisor','Application','elem','tuple_size','map_size','byte_size')

CLJ_KW = S('def','defn','defmacro','defmulti','defmethod','defprotocol','defrecord','deftype','defonce',
    'fn','let','if','if-let','when','when-let','cond','case','do','loop','recur','try','catch','finally',
    'throw','new','quote','and','or','not','nil','true','false','ns','in-ns','require','use','import','refer',
    'alias','map','filter','reduce','apply','assoc','dissoc','conj','into','first','rest','nth','count','get',
    'contains','seq','vec','hash-map','vector','list','str','println','print','slurp','spit','atom','swap',
    'reset','deref','prn','doseq','dotimes','binding','with-open','with-redefs','defn-','when-not','if-not',
    'comment','->','->>','cond->','some->')

FS_KW = S('let','rec','and','mutable','ref','val','member','abstract','override','inherit','interface','type',
    'module','namespace','open','struct','class','new','do','done','if','then','else','elif','match','with',
    'when','function','fun','for','to','downto','while','begin','try','finally','raise','failwith','async',
    'return','yield','true','false','null','unit','int','float','string','bool','char','byte','sbyte','int16',
    'uint16','int32','uint32','int64','uint64','nativeint','unativeint','decimal','bigint','option','list',
    'seq','array','map','filter','fold','reduce','printf','sprintf','printfn','ignore','fst','snd','Some',
    'None','Ok','Error','Result','typeof','nameof')

PAS_KW = S('program','unit','library','uses','const','var','type','procedure','function','begin','end','if',
    'then','else','case','of','for','to','downto','do','while','repeat','until','with','goto','exit','break',
    'continue','not','and','or','xor','div','mod','array','record','set','file','string','integer','real',
    'boolean','char','byte','word','longint','cardinal','shortint','smallint','int64','single','double',
    'extended','nil','true','false','class','object','interface','implementation','initialization','finalization',
    'inherited','override','virtual','dynamic','private','public','protected','published','property','read',
    'write','constructor','destructor','asm','label','absolute','external','far','near')

F90_KW = S('program','end','subroutine','function','module','use','implicit','none','integer','real','double',
    'precision','complex','character','logical','dimension','parameter','save','allocatable','intent','in',
    'out','inout','if','then','else','elseif','endif','do','while','enddo','select','case','selectcase',
    'default','exit','cycle','return','stop','call','allocate','deallocate','write','read','print','format',
    'contains','interface','procedure','type','class','abstract','private','public','protected','pure',
    'elemental','recursive','open','close','inquire','error','only','operator','assignment','extends','final',
    'bind','c','c_int','c_double','c_float','c_char','c_bool','c_size_t','iso_c_binding','iso_fortran_env')

ASM_KW = S('mov','add','sub','mul','div','imul','idiv','inc','dec','push','pop','pusha','popa','jmp','je',
    'jne','jg','jl','jge','jle','ja','jb','jae','jbe','jc','jz','jnz','call','ret','int','syscall','lea',
    'cmp','test','and','or','xor','not','neg','shl','shr','sal','sar','rol','ror','loop','nop','hlt','end',
    'org','db','dw','dd','dq','resb','resw','resd','section','global','extern','text','data','bss','code',
    'stack','model','small','large','segment','ends','assume','proc','endp','macro','endm','equ','include',
    'byte','word','dword','qword','ptr','offset','far','near','cs','ds','es','ss','fs','gs')

ASM_SP = S('al','ah','bl','bh','cl','ch','dl','dh','ax','bx','cx','dx','si','di','bp','sp','eax','ebx','ecx',
    'edx','esi','edi','ebp','esp','rax','rbx','rcx','rdx','rsi','rdi','rbp','rsp','rip','r8','r9','r10','r11',
    'r12','r13','r14','r15','xmm0','xmm1','xmm2','xmm3','xmm4','xmm5','xmm6','xmm7','st0','st1','st2','mm0','mm1')

CSS_KW = S('important','inherit','initial','unset','auto','none','block','inline','inline-block','flex',
    'grid','absolute','relative','fixed','sticky','static','center','left','right','top','bottom','hidden',
    'visible','bold','italic','normal','nowrap','wrap','repeat','no-repeat','cover','contain','transparent',
    'solid','dashed','dotted','hover','focus','active','visited','link','first-child','last-child','nth-child',
    'nth-of-type','before','after','root','first-line','first-letter','selection','not','is','where','has',
    'global','local','both','scroll','row','column','space-between','space-around','flex-start','flex-end',
    'stretch','baseline','uppercase','lowercase','capitalize','underline','line-through','pointer','crosshair',
    'ease','linear','ease-in','ease-out','ease-in-out','forwards','backwards','content-box','border-box',
    'rgb','rgba','hsl','hsla','calc','min','max','clamp')

CSS_ATTR = S('color','background','background-color','background-image','background-size','background-position',
    'background-repeat','background-attachment','background-clip','margin','margin-top','margin-right',
    'margin-bottom','margin-left','padding','padding-top','padding-right','padding-bottom','padding-left',
    'border','border-top','border-right','border-bottom','border-left','border-color','border-style',
    'border-width','border-radius','border-collapse','width','height','min-width','max-width','min-height',
    'max-height','display','position','top','right','bottom','left','float','clear','overflow','overflow-x',
    'overflow-y','visibility','opacity','z-index','font','font-family','font-size','font-weight','font-style',
    'font-variant','font-stretch','line-height','letter-spacing','word-spacing','text-align','text-decoration',
    'text-transform','text-indent','text-overflow','text-shadow','white-space','vertical-align','cursor',
    'box-shadow','box-sizing','flex-direction','flex-wrap','flex-flow','flex-grow','flex-shrink','flex-basis',
    'justify-content','align-items','align-content','align-self','order','gap','row-gap','column-gap',
    'grid-template','grid-template-columns','grid-template-rows','grid-template-areas','grid-column','grid-row',
    'grid-area','transform','transform-origin','transition','transition-property','transition-duration',
    'transition-timing-function','transition-delay','animation','animation-name','animation-duration',
    'animation-timing-function','animation-delay','animation-iteration-count','animation-direction',
    'animation-fill-mode','content','list-style','list-style-type','list-style-position','outline',
    'outline-color','outline-style','outline-width','pointer-events','user-select','appearance','object-fit',
    'object-position','filter','backdrop-filter','mix-blend-mode','place-items','place-content','place-self')

YAML_KW = S('true','false','null','yes','no','on','off','True','False','Null')

# Cangjie (Huawei) — official 71 reserved words
CJ_KW = S('as','abstract','break','Bool','case','catch','class','const','continue','Rune','do','else',
    'enum','extend','for','func','false','finally','foreign','Float16','Float32','Float64','if','in',
    'is','init','import','interface','Int8','Int16','Int32','Int64','IntNative','let','mut','main',
    'macro','match','Nothing','open','operator','override','prop','public','package','private','protected',
    'quote','redef','return','spawn','super','static','struct','synchronized','try','this','true','type',
    'throw','This','unsafe','Unit','UInt8','UInt16','UInt32','UInt64','UIntNative','var','VArray','where','while')

# Language registry: name -> config
LANG = {
    'python':     {'name':'Python','kw':PY_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False,'triple':('"""',"'''"),'atword':True},
    'c':          {'name':'C','kw':C_KW,'sp':C_SP,'hash':'macro','slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'c++':        {'name':'C++','kw':CXX_KW,'sp':C_SP,'hash':'macro','slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'java':       {'name':'Java','kw':JAVA_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False,'atword':True},
    'js':         {'name':'JavaScript','kw':JS_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':True},
    'typescript': {'name':'TypeScript','kw':TS_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':True,'atword':True},
    'go':         {'name':'Go','kw':GO_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'rust':       {'name':'Rust','kw':RUST_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'ruby':       {'name':'Ruby','kw':RUBY_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':True,'dollar':True},
    'shell':      {'name':'Shell','kw':SH_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':True,'dollar':True},
    'lua':        {'name':'Lua','kw':LUA_KW,'sp':set(),'hash':None,'slash':False,'dash':True,
                   'block':('--[[',']]'),'quotes':'"\'','backtick':False},
    'sql':        {'name':'SQL','kw':SQL_KW,'sp':set(),'hash':None,'slash':False,'dash':True,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'php':        {'name':'PHP','kw':PHP_KW,'sp':set(),'hash':'comment','slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False,'dollar':True},
    'c#':         {'name':'C#','kw':CS_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'css':        {'name':'CSS','kw':CSS_KW,'sp':CSS_ATTR,'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False,'dashident':True},
    'html':       {'name':'HTML','kw':set(),'sp':set(),'hash':None,'slash':False,'dash':False,
                   'block':('<!--','-->'),'quotes':'"\'','backtick':False,'tags':True},
    'json':       {'name':'JSON','kw':JSON_KW,'sp':set(),'hash':None,'slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False},
    'yaml':       {'name':'YAML','kw':YAML_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False,'colon_target':True},
    'cangjie':    {'name':'Cangjie','kw':CJ_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False,'triple':('"""',),'atword':True},
    'kotlin':     {'name':'Kotlin','kw':KT_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':True,'atword':True},
    'swift':      {'name':'Swift','kw':SW_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':True,'atword':True},
    'dart':       {'name':'Dart','kw':DART_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':True,'atword':True},
    'r':          {'name':'R','kw':R_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False},
    'perl':       {'name':'Perl','kw':PL_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False,'dollar':True},
    'objective-c':{'name':'Objective-C','kw':OBJC_KW,'sp':set(),'hash':'macro','slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False,'atword':True},
    'matlab':     {'name':'MATLAB','kw':MAT_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':('%{','%}'),'quotes':'"\'','backtick':False},
    'scala':      {'name':'Scala','kw':SCALA_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':True},
    'haskell':    {'name':'Haskell','kw':HS_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('{-','-}'),'quotes':'"\'','backtick':False},
    'julia':      {'name':'Julia','kw':JL_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':('#=','=#'),'quotes':'"\'','backtick':False,'atword':True,'triple':('"""',)},
    'zig':        {'name':'Zig','kw':ZIG_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False},
    'groovy':     {'name':'Groovy','kw':GROOVY_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':True,'dollar':True},
    'powershell': {'name':'PowerShell','kw':PS_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':('<#','#>'),'quotes':'"\'','backtick':True,'dollar':True},
    'batch':      {'name':'Batch','kw':BAT_KW,'sp':set(),'hash':None,'slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False},
    'vb':         {'name':'Visual Basic','kw':VB_KW,'sp':set(),'hash':None,'slash':False,'dash':False,
                   'block':None,'quotes':'"','backtick':False,'apos':True},
    'arduino':    {'name':'Arduino','kw':ARDUINO_KW,'sp':C_SP,'hash':'macro','slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'makefile':   {'name':'Makefile','kw':MAKE_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False,'colon_target':True,'dollar':True},
    'dockerfile': {'name':'Dockerfile','kw':DOCKER_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False},
    'ini':        {'name':'INI/TOML','kw':INI_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False,'semi':True},
    'markdown':   {'name':'Markdown','kw':set(),'sp':set(),'hash':None,'hashline':'keyword','slash':False,
                   'dash':False,'block':None,'quotes':'','backtick':True},
    'tex':        {'name':'LaTeX','kw':TEX_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False},
    'cmake':      {'name':'CMake','kw':CMAKE_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False},
    'solidity':   {'name':'Solidity','kw':SOL_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('/*','*/'),'quotes':'"\'','backtick':False},
    'erlang':     {'name':'Erlang','kw':ERL_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False},
    'elixir':     {'name':'Elixir','kw':EX_KW,'sp':set(),'hash':'comment','slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':True},
    'clojure':    {'name':'Clojure','kw':CLJ_KW,'sp':set(),'hash':None,'slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False,'semi':True,'dashident':True},
    'fsharp':     {'name':'F#','kw':FS_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('(*','*)'),'quotes':'"\'','backtick':False},
    'pascal':     {'name':'Pascal','kw':PAS_KW,'sp':set(),'hash':None,'slash':True,'dash':False,
                   'block':('{','}'),'quotes':'"\'','backtick':False},
    'fortran':    {'name':'Fortran','kw':F90_KW,'sp':set(),'hash':None,'slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False,'bang':True},
    'assembly':   {'name':'Assembly','kw':ASM_KW,'sp':ASM_SP,'hash':None,'slash':False,'dash':False,
                   'block':None,'quotes':'"\'','backtick':False,'semi':True},
}

# Extension -> language key
EXT2LANG = {
    '.py':'python','.pyw':'python',
    '.c':'c','.h':'c',
    '.cpp':'c++','.cc':'c++','.cxx':'c++','.hpp':'c++','.hh':'c++','.hxx':'c++','.c++':'c++',
    '.java':'java',
    '.js':'js','.jsx':'js','.mjs':'js','.cjs':'js',
    '.ts':'typescript','.tsx':'typescript','.mts':'typescript','.cts':'typescript',
    '.go':'go',
    '.rs':'rust',
    '.rb':'ruby',
    '.sh':'shell','.bash':'shell','.zsh':'shell',
    '.lua':'lua',
    '.sql':'sql',
    '.php':'php','.php3':'php','.php4':'php','.php5':'php','.phtml':'php',
    '.cs':'c#',
    '.css':'css','.scss':'css','.less':'css',
    '.html':'html','.htm':'html','.xhtml':'html',
    '.xml':'html','.svg':'html','.vue':'html',
    '.json':'json','.jsonc':'json','.json5':'json',
    '.yml':'yaml','.yaml':'yaml',
    '.cj':'cangjie',
    '.kt':'kotlin','.kts':'kotlin',
    '.swift':'swift',
    '.dart':'dart',
    '.r':'r',
    '.pl':'perl','.pm':'perl','.t':'perl',
    '.m':'ambig_m','.mm':'objective-c',
    '.scala':'scala','.sc':'scala',
    '.hs':'haskell','.lhs':'haskell',
    '.jl':'julia',
    '.zig':'zig',
    '.groovy':'groovy','.gradle':'groovy',
    '.ps1':'powershell','.psm1':'powershell','.psd1':'powershell',
    '.bat':'batch','.cmd':'batch',
    '.vb':'vb','.vba':'vb','.bas':'vb',
    '.ino':'arduino','.pde':'arduino',
    '.mk':'makefile','.mak':'makefile',
    '.ini':'ini','.cfg':'ini','.conf':'ini','.toml':'ini','.properties':'ini',
    '.md':'markdown','.markdown':'markdown',
    '.tex':'tex','.sty':'tex','.cls':'tex',
    '.cmake':'cmake',
    '.sol':'solidity',
    '.erl':'erlang','.hrl':'erlang',
    '.ex':'elixir','.exs':'elixir',
    '.clj':'clojure','.cljs':'clojure','.cljc':'clojure','.edn':'clojure',
    '.fs':'fsharp','.fsx':'fsharp','.fsi':'fsharp',
    '.pas':'pascal','.pp':'pascal',
    '.f':'fortran','.f90':'fortran','.f95':'fortran','.f03':'fortran','.f08':'fortran','.for':'fortran',
    '.asm':'assembly','.s':'assembly','.nasm':'assembly',
}

# Basename -> language key (extension-less files)
BASE2LANG = {
    'makefile':'makefile','gnumakefile':'makefile',
    'dockerfile':'dockerfile','containerfile':'dockerfile',
    'cmakelists.txt':'cmake','cmakelists.cmake':'cmake',
}

# Fallback for unknown extensions: minimal, comment-friendly.
DEFAULT_CFG = {'name':'Text','kw':set(),'sp':set(),'hash':'comment','slash':True,
               'dash':False,'block':('/*','*/'),'quotes':'"\'','backtick':False}


def detect_cfg(fname, head=None):
    ext = os.path.splitext(fname)[1].lower()
    key = EXT2LANG.get(ext)
    if key == 'ambig_m' and head:
        # .m is shared by MATLAB and Objective-C: sniff the first lines.
        low = '\n'.join(head[:8]).lower()
        if ('#import' in low or '@interface' in low or '@implementation' in low
                or '@property' in low or 'nsstring' in low):
            key = 'objective-c'
        else:
            key = 'matlab'
    if not key:
        key = BASE2LANG.get(os.path.basename(fname).lower())
    if key and key in LANG:
        return LANG[key]
    return DEFAULT_CFG


def display_len(text):
    n = 0
    for ch in text:
        if ch == '\t':
            n += TAB_WIDTH - (n % TAB_WIDTH)
        else:
            n += 1
    return n


def leading_display(line):
    """Display width of the leading whitespace of a line."""
    n = 0
    for ch in line:
        if ch == '\t':
            n += TAB_WIDTH - (n % TAB_WIDTH)
        elif ch == ' ':
            n += 1
        else:
            break
    return n


def tokenize_line(line, in_block, in_triple, cfg):
    bstart, bend = cfg.get('block') or ('', '')
    triples = cfg.get('triple') or ()
    t, i, n = [], 0, len(line)
    if in_block:
        if bstart:
            k = line.find(bend)
        else:
            k = -1
        if k < 0:
            return [(line, 'comment')], True, in_triple
        t.append((line[:k+len(bend)], 'comment'))
        i = k + len(bend)
        in_block = False
    if in_triple:
        k = line.find(in_triple)
        if k < 0:
            return t + [(line, 'string')], in_block, in_triple
        t.append((line[:k+len(in_triple)], 'string'))
        i = k + len(in_triple)
        in_triple = None
    while i < n:
        c = line[i]
        # full-line highlight (Markdown headings)
        if cfg.get('hashline') and i == 0 and line.lstrip().startswith('#'):
            return t + [(line, cfg['hashline'])], in_block, in_triple
        # colon target: Makefile rules, YAML keys
        if cfg.get('colon_target') and i == 0:
            j = 0
            while j < n and line[j] in ' \t': j += 1
            k = j
            while k < n and line[k] not in ' \t:#': k += 1
            if k < n and line[k] == ':':
                t.append((line[:k+1], 'macro')); i = k + 1
                continue
        # block comment
        if bstart and line[i:i+len(bstart)] == bstart:
            j = line.find(bend, i+len(bstart))
            if j < 0:
                return t + [(line[i:], 'comment')], True, in_triple
            t.append((line[i:j+len(bend)], 'comment'))
            i = j + len(bend)
            continue
        # triple-quoted strings (Python/Rust/Julia)
        if triples and line[i:i+3] in triples:
            td = line[i:i+3]
            j = line.find(td, i+3)
            if j < 0:
                return t + [(line[i:], 'string')], in_block, td
            t.append((line[i:j+3], 'string'))
            i = j + 3
            continue
        # hash: comment or macro
        if cfg.get('hash') == 'comment' and c == '#':
            t.append((line[i:], 'comment')); break
        if cfg.get('hash') == 'macro' and c == '#' and line[:i].strip() == '':
            t.append((line[i:], 'macro')); break
        # // line comment
        if cfg.get('slash') and c == '/' and i+1 < n and line[i+1] == '/':
            t.append((line[i:], 'comment')); break
        # -- line comment
        if cfg.get('dash') and c == '-' and i+1 < n and line[i+1] == '-':
            t.append((line[i:], 'comment')); break
        # ; line comment (ini, asm, clojure)
        if cfg.get('semi') and c == ';':
            t.append((line[i:], 'comment')); break
        # ! line comment (Fortran)
        if cfg.get('bang') and c == '!':
            t.append((line[i:], 'comment')); break
        # strings (incl. backtick templates)
        str_delims = set(ch for ch in cfg.get('quotes','"\'') if ch in '"\'')
        if cfg.get('backtick'):
            str_delims.add('`')
        if c in str_delims:
            q = c; j = i+1
            while j < n and line[j] != q:
                if line[j] == '\\': j += 1
                j += 1
            if j < n: j += 1
            t.append((line[i:j], 'string')); i = j; continue
        # ' line comment (Visual Basic)
        if cfg.get('apos') and c == "'":
            t.append((line[i:], 'comment')); break
        # html/xml tag names
        if cfg.get('tags') and c == '<':
            j = i + 1
            if j < n and line[j] == '/':
                j += 1
            if j < n and line[j].isalpha():
                while j < n and (line[j].isalnum() or line[j] in '-_:'):
                    j += 1
                t.append((line[i:j], 'tag')); i = j; continue
        # @word (annotations, ObjC directives, decorators, Julia macros)
        if cfg.get('atword') and c == '@':
            j = i + 1
            if j < n and (line[j].isalpha() or line[j] == '_'):
                while j < n and (line[j].isalnum() or line[j] == '_'):
                    j += 1
                t.append((line[i:j], 'keyword')); i = j; continue
        # $var (shell / powershell / perl / php / make)
        if cfg.get('dollar') and c == '$' and i+1 < n:
            j = i + 1
            if line[j] == '{' or line[j] == '(':
                closer = '}' if line[j] == '{' else ')'
                j += 1
                while j < n and line[j] != closer: j += 1
                j = min(j + 1, n)
            else:
                while j < n and (line[j].isalnum() or line[j] in '_:'):
                    j += 1
            if j > i + 1:
                t.append((line[i:j], 'var')); i = j; continue
        if c in ' \t':
            j = i
            while j < n and line[j] in ' \t': j += 1
            t.append((line[i:j], 'space')); i = j; continue
        if c.isdigit() or (c=='0' and i+1<n and line[i+1] in 'xXbB'):
            if c=='0' and i+1<n and line[i+1] in 'xXbB': j = i+2
            else: j = i
            while j < n and (line[j].isalnum() or line[j] in '.xXa-fA-FbBoOdD'): j += 1
            t.append((line[i:j], 'number')); i = j; continue
        if c.isalpha() or c == '_':
            j = i
            if cfg.get('dashident'):
                while j < n and (line[j].isalnum() or line[j] in '_-'): j += 1
            else:
                while j < n and (line[j].isalnum() or line[j] == '_'): j += 1
            w = line[i:j]
            if w in cfg['kw']: t.append((w,'keyword'))
            elif w in cfg.get('sp',set()): t.append((w,'register'))
            else: t.append((w,'text'))
            i = j; continue
        t.append((c,'text')); i += 1
    if not t:
        t.append(('','space'))
    return t, in_block, in_triple


def tokenize_full(lines, cfg):
    result, in_block, in_triple = [], False, None
    for line in lines:
        toks, in_block, in_triple = tokenize_line(line, in_block, in_triple, cfg)
        result.append(toks)
    return result


def wrap_line_tokens(tokens, max_px, cw, indent_px):
    text = ''.join(val for val, typ in tokens)
    if not text.strip():
        return [(tokens, False)]
    raw = text
    dl = display_len(raw.rstrip('\r\n'))
    if dl * cw <= max_px:
        return [(tokens, False)]

    max_chars = int(max_px / cw)
    parts = []
    remaining = raw
    is_first = True
    while remaining:
        avail = max_chars if is_first else int((max_px - indent_px) / cw)
        if avail < 10:
            avail = max_chars
        rem_dl = display_len(remaining.rstrip('\r\n'))
        limit_px = max_px if is_first else max_px - indent_px
        if rem_dl * cw <= limit_px:
            parts.append((tokenize_line(remaining, False, None, DEFAULT_CFG)[0], not is_first))
            break
        wrap_pos = -1
        pos = 0
        for i, ch in enumerate(remaining):
            if ch == '\t':
                pos += TAB_WIDTH - (pos % TAB_WIDTH)
            else:
                pos += 1
            if ch in WRAP_PUNCT:
                wrap_pos = i + 1
            elif ch == ' ' and pos > avail * 0.6:
                wrap_pos = i + 1
            if pos > avail and wrap_pos > 0:
                break
        if wrap_pos <= 0:
            pos = 0
            for i, ch in enumerate(remaining):
                if ch == '\t':
                    pos += TAB_WIDTH - (pos % TAB_WIDTH)
                else:
                    pos += 1
                if pos > avail:
                    wrap_pos = i
                    break
            if wrap_pos <= 0 or wrap_pos >= len(remaining):
                wrap_pos = len(remaining)
        if wrap_pos >= len(remaining):
            parts.append((tokenize_line(remaining, False, None, DEFAULT_CFG)[0], not is_first))
            break
        seg = remaining[:wrap_pos]
        parts.append((tokenize_line(seg, False, None, DEFAULT_CFG)[0], not is_first))
        remaining = remaining[wrap_pos:]
        is_first = False
    return parts


def compute_layout(lines, font_size):
    fs = round(font_size, 1)
    cw = round(fs * CHAR_RATIO, 1)
    lh = round(fs * LINE_HEIGHT_RATIO, 1)
    max_ln = len(str(len(lines)))
    gutter = round(max(44, max_ln * cw + 20), 1)
    code_x = round(gutter + 12, 1)
    code_w = round(A4_W - code_x - PAD_R, 1)
    baseline_ofs = round(fs * 0.85, 1)
    return fs, cw, lh, gutter, code_x, code_w, baseline_ofs


def compute_optimal_font(lines, base_fs, min_fs):
    max_digits = len(str(len(lines)))
    est_g = max(44, max_digits * (base_fs * CHAR_RATIO) + 20)
    est_w = A4_W - est_g - 12 - PAD_R
    max_chars = max((display_len(l.rstrip('\r\n')) for l in lines), default=1)
    if max_chars == 0: max_chars = 1
    fs = max(min_fs, min(base_fs, est_w / (max_chars * CHAR_RATIO)))
    est_g2 = max(44, max_digits * (fs * CHAR_RATIO) + 20)
    est_w2 = A4_W - est_g2 - 12 - PAD_R
    fs = max(min_fs, min(base_fs, est_w2 / (max_chars * CHAR_RATIO)))
    return round(fs, 1)


def gen_svg_page(display_lines, total_lines, page_num, total_pages,
                 fname, lang, font_key, fs, cw, lh, gutter, code_x, code_w, baseline_ofs):
    fn = FONT_NAMES.get(font_key, 'Cascadia Code')
    font_family = '"' + fn + '","Fira Code","Consolas","Courier New",monospace'
    ff_sans = 'Arial, Helvetica, sans-serif'
    wrap_px = WRAP_IDENT * cw

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {A4_W} {A4_H}">']
    out.append('<defs>')
    out.append(f'<clipPath id="pageClip"><rect x="0" y="0" width="{A4_W}" height="{A4_H}"/></clipPath>')
    out.append(f'<clipPath id="codeClip"><rect x="{code_x}" y="{PAD_T}" width="{code_w}" height="{CONTENT_H}"/></clipPath>')
    out.append('</defs>')
    out.append(f'<g clip-path="url(#pageClip)">')

    out.append(f'<rect width="{A4_W}" height="{A4_H}" fill="{BG}"/>')
    out.append(f'<rect x="0" y="0" width="{A4_W}" height="{HDR_H}" fill="{HDR_BG}"/>')
    out.append(f'<line x1="0" y1="{HDR_H}" x2="{A4_W}" y2="{HDR_H}" stroke="{HDR_BD}" stroke-width="1.5"/>')

    fl = font_key.capitalize()
    out.append(f'<text x="20" y="24" fill="#343a40" font-size="16" font-family="{ff_sans}" font-weight="700">FILE {fname}</text>')
    out.append(f'<text x="20" y="44" fill="#868e96" font-size="11" font-family="{ff_sans}">Pg {page_num}/{total_pages}  Lns {total_lines}  {lang}  Font {fl} {fs}px</text>')

    out.append(f'<rect x="0" y="{HDR_H}" width="{gutter+8}" height="{A4_H-HDR_H}" fill="{GT_BG}"/>')
    out.append(f'<line x1="{gutter+8}" y1="{HDR_H}" x2="{gutter+8}" y2="{A4_H}" stroke="{GT_BD}" stroke-width="1"/>')

    for idx, (tokens, is_cont, src_ln, lead) in enumerate(display_lines):
        if not src_ln:
            continue
        ly = PAD_T + idx * lh
        tb = ly + baseline_ofs
        out.append(f"<text x=\"{gutter-8}\" y=\"{tb:.1f}\" fill=\"{LN_COLOR}\" text-anchor=\"end\" font-size=\"{fs-1}\" font-family=\'{font_family}\'>{src_ln}</text>")

    out.append(f'<g clip-path="url(#codeClip)">')
    for idx, (tokens, is_cont, src_ln, lead) in enumerate(display_lines):
        ly = PAD_T + idx * lh
        tb = ly + baseline_ofs
        start_x = code_x + lead * cw
        tx = start_x
        seen_code = False
        for val, typ in tokens:
            if typ == 'space':
                if not seen_code:
                    continue
                for ch in val:
                    if ch == '\t':
                        col = int(round((tx - start_x) / cw))
                        ns = ((col // TAB_WIDTH) + 1) * TAB_WIDTH
                        tx = start_x + ns * cw
                    else:
                        tx += cw
            else:
                seen_code = True
                c = CO.get(typ, '#212529')
                e = val.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                out.append(f"<text x=\"{tx:.1f}\" y=\"{tb:.1f}\" fill=\"{c}\" font-size=\"{fs}\" font-family=\'{font_family}\'>{e}</text>")
                tx += len(val) * cw
    out.append('</g>')

    out.append(f'<text x="{A4_W//2}" y="{A4_H-10}" text-anchor="middle" fill="#adb5bd" font-size="10" font-family="{ff_sans}">- {page_num} -</text>')
    out.append('</g></svg>')
    return '\n'.join(out)


# ===== MAIN =====
BASE = os.getcwd()
for fname in FILES:
    src = os.path.join(BASE, fname)
    if not os.path.exists(src):
        print(f'SKIP {fname}')
        continue
    with open(src, 'r', encoding='utf-8') as f:
        lines = [l.rstrip('\r\n') for l in f.readlines()]
    cfg = detect_cfg(fname, lines)

    all_tokens = tokenize_full(lines, cfg)
    all_lead = [leading_display(l) for l in lines]
    fs = compute_optimal_font(lines, FONT_SIZE, MIN_FONT_SIZE)
    fs, cw, lh, gutter, code_x, code_w, baseline_ofs = compute_layout(lines, fs)
    lpp = max(1, int(CONTENT_H / lh))

    display_lines = []
    for idx, toks in enumerate(all_tokens):
        lead = all_lead[idx]
        avail_w = code_w - lead * cw
        indent_px = (lead + WRAP_IDENT) * cw
        wrapped = wrap_line_tokens(toks, avail_w, cw, indent_px)
        for i, (seg, isc) in enumerate(wrapped):
            cl = lead if i == 0 else lead + WRAP_IDENT
            display_lines.append((seg, isc, idx+1 if i == 0 else None, cl))

    td = len(display_lines)
    np = (td + lpp - 1) // lpp
    out_dir = os.path.join(BASE, fname + '_images')
    os.makedirs(out_dir, exist_ok=True)

    for p in range(1, np+1):
        s = (p-1) * lpp
        e = min(s + lpp, td)
        svg = gen_svg_page(display_lines[s:e], len(lines), p, np, fname, cfg['name'],
                           FONT_KEY, fs, cw, lh, gutter, code_x, code_w, baseline_ofs)
        with open(os.path.join(out_dir, f'code_page_{p}.svg'), 'w', encoding='utf-8') as f:
            f.write(svg)

    wraps = td - len(lines)
    print(f'{fname} [{cfg["name"]}]: {len(lines)} src -> {td} disp ({wraps} wraps), font={fs}px, {lpp} ln/pg, {np} pgs -> SVG OK')

    js = ('const fs=require("fs");const{Resvg}=require("@resvg/resvg-js");'
          'const dir=' + json.dumps(out_dir.replace('\\','\\\\')) + ';'
          'for(let p=1;p<='+str(np)+';p++){'
          'const s=dir+"\\\\code_page_"+p+".svg";'
          'const pn=dir+"\\\\code_page_"+p+".png";'
          'try{const d=fs.readFileSync(s,"utf8");const r=new Resvg(d,{background:"#ffffff"});'
          'const b=r.render();fs.writeFileSync(pn,b.asPng())}'
          'catch(e){console.log("  ERR:"+p+" "+e.message)}}')
    subprocess.run([NODE_EXE, '-e', js], check=True)
    print(f'{fname}: PNG OK')

    import img2pdf
    pngs = sorted([os.path.join(out_dir,f) for f in os.listdir(out_dir) if f.endswith('.png')],
                  key=lambda x: int(os.path.basename(x).replace('code_page_','').replace('.png','')))
    pdf_path = os.path.join(BASE, fname+'.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(img2pdf.convert(pngs))
    print(f'{fname}: PDF -> {pdf_path} ({os.path.getsize(pdf_path)//1024}KB)')

print('\n=== All done! ===')
