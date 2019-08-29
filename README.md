_Have you ever wanted to debug something without bothering to learn how to use a real debugger?_  
_Seapie opens python prompt when you need something quick, dirty and interactive in your code._

<img src="https://raw.githubusercontent.com/hirsimaki-markus/SEAPIE/master/images/SEAPIE.png" width="70" height="70"/>

# SEAPIE


```SEAPIE``` stands for ``Scope Escaping Arbitrary Python Injection Executor``

You can call ``seapie()`` anywhere in your code to open python interpeter like console that can edit global, local
and any other variable available in any scope that is in the current call stack.

## Example

```
>>> import seapie
>>>
>>> def test():
...     x = 1
...     seapie.seapie()
...     print("new value of x is", x)
...
>>> test()
SEAPIE v0.4 type !help for SEAPIE help
>>> x = 2 # anow we change the value of x in scope of test()
>>> !exit
new value of x is 2
```

## Known issues

Assinging completely new variables via seapie prompt works but calling variable that has only been defined in seapie prompt
will result in NameError. You can try circumventing this by calling and parsing locals() to get your newly and hackily
assinged variable name and using exec() instead of directly calling the variable. Same goes for importing new modules as they
act like variables. So if you import datetime in seapie prompt you should call exec("print(datetime)") instead of calling
print(datetime) in your main program. This happends because exec() doesn't optimized variable lookup unlike just directly
calling said variables

You most likely shouldn't structure your code to call variables that have been defined via interactive prompt only but you
can do it if you wish to shoot yourself in the foot.

## Todo
* Implement support for global variables
* Implement way to easily change scope inside the prompt

## Unlicensing
Distributed under [The Unlicense](https://choosealicense.com/licenses/unlicense/) <img src="https://raw.githubusercontent.com/hirsimaki-markus/SEAPIE/master/images/unlisence.png" width="12" height="12"/> by Markus Hirsimäki in 2019
