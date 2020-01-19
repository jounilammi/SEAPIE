"""Seapie is debugger like tool. SEAPIE stands for Scope Escaping Arbitary Python Injection Executor

usage as breakpoint: import seapie;seapie.seapie()
"""


import sys
import code
import codeop
import inspect
import traceback
from ctypes import pythonapi, py_object, c_int




class SingletonException(Exception):
    """helper exception used in case someone tries to initialize seapie instance instead of using the class without instance"""
    pass


class SeapieReplExitException(Exception):
    """raised to close seapie repl"""
    pass


class Seapie:
    """This class is only container. Use 'import seapie;seapie()'"""
    exit_permanently = False
    until_expr = None
    until_line = None
    scope = 0

    def __init__(self):
        """Initializes a seapie instance. seapie objects should not be initialized as the class is only a logical collection of functons"""
        # this behaviour is chosen so that code stepping can be implemented easier
        raise SingletonException("The Seapie class is a logical and instanceless singleton! Access the prompt with Seapie.repl() or convenient seapie() that points to Seapie.repl()")

    @classmethod
    def trace_calls(cls, frame, event, arg): # triggers on new frame (?) # tämä vastaa tracecallssia. kutsutaan scopn vaihdossa
    
    
        if frame.f_code.co_name == "seapie" : # dont trace seapie() itself if it is called multiple times. treat it as breakpoint
            return
        print("Executed line", frame.f_lineno, "entered", frame.f_code.co_name, "in", inspect.getsourcefile(frame)) # make this conditinal?
        return cls._repl_and_tracelines # tämö funktio suoritetaan joka kerta mutta tämän funktion sisältä ei lähdetä ?. tämä vastaa tracelinessia kutsutaan joka rivillä

    @classmethod
    def seapie(cls):
        if not cls.exit_permanently:
            if sys.gettrace() is not None: # tracking is not already active
                print("Stopping on breakpoint")
                cls.until_expr = None
                cls.until_line = None # remove !until conditions
            else:
                print("=" * 28 + "[ Starting seapie v2.0 ]" + "=" * 28)
                sys.settrace(cls.trace_calls)
                sys._getframe(1).f_trace = cls._repl_and_tracelines # set tracing in the calling scope immediately. settrace enables tracing not in the immediate scope




    @classmethod
    def _repl_and_tracelines(cls, frame, event, arg):
        """Main code injector loop"""
        try:
            if str(type(arg[2])) == "<class 'traceback'>":
                cls.until_expr = None
                cls.until_line = None
                print()
                traceback.print_exception(*arg)
                print()
                print("=" * 14 + "[ Entering post mortem. Program state is preserved ]" + "=" * 14)
                print("Further stepping will trace into intenal error handling and ultimatly crash")
        except TypeError: # arg was none
            pass
    
        while True:
            #print(sys.exc_info())
            codeblock = cls._step_until_handler(frame)
            if isinstance(codeblock, str):  # got magic string
                try:
                    cls.magic_handler(codeblock)
                    continue # magic is handled. get new command
                except SeapieReplExitException: # this is raised in magic handler if the repl should exit. magic handler never returns anything
                    return
                    #return cls._repl_and_tracelines # this might be needed but not really??
            else:
                #try:
                cls.arbitary_scope_exec(codeblock, 1) # 1 to escape the call to this scope
                #except Exception:  # catch arbitary exceptions from exec
                #    traceback.print_exc()

    @classmethod
    def _step_until_handler(cls, frame):
        """returns executable block of code or !step magic string if required by !until condition"""
        # no special until conditions
        if cls.until_line is None and cls.until_expr is None:
            return cls.single_prompt()
        # walk to line condition
        elif cls.until_line is not None:
            if cls.until_line != frame.f_lineno:
                return "!step"
            else:
                cls.until_line = None
                return cls.single_prompt()
        # walk until expression
        elif cls.until_expr is not None:
            try:
                if eval(cls.until_expr, frame.f_globals, frame.f_locals):
                    cls.until_expr = None
                    return cls.single_prompt()
                else:
                    return "!step"
            except NameError: # could not find variable to even try to satisfy condition. skipping.
                return "!step"

    @classmethod
    def arbitary_scope_exec(cls, codeblock, scope=0):
        parent = sys._getframe(cls.scope+scope+1)  # frame enclosing seapie() call. +1 escapes this arbitary_executor function itself
        # sys._getframe(scope+1).f_code.co_name # frame contains multiple things like the co_name
        parent_globals = parent.f_globals
        parent_locals = parent.f_locals
        try:
            exec(codeblock, parent_globals, parent_locals)
        except KeyboardInterrupt:  # emulate behaviour of ctrl+c
            print("\nKeyboardInterrupt")
        except Exception:  # catch arbitary exceptions from exec
            traceback.print_exc()
        # the following call forces update to locals()
        # adding new variables is allowed but calling them requires
        # some indirection like using exec() or a placeholder
        # otherwise you will get nameError when calling the variable
        # the magic value 1 stands for ability to introduce new variables. 0 for update-only
        pythonapi.PyFrame_LocalsToFast(py_object(parent), c_int(1))

    @classmethod
    def magic_handler(cls, magicstring):
        """Any magic strings starting with ! are handled here"""
        if magicstring in ("!help", "!h"):
            help = [" ",
            "(!h)elp       : Show this info block",
            "(!e)xit       : Close seapie, end tracing and resume main",
            "(!q)uit       : Exit and ignore all future breakpoints and post mortem",
            "",
            "(!t)raceback  : Show traceback excluding seapie",
            "(!l)ocals     : locals() in prettyprinted from",
            "(!g)lobals    : globals() in prettyprinted from",
            "(!w)here      : Show executing line and it's surroundings",
            "",
            "(!n)amespace  : Show current scope/namespace name",
            "(!+)namespace : Go down in callstack towards global scope",
            "(!-)namespace : Go up in callstack towards local scope",
            "(!0)namespace : Go back to currently executing scope",
            "",
            "(!s)tep       : Execute the next line of source code",
            "(!r)un        : Execute until next seapie() breakpoint or post mortem",
            "(!u)ntil 1234 : Step until line source code line 1234 or beakpoint or post mortem",
            "                └─> note: line must be executable code;",
            "                          not comment, def or class etc.",
            "(!u)ntil expr : Step until eval('my_expression') == True or breakpoint ir post mortem",
            "                ├─> e.g.: '!u x==10' or '!u bool(my_var)'",
            "                └─> note: eval is done in executing scope",
            "                          be aware of side effects",
            "(!c)ode obj   : Show source code of object",
            "                └─> e.g.: code my_function_name",
            ""]
            for line in help: print("    " + line)
        elif magicstring in ("!exit", "!e"):
            print("Continuing from line", sys._getframe(cls.scope+2).f_lineno)
            sys.settrace(None)
            sys._getframe(cls.scope+2).f_trace = None # set tracing in the calling scope immediately. settrace enables tracing not in the immediate scope
            # stepping is caused by re-entering seapie
            # SeapieReplExitException is used to exit seapie
            # and re-entering wont happen because tracing was unset
            raise SeapieReplExitException
        elif magicstring in ("!quit", "!q"):
            print("Continuing from line", sys._getframe(cls.scope+2).f_lineno, "and ignoring future breakpoints")
            sys.settrace(None)
            sys._getframe(cls.scope+2).f_trace = None # set tracing in the calling scope immediately. settrace enables tracing not in the immediate scope
            cls.exit_permanently = True
            # stepping is caused by re-entering seapie
            # SeapieReplExitException is used to exit seapie
            # and re-entering wont happen because tracing was unset
            raise SeapieReplExitException
        elif magicstring in ("!step", "!s"):
            if cls.scope != 0:
                print("Stepping is only available in current namespace")
                # print("Use '!step force' to bypass this warning")
            else:
                print("Executed line", sys._getframe(cls.scope+2).f_lineno)
                # stepping is caused by re-entering seapie
                # SeapieReplExitException is used to exit seapie
                # and it is re-entering because of tracing
                raise SeapieReplExitException
        elif magicstring in ("!run", "!r"):
            if cls.scope != 0:
                print("Stepping is only available in current namespace")
                #print("Use '!until expr force' to bypass this warning")
                #print("Use '!until 1234 force ' to bypass this warning")
                return
            cls.until_expr = "False" # this will run until hitting breakpoint as this will always evaluate to False
        elif magicstring[:7] in ("!until ", "!until") or magicstring[:3] in ("!u ", "!u"):
            if cls.scope != 0:
                print("Stepping is only available in current namespace")
                #print("Use '!until expr force' to bypass this warning")
                #print("Use '!until 1234 force ' to bypass this warning")
                return
            if magicstring[:6] == "!until":
                command = magicstring[7:]
            elif magicstring[:2] == "!u":
                command = magicstring[3:]
            # this try block sets stepping to line
            try:
                cls.until_line = int(command)
            except ValueError: # the command was not intended to be linenumber
                pass
            else:
                return
            # this block sets stepping to expressions
            try:
                eval(command) # check that the condition is valid
            except SyntaxError:
                print("'" + command + "'", "is not expression or line")
            except NameError:
                cls.until_expr = command # nameError might happen in this namespace but it might be valid condition somewhere else
            else:
                cls.until_expr = command
        elif magicstring in ("!traceback", "!t"):
            print()
            for call in traceback.format_stack()[:-2]:
                print(call)
        elif magicstring in ("!where", "!w"):
            # getsourcefile
            # getsourcelines
            current_line = sys._getframe(cls.scope+2).f_lineno
            path = inspect.getsourcefile(sys._getframe(cls.scope+2))
            with open(path, "r", encoding="utf-8") as file:
                source = file.read().splitlines()
            print()
            for line_no, line in enumerate(source):
                line_no +=1 # fix off by one. enumerate starts at 0
                if current_line == line_no:
                    print("--->")
                if abs(line_no+0.6 - current_line) <= 5: # +0.6 rounds so that even amount of lines is shown instead of odd
                    print("   ", line_no, line)
            print()
        elif magicstring in ("!locals", "!l"):
            # normal locals() cant be used here. it displays wrong scope.
            frame = sys._getframe(cls.scope+2)
            print()
            try:
                max_pad = len(max(frame.f_locals.keys(), key=len)) # lenght of longest var name
            except ValueError: # there are no keys
                return
            for name, value in frame.f_locals.items():
                pad = (max_pad-len(name))*" "
                print("   ", name + pad, "=", value)
            print()
        elif magicstring in ("!globals", "!g"):
            # normal globals() cant be used here. it displays wrong scope.
            frame = sys._getframe(cls.scope+2)
            print()
            try:
                max_pad = len(max(frame.f_globals.keys(), key=len)) # lenght of longest var name
            except ValueError: # there are no keys
                return
            for name, value in frame.f_globals.items():
                pad = (max_pad-len(name))*" "
                print("   ", name + pad, "=", value)
            print()
        elif magicstring in ("!namespace", "!n"):
            print(sys._getframe(cls.scope+2).f_code.co_name)
        elif magicstring in ("!+namespace", "!+"):
            try:
                sys._getframe(cls.scope+3)  # +2 like elsewhere to escape seapie itself and +1 for lookahead
            except ValueError:
                print("Call stack is not deep enough")
            else:
                cls.scope += 1
        elif magicstring in ("!-namespace", "!-"):
            if cls.scope == 0:
                print("You are at the top of stack (seapie is excluded)")
            else:
                cls.scope -= 1
        elif magicstring in ("!0namespace", "!0"):
            cls.scope = 0
        elif magicstring[:6] in ("!code ", "!code") or magicstring[:3] in ("!c ", "!c"):
            if magicstring[:6] == "!code ":
                argument = magicstring[6:]
            if magicstring[:3] == "!c ":
                argument = magicstring[3:]
            try:
                frame = sys._getframe(cls.scope+2)
                source = inspect.getsource(eval(argument, frame.f_globals, frame.f_locals))
            except :
                print(traceback.format_exc().splitlines()[-1])
            else:
                print()
                for line in source.splitlines():
                    print("    " + line.rstrip())
                print()
        else:
            print("Unknown magic command!")

    @staticmethod
    def single_prompt():
        """Interactive prompt that stays open until it can return single compiled expression/statement or magic string"""
        accumulator = ""
        raw_text = ""
        while True:
            try:
                if not accumulator:  # if on first line of incoming block
                    raw_text = input(str("(S2) " + sys.ps1))
                else:  # if on continuing line
                    raw_text = input(str("(S2) " + sys.ps2))
            except KeyboardInterrupt:  # emulate behaviour of ctrl+c
                print("\nKeyboardInterrupt")
                accumulator = ""
                continue
            except EOFError:  # emulate behaviour of ctrl+z
                sys.exit(1)
            if accumulator == "" and raw_text.startswith("!"):  # got magic
                return raw_text
            # this block should catch situation where two or more newlines
            # are entered during function definition or other such things
            if raw_text == "":
                try:
                    accumulator = "\n"+accumulator
                    codeop.compile_command(accumulator, "<input>", "single")
                except:  # catch exceptions compiling and reset
                    traceback.print_exc()
                    accumulator = ""
                    continue
            accumulator += "\n"+raw_text  # manually add newline after inputs
            try:
                result = code.compile_command(accumulator)
            except SyntaxError:  # allow incorrect commands to just pass thru
                # return accumulator # tämä muutos alla korjaa lambdat???
                traceback.print_exc()
                accumulator = ""
                continue
            if result is None:
                pass  # incomplete but possibly valid command
            else:
                return result

seapie = Seapie.seapie



# THIS BLOCK IS RUN AT IMPORT TIME
# it is INTENTIONALLY not placed inside of """ if name: '__main__': """
# as it is used to initialize the library during import
# and it is used to initialize sys.ps1 and sys.ps2

# support for sys.ps1 and sys.ps2
try:
    sys.ps1
except AttributeError:
    sys.ps1 = ">>> "
try:
   sys.ps2
except AttributeError:
    sys.ps2 = "... "

