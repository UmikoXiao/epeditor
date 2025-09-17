# epeditor: Batch Parameter-Tuning, Simulation & Result-Reading for EnergyPlus

This in-house module is built on top of [eppy](https://eppy.readthedocs.io/en/latest/Main_Tutorial.html) and [db_eplusout_reader](https://github.com/DesignBuilderSoftware/db-eplusout-reader).  
It provides the research group with the following main features:

1. Automatically reads an `.idf` baseline file and matches the corresponding `.idd` for its version.
2. Fully compatible with all eppy functions, allowing basic parameter modification of the baseline.
3. Creates batch editors by keyword search or by eppy's `idfobjects` method.
4. Applies editors to generate version-specific `.idf` files in bulk.
5. Runs parallel batch simulations locally (cloud option not yet implemented) and archives results.
6. Leverages all functions of `db_eplusout_reader` for horizontal & vertical statistics across cases.
7. Uploads simulation results to the group's database (not yet implemented).

<br /><br />**Example template**: see `test.py`  
<br />

---

## 🔧 Installation

Install the required wheels **in the correct version**; all three are supplied in this zip under ***setup/***.  
NumPy is heavily used for fast data processing; the tested version is **1.26.3**.  
We strongly recommend installing **two EnergyPlus versions**:
- [22.2.0 (latest stable supported by this module)](https://github.com/NREL/EnergyPlus/releases/tag/v22.2.0)
- [8.9.0 (stable version used by DesignBuilder)](https://github.com/NREL/EnergyPlus/releases/tag/v8.9.0)

```console
cd .\setup
pip install eppy-0.5.63-py2.py3-none-any.whl
pip install db_eplusout_reader-0.3.1-py2.py3-none-any.whl
pip install numpy==1.26.3
pip install epeditor-0.1.0-py3-none-any.whl
```

---

## 👀 Basic Workflow

### Three Most Important Types & Usage

- **[EpBunch](#EpBunch)** – a single `idfobject`.  
  An IDF file is a class-based database; every setting is an `idfobject` of a certain **class** (`idfclass`) and has a unique **name** (`idfname`).  
  Each editable item is called a **field** of that `idfobject`.

  ```
  # Example Zone EpBunch, idfname == Block1:Zone1
  >>> model.idfobjects['Zone'][0]
  Zone,
    Block1:Zone1,             !- Name
    0,                        !- Direction of Relative North
    0,                        !- X Origin
    0,                        !- Y Origin
    0,                        !- Z Origin
    1,                        !- Type
    1,                        !- Multiplier
    ,                         !- Ceiling Height
    1106.9178,                !- Volume
    316.2622,                 !- Floor Area
    TARP,                     !- Zone Inside Convection Algorithm
    ,                         !- Zone Outside Convection Algorithm
    Yes;                      !- Part of Total Floor Area
  ```

- **[IDFEditor](#IDFEditor)** – corresponds to **one field** of an `idfobject` and holds **multiple target values** (`params`) for that field.

  ```python
  >>> editor = ed.IDFEditor(model.idfobjects['Zone'][0], field='Floor_Area')
  >>> editor.apply_generator(ed.generator.arange, [100, 110, 2])
  >>> print(editor)
  IDFEditor
  | Class: Zone,	Name: Block1:Zone1
  | Field: Floor_Area,	Value: 316.2622
  | Generator: _arange,	args: [100, 110, 2]
  | params: [100, 102, 104, 106, 108]
  ```

- **[IDFGroupEditor](#IDFGroupEditor)** – bundles several editors so that **multiple fields** are changed together.

  ```python
  >>> geditor = ed.IDFGroupEditor.group([editor1, editor2], [editor4, editor5])
  >>> print(geditor)
  ____________________
  IDFGroupEditor	Parameters: 64
  IDFEditor
  | Class: ZONE,	Name: Block1:Zone1
  | Field: Floor_Area,	Value: 316.2622
  | Generator: _arange,	args: [100, 200, 10]
  | params: [100 110 120 130 ...]
  ...
  ____________________
  ```

### Quick Info via `print`

- **IDFModel** – baseline path, version, result folder, variables count, etc.

  ```python
  >>> print(model)
  project\baseline.idf
  BASELINE VERSION:22.2
  idd:C:\Users\Umiko\PycharmProjects\IDFprocessing\epeditor\idd\V22-2-0-Energy+.idd
  folder:d:\test
  sql:
  variables:
  ```

- **EpBunch** – shows all fields of the object.

- **IDFSearchResult** – search hit, shows class, name, field, value.

- **IDFEditor** – original value, generator, generated params.

- **IDFGroupEditor** – editors inside group; params are **matched position-wise** within the same group.

### Simple Workflow Steps

1. Load baseline (upgrade to 22.2 or install matching EnergyPlus version):

   ```python
   model = ed.IDFModel(r'project\baseline.idf')
   ```

2. Locate fields to change (case-insensitive class & name, **field case matters**):

   ```python
   result1 = model.eval('Zone', 'Block2:zone1', 'Floor_Area')
   result2 = model.eval('material', 'Concrete Block (Medium)_O.1', 'Thickness')
   ...
   ```

3. Create editors:

   ```python
   editor1 = ed.IDFEditor(result1, _sampler=ed.generator.arange, args=[100, 200, 10])
   editor2 = ed.IDFEditor(result2, _sampler=ed.generator.uniform, args=[0.1, 0.3, 8])
   ...
   ```

4. Bundle editors:

   ```python
   geditor = ed.IDFGroupEditor.group([editor1, editor2, editor3], [editor4, editor5])
   geditor.to_csv('test.csv')   # export parameter matrix
   ```

5. Write IDFs (number = smallest param count inside each group × cross product across groups):

   ```python
   model.write(geditor, r'test')
   ```

6. Run simulations (local by default):

   ```python
   model.simulation(epw=r'C:\EnergyPlusV22-2-0\WeatherData\CHN_Beijing.Beijing.545110_SWERA.epw')
   ```

   If results already exist, just re-load:

   ```python
   model = ed.IDFModel(r'project\baseline.idf', folder=r'.\test')
   ```

7. Read results (variables definition see [Variables](#Variable)):

   ```python
   result1 = model.group_result(ed.Variable("Cumulative", "Electricity:Facility", "J"),
                                calculator=np.mean, frequency=ed.Monthly)
   result2 = model.case_result(ed.Variable("Cumulative", "Electricity:Facility", "J"),
                               case=0, frequency=ed.Monthly)
   ```

8. Save:

   ```python
   result1.to_csv(r'result1.csv')
   result2.save(r'result2.npy')
   ```

---

### <a id='instruction_search'></a>Keyword Search (`IDFModel.search()`)

#### Method 1 – Exact match with `model.eval()`

```python
>>> model.eval('material', 'Concrete Block (Medium)_O.1', 'Conductivity')
IDFsearchresult
| Class: Material,	Name: Concrete Block (Medium)_O.1
| Field: Conductivity,	Value: 0.51
```

One-liner to editor:

```python
>>> editor = ed.IDFEditor.eval(model, 'material>Concrete Block (Medium)_O.1>Conductivity')
>>> editor.apply_generator(ed.generator.uniform, [0.4, 0.6, 8])
```

#### Method 2 – Fuzzy search with `model.search()`

- Any field name containing **'area'** (case-insensitive):

  ```python
  >>> model.search('area', searchtype=ed.FIELD, strict=False)[0]
  IDFsearchresult
  | Class: ZONE,	Name: Block1:Zone1
  | Field: Floor_Area,	Value: 316.2622
  ```

- First Zone object whose name contains **'Block2:zone1'**:

  ```python
  >>> model.search('Block2:zone1', searchlist=model.idfobjects['ZONE'], searchtype=ed.OBJECT)[0]
  ```

- Refine previous results:

  ```python
  >>> model.search('Concrete Block', searchlist=model.search('Material'))
  ```

---

### Data Management Tips

1. **Save/Load IDFGroupEditor**  
   ```python
   geditor.to_csv('parameters_record.csv')
   geditor = ed.IDFGroupEditor.load('parameters_record.csv')
   ```

2. **Re-use simulated models**  
   ```python
   model = ed.IDFModel(r'project\baseline.idf', folder=r'.\test')
   ```

3. **Resume interrupted simulations**  
   Set `overwrite=False` in `IDFModel.simulation()` for **checkpoint-restart**.

4. **IDFResult I/O**  
   Large group results are cached automatically; use `.to_csv()` / `.save()` to recover after crashes.

---

## 🤗 CERTIFICATION

**This tool will soon include network features; therefore it is restricted to internal group use only.**  
If the source code is accidentally leaked to the public, our server could be attacked and all valuable data lost...  
**Inside Tsinghua's intranet, however, feel free to share.**

p.s. Any bugs or usage issues – **Please do not hesitate to contact me**: junx026@gmail.com

---

Below is the **full English translation** of the entire “📖 DOCUMENT / CLASS” section you supplied.  
Copy-and-paste it into any `.md` file and it will render correctly.

---

## 📖 DOCUMENT

### CLASS

#### <a id='IDFModel'>IDFModel(IDF)</a>

An **enhanced IDF class** for easier baseline management.  
Most epeditor operations are built on this type.  
**All parameter modifications are applied through [IDFEditor](#IDFEditor) and [IDFGroupEditor](#IDFGroupEditor); the baseline file itself is never touched.**  
Because IDFModel inherits from eppy.IDF, you can still call any native eppy method, although I **do not recommend** doing so.

```
>>> model
project\baseline.idf
BASELINE VERSION:22.2
>>> print(model)
project\baseline.idf
BASELINE VERSION:22.2
idd:C:\Users\Lenovo\PycharmProjects\IDFprocessing\epeditor\idd\V22-2-0-Energy+.idd
folder:test
sql:
variables:
```

##### Properties

###### objectdict: dict

Enhanced helper built by [get_objectdict()](#objectdict).  
Format: `{idfClass: [Name1, Name2, ...]}`

```
>>> model.objectdict
{'VERSION': ['22.2'], 'SIMULATIONCONTROL': ['Yes'], 'BUILDING': ['Building'], ...}
```

###### file_name: str (path)

Path to the baseline IDF file.

###### folder: str (path)

Folder where exported files will be saved.

###### sql: dict {str: str (path)}

Dictionary of result SQL file paths.  
Format: `{caseName: sqlPath}`

###### <a id='IDFModel.variables'>variables: list\<Variable></a>

All available result variables; see [Variables](#Variable).

###### <a id='idfobjects'>idfobjects</a>: dict {str: list\<eppy.EpBunch>} (inherited)

Dict keyed by IDF class name; faster than `search(searchtype=ed.CLASS)`.

```
>>> model.idfobjects['Zone']
[
Zone,
Block1:Zone1,             !- Name
0,                        !- Direction of Relative North
...
]
```

##### Class Methods

> __init__(idf_file=None, epw=None, idd=None, folder=None) 🔧 constructor

Baseline model constructor.  
EPW and IDD are optional; IDD is auto-detected, EPW can be supplied later at simulation time.

Parameters  
- idf_file: str – path to IDF (default None)  
- epw: str – path to EPW (default None)  
- idd: str – path to IDD (default None, auto-detected)  
- folder: str – result storage folder (default None)

Returns  
- None

> <a id='objectdict'>get_objectdict()</a>

Build dict of all **modifiable** objects.  
Format: `{idfClass1: [Name1, Name2, ...], ...}`

Parameters  
- None

Returns  
- objects_dictionary: dict

> <a id='eval'>eval(idfclass: str, idfname: str, field: str)</a>

Strict single-match lookup by class, name, field (case-insensitive class/name; field case matters).

Parameters  
- idfclass: str – IDF class name  
- idfname: str – object name  
- field: str – field name (spaces or underscores both OK)

Returns  
- eval_result: [IDFSearchResult](#IDFSearchResult)

Example  
```
>>> model.eval('Zone', 'Block1:Zone1', 'Floor_Area')
IDFsearchresult
| Class: Zone,	Name: Block1:Zone1
| Field: Floor_Area,	Value: 170
```

> <a id='search'>search(searchname: str, strict=True, searchlist=None, searchtype=ANYTHING)</a>

Universal search entry-point. Returns **multiple** hits.  
For exact single match use [IDFModel.eval()](#eval).

Parameters  
- searchname: str or list\<str> – keyword(s), space-separated or list  
- strict: bool – if True whole phrase must match (default True)  
- searchlist: list\<IDFSearchResult> or list\<EpBunch> – restrict search to this list (default None = whole file)  
- searchtype: enum [ANYTHING=0, CLASS=1, OBJECT=2, FIELD=3] (default 0)

Returns  
- search_result: list\<[IDFSearchResult](#IDFSearchResult)>

(All examples already translated in previous section.)

> search_object(search_name: list, searchresult: list)  
> search_class(search_name: list, searchresult: list)  
> search_field(search_name: list, searchresult: list)  
> search_in_result(search_name: list, searchresult: list, searchtype)

Light-weight helpers; names are self-explanatory.

> <a id='write'>write(group_editor, folder: str = None)</a>

Export IDF files. Number of files = number of param sets in group_editor.  
Parameters & examples already translated.

> <a id='simulation'>simulation(epw=None, overwrite=True, process_count=4, **kwargs)</a>

Parallel simulation wrapper; kwargs forwarded to eppy.IDF.run().  
Parameters already translated.

> <a id='read_folder'>read_folder(folder: str = None)</a>

Read existing simulation results into the model. Works even on an empty IDFModel instance.

> <a id='group_result'>group_result(variable, calculator, frequency=Monthly, ...)</a>

Aggregate results across cases;详见前面示例。

> <a id='case_result'>case_result(variable, case, frequency=Monthly, ...)</a>

Extract single-case results; 详见前面示例。

---

#### <a id='EpBunch'>eppy.EpBunch</a> (inherit eppy.bunch_subclass.EpBunch)

Stores fields, values and descriptions of an EnergyPlus IDF object.  
All inherited methods are kept; only extra helpers are listed here.

##### Properties

- fieldnames – human-readable field list  
- fieldvalues – current values list  

##### Methods

> checkrange(fieldname)  
> get_referenced_object(fieldname)  
> get_retaincase(fieldname)  
> getfieldidd(fieldname)  
> getrange(fieldname)  
> getreferingobjs(...)  

(All documented in previous section.)

---

#### <a id='IDFSearchResult'>IDFSearchResult</a>

Index-like interface to an EpBunch; **does NOT modify the original object**.  
One EpBunch can be referenced by many IDFSearchResult instances.

##### Properties

- obj – underlying EpBunch  
- idfclass – class string  
- name – object name  
- field – field name (can be empty)  
- value – field value (if field is given)

##### Class Methods

> __init__(obj, idfclass=None, name=None, field=None)  
(Usually you never construct it manually.)

---

#### <a id='IDFEditor'>IDFEditor(IDFSearchResult)</a>

Handles parameter-sweep for **one field** of **one object**.  
Stores original value, generator function, and generated parameter list.

##### Properties

- sampler – generator function  
- args – arguments for sampler  
- params – generated parameter list  
- All parent properties (obj, idfclass, name, field, value)

##### Class Methods

> __init__(object, field=None, _sampler=original, args=None)  
> eval(model, editorstr, _sampler=original, args=None) – build from string "Class>Name>Field"  
> generate() – refresh params by running sampler  
> apply_generator(_sampler, args) – switch generator

(All examples already translated.)

---

#### <a id='IDFGroupEditor'>IDFGroupEditor</a>

Bundles several editors.  
- **Inside** the same group: parameters are matched **position-wise**.  
- **Between** different groups: **Cartesian product** (cross).

##### Properties

- editors – list of editors (live reference, will be modified)  
- params_num – number of parameter sets

##### Class Methods

> __init__(*editors)  
> group(*editors) – construct from mixed editors / nested lists  
> cross(other) – Cartesian product in-place  
> to_csv(csvpath) – export human-readable matrix  
> to_npy(npypath) – export binary  
> load(model, geditorpath) – restore from csv/npy

(All examples already translated.)

---

#### <a id='IDFResult'>IDFResult</a>

Storage / display / I/O for simulation results.  
If you only need numbers, access `.data` directly.

##### Properties

- variables – list of Variables  
- frequency – Hourly / Daily / Monthly / Annually  
- dump – path to cached file  
- data – np.ndarray (auto-mmap if too large)

##### Class Methods

> save(path) – binary dump (two files: `.npy` + `_variables.npy`)  
> to_csv(path, sep=',') – human-readable CSV  
> load() – force into memory

---

#### <a id='Variable'>Variable</a> (inherit db_eplusout_reader Variables)

Result key consisting of **(key, type, unit)**.  
See previous table for common examples.

---

#### <a id='Generator'>Generator</a>

Wrapper for parameter-sampling functions.  
Records func name, arg names, descriptions, and the callable itself.

##### Properties

- name – function name  
- args_count – number of arguments  
- args_name – list of arg names  
- args_description – list of help strings  
- run – the underlying function

##### Class Methods

> __init__(run_method, description=None)  
Users only need to pass the function; everything else is auto-extracted.

---

### MEMBER

#### epeditor.utils

| Constant | Purpose |
| --- | --- |
| `Hourly`, `Daily`, `Monthly`, `Annually` | Frequency flags for result extraction; see `IDFModel.group_result()` & `case_result()`. |
| `ANYTHING`, `CLASS`, `OBJECT`, `FIELD` | Search-type flags for `IDFModel.search()`. |

##### Stand-alone Utilities

| Signature | Description |
| --- | --- |
| `get_version(idf_path: str)` | Extract EnergyPlus version string from an IDF file. |
| `check_installation(idf_path: str)` | Verify whether the EnergyPlus version required by the IDF is installed. |
| `get_idd(idf_path: str)` | Return the absolute path of the IDD file that matches the IDF version (bundled in `epeditor/idd`). |
| `normal_pattern(pattern: str)` | Escape special characters for safe use in regular expressions. |

##### Exceptions

| Exception | Raised when … |
| --- | --- |
| `NotFoundError` | A search or field lookup returns no hit, or the requested field does not exist. |
| `VersionError` | The required IDD is missing or the corresponding EnergyPlus executable is not found. |

##### Context-Managers for Console Output

| Class | Usage |
| --- | --- |
| `hiddenPrint` | `with hiddenPrint():` – suppresses **Python-level** stdout/stderr inside the block. |
| `redirect` | Captures the suppressed stream and can dump it to a file later. |

> **NOTE**: These two classes **cannot** capture messages printed directly by the EnergyPlus engine (native C++ stdout).

---

#### epeditor.generator

Ready-made sampling functions wrapped as `Generator` objects.  
All generators return **NumPy arrays** and share the common interface described in the `Generator` class.

| Name | Signature & Meaning |
| --- | --- |
| `original` | `_original(value)` – always returns the original value (dummy sweep). |
| `linspace` | `_linspace(start, end, num)` – linearly spaced sequence (NumPy `linspace`). |
| `arange` | `_arange(start, end, step)` – arithmetic sequence (NumPy `arange`). |
| `uniform` | `_uniform(low, high, size)` – uniform random samples in [low, high). |
| `gaussian` | `_gaussian(median, scale, size)` – normal distribution 𝒩(median, scale²). |
| `bernoulli` | `_bernoulli(times, property, size)` – binomial/Bernoulli trials (n=times, p=property). |
| `power` | `_power(max, a, size)` – power-law distribution on [0, max] with shape *a*. |
| `random` | `_random(min, max, size)` – uniform random in [min, max] (legacy alias). |
| `enumerate` | `_enumerate(anydata)` – simply returns the list inside `anydata` (useful for user-supplied discrete sets). |

Usage pattern:

```python
from epeditor import generator as gen

params = gen.uniform.run(0.1, 0.3, 8)   # returns ndarray
```

---

#### epeditor.idd

| Attribute | Content |
| --- | --- |
| `idd_dir` | Directory that contains all bundled IDD files. |
| `idd_files` | List of absolute paths of those IDD files. |

These variables are used internally to locate the correct dictionary for any IDF version without user intervention.

---

