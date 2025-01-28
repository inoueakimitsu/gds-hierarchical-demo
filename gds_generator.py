"""ネストされたパターンを持つ GDSII ファイルを生成します。"""

from typing import Dict, Optional, Tuple, Union

import gdstk


# 配置の設定を行います。
class PlacementConfig:
    def __init__(self, rows: int, cols: int, spacing: float) -> None:
        self.rows = rows  # 行数を指定します。
        self.cols = cols  # 列数を指定します。
        self.spacing = spacing  # 間隔を nm 単位で指定します。

    @property
    def total_elements(self) -> int:
        return self.rows * self.cols


# デフォルトの配置設定を行います。
DEFAULT_CONFIG: Dict[str, Union[Dict[str, float], PlacementConfig]] = {
    "element": {"size": 5},  # エレメントのサイズを nm 単位で指定します。
    "sub_container": PlacementConfig(rows=2, cols=2, spacing=10),
    "container": PlacementConfig(rows=2, cols=2, spacing=25),
    "top": PlacementConfig(rows=2, cols=2, spacing=50),
}

# GDSII ライブラリを作成します。
lib = gdstk.Library()


def create_element(size: Optional[float] = None) -> gdstk.Cell:
    """エレメントを作成します。

    Parameters
    ----------
    size : float, optional
        エレメントのサイズを nm 単位で指定します。デフォルトは None です。その場合は DEFAULT_CONFIG から値を取得します。

    Returns
    -------
    gdstk.Cell
        作成されたエレメントのセルを返します。
    """
    if size is None:
        size = DEFAULT_CONFIG["element"]["size"]

    cell = lib.new_cell("element")
    rect = gdstk.rectangle((0, 0), (size, size))
    cell.add(rect)
    return cell


def create_sub_container(config: Optional[PlacementConfig] = None) -> gdstk.Cell:
    """サブコンテナーを作成します。

    Parameters
    ----------
    config : PlacementConfig, optional
        配置の設定を行います。デフォルトは None です。その場合は DEFAULT_CONFIG から値を取得します。

    Returns
    -------
    gdstk.Cell
        作成されたサブコンテナーのセルを返します。
    """
    if config is None:
        config = DEFAULT_CONFIG["sub_container"]

    cell = lib.new_cell("sub_container")
    element = lib.cells[0]
    element_size = DEFAULT_CONFIG["element"]["size"]

    # エレメントを配置します。
    for row in range(config.rows):
        for col in range(config.cols):
            x = col * (element_size + config.spacing)
            y = row * (element_size + config.spacing)
            ref = gdstk.Reference(element, (x, y))
            cell.add(ref)

    return cell


def calculate_sub_container_size() -> Tuple[float, float]:
    """サブコンテナーの全体サイズを計算します。

    Returns
    -------
    tuple of float
        (width、height) の形式でサブコンテナーの幅と高さを返します。
    """
    sub_config = DEFAULT_CONFIG["sub_container"]
    element_size = DEFAULT_CONFIG["element"]["size"]
    width = (sub_config.cols - 1) * sub_config.spacing + sub_config.cols * element_size
    height = (sub_config.rows - 1) * sub_config.spacing + sub_config.rows * element_size
    return width, height


def calculate_container_size() -> Tuple[float, float]:
    """コンテナーの全体サイズを計算します。

    Returns
    -------
    tuple of float
        (width、height) の形式でコンテナーの幅と高さを返します。
    """
    container_config = DEFAULT_CONFIG["container"]
    sub_width, sub_height = calculate_sub_container_size()
    width = (
        container_config.cols - 1
    ) * container_config.spacing + container_config.cols * sub_width
    height = (
        container_config.rows - 1
    ) * container_config.spacing + container_config.rows * sub_height
    return width, height


def create_container(config: Optional[PlacementConfig] = None) -> gdstk.Cell:
    """コンテナーを作成します。

    Parameters
    ----------
    config : PlacementConfig, optional
        配置の設定を行います。デフォルトは None です。その場合は DEFAULT_CONFIG から値を取得します。

    Returns
    -------
    gdstk.Cell
        作成されたコンテナーのセルを返します。
    """
    if config is None:
        config = DEFAULT_CONFIG["container"]

    cell = lib.new_cell("container")
    sub_container = lib.cells[1]

    # サブコンテナーのサイズを取得します。
    sub_width, sub_height = calculate_sub_container_size()

    # サブコンテナーを配置します。
    for row in range(config.rows):
        for col in range(config.cols):
            x = col * (sub_width + config.spacing)
            y = row * (sub_height + config.spacing)
            ref = gdstk.Reference(sub_container, (x, y))
            cell.add(ref)

    return cell


def create_top(config: Optional[PlacementConfig] = None) -> gdstk.Cell:
    """トップを作成します。

    Parameters
    ----------
    config : PlacementConfig, optional
        配置の設定を行います。デフォルトは None です。その場合は DEFAULT_CONFIG から値を取得します。

    Returns
    -------
    gdstk.Cell
        作成されたトップのセルを返します。
    """
    if config is None:
        config = DEFAULT_CONFIG["top"]

    cell = lib.new_cell("top")
    container = lib.cells[2]

    # コンテナーのサイズを取得します。
    container_width, container_height = calculate_container_size()

    # コンテナーを配置します。
    for row in range(config.rows):
        for col in range(config.cols):
            x = col * (container_width + config.spacing)
            y = row * (container_height + config.spacing)
            ref = gdstk.Reference(container, (x, y))
            cell.add(ref)

    return cell


def main(
    configs: Optional[Dict[str, Union[Dict[str, float], PlacementConfig]]] = None,
) -> None:
    """メイン処理を実行します。

    Parameters
    ----------
    configs : dict, optional
        各レベルの配置設定を上書きする辞書を指定します。デフォルトは None です。その場合は DEFAULT_CONFIG を使用します。

    Notes
    -----
    出力ファイルは以下の通りです。
        - output.gds: GDSII ファイルを出力します。
        - output.svg: SVG 画像ファイルを出力します。
    """
    if configs is None:
        configs = DEFAULT_CONFIG

    # 各セルを作成します。
    create_element(configs.get("element", {}).get("size"))
    create_sub_container(configs.get("sub_container"))
    create_container(configs.get("container"))
    create_top(configs.get("top"))

    # GDSII ファイルを保存します。
    lib.write_gds("output.gds")

    # 画像ファイルを生成します。
    top_cell = lib.cells[3]
    top_cell.write_svg("output.svg")


if __name__ == "__main__":
    # カスタム設定で実行します。
    custom_configs = {
        "element": {"size": 5},
        "sub_container": PlacementConfig(rows=3, cols=3, spacing=10),
        "container": PlacementConfig(rows=2, cols=3, spacing=60),
        "top": PlacementConfig(rows=2, cols=2, spacing=200),
    }
    main(custom_configs)
