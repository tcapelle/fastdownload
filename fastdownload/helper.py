# AUTOGENERATED! DO NOT EDIT! File to edit: 00_helpers.ipynb (unless otherwise specified).

__all__ = ['Config', 'download_url', 'download_data', 'newest_folder', 'rename_extracted', 'file_extract']

# Cell
import yaml
import requests
import json
import hashlib
import tarfile, zipfile
from rarfile import RarFile
from nbdev.showdoc import *
from fastcore.all import *
from fastprogress.fastprogress import progress_bar

# Cell
class Config:
    "Setup config at `~/.fastai` unless it exists already."
    config_path = Path('~/.fastai').expanduser()
    config_file = config_path/'config.yml'

    def __init__(self):
        self.config_path.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists(): self.create_config()
        self.d = self.load_config()

    def __getitem__(self,k):
        k = k.lower()
        if k not in self.d: k = k+'_path'
        return Path(self.d[k])

    def __getattr__(self,k):
        if k=='d': raise AttributeError
        return self[k]

    def __setitem__(self,k,v): self.d[k] = str(v)
    def __contains__(self,k): return k in self.d

    def load_config(self):
        "load and return config if version equals 2 in existing, else create new config."
        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f)
            return config

    def create_config(self, cfg=None):
        "create new config with default paths"
        config = {
            'data_path':    str(self.config_path/'data'),
            'archive_path': str(self.config_path/'archive')
        }
        if cfg is not None:
            config = merge(config, cfg)
        self.save_file(config)

    def save(self): self.save_file(self.d)
    def save_file(self, config):
        "save config file at default config location `~/.fastai/config.yml`."
        with self.config_file.open('w') as f: yaml.dump(config, f, default_flow_style=False)

# Cell
def download_url(url, dest, overwrite=False, pbar=None, show_progress=True, chunk_size=1024*1024,
                timeout=4, retries=5):
    "Download `url` to `dest` unless it exists and not `overwrite`"
    if os.path.exists(dest) and not overwrite: return

    s = requests.Session()
    s.mount('http://',requests.adapters.HTTPAdapter(max_retries=retries))
    # additional line to identify as a firefox browser, see fastai/#2438
    s.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0'})
    u = s.get(url, stream=True, timeout=timeout)
    try: file_size = int(u.headers["Content-Length"])
    except: show_progress = False

    with open(dest, 'wb') as f:
        nbytes = 0
        if show_progress: pbar = progress_bar(range(file_size), leave=False, parent=pbar)
        try:
            if show_progress: pbar.update(0)
            for chunk in u.iter_content(chunk_size=chunk_size):
                nbytes += len(chunk)
                if show_progress: pbar.update(nbytes)
                f.write(chunk)
        except requests.exceptions.ConnectionError as e:
            fname = url.split('/')[-1]
            data_dir = dest.parent
            print(f'\n Download of {url} has failed after {retries} retries\n'
                f' Fix the download manually:\n'
                f'$ mkdir -p {data_dir}\n'
                f'$ cd {data_dir}\n'
                f'$ wget -c {url}\n'
                f'$ tar xf {fname}\n'
                f' And re-run your code once the download is successful\n')

# Cell
def download_data(src, dest, force_download=False):
    "Download `url` to `fname`."
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or force_download: download_url(src, dest)
    return dest

# Cell
def newest_folder(path):
    "Return newest folder on path"
    list_of_paths = path.glob('*')
    return max(list_of_paths, key=lambda p: p.stat().st_ctime)

# Cell
def rename_extracted(fname):
    "Rename file if different from fname"
    extracted = newest_folder(fname.parent)
    if not (extracted.name == fname.name): extracted.rename(fname)
    return fname

# Cell
def file_extract(fname, dest=None):
    "Extract `fname` to `dest` using `tarfile` or `zipfile`."
    if dest is None: dest = Path(fname).parent
    fname = str(fname)
    if   fname.endswith('gz'):  tarfile.open(fname, 'r:gz').extractall(dest)
    elif fname.endswith('zip'): zipfile.ZipFile(fname     ).extractall(dest)
    elif fname.endswith('rar'):
        with RarFile(fname, 'r') as rar_file: rar_file.extractall(dest)
    else: raise Exception(f'Unrecognized archive: {fname}')
    rename_extracted(Path(fname).with_suffix(''))