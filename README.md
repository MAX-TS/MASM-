# MASM++ compiler

By using this compiler you will be able to esily write code to compile it later to mindustry assembly-like language.
In this language you will be granted with ability to write expressins with all operations that are available in mindustry:
```
a = asin(cos(b * -c) // 2)
```
also you will have jump instructions with expressions in them:
```
:some_place
  #some code
jump some_place x * 2 == 0 or y != 0
```
You will be able different variables:
```
define mem1 bank1
```
You will also will be able to easily access information from banks and cells:
```
define buffer_vert bank1
define buffer_face bank2

buffer_vert[x + 1] = buffer_face[adress] + 2
```
> ⚠️ **Note:** This compiler doesn't have error checking <ins>**AT ALL**</ins>!


---
### Credits

[MAX-TS](https://github.com/MAX-TS) - main developer

[Sergey5588](https://github.com/Sergey5588) - friend 


---
### License

[MIT](https://mit-license.org/)

