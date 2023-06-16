from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Include data files and submodules for NumPy
datas = collect_data_files('numpy')
hiddenimports = collect_submodules('numpy')
