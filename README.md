# epeditor: Batch Parameter-Tuning, Simulation & Result-Reading for EnergyPlus

This in-house module is built on top of [eppy](https://eppy.readthedocs.io/en/latest/Main_Tutorial.html) 
and [db_eplusout_reader](https://github.com/DesignBuilderSoftware/db-eplusout-reader).  
It provides the research group with the following main features:

1. Automatically reads an `.idf` baseline file and matches the corresponding `.idd` for its version.
2. Fully compatible with all eppy functions, allowing basic parameter modification of the baseline.
3. Creates batch editors by keyword search or by eppy's `idfobjects` method.
4. Applies editors to generate version-specific `.idf` files in bulk.
5. Runs parallel batch simulations locally (cloud option not yet implemented) and archives results.
6. Leverages all functions of `db_eplusout_reader` for horizontal & vertical statistics across cases.
7. Uploads simulation results to the group's database (not yet implemented).

---

## 🔧 Installation

This is a pure version for epeditor. To deploy the interface, please run the setup.py by python.  
if you do not have a python in your computer (really???) you can download here:  
[python](https://www.python.org/downloads/release/python-3137/)  

```console
python setup.py
```

---

## 👀 Any Instruction
- [python workflow](doc/workflow.md)
- [python workflow CN](doc/workflow_CN.md)
- [interface workflow](doc/EpeditorWUserManual.pdf)
- [interface workflow CN](doc/EpeditorWUserManual_CN.pdf)
- [EnergyPlus Reference](https://energyplus.net/assets/nrel_custom/pdfs/pdfs_v25.1.0/InputOutputReference.pdf)
- cloud deployment instruction: coming soon!

## 🤗 CERTIFICATION
Developed by Research team directed by **Prof. Borong Lin** from Key Laboratory of Eco Planning & Green Building, Ministry of Education, Tsinghua University.  
**For collaboration, Please contact:**  
linbr@tsinghua.edu.cn  
**If you have any technical problems, Please reach to:**  
junx026@gmail.com
---
