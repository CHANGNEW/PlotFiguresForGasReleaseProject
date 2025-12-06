import shutil
from pathlib import Path

def copy_target_files(src_dir: Path, new_dir: Path, laf_names: list[str]):
    target_subdir = new_dir / src_dir.name
    target_subdir.mkdir(parents=True, exist_ok=True)

    src_files = sorted(
        [f for f in src_dir.iterdir() if f.is_file()],
        key=lambda x: x.name
    )
    pairs = zip(laf_names, src_files) if len(laf_names) == len(src_files) else zip(laf_names[:len(src_files)], src_files)

    for new_name, old_file in pairs:
        target_file = target_subdir / (new_name + old_file.suffix)
        if target_file.exists():
            print(f"Info: {target_file} files exist")
            continue
        shutil.copy2(old_file, target_file)

def copy_files(root_dir: str, src_name: str):
    new_dir = Path(".")
    laf_dir = Path(root_dir) / "LAF"
    p_dir = Path(root_dir) / "P"
    src_dir = Path(root_dir) / src_name
    laf_files = [
        f for f in laf_dir.iterdir()
        if f.is_file()
        and f.suffix.lower() == ".xlsx"
        and "所有工况" not in f.name  # 忽略包含“所有工况”的文件
    ]

    laf_names = sorted(f.stem for f in laf_files)
    laf_target_dir = new_dir / laf_dir.name
    laf_target_dir.mkdir(parents=True, exist_ok=True)

    for f in laf_files:
        target_file = laf_target_dir / f.name
        if target_file.exists():
            print(f"Info: LAF exist, skip: {target_file}")
        else:
            shutil.copy2(f, target_file)
    
    copy_target_files(p_dir, new_dir, laf_names)
    copy_target_files(src_dir, new_dir, laf_names)

copy_files("./burn", 'F')
copy_files("./unburn", 'N')

print("Sucess: all file renamed!")