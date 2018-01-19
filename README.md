# Typpete


<p align="left">
  <img src ="https://raw.githubusercontent.com/caterinaurban/Typpete/master/typpete.png" width="30%"/>
</p>

## **SMT-based Static Type Inference for Python 3.x**


### Installation
- Build Z3 SMT solver. Follow the steps found [here](https://github.com/Z3Prover/z3 "Z3 GitHub Repository").
- In the root folder (the one which contains the package and `setup.py`), run `pip install .` or `python3 setup.py install`. Note that installation via `pip` is recommended since packages installed with `setup.py` are not uninstallable (They can only be uninstalled by manually deleting their files)

### Usage
You can run the inference with the following command
```
$ typpete <file_name> [flags]
```
Where flags is a space separated list of options for configuring the type inference. Each flag must have the following syntax: `--flag_name=flag_value`. For example, the following is a valid configuration flag: `--allow_attributes_outside_init=True`

The currently supported flags are the following:

| Flag   |      Description      |  Possible values |
|:----------:|:-------------:|:------:|
| ignore_fully_annotated_function |  Whether to ignore the body of fully annotated functions and just take the provided types for args/return | True, False* |
| enforce_same_type_in_branches |    Whether to allow different branches to use different types of same variable.   |  True, False* |
| allow_attributes_outside_init | Whether to allow to define instance attribute outside `__init__` |    True*, False |
| none_subtype_of_all | Whether to make None a subtype of all types. |    True*, False |

\* Default flag value

Example:
```
$ typpete python_file.py --ignore_fully_annotated_function=True
```
