from copy import deepcopy
import pandas as pd
import numpy as np 
from quantfin.utils import same_index 

def cum_ret(rets):
    return (rets + 1).cumprod() 

def ret_from_cum_ret(cumulative_return):
    rets = pd.concat([pd.Series([1]), cumulative_return])
    return rets.pct_change().iloc[1:]


def beta(p_rets, market):
    p_rets, market = same_index(p_rets, market)
    
    m = np.matrix([p_rets, market])
    cov = np.cov(m)
    return (cov[0][1] / cov[1][1])

def ret_total(p_rets):
    return ((p_rets + 1).product()) - 1     


def ret_annual(p_rets):
    return ((p_rets + 1).product())**(252/p_rets.size) - 1 


def vol_annual(p_rets):
    return p_rets.std()*np.sqrt(252)


def sharpe(p_rets, rfr = 0): 
    return (ret_annual(p_rets)- rfr) / vol_annual(p_rets)


def down_stdev(p_rets):
    negative_returns = p_rets.loc[p_rets < 0]
    return negative_returns.std()*np.sqrt(252)  


def sortino(p_rets, rfr = 0):
    return (ret_annual(p_rets) - rfr)  /(down_stdev(p_rets)*np.sqrt(252))     


def treynor(p_rets, market, rfr = 0):
    p_rets, market = same_index(p_rets, market)
    return (ret_annual(p_rets) - rfr ) / beta(p_rets, market)


def var(p_rets, var_level):
    var_value = np.percentile(p_rets, var_level)
    return var_value


def cvar(p_rets, var_level, return_var = False):
    var_value = var(p_rets, var_level)
    cvar_value = p_rets[p_rets <= var_value].mean()
    if return_var == False:
        return cvar_value 
    else:
        return cvar_value, var_value

def starr(p_rets, var_level):
    return ret_annual(p_rets)/cvar(p_rets, var_level)

def max_dd(p_rets):

    df = cum_ret(p_rets)

    # Calcula o valor máximo em uma janela de 252 dias 
    roll_max = df.rolling(center=False,min_periods=1,window=252).max()

    # Calcula o draw-down diário relativo ao máximo
    daily_draw_down = df/roll_max - 1.0

    # Calcula o menor (negativo) draw-down
    max_daily_draw_down = daily_draw_down.rolling(center=False,min_periods=1,window=252).min()
    
    return max(abs(max_daily_draw_down))