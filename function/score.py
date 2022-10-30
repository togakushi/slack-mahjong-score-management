def CalculationPoint(rpoint, rank): # 順位点計算
    oka = 20
    uma = [oka + 20, 10, -10, -20]
    point = (rpoint - 300) / 10 + uma[rank - 1]

    return(float(f"{point:>.1f}"))
