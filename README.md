# Overview

This repositery contains ANTIGONE source code, a model developped at EDF R&D to study long-term stakes of electricity market design.

# Credits

- The model was conceptualized and initiated by Marie Petitet and Marcelo Saguan at EDF R&D.
- The first version was developed by Eli RAKOTOMISA in 2019 (internship with École des Mines, France)
- Alicia Bassière and Luca Brunod Indrigo contributed in 2020 (interships with École Polytechnique - ENSAE, France and École Nationale des Pontes et Chaussées, France, respectively)
- Alexis Lebeau has been contributing since January 2021 (PhD with CentraleSupélec, France)

# Documentation

ANTIGONE is documented in `Lebeau et al. 2023 Long-Term Issues with the Energy-Only Market Design in the Context of Deep Decarbonization`

# Requirements

ANTIGONE was developed and runs on Python 3.8.3. Optimization models are implemented with the PuLP package that we interface with CPLEX (12.8). PuLP allows using alternative solvers.

Package versions are given in the packages.txt file.

# Running ANTIGONE

## Running the Generation Expansion Planning (GEP) module

```
python main_generation_mix_cible_V2.py path_to_dataset optim_type
```

where `optim_type` can be `LP` (unit numbers are continuous) or `MIP` (unit number are integer).


## Running the Market Simulator (MS) module

```
python main_merchantModule.py path_to_dataset 
```

# Dataset

A stylized Californian dataset is available [here](https://zenodo.org/record/8138257).
