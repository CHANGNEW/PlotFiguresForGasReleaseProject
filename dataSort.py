import os, glob, re
import pandas as pd
from collections import defaultdict
import numpy as np

# 定义检测剧烈变化时间的函数
def detect_change_times(df, location_cols, threshold_factor=10):
    df = df.copy()
    for col in location_cols:
        df[col] = df[col].interpolate(method='linear', limit_direction='both')

    thresholds = {}
    start_times = {}

    for col in location_cols:
        diffs = np.diff(df[col])
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs)
        thresholds[col] = mean_diff + std_diff * threshold_factor

        # 判断是上升还是下降，并找到第一个变化点
        if col.startswith('Location'):
            idx_candidates = np.where(diffs > thresholds[col])[0]
            time_col = 'LAFTime'
        # elif col.startswith('P') and col[1:].isdigit():
        else:
            down_threshold = mean_diff - std_diff * threshold_factor
            idx_candidates = np.where(diffs < down_threshold)[0]
            time_col = 'Time(s)'

        if len(idx_candidates) > 0:
            start_idx = idx_candidates[0]  # 第一个变化点（在 diff 中的索引）
            start_times[col] = df.loc[start_idx + 1, time_col]
        else:
            start_times[col] = None

        try: min_value = min([v for v in start_times.values() if v is not None])
        except ValueError: min_value = None

    return min_value, start_times

def get_modified_times(df_out, threshold_factor=10):
    # 获得剧烈变化的时间点，并重新保存到新的时间列中
    location_cols = ['Location 1', 'Location 2', 'Location 3']
    p_cols = [f'P{i}' for i in range(1, 6)]
    f_cols = [f'F{i}' for i in range(1, 3)]
    laf_start_time, _ = detect_change_times(df_out, location_cols, threshold_factor)
    P_start_time, _ = detect_change_times(df_out, p_cols, threshold_factor)
    try: 
        threshold_factor = 2
        F_start_time, _ = detect_change_times(df_out, f_cols, threshold_factor)
    except RuntimeError:
        F_start_time = P_start_time
        print("Warning: f start time not se default Time(s) for")
    if laf_start_time is not None and P_start_time is not None:
        df_out['LAFTime'] = pd.to_numeric(df_out['LAFTime'], errors='coerce')
        df_out['Time(s)'] = pd.to_numeric(df_out['Time(s)'], errors='coerce')
        if pd.notna(laf_start_time): df_out['modified_LAFTime'] = df_out['LAFTime'] - float(laf_start_time) + 3
        if pd.notna(P_start_time): df_out['modified_Time(s)'] = df_out['Time(s)'] - float(P_start_time) + 3
        if pd.notna(F_start_time): df_out['f_start_Time(s)'] = df_out['Time(s)'] - float(F_start_time) + 4
    else: 
        print(f"Warning: data from {filename} does not have valid change times, trying new threshold adjustment") 
        raise KeyError
    return df_out
    
output_dir = 'csv'
os.makedirs(output_dir, exist_ok=True)

P_COLS = ['P1','P2','P3','P4','P5','P6','FX','FS','V1','V2','V3','V4','TUP','TDOWN']

file_groups = defaultdict(list)
for src in ['LAF', 'P', 'N', 'F']:
    for f in glob.glob(f'{src}/*.xlsx'):
        file_groups[os.path.basename(f)].append((src, f))

for filename, files in file_groups.items():
    folder_name = os.path.join("figures", os.path.splitext(filename)[0])
    os.makedirs(folder_name, exist_ok=True)
    data = {}
    for src, path in files:
        try:
            if src == 'LAF':
                df = pd.read_excel(path, header=None, engine='openpyxl')
                df = df.iloc[:, :4]
                df = df.replace(r'^\s*$', pd.NA, regex=True)
                df = df.dropna(how="all")
                df.columns = ['LAFTime', 'Location 1', 'Location 2', 'Location 3']
                df['LAFTime'] = df['LAFTime'].astype(str).str.replace('S', '', regex=False)
                data['LAF'] = df.reset_index(drop=True)
            elif src == 'P':
                df = pd.read_excel(path, engine='openpyxl')
                df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]
                # 把正文风向风速改成拼音大写
                col_rename_map={'风向': "FX", '风速':'FS'}
                df=df.rename(columns=col_rename_map)
                time_col = df.get('Time(s)')

                # 互换v2 v3这里以文件名称数字开头为判断依据
                # num = int(re.match(r'^(\d+)', filename).group(1))
                # if num >= 100: df = df.rename(columns={'V2':'V3', 'V3':'V2'})

                cols = [c for c in P_COLS if c in df.columns]
                df_clean = df[cols].reset_index(drop=True)
                df_clean.insert(0, 'Time(s)', time_col.values)
                
                # 替换负数为推测值
                df_clean.loc[df_clean['P1'] < 0.01, 'P1'] = pd.NA
                df_clean['P1'] = df_clean['P1'].interpolate(method='linear', limit_direction='both')

                data['P'] = df_clean
            elif src == 'N':
                print('Trying')
                df = pd.read_excel(path, engine='openpyxl')
                df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]
                df = df.replace(r'^\s*$', pd.NA, regex=True)
                data['N'] = df.reset_index(drop=True)
            elif src == 'F':
                df = pd.read_excel(path, engine='openpyxl')
                df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]
                df = df.replace(r'^\s*$', pd.NA, regex=True)
                data['F'] = df.reset_index(drop=True)
        except Exception as e:
            print(f"Error: fail to read {path}: {e}")

    if "N" not in data:
        print(f"Warning: not Find N files, return empty list: {filename}")
        data['N'] = pd.DataFrame(
            columns=['N1','N2','N3','N4','N5','N6','N7','N8','N9','N10','N11','N12','N13','N14','N15'])
    elif "F" not in data:
        print(f"Warning: not Find F files, return empty list: {filename}")
        data['F'] = pd.DataFrame(
            columns=['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11'])
        
    # 合并数据
    df_out = pd.concat([data['P'], data['N'], data['LAF'], data['F']], axis=1)

    # 线性插值 V4 列
    interpolate_cols = ['V4_extended', 'V3_extended', 'V2_extended', 'V1_extended']
    for col in interpolate_cols:
        df_out[col] = df_out[col.split('_')[0]].interpolate(method='linear', limit_direction='both')

    for thresholds in [10, 5, 2]:
        try: 
            df_out_cache = get_modified_times(df_out, threshold_factor=thresholds)
            break
        except KeyError: continue
    df_out = df_out_cache
    
    # 保存
    output = os.path.join(output_dir, filename.replace('.xlsx', '.csv'))
    df_out.to_csv(output, index=False, encoding='utf-8-sig')
    # break

print(f"Success: convey xlsx files into csv")
