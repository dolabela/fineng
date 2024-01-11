import numpy as np 
import pandas as pd 
import quantfin.calculation as calc 

def ret(weights, rets):
    """ Calcula o retorno anualizado do portfólio. 
    O cálculo não é feito da forma mais precisa possível, então deve ser utilizada apenas no processo de otimização.
    
    Arguments:
        rets {dataframe} -- Tabela com retornos
        weights {dataframe} -- Tabela com pesos
    
    Returns:
        float -- Retorno
    """

    port_ret =(rets*weights).sum(axis = 1)

    return calc.ret_annual(port_ret)

def vol(weights, rets):
    """  Calcula a volatilidade anualizado do portfólio
    
    Arguments:
        rets {dataframe} -- Tabela com retornos
        weights {dataframe} -- Tabela com pesos
    
    Returns:
        float -- Volatilidade
    """

    port_ret =(rets*weights).sum(axis = 1)

    return calc.vol_annual(port_ret)

def sharpe(weights, rets): 
    """ Calcula o sharpe anualizado do portfólio
    
    Arguments:
        rets {dataframe} -- Tabela com retornos
        weights {dataframe} -- Tabela com pesos
    
    Returns:
        float -- Sharpe
    """

    port_ret =(rets*weights).sum(axis = 1)

    return calc.sharpe(port_ret)


def cvar(weights, rets, var_level):
    """ Calcula o sharpe anualizado do portfólio
    
    Arguments:
        rets {dataframe} -- Tabela com retornos
        weights {dataframe} -- Tabela com pesos
    
    Returns:
        float -- CVar
    """

    port_ret =(rets*weights).sum(axis = 1)
    return calc.cvar(port_ret, var_level)
