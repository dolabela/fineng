from copy import deepcopy
import datetime
import statistics

import numpy as np
import pandas as pd
from IPython.display import display
import plotly.graph_objects as go
import plotly.io as pio

import fineng.calculation as calc


def analyse_log(log_path):
    data = pd.read_csv(log_path, sep=";")
    data.sort_values(by=["id"])
    data["date"] = pd.to_datetime(data["date"])

    data["id_text"] = data["id"].astype(str) + "; " + data["text"]

    data = data.pivot(index="id_text", columns="type", values="date")

    data["diff"] = data["finish"] - data["start"]

    data.reset_index(inplace=True)
    data = data[["id_text", "diff"]]
    data.index.name = "id"

    fig = go.Figure(
        data=[
            go.Bar(
                y=data["diff"],
                x=data.index,
                text=data["id_text"],
            )
        ]
    )

    fig.show()


def plot_strategy(strategy_list):
    """Plota gráfico de retorno acumulado de uma lista de estratégias

    Arguments:
        strategy_list {list} -- Lista de estratégias/benchmarks
    """

    min_date = strategy_list[0].strategy_cumret.index[0]
    max_date = strategy_list[0].strategy_cumret.index[-1]
    for s in strategy_list:
        if s.strategy_cumret.index[0] > min_date:
            min_date = s.strategy_cumret.index[0]
        if s.strategy_cumret.index[-1] < max_date:
            max_date = s.strategy_cumret.index[-1]

    # Inicia a criação do gráfico
    fig = go.Figure()
    # Calcula o retorno acumulado de cada estratégia e plota seu gráfico
    for s in strategy_list:
        ret = deepcopy(s.strategy_ret).loc[min_date:max_date]
        cumulative_return = calc.cum_ret(ret)
        fig.add_trace(
            go.Scatter(
                x=cumulative_return.index, y=cumulative_return.values, name=s.name
            )
        )

    # Apresenta o título
    fig.update_layout(
        title_text="Portfolios Comparison", xaxis_rangeslider_visible=True
    )

    # Apresenta o gráfico
    fig.show()


def analyse_strategy(strategy, benchmark, days_back=0, show_weight=True):
    """Analisar estratégia

    Arguments:
        strategy {Strategy} -- Estratégia a ser analisada
        benchmark {Benchmark} -- Benchmark para comparar
        days_back {int} -- [description] (default: {0})
        show_weight {bool} -- [description] (default: {True})
    """

    min_date = strategy.strategy_ret.index[0]
    max_date = strategy.strategy_ret.index[-1]
    benchmark.strategy_ret = deepcopy(benchmark).strategy_ret.loc[min_date:max_date]

    # Se valor default é deixado, pega a maior quantidade de dias possível
    if days_back <= 0:
        days_back = strategy.strategy_cumret.size

    stats = StrategyStats(strategy, days_back, benchmark)

    print("Strategy:", stats.name)
    print("Annual Return:", "{0:.2%}".format(stats.annual_return))
    print("Annual Volatility", "{0:.2%}".format(stats.volatility))
    print("Beta:", "{0:.2f}".format(stats.beta))
    print("Sharpe:", "{0:.2f}".format(stats.sharpe))
    print("Sortino:", "{0:.2f}".format(stats.sortino))
    print("Treynor:", "{0:.2f}".format(stats.treynor))
    print("Starr: ", "{0:.2f}".format(stats.starr))
    print("Kurtosis:", "{0:.2f}".format(stats.kurtosis))
    print("Skew:", "{0:.2f}".format(stats.skew))
    print("CVar 5%::", "{0:.2%}".format(stats.cvar))
    print("Var 5%:", "{0:.2%}".format(stats.var))
    print("Maximum Drawdown: ", "{0:.2%}".format(stats.max_dd))
    print("Avg. Turnover:", "{0:.2%}".format(stats.turnover))
    print("Avg. Size:", "{0:.2f}".format(stats.size))

    # Gráficos
    plot_strategy([strategy, benchmark])
    plot_rolling_ret([strategy, benchmark])
    plot_rolling_sharpe([strategy, benchmark])
    plot_rolling_vol([strategy, benchmark])
    plot_daily_drawdown(strategy)

    # Imprimir pesos e turnover
    if show_weight == True:
        strategy.print_weights()


def compare_strategies(list_of_strategies, benchmark, days_back=0, display_table=False):
    """Compara estratégias em relação a diferentes indicadores

    Arguments:
        list_of_strategies {list} -- Lista de estratégias

    Keyword Arguments:
        benchmark {bool} -- [description] (default: {False})
        days_back {int} -- [description] (default: {0})
        display_table {bool} -- [description] (default: {False})

    Returns:
        Dataframe -- Tabela com dados resumidos
    """

    # Pega a maior data inicial e menor data final (Para padronizar)
    list_of_strategies.append(benchmark)
    min_date = list_of_strategies[0].strategy_cumret.index[0]
    max_date = list_of_strategies[0].strategy_cumret.index[-1]
    for s in list_of_strategies:
        if s.strategy_cumret.index[0] > min_date:
            min_date = s.strategy_cumret.index[0]
        if s.strategy_cumret.index[-1] < max_date:
            max_date = s.strategy_cumret.index[-1]

    # Padronizar o range de todas estratégias
    for s in list_of_strategies:
        s.strategy_ret = deepcopy(s.strategy_ret).loc[min_date:max_date]
    benchmark.strategy_ret = deepcopy(benchmark.strategy_ret).loc[min_date:max_date]

    # Se valor default é deixado, pega a maior quantidade de dias possível
    if days_back <= 0:
        days_back = list_of_strategies[0].strategy_cumret.size

    # Plota gráficos
    plot_strategy(list_of_strategies)

    plot_return_volatility(list_of_strategies)

    list_of_statistics = []
    for s in list_of_strategies:
        stats = StrategyStats(s, days_back, benchmark)
        aux = pd.DataFrame.from_dict(
            {
                "Strategy": stats.name,
                "Annaul Return": ["{0:.2%}".format(stats.annual_return)],
                "Annual Volatility": ["{0:.2%}".format(stats.volatility)],
                "Beta": ["{0:.2f}".format(stats.beta)],
                "Sharpe": ["{0:.2f}".format(stats.sharpe)],
                "Sortino": ["{0:.2f}".format(stats.sortino)],
                "Treynor": ["{0:.2f}".format(stats.treynor)],
                "Starr": ["{0:.2%}".format(stats.starr)],
                "Kurtosis": ["{0:.2f}".format(stats.kurtosis)],
                "Skew": ["{0:.2f}".format(stats.skew)],
                "CVar 5%": ["{0:.2%}".format(stats.cvar)],
                "Var 5%": ["{0:.2%}".format(stats.var)],
                "Maximum Drawdown": ["{0:.2%}".format(stats.max_dd)],
                "Avg. Turnover:": ["{0:.2%}".format(stats.turnover)],
                "avg. Size:": ["{0:.0f}".format(stats.size)],
            }
        )

        aux = aux.set_index("Strategy")
        list_of_statistics.append(aux)
    if display == True:
        display(pd.concat(list_of_statistics))
    else:
        return pd.concat(list_of_statistics)


def plot_rolling_vol(strategy_list):
    """Plota gráfico de retorno acumulado de uma lista de estratégias

    Arguments:
        strategy_list {list} -- Lista de estratégias/benchmarks
    """

    min_date = strategy_list[0].strategy_cumret.index[0]
    max_date = strategy_list[0].strategy_cumret.index[-1]
    for s in strategy_list:
        if s.strategy_cumret.index[0] > min_date:
            min_date = s.strategy_cumret.index[0]
        if s.strategy_cumret.index[-1] < max_date:
            max_date = s.strategy_cumret.index[-1]

    # Inicia a criação do gráfico
    fig = go.Figure()
    # Calcula o retorno acumulado de cada estratégia e plota seu gráfico
    for s in strategy_list:
        ret = deepcopy(s.strategy_ret).loc[min_date:max_date]
        rolling_sharpe = ret.rolling(252).apply(calc.vol_annual, raw=False)
        rolling_sharpe = rolling_sharpe.dropna()
        fig.add_trace(
            go.Scatter(x=rolling_sharpe.index, y=rolling_sharpe.values, name=s.name)
        )

    # Apresenta o título
    fig.update_layout(
        title_text="Rolling Volatility 252 days", xaxis_rangeslider_visible=True
    )

    # Apresenta o gráfico
    fig.show()


def plot_rolling_ret(strategy_list):
    """Plota gráfico de retorno acumulado de uma lista de estratégias

    Arguments:
        strategy_list {list} -- Lista de estratégias/benchmarks
    """

    min_date = strategy_list[0].strategy_cumret.index[0]
    max_date = strategy_list[0].strategy_cumret.index[-1]
    for s in strategy_list:
        if s.strategy_cumret.index[0] > min_date:
            min_date = s.strategy_cumret.index[0]
        if s.strategy_cumret.index[-1] < max_date:
            max_date = s.strategy_cumret.index[-1]

    # Inicia a criação do gráfico
    fig = go.Figure()
    # Calcula o retorno acumulado de cada estratégia e plota seu gráfico
    for s in strategy_list:
        ret = deepcopy(s.strategy_ret).loc[min_date:max_date]
        rolling_sharpe = ret.rolling(252).apply(calc.ret_annual, raw=False)
        rolling_sharpe = rolling_sharpe.dropna()
        fig.add_trace(
            go.Scatter(x=rolling_sharpe.index, y=rolling_sharpe.values, name=s.name)
        )

    # Apresenta o título
    fig.update_layout(
        title_text="Rolling Return 252 days", xaxis_rangeslider_visible=True
    )

    # Apresenta o gráfico
    fig.show()


def plot_rolling_cvar(strategy_list):
    """Plota gráfico de retorno acumulado de uma lista de estratégias

    Arguments:
        strategy_list {list} -- Lista de estratégias/benchmarks
    """

    min_date = strategy_list[0].strategy_cumret.index[0]
    max_date = strategy_list[0].strategy_cumret.index[-1]
    for s in strategy_list:
        if s.strategy_cumret.index[0] > min_date:
            min_date = s.strategy_cumret.index[0]
        if s.strategy_cumret.index[-1] < max_date:
            max_date = s.strategy_cumret.index[-1]

    # Inicia a criação do gráfico
    fig = go.Figure()
    # Calcula o retorno acumulado de cada estratégia e plota seu gráfico
    for s in strategy_list:
        ret = deepcopy(s.strategy_ret).loc[min_date:max_date]
        rolling_sharpe = ret.rolling(252).apply(calc.cvar, args=tuple(5), raw=False)
        rolling_sharpe = rolling_sharpe.dropna()
        fig.add_trace(
            go.Scatter(x=rolling_sharpe.index, y=rolling_sharpe.values, name=s.name)
        )

    # Apresenta o título
    fig.update_layout(
        title_text="Rolling CVar 5% 252 days", xaxis_rangeslider_visible=True
    )

    # Apresenta o gráfico
    fig.show()


def plot_rolling_sharpe(strategy_list):
    """Plota gráfico de retorno acumulado de uma lista de estratégias

    Arguments:
        strategy_list {list} -- Lista de estratégias/benchmarks
    """

    min_date = strategy_list[0].strategy_cumret.index[0]
    max_date = strategy_list[0].strategy_cumret.index[-1]
    for s in strategy_list:
        if s.strategy_cumret.index[0] > min_date:
            min_date = s.strategy_cumret.index[0]
        if s.strategy_cumret.index[-1] < max_date:
            max_date = s.strategy_cumret.index[-1]

    # Inicia a criação do gráfico
    fig = go.Figure()
    # Calcula o retorno acumulado de cada estratégia e plota seu gráfico
    for s in strategy_list:
        ret = deepcopy(s.strategy_ret).loc[min_date:max_date]
        rolling_sharpe = ret.rolling(252).apply(calc.sharpe, raw=False)
        rolling_sharpe = rolling_sharpe.dropna()
        fig.add_trace(
            go.Scatter(x=rolling_sharpe.index, y=rolling_sharpe.values, name=s.name)
        )

    # Apresenta o título
    fig.update_layout(
        title_text="Rolling Sharpe 252 days", xaxis_rangeslider_visible=True
    )

    # Apresenta o gráfico
    fig.show()


def plot_daily_drawdown(strategy):
    """Plota gŕafico do Daily Drawdown"""

    df = deepcopy(strategy.strategy_cumret)

    # Calcula o valor máximo em uma janela de 252 dias
    roll_max = df.rolling(center=False, min_periods=1, window=252).max()

    # Calcula o draw-down diário relativo ao máximo
    daily_draw_down = df / roll_max - 1.0

    # Calcula o menor (negativo) draw-down
    max_daily_draw_down = daily_draw_down.rolling(
        center=False, min_periods=1, window=252
    ).min()

    # Apresenta gráfico
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=daily_draw_down, name="Daily drawdown"))
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=max_daily_draw_down,
            name="Maximum daily drawdown in time-window",
        )
    )
    fig.update_layout(title_text="Daily drawdown", xaxis_rangeslider_visible=True)
    fig.show()


class StrategyStats:
    def __init__(self, strategy, days_back, benchmark):
        """Calcula principais estatísticas do retorno

        Arguments:
            strategy {Strategy} -- Classe da estratégia a ser analisada
            days_back {int} -- Dias de estudo em relação à última data
            benchmark {Strategy} -- Benchmark
        """
        self.name = strategy.name
        rets = strategy.strategy_ret.iloc[-days_back:]
        self.annual_return = calc.ret_annual(rets)
        self.volatility = calc.vol_annual(rets)
        self.skew = rets.skew()
        self.kurtosis = rets.kurtosis()
        self.beta = calc.beta(rets, benchmark.strategy_ret)
        self.sharpe = calc.sharpe(rets)
        self.treynor = calc.treynor(rets, benchmark.strategy_ret)
        self.sortino = calc.sortino(rets)
        self.cvar, self.var = calc.cvar(rets, 5, return_var=True)
        self.starr = calc.starr(rets, 5)
        self.max_dd = calc.max_dd(rets)

        turnover_list = []
        size_list = []

        if "quantfin.strategy.Strategy" in str(type(strategy)):
            weights = deepcopy(strategy.strategy_weights)
            weights.fillna(0, inplace=True)
            for i, row in enumerate(weights.iterrows()):
                size = row[1][row[1] > 0.00001].size
                size_list.append(size)
                if i >= 1:
                    turnover = weights.iloc[i, :] - weights.iloc[i - 1, :]
                    turnover = turnover[turnover > 0].sum()
                    turnover_list.append(turnover)
            self.turnover = statistics.mean(turnover_list)
            self.size = statistics.mean(size_list)
        else:
            self.turnover = 0
            self.size = 0


def plot_return_volatility(list_of_strategies):
    """Plota a relação Risco x Retorno de uma lista de estratégias

    Arguments:
        list_of_strategies {[list]} -- Lista contendo variáveis da clase Strategy
    """
    ret_list = []
    vol_list = []
    sharpe_list = []
    name_list = []
    for p in list_of_strategies:
        ret = calc.ret_annual(p.strategy_ret)
        vol = calc.vol_annual(p.strategy_ret)
        sharpe = ret / vol
        name = p.name
        ret_list.append(ret)
        vol_list.append(vol)
        sharpe_list.append(sharpe)
        name_list.append(name)

    data = [
        go.Scatter(
            x=vol_list,
            y=ret_list,
            name="",
            mode="markers",
            hovertemplate="<b>%{text}</b>"
            "<br><b>Volatility</b>: %{x:.2%}"
            "<br><b>Return</b>: %{y:.2%}"
            "<br><b>Sharpe</b>: %{marker.color:.2f}",
            text=name_list,
            showlegend=False,
            marker=dict(color=sharpe_list, colorscale="Viridis", line_width=1),
        ),
    ]

    layout = go.Layout(
        title="Return x Volatility",
        template=pio.templates["plotly"],
        xaxis=dict(title="Volatility"),
        yaxis=dict(title="Return"),
    )

    fig = go.Figure(data=data, layout=layout)
    fig.show()
