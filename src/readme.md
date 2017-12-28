# rules for load/unload/clear

* a `D` type can be converted to a `U` type module if a user load that module again manually
* a `U` type module can only be unloaded by the user, even if it's a dependency of another module
* a `D` type module can be unloaded automatically in the dependencies, and also by a user
* If a module to be unloaded by the user is a dependency of some other modules, show a warning message. But still unload it since it's unloaded by the user

# The format of `seq`

```
seq = {
            "<name of the module>": {
                'type': 'U' | 'D',   # U means  laoded by user, and D means by dependencies
                'deps': [...]
            },
            ...
      }
```
