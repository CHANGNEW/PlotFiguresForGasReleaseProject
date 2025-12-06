import os
import matplotlib.pyplot as plt
from matplotlib import rcParams
import pandas as pd
from typing import List, Optional, Tuple, Union, Any
import numpy as np
from pathlib import Path

class BaseLinePlotter:
    
    def plot(
        self,
        df: pd.DataFrame,
        y_cols: Union[str, List[str]], # 必须指定至少一个 y 列，可为单列或多列
        y2_cols: Optional[Union[str, List[str]]] = None, # 可选右边 y 轴列
        x_col: Optional[str] = None, # 可选 x 列，默认使用Time(s)
        colors: Optional[Union[str, List[str]]] = None,
        y_label: Optional[str] = None, # 可选设置y轴标签名称
        y2_label: Optional[str] = None,
        legend_names: Optional[List[str]] = None, 
        legend_loc: Optional[str] = 'best', # 图例默认位置
        legend_ncol: Optional[int] = 1, # 默认一列图例
        save_fig: Optional[bool] = False, # 默认不保存
        save_path: Optional[str] = 'figures/plot_for_instance',
        figsize: Optional[Tuple[float, float]] = (2.3*1.5, 1.88*1.5),
        yscale: Optional[str] = 'linear', # 'log',
        ylim: Optional[List[int]] = None,
        xlim: Optional[List[int]] = [0,60]
    ):
        # 标准化列输入
        y_cols = [y_cols] if isinstance(y_cols, str) else (y_cols or [])
        y2_cols = [y2_cols] if isinstance(y2_cols, str) else (y2_cols or [])
        if set(y_cols) & set(y2_cols): y2_cols = []
        all_cols = y_cols + y2_cols

        [colors, legend_names, x] = self._set_preprocess(colors, legend_names, x_col, all_cols, df)

        # 创建图形和轴
        self._set_fonts()
        _, ax1 = plt.subplots(figsize=figsize, layout='constrained', dpi=120)
        lines = self._plot_lines(ax1, df, x, y_cols, y2_cols, colors, y_label, y2_label)

        self._set_legend(lines, legend_names, legend_loc, legend_ncol)
        self._set_ticks(ax1, yscale, ylim, xlim, y_cols, df)
        self._save_figure(save_path, save_fig)

        # plt.show()

    def _set_preprocess(self, colors, legend_names, x_col, all_cols, df)-> list[Any]:
        # 处理 x 轴
        if x_col is None:
            if 'Time' in df.columns:
                x_col = 'Time'
            elif 'Time(s)' in df.columns:
                x_col = 'Time(s)'
            else:
                x_col = df.columns[0]  # 使用索引作为 x 轴
        x = df[x_col]
        num_lines = len(all_cols)

        # 处理颜色
        if colors is None:
            colors = [None] * num_lines
        elif isinstance(colors, str):
            colors = [colors] * num_lines
        elif len(colors) != num_lines:
            raise ValueError("colors should has the same length as lines")

        # 处理图例名称
        if legend_names is None:
            legend_names = all_cols
        elif len(legend_names) != num_lines:
            raise ValueError("legend_names should has the same length as lines")
        
        return [colors, legend_names, x]

    def _set_legend(
        self,
        lines: List[Any],
        legend_names: List[str],
        loc: str,
        ncol: int
    ) -> None:
        # labels = [line.get_label() for line in lines]
        handles = lines
        if ncol > 1:
            if len(handles) > 12:
                while len(handles) < 4 * 4: 
                    handles.append(plt.Line2D([], [], alpha=0))
                    legend_names.append('')
                handles = np.array(handles).reshape(4, 4).T.ravel()
                legend_names = np.array(legend_names).reshape(4, 4).T.ravel()
            else: 
                while len(handles) < 3 * 4: 
                    handles.append(plt.Line2D([], [], alpha=0))
                    legend_names.append('')
                handles = np.array(handles).reshape(3, 4).T.ravel()
                legend_names = np.array(legend_names).reshape(3, 4).T.ravel()
        legend=plt.legend(handles, legend_names, loc=loc, ncol=ncol, facecolor='w',
                          edgecolor='black', framealpha=0.8, fancybox=False,
                          columnspacing=0.5, 
                          fontsize='small' if ncol <= 1 else 'x-small'
                          )
        legend.get_frame().set_linewidth(0.2)

    def _set_fonts(self) -> None:
        config = {
            "font.family": 'serif',
            "mathtext.fontset": 'stix',
            "font.serif": ['Times New Roman'],
        }
        rcParams.update(config)

    def _save_figure(self, save_path: str, save_fig: bool) -> None:
        """保存图像，自动创建目录"""
        if save_fig:
            os.makedirs(os.path.dirname(f'{save_path}.png'), exist_ok=True)
            plt.savefig(f'{save_path}.png', dpi=200)
            plt.savefig(f'{save_path}.svg')
        else: 
            pass

    def _set_ticks(self, ax: plt.Axes, yscale: str,
                   ylim: list, xlim: list, 
                   y_cols: Union[str, List[str]],
                   df: pd.DataFrame) -> None:
        ax.set(yscale=yscale)
        if ylim != None: 
            ax.set(ylim=ylim)
            if ylim == [0, 360]: ax.set_yticks(range(0, 361, 60)) 
            if y_cols[-1] == "TDOWN": 
                y_min, y_max = ax.get_ylim()
                temp_max = max(df["TUP"].max(), df["TDOWN"].max())
                if temp_max > y_max: 
                    ax.set_ylim(y_min, temp_max*1.1)
                    print(f"Alert: maximum temprature: {temp_max}\n Reimplement"
                          " temperature range")
        else: 
            ax.set_ylim(bottom=0)
        if xlim != None: ax.set(xlim=xlim)
        ax.tick_params(which='both', direction='in')
        ax.set_xlabel("Times (s)")
        # ax.margins(y=0)

    def _plot_lines(
        self,
        ax1: plt.Axes,
        df: pd.DataFrame,
        x: pd.Series,
        y_cols: List[str],
        y2_cols: List[str],
        colors: List[Optional[str]],
        y_label: Optional[str],
        y2_label: Optional[str],
    ) -> List[Any]:
        """
        抽象方法：由子类实现具体绘图逻辑。
        返回所有 line 对象用于图例。
        """
        raise NotImplementedError("子类必须实现 _plot_lines 方法")

class SingleYLinePlotter(BaseLinePlotter):
    """单 y 轴绘图器"""
    
    def _plot_lines(
        self,
        ax1: plt.Axes,
        df: pd.DataFrame,
        x: pd.Series,
        y_cols: List[str],
        y2_cols: List[str],
        colors: List[Optional[str]],
        y_label: Optional[str],
        y2_label: Optional[str]
    ) -> List[Any]:
        if y2_cols:
            raise ValueError("SingleYLinePlotter not support multiple y axis")
        
        lines = []
        for i, col in enumerate(y_cols):
            if df[col].isnull().all(): raise RuntimeError(f"empty column {col}, skip plotting")
            line, = ax1.plot(x, df[col], color=colors[i], label=col, linewidth=0.5,)
            lines.append(line)

        ax1.set_ylabel(y_label)
        return lines

class DualYLinePlotter(BaseLinePlotter):
    """双 y 轴绘图器"""
    
    def _plot_lines(
        self,
        ax1: plt.Axes,
        df: pd.DataFrame,
        x: pd.Series,
        y_cols: List[str],
        y2_cols: List[str],
        colors: List[Optional[str]],
        y_label: Optional[str],
        y2_label: Optional[str],
    ) -> List[Any]:
        lines = []

        # 左 y 轴
        # for i, col in enumerate(y_cols[0]):
        for i, col in enumerate(y_cols):
            line, = ax1.plot(x, df[col], color=colors[i], linewidth=0.5, label=col)
            lines.append(line)
        ax1.set_ylabel(y_label)

        # 右 y 轴
        ax2 = ax1.twinx()
        offset = len(y_cols)
        for j, col in enumerate(y2_cols):
            line, = ax2.plot(x, df[col], color=colors[offset + j], lw=0.5, label=col)
            lines.append(line)
        ax2.set_ylabel(y2_label)
        self._set_right_ticks(ax2, df[col].max())

        return lines

    def _set_right_ticks(self, ax: plt.Axes, ymax: float) -> None:
        # super()._set_ticks(ax)
        ax.tick_params(axis='y', colors='red', direction='in')
        ax.yaxis.label.set_color('red')
        ax.spines['right'].set_color('red')
        ax.set_ylim(bottom=0)

class BatchPlotter:

    def __init__(self, SingleYLinePlotter, DualYLinePlotter):
        self.SingleYLinePlotter = SingleYLinePlotter
        self.DualYLinePlotter = DualYLinePlotter
        self.csv_dir = "./csv/"
        self.x_col = 'modified_Time(s)'
        self.save_dir = './figures'
        self.xlim = [0, 15]

    def plot_pressure_profiles(
        self, csv_file: Optional[Path] = None, df: Optional[pd.DataFrame] = None,
        debug: Optional[bool] = False,
        y_cols: Optional[List[str]] = ["P1", "P2", "P3", "P4", "P5"],
        save_fig: Optional[bool] = False,
        colors: Optional[Union[str, List[str]]] = ['k', 'r', 'b', 'g', 'purple'],
        **plot_kwargs
    ):
        print(f"Plotting: pressure profiles")
        
        def _read_plot(csv_file: Path, df: pd.DataFrame):
            plotter = self.SingleYLinePlotter()
            plotter.plot(
                df=df,
                y_cols=y_cols,
                x_col=self.x_col,
                xlim=self.xlim,
                save_fig=save_fig,
                save_path=f'{self.save_dir}/{csv_file.stem}/1_Pressure',
                colors=colors,
                yscale='log',
                y_label='Pressure (kPa)',
                legend_loc='upper right',
                **plot_kwargs
            )

        if csv_file is not None and df is not None:
            _read_plot(csv_file, df)
        else:
            for csv_file in Path(self.csv_dir).glob("*.csv"):
                df = pd.read_csv(csv_file)
                _read_plot(csv_file, df)
                if debug: break

    def plot_velocity_profiles(
        self, csv_file: Optional[Path] = None, df: Optional[pd.DataFrame] = None,
        debug: Optional[bool] = False,
        y_cols: Optional[List[str]] = ["V1_extended", "V2_extended", "V3_extended", "V4_extended"],
        save_fig: Optional[bool] = False,
        colors: Optional[Union[str, List[str]]] = ['k', 'r', 'b', 'g'],
        **plot_kwargs
    ):
        print(f"Plotting: velocity profiles")

        def _read_plot(csv_file: Path, df: pd.DataFrame):
            plotter = self.SingleYLinePlotter()
            plotter.plot(
                df=df,
                y_cols=y_cols,
                x_col=self.x_col,
                xlim=self.xlim,
                save_fig=save_fig,
                save_path=f'{self.save_dir}/{csv_file.stem}/2_velocity',
                colors=colors,
                yscale='linear',
                y_label=r'$v$ (m/s)',
                legend_loc='upper right',
                legend_names=['V1', 'V2', 'V3', 'V4'],
                **plot_kwargs
            )

        if csv_file is not None and df is not None:
            _read_plot(csv_file, df)
        else:
            for csv_file in Path(self.csv_dir).glob("*.csv"):
                df = pd.read_csv(csv_file)
                _read_plot(csv_file, df)
                if debug: break

    def plot_wind_direction_profiles(
        self, csv_file: Optional[Path] = None, df: Optional[pd.DataFrame] = None,
        debug: Optional[bool] = False,
        y_cols: Optional[List[str]] = ["FX"],
        save_fig: Optional[bool] = False,
        colors: Optional[Union[str, List[str]]] = ['k', 'r'],
        **plot_kwargs
    ):
        print(f"Plotting: wind direction profiles")

        def _read_plot(csv_file: Path, df: pd.DataFrame):
            plotter = self.DualYLinePlotter()
            plotter.plot(
                df=df,
                x_col=self.x_col,
                y_cols=y_cols,
                y2_cols=["FS"],
                xlim=self.xlim,
                ylim=[0, 360],
                save_fig=save_fig,
                save_path=f'{self.save_dir}/{csv_file.stem}/3_wind_direction',
                colors=colors,
                yscale='linear',
                y_label=r'wind direction ($ ^\circ$)',
                y2_label=r'$v$ (m/s)',
                legend_loc='upper left',
                legend_names=['wind direction', '$v$'],
                figsize=(2.5*1.5, 1.88*1.5),
                **plot_kwargs
            )

        if csv_file is not None and df is not None:
            _read_plot(csv_file, df)
        else:
            for csv_file in Path(self.csv_dir).glob("*.csv"):
                df = pd.read_csv(csv_file)
                _read_plot(csv_file, df)
                if debug: break

    def plot_temperature_profiles(
        self, csv_file: Optional[Path] = None, df: Optional[pd.DataFrame] = None,
        debug: Optional[bool] = False,
        y_cols: Optional[List[str]] = ["TUP", "TDOWN"],
        save_fig: Optional[bool] = False,
        colors: Optional[Union[str, List[str]]] = ['k', 'r'],
        **plot_kwargs
    ):
        print(f"Plotting: temperature profiles")

        def _read_plot(csv_file: Path, df: pd.DataFrame):
            plotter = self.SingleYLinePlotter()
            plotter.plot(
                df=df,
                y_cols=y_cols,
                x_col=self.x_col,
                xlim=self.xlim,
                save_fig=save_fig,
                save_path=f'{self.save_dir}/{csv_file.stem}/4_temperature',
                colors=colors,
                yscale='linear',
                y_label=r'Temperature ($ ^\circ $C)',
                legend_loc='upper right',
                ylim=[-20, 20],
                **plot_kwargs
            )

        if csv_file is not None and df is not None:
            _read_plot(csv_file, df)
        else:
            for csv_file in Path(self.csv_dir).glob("*.csv"):
                df = pd.read_csv(csv_file)
                _read_plot(csv_file, df)
                if debug: break

    def plot_concentration_profiles(
        self, csv_file: Optional[Path] = None, df: Optional[pd.DataFrame] = None,
        debug: Optional[bool] = False,
        y_cols: Optional[List[str]] = ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8",
                                       "N9", "N10", "N11", "N12", "N13", "N14", "N15"],
        save_fig: Optional[bool] = False,
        colors: Optional[Union[str, List[str]]] = ["#2C2C2C", "#FF0000", "#4040D3", "#00AB00", 
                                                   "#EA78EA", "#DAB97B", '#00FFFF', '#A52A2A', 
                                                   '#808000', '#FFA500', '#87CEEB', '#7CFC00',
                                                   '#FF69B4', '#FFFF00', '#FF00FF'],
        **plot_kwargs
    ):
        print(f"Plotting: concentration profiles")

        def _read_plot(csv_file: Path, df: pd.DataFrame):
            plotter = self.SingleYLinePlotter()
            try:
                plotter.plot(
                    df=df,
                    y_cols=y_cols,
                    x_col=self.x_col,
                    # x_col='Time(s)',
                    xlim=self.xlim,
                    save_fig=save_fig,
                    save_path=f'{self.save_dir}/{csv_file.stem}/5_concentration',
                    colors=colors,
                    yscale='linear',
                    y_label=r'Hydrogen concentration (%)',
                    legend_loc='upper right',
                    legend_ncol=4,
                    **plot_kwargs
                )
            except RuntimeError:
                print(f"Warning: empty N column, skip plotting: {csv_file.name}")

        if csv_file is not None and df is not None:
            _read_plot(csv_file, df)
        else:
            for csv_file in Path(self.csv_dir).glob("*.csv"):
                df = pd.read_csv(csv_file)
                _read_plot(csv_file, df)
                if debug: break

    def plot_sound_profiles(
        self, csv_file: Optional[Path] = None, df: Optional[pd.DataFrame] = None,
        debug: Optional[bool] = False,
        x_col: Optional[str] = 'modified_LAFTime',
        y_cols: Optional[List[str]] = ["Location 1", "Location 2", "Location 3"],
        save_fig: Optional[bool] = False,
        colors: Optional[Union[str, List[str]]] = ['k', 'r', 'b'],
        **plot_kwargs
    ):
        print(f"Plotting: sound profiles")
        
        def _read_plot(csv_file: Path, df: pd.DataFrame):
            plotter = self.SingleYLinePlotter()
            plotter.plot(
                df=df,
                y_cols=y_cols,
                xlim=self.xlim,
                x_col=x_col,
                save_fig=save_fig,
                save_path=f'{self.save_dir}/{csv_file.stem}/6_LAF',
                colors=colors,
                yscale='linear',
                y_label='LAF (dB)',
                legend_loc='upper left',
                **plot_kwargs
            )

        if csv_file is not None and df is not None:
            _read_plot(csv_file, df)
        else: 
            for csv_file in Path(self.csv_dir).glob("*.csv"):
                df = pd.read_csv(csv_file)
                _read_plot(csv_file, df)
                if debug: break

    def plot_fuel_profiles(
        self, csv_file: Optional[Path] = None, df: Optional[pd.DataFrame] = None,
        debug: Optional[bool] = False,
        y_cols: Optional[List[str]] = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8",
                                       "F9", "F10", "F11"],
        save_fig: Optional[bool] = False,
        colors: Optional[Union[str, List[str]]] = ["#2C2C2C", "#FF0000", "#4040D3", "#00AB00", 
                                                   "#EA78EA", "#DAB97B", '#00FFFF', '#A52A2A', 
                                                   '#808000', '#FFA500', '#87CEEB'],
        **plot_kwargs
    ):
        print(f"Plotting: fuel profiles")
    
        def _read_plot(csv_file: Path, df: pd.DataFrame):
            plotter = self.SingleYLinePlotter()
            try:
                plotter.plot(
                    df=df,
                    y_cols=y_cols,
                    # x_col=self.x_col,
                    xlim=self.xlim,
                    x_col='f_start_Time(s)',
                    save_fig=save_fig,
                    save_path=f'{self.save_dir}/{csv_file.stem}/5_burner_fuel',
                    colors=colors,
                    yscale='linear',
                    y_label=r'Radiation Heat Flux Density (kW/$m^2$)',
                    legend_loc='upper right',
                    legend_ncol=4,
                    **plot_kwargs
                )
            except RuntimeError and KeyError:
                print(f"Warning: empty F column, skip plotting: {csv_file.name}")

        if csv_file is not None and df is not None:
            _read_plot(csv_file, df)
        else:
            for csv_file in Path(self.csv_dir).glob("*.csv"):
                df = pd.read_csv(csv_file)
                _read_plot(csv_file, df)
                if debug: break

    def plot_figures(self, savefig : Optional[bool] = False, debug : Optional[bool] = False):
        for csv_file in Path(self.csv_dir).glob("*.csv"):
            print(f"\nReading: {csv_file}")
            # if int(csv_file.name.split('-')[0]) > 47: self.xlim = [0, 35]
            df = pd.read_csv(csv_file)
            self.plot_pressure_profiles(save_fig=savefig, csv_file=csv_file, df=df)
            self.plot_velocity_profiles(save_fig=savefig, csv_file=csv_file, df=df)
            self.plot_concentration_profiles(save_fig=savefig, csv_file=csv_file, df=df)
            self.plot_fuel_profiles(save_fig=savefig, csv_file=csv_file, df=df)
            self.plot_wind_direction_profiles(save_fig=savefig, csv_file=csv_file, df=df)
            self.plot_temperature_profiles(save_fig=savefig, csv_file=csv_file, df=df)
            self.plot_sound_profiles(save_fig=savefig, csv_file=csv_file, df=df)
            if debug: break

batch_plotter = BatchPlotter(SingleYLinePlotter, DualYLinePlotter)

# 开启debug模式只导出一个文件的一个图，节省时间
# batch_plotter.plot_pressure_profiles(save_fig=True, debug=False)
# batch_plotter.plot_velocity_profiles(save_fig=True, debug=True)
# batch_plotter.plot_concentration_profiles(save_fig=True, debug=True)
# batch_plotter.plot_fuel_profiles(save_fig=True, debug=False)
# batch_plotter.plot_wind_direction_profiles(save_fig=True, debug=False)
# batch_plotter.plot_temperature_profiles(save_fig=True, debug=False)
# batch_plotter.plot_sound_profiles(save_fig=True, debug=True)

# 如果检查没有问题，不想一条一条导出，也可以直接用下面的命令
# 开启debug模式只导出一个文件的所有图，节省时间
batch_plotter.plot_figures(savefig=True, debug=False)