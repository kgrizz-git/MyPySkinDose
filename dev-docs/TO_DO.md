# TO DO

- check what all the original flow uses for inputs
    - json files like beam_collimation, beam_rotations etc?
    - normalization settings?
    - should some of the example RDSRs use other data/settings from files in the repo?
    - examples are projecting dose onto strange parts of body - seems like maybe some offset (in a setting or in RDSR) isn't being applied
- K_IRP is all "-" in results table - took screenshot
- redesign GUI according to DESIGN.md
- download/export HTML button didn't work
    - not sure about others
- extend code to be able to handle dose event data exported from Radimetrics or similar software
    - these files may have more/less data than RDSR files
    - typically a table in csv format with one row per dose event
    - will likely have different column names that will need to be mapped/normalized
- add help docs explaining what all the settings are in the GUI and how to use it
- move Geometry tab to position 3 instead of 2