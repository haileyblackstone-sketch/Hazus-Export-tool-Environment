r"""
patch_hazpy.py
--------------
Applies ALL fixes needed to make the legacy Hazus Export Tool (nhrap-hazus/export,
2021) work with modern Hazus installations. Safe to run multiple times (idempotent).
Re-run this any time the tool auto-updates hazpy and the fixes get wiped.

Run from inside the activated hazus_env:
    conda activate C:\condaenvs\hazus_env
    python legacy_hazus_patching.py

Fixes applied:
  1. AUTH:    Replace dead hardcoded SQL logins (SA / Gohazusplus_02) with
              Windows Authentication (Trusted_Connection).
  2. DRIVER:  Replace 'ODBC Driver 13' (not installed on modern Windows)
              with 'ODBC Driver 17'.
  3. DBNAME:  Qualify INFORMATION_SCHEMA lookups with the study region
              database. (Connection lands in 'master', so unqualified
              lookups silently return nothing -> "No essential facility
              loss information" even when the data exists.)
  4. OFFBYONE: Fix 'len(df) > 1' bug that silently drops facility types
              with exactly one damaged facility.
  5. SHAPEFILE: Split mixed-geometry facility exports into _Point.shp /
              _LineString.shp (shapefiles cannot store mixed geometry).
  6. DEBUG:   Replace useless 'Unexpected error: <class ...>' messages
              with full tracebacks so future problems are diagnosable.
"""
import os
import sys

# ---------------------------------------------------------------- locate hazpy
try:
    import hazpy
    HAZPY_DIR = os.path.dirname(hazpy.__file__)
except ImportError:
    HAZPY_DIR = sys.argv[0]
    if not os.path.isdir(HAZPY_DIR):
        sys.exit("ERROR: could not find hazpy. Activate the hazus_env "
                 "environment first (conda activate C:\\condaenvs\\hazus_env).")

print(f"Patching hazpy at: {HAZPY_DIR}\n")

applied, skipped = [], []


def patch_file(relpath, replacements):
    """Apply (old, new) replacements to one file, skipping any already done."""
    path = os.path.join(HAZPY_DIR, relpath)
    if not os.path.exists(path):
        skipped.append(f"{relpath} (file not found)")
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()
    changed = False
    for label, old, new in replacements:
        if old in src:
            src = src.replace(old, new)
            applied.append(f"{relpath}: {label}")
            changed = True
        elif new in src:
            skipped.append(f"{relpath}: {label} (already patched)")
        else:
            skipped.append(f"{relpath}: {label} (pattern not found)")
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)


def patch_all_py(replacements):
    """Apply replacements across every .py file in the hazpy package."""
    for root, _dirs, files in os.walk(HAZPY_DIR):
        for name in files:
            if name.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, name), HAZPY_DIR)
                patch_file(rel, replacements)


# ------------------------------------------------- 1 & 2 & 6: package-wide fixes
patch_all_py([
    ("AUTH pyodbc string",
     "UID=SA;PWD=Gohazusplus_02",
     "Trusted_Connection=yes"),
    ("AUTH sqlalchemy odbc string",
     "UID={3};PWD={4};TDS_Version=8.0;",
     "Trusted_Connection=yes;"),
    ("AUTH sqlalchemy url user",
     "hazuspuser:Gohazusplus_02@",
     "@"),
    ("AUTH sqlalchemy url trusted flag",
     "?driver=SQL+Server'",
     "?driver=SQL+Server&trusted_connection=yes'"),
    ("DRIVER 13 -> 17",
     "ODBC Driver 13 for SQL Server",
     "ODBC Driver 17 for SQL Server"),
    ("DEBUG tracebacks",
     'print("Unexpected error:", sys.exc_info()[0])',
     "import traceback; traceback.print_exc()"),
])

# ------------------------------------------------- 3 & 4: studyregion.py fixes
patch_file(os.path.join("legacy", "studyregion.py"), [
    ("DBNAME qualify INFORMATION_SCHEMA",
     "FROM INFORMATION_SCHEMA.COLUMNS",
     "FROM [{s}].INFORMATION_SCHEMA.COLUMNS"),
    ("DBNAME format arg",
     "f=facility, p=prefix)",
     "f=facility, p=prefix, s=self.name)"),
    ("OFFBYONE single-facility bug",
     "if len(df) > 1:",
     "if len(df) > 0:"),
])

# ------------------------------------------------- 5: shapefile geometry split
SHP_OLD = "gdf.to_file(path, driver='ESRI Shapefile')"
SHP_NEW = """geomTypes = list(gdf.geometry.geom_type.unique())
            if len(geomTypes) > 1:
                for gt in geomTypes:
                    gdf[gdf.geometry.geom_type == gt].to_file(path.replace('.shp', '_' + str(gt) + '.shp'), driver='ESRI Shapefile')
            else:
                gdf.to_file(path, driver='ESRI Shapefile')"""
patch_file(os.path.join("legacy", "studyregiondataframe.py"), [
    ("SHAPEFILE mixed-geometry split", SHP_OLD, SHP_NEW),
])

# ---------------------------------------------------------------- summary
print("APPLIED:")
for a in applied or ["  (nothing - everything was already patched)"]:
    print("  +", a)
print("\nSKIPPED (already patched or not applicable):")
for s in skipped:
    print("  -", s)

print("\nDone. Launch the tool with:  python hazus-export-tool.py")