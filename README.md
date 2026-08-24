# Installing Hazus export guide
### Anaconda Download/Install
1. Download the [Anaconda Distribution & navigator](https://www.anaconda.com/download/success?reg=auth)
2. Run the installer as administrator and be sure to select all options to add environment variables to the PATH.
   
### Setup of Anaconda
1. Open the folder for `Hazus-Export-tool-Environment` and and copy folder `hazus_env` to `anaconda_location/envs/` folder.
   - Note: Since anaconda was installed, Python has been installed too!
2. Now right click inside `Hazas-Export-tool-Environment` and click `Open in Terminal`
3. Next open `Anaconda Navigator`. You should see `Environments`, click that and this click the arrow on `hazus_env`, and click `Open Terminal`.
4. A command prompt will open. navigate the the Hazus-Export-tool-Environment. by typing: `cd <path_to_directory>`.
5. Now type: `python legacy_hazus_patching.py "<path_to_anaconda_env/hazus_env>"` and hit enter key.
6. After this script runs, double-click `hazus-export-tool.py` and it should launch the export tool!
7. Be sure to select all export options except `Draft Email` when running the export tool.
