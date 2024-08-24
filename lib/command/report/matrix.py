import os

import lib.database as d
from lib.function import global_value as g


def plot():
    df = d.aggregate.matrix_table()

    file_name = os.path.join(
        g.work_dir,
        f"{g.opt.filename}" if g.opt.filename else "matrix"
    )

    if g.opt.format == "csv":
        file_path = file_name + ".csv"
        df.to_csv(file_path)
    else:
        file_path = file_name + ".txt"
        df.to_markdown(file_path, tablefmt="outline")

    return (file_path)
