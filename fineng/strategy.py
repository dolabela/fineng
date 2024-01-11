import datetime
import os
from random import random
from copy import deepcopy
from multiprocessing import Pool

import numpy as np
import pandas as pd

from fineng.utils import printProgressBar, gen_dates, log
import fineng.calculation as calc
import fineng.port_optimization as p_opt


class Strategy:
    def __init__(
        self,
        method,
        name,
        rets,
        log_path="log.csv",
        args=False,
        time_is=12,
        time_os=3,
        min_w=0,
        max_w=0.05,
        date_from="2013-01-01",
        date_to="2017-12-31",
        threads=1,
        os_equal_is=False,
        rsi=False,
        ewma=1,
        minimization_tolerance=None,
    ):
        """Classe principal para simular rendimento em um período de tempo

        Arguments:
            method {str} -- Método a ser utilizado
            name {str} -- Nome da estratégia
            rets {Dataframe} -- Dataframe de retornos
            args {bool} -- argumentos extras (default: {False})
            time_is {int} -- Período in-sample em dias (default: {12})
            time_os {int} -- Período out-of-sample em dias (default: {3})
            min_w {float} -- Peso mínimo mínimo por ação (Se negativo, permite shorting)(default: {0})
            max_w {float} -- Peso máximo por ação(default: {0.05})
            date_from {str} -- Data de início da análise (default: {'2013-01-01'})
            date_to {str} -- Data do fim da análise (default: {'2017-12-31'})
            threads {int} -- Quantidade de threads a serem utilizadas  (default: {1})
            os_equal_is {bool} -- Se True, o período analisado será o mesmo período simulado (default: {False})
            rsi {bool} -- Valor do RSI (default: {False})
            ewma {int} -- Valor do EWMA (default: {1})
        """

        self.log_path = log_path
        log(log_path=log_path, init=True)
        log("start", "Defining Variables.", 1, log_path)
        # Define variáveis
        self.method = method
        self.name = name
        self.__args = args
        self.__ewma = ewma
        self.__rsi = rsi
        self.__min_w = min_w
        self.__max_w = max_w
        self.__minimization_tolerance = minimization_tolerance

        self.details = {
            "RSI": self.__rsi,
            "EWMA": self.__ewma,
            "ARGS": self.__args,
            "Min. Weight": self.__min_w,
            "Max. Weight": self.__max_w,
            "Min tol": self.__minimization_tolerance,
        }
        log("finish", "Defining Variables.", 1, log_path)

        # Gerar todas as datas. Se a variável os_equal_is é True, os períodos OS são iguais aos IS
        log("start", "Generating dates and filtering returns.", 2, log_path)
        if os_equal_is:
            self.list_of_dates = [[date_from, date_to, date_from, date_to]]
        else:
            self.list_of_dates = gen_dates(
                time_is=time_is, time_os=time_os, date_from=date_from, date_to=date_to
            )

        # Calcula retornos e filtra variáveis pelas datas
        self.rets = deepcopy(rets)
        self.rets = self.rets.loc[date_from:date_to]
        self.rets = self.rets.iloc[1:, :]
        log("finish", "Generating dates and filtering returns.", 2, log_path)

        # Calcular peso para cada período utilizando multithread
        log(
            "start",
            "Calculating weights from {} periods".format(len(self.list_of_dates)),
            3,
            log_path,
        )
        p = Pool(threads)
        self.strategy_weights = p.map(self.calculate_weights, self.list_of_dates)
        p.close()
        p.join()
        self.strategy_weights = pd.concat(self.strategy_weights, sort=True)
        log(
            "finish",
            "Calculating weights from {} periods".format(len(self.list_of_dates)),
            3,
            log_path,
        )

        log("start", "Simulating Strategy", 5, log_path)
        self.strategy_cumret = self.calculate_return(self.rets, self.strategy_weights)
        self.strategy_ret = calc.ret_from_cum_ret(self.strategy_cumret)
        log("finish", "Simulating Strategy", 5, log_path)

    def calculate_weights(self, dates):
        """Calcula o peso das ações utilizando cada estratégia

        Arguments:
            dates {[type]} -- [description]

        Returns:
            [type] -- [description]
        """

        date_from_is, date_to_is, date_from_os, date_to_os = dates
        log(
            "start",
            "Calculating portfolio weights from {} to {}".format(
                datetime.datetime.strptime(date_from_is, "%Y-%m-%d").date(),
                datetime.datetime.strptime(date_to_is, "%Y-%m-%d").date(),
            ),
            4,
            self.log_path,
        )
        # Obtém datas in sample e out of sample, e filtra os retornos para ter apenas o que é in-sample.

        rets_is = deepcopy(self.rets.loc[date_from_is:date_to_is])
        rets_is.dropna(axis="columns", inplace=True)
        # Tentativa de aplicação de conceitos de EWMA (Performance e implementação ainda não validados)
        if self.__ewma > 1:
            rets_is = rets_is.sort_index(ascending=False)
            rets_is = rets_is.ewm(
                span=self.__ewma, min_periods=0, adjust=False, ignore_na=False
            ).mean()
            rets_is = rets_is.sort_index(ascending=True)

        # Tentativa de aplicação de conceitos de RSI (Performance e implementação ainda não validados)
        if self.__rsi == True:
            delta = deepcopy(rets_is)
            dUp = delta[delta > 0]
            dDown = delta[delta < 0]
            dUp[delta <= 0] = 0
            dDown[delta >= 0] = 0
            n = 21 * 4
            RolUp = dUp.rolling(n).mean()
            RolDown = dDown.rolling(n).mean().abs()
            RS = 100 - 100 / (1 + RolUp / RolDown)
            rets_is = rets_is.iloc[:, np.array(RS.iloc[-1, :] < 70)]

        # Com base no critério de seleção de portfólio escolhido, calcula os pesos
        if self.method == "random" or self.method == "equally_weighted":
            portfolio = p_opt.gen_port(
                rets=rets_is,
                opt_method=self.method,
                date_from=date_from_is,
                date_to=date_to_is,
                row_name=str(date_from_os) + "/" + str(date_to_os),
            )

        else:
            portfolio = p_opt.gen_port_optimized(
                rets_is,
                date_from=date_from_is,
                date_to=date_to_is,
                opt_method=self.method,
                extra_args=self.__args,
                row_name=str(date_from_os) + "/" + str(date_to_os),
                min_w=self.__min_w,
                max_w=self.__max_w,
                minimization_tolerance=self.__minimization_tolerance,
            )

        log(
            "finish",
            "Calculating portfolio weights from {} to {}".format(
                datetime.datetime.strptime(date_from_is, "%Y-%m-%d").date(),
                datetime.datetime.strptime(date_to_is, "%Y-%m-%d").date(),
            ),
            4,
            self.log_path,
        )
        return portfolio

    def calculate_return(self, rets, weights):
        """Calcula o retorno dos diferentes pesos por período

        Arguments:
            rets {Dataframe} -- Retornos
            weights {Dataframe} -- Pesos

        Returns:
            Series -- Retornos da estratégia
        """

        # Filtra os retornos do período
        rets = deepcopy(rets)
        rets = rets.loc[
            weights.index[0].split("/")[0] : weights.index[-1].split("/")[1]
        ]
        rets = rets.fillna(0)
        calculated_ret = pd.Series()

        # Define uma cota com o valor de 1.
        share = 1
        # A cada iteração do primeiro loop, é selecionado uma linha do peso
        for index_p, row_p in weights.iterrows():
            date_from, date_to = index_p.split("/")
            row_p = row_p * share
            # A cada iteração do segundo loop, é calculada cada peso multiplicado pelo seu retorno, e a sua soma é salva para ser retornada
            for index_r, row_r in rets.iterrows():
                if index_r >= date_from and index_r < date_to:
                    row_p = row_p.multiply(1 + row_r)
                    calculated_ret[index_r] = row_p.sum()

                    # Ao final, é salvo o valor da sua cota para ser utilizada no próximo peso
                    share = calculated_ret[index_r]
                elif index_r > date_to:
                    break

        return calculated_ret

    def print_weights(self):
        """Imprime pesos do portfólio"""

        s_weights = deepcopy(self.strategy_weights)
        s_weights.fillna(0.0, inplace=True)
        for i, row in enumerate(self.strategy_weights.iterrows()):
            print("")
            print("-" * 10)
            print(row[0])
            if i >= 1:
                turnover = s_weights.iloc[i, :] - s_weights.iloc[i - 1, :]
                turnover = turnover[turnover > 0.000001].sum()
                print("Turnover:", "{0:.2%}".format(turnover))
                print(
                    "Stocks that left:",
                    (
                        (s_weights.iloc[i, :] < 0.000001)
                        & (s_weights.iloc[i - 1, :] > 0.000001)
                    ).sum(),
                )
                print(
                    "New Stocks:",
                    (
                        (s_weights.iloc[i, :] > 0.000001)
                        & (s_weights.iloc[i - 1, :] < 0.000001)
                    ).sum(),
                )
            print("Portfolio size:", row[1][row[1] > 0.000001].size)
            weights = row[1][row[1] > 0.000001].sort_values(ascending=False).to_frame()
            weights.columns = [""] * len(weights.columns)
            weights[""] = round(weights[""] * 100, 2)
            weights = weights.astype(str)
            weights[""] = weights[""] + "%"
            print(weights)


class Benchmark:
    def __init__(self, benchmark_rets, name):
        """Classe que dá ao benchmark características similares à classe Strategy

        Arguments:
            benchmark_rets {DataFrame} -- Retornos do benchmark
            name {str} -- Nome do benchmark
        """
        self.strategy_ret = benchmark_rets["Return"]
        self.name = name
        self.strategy_cumret = calc.cum_ret(benchmark_rets)
        self.strategy_ret.index = self.strategy_ret.index.map(str)
        self.strategy_cumret.index = self.strategy_cumret.index.map(str)
