import datetime
import os
import pandas as pd
import pandas_datareader.data as web
import pickle

from fineng.utils import printProgressBar, log


def merge_csv_to_df():
    """Une os CSV's de ações na pasta para um mesmo DataFrame

    Returns:
        DataFrame -- Pandas Dataframe com os dados
    """

    # Lista todos arquivos na pasta dataset/stocks
    list_of_csvs = os.listdir(os.path.join("dataset", "stocks"))

    # Cria lista vazias
    last_row_date = []
    first_row_date = []

    # Checa todos arquivos de CSV
    for n, company in enumerate(list_of_csvs):
        # Na primeira iteração cria a variável prices
        if n == 0:
            prices = pd.DataFrame(
                index=pd.read_csv(os.path.join("dataset", "stocks", company))[
                    "Unnamed: 0"
                ]
            )

        # Lê cada ação e seleciona sua coluna de fechamentos
        company_data = pd.read_csv(os.path.join("dataset", "stocks", company))
        ticker = company[:-4]

        # Se o arquivo está vazio, a ação é pulada
        if company_data.empty:
            pass

        # Se contém preços, salva no arquivo prices a coluna com o nome da ação.
        else:
            last_row_date.append(company_data.loc[company_data.index[-1]]["Unnamed: 0"])
            first_row_date.append(company_data.loc[0]["Unnamed: 0"])
            company_data.rename(columns={"close": ticker}, inplace=True)
            company_data.drop(
                [
                    "open",
                    "high",
                    "low",
                    "volume_dollar",
                    "volume_shares",
                    "volume_ticks",
                    "avg",
                ],
                1,
                inplace=True,
            )
            company_data.set_index("Unnamed: 0", drop=True, inplace=True)
            del company_data.index.name
            prices = prices.join(company_data, how="outer")

    log("Stock market CSV's merged!")
    return prices


def get_sp500(symbol="^GSPC"):
    """Busca cotações de determinado código no Yahoo Finance e calcula o seu retorno

    Returns:
        DataFrame -- Dataframe contendo Retorno de fechamento.
    """

    # Busca preços do Yahoo Finance
    df = web.DataReader(symbol, "yahoo", "2009-01-01", "2018-12-31")

    # Calcula o seu retorno
    df["Return"] = df["Close"].pct_change()
    df = df[["Return"]]
    log("S&P 500 Returns obtained")

    return df.iloc[1:]



def save_to_pickle(path, variables):
    """Salva variáveis em arquivo .pickle

    Arguments:
        path {str}-- Caminho do arquivo
        variables {list} -- Lista de variáveis a serem salvas
    """
    with open(path, "wb") as f:
        pickle.dump(variables, f)
        log("Variables saved in path {}".format(path))


def return_from_pickle(path):
    """Retorna variáveis de um arquivo .pickle

    Arguments:
        path {str}-- Caminho do arquivo

    Returns:
        variables {list} -- Lista de variáveis
    """
    with open(path, "rb") as f:
        # log(text = "Variables returned from path {}".format(path))
        return pickle.load(f)
