<p align="center">
  <img src="https://raw.githubusercontent.com/devojyoti96/aNKflag/refs/heads/master/anklogo.png" alt="aNKflag Logo" width="200"/>
</p>
<p align="center">
  <h1>aNKflag</h1> An intelligent radio frequency interference (RFI) removal tool to work in multi-dimensions radio interferometric data.
</p>

## Background

<!-- start elevator-pitch -->

Radio interferometric observations are generally affected by terrestrial radio emission, known as radio frequency interference (RFI). **aNKflag** is an intelligent tool developed to detect and remove these RFIs both in time-frequency as well as in the Fourier domain, popularly known as **uv-domain** in radio interferometry.

- aNKflag works on UVFITS files
- Before flagging one needs to convert CASA measurement set to UVFITS
- After flagging one needs to convert UVFITS to CASA measurement set and copy the flags to original measurement set.
- These features are not provided in **aNKflag**, as these are readily available in CASA.
- This python version uses precompiled and containersed sourcecode of **aNKflag**, so no need to worry about installing C/C++ libraries.

<!-- end elevator-pitch -->

## Documentation

aNKflag documentation is available at: [ankflag.readthedocs.io]

[ankflag.readthedocs.io]: https://ankflag.readthedocs.io 

## Quickstart

<!-- start quickstart -->

**aNKflag** is distributed on [PyPI]. To use it:

1. Create conda environment with python 3

    ```text
    conda create -n ankflag_env python=3.10
    conda activate ankflag_env
    ```

2. Install aNKflag in conda environment

   ```text
   pip install ankflag
   ```

3. Initiate necessary metadata

    ```text
    run-ankflag init --datadir </full/path/to/data/directory>
    ```
    
    Contaniers will be stored in the data directory.
    
4. Run aNKflag

    ```text
    run-ankflag run </full/path/to/input/uvfits> </full/path/to/output/uvfits> --scratchdir </full/path/to/ankflag/workdir> --flagmode <uvbin/baseline> --npol <num_of_polarisation> --nthreads <num_of_cpu_threads> --target_type <target_type>
    ```    

That's all. You run aNKflag for analysing flagging RFI. It will create a UVFITS file with output file location 🎉.

[pypi]: https://pypi.org/project/meersolar/

<!-- end quickstart -->

## Acknowledgements

aNKflag is developed by Apurba Bera (ASTRON, NL) and Devojyoti Kansabanik (IAA-CSIC, Spain). If you use **aNKflag** for analysing your work, include the following statement in your paper

```text
RFI flagging is perfomed using aNKflag.
```

1. Cite aNKflag software in zenodo: https://doi.org/10.5281/zenodo.20568784

and cite the following papers.

2. [aNKflag paper: Kansabanik et al., ApJs 2023] [kansabanik2023]

[Kansabanik2023]: https://doi.org/10.3847/1538-4365/acac79


## License

This project is licensed under the MIT License.
