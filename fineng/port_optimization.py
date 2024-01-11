
import random 
import time 

import numpy as np 
import scipy.optimize as sco 
import pandas as pd 

from quantfin.utils import printProgressBar, log, gen_dates
import quantfin.objective_function as obj 
import quantfin.calculation as calc

def gen_port(rets, opt_method, date_from, date_to, extra_args = False, allow_short = False, row_name = ''):
    """Gera pesos de portfólio igualmente distribuído ou aleatório
    
    Arguments:
        opt_method {[type]} -- [description]
        date_from {[type]} -- [description]
        date_to {[type]} -- [description]
    
    Keyword Arguments:
        extra_args {bool} -- [description] (default: {False})
        allow_short {bool} -- [description] (default: {False})
        row_name {str} -- [description] (default: {''})
    
    Returns:
        [type] -- [description]
    """
    
    noa = len(rets.columns)

    if (opt_method == 'equally_weighted'):
        weights = np.array(noa * [1. / noa]) 

    elif (opt_method == 'random'):
        weights = [random.random() for x in range(len(rets.columns))]
        weights = np.array(weights)
        weights = weights/sum(weights)

    df = pd.DataFrame(weights, columns=[row_name], index=rets.columns)
    return df.transpose()

def gen_port_optimized (rets, opt_method, date_from, date_to, min_w, max_w, extra_args = False, allow_short = False, row_name = '', minimization_tolerance = None):
    """Gera portfólio otimizado
    
    Arguments:
        rets {dataframe} -- Dataframe com retornos das ações
        opt_method {str} -- String contendo nome do método a ser utilizado para otimizar. 
            min_vol: Dado um retorno desejado, calcula o portfólio com o menor devio padrão possível.
            max_sharpe: Tenta maximizar o Sharpe Ratio, que é a razão entre retorno e volatilidade do portfólio. Isso significa que quanto maior o seu valor, maior é seu retorno por risco, então quanto maior melhor.
            min_cvar: Tenta diminuir o valor médio das piores perdas do portfólio. Deve ser inserido no argumento 'args' o percentual dessas piores perdas (Geralmente é utilizado 5%)
            max_treynor: Tem como objetivo maximizar o retorno do portfólio divido pelo seu Beta. O beta é a relação entre o retorno do portfólio e o retorno do mercado. Quanto mais alto, mais arriscado é.
            max_sortino: Busca maximizar o retorno do portfólio divido variância dos retornos negativos. Ou seja, não leva em consideração a variação total, mas sim a variância das perdas.
        date_from {[type]} -- [description]
        date_to {[type]} -- [description]
    
    Keyword Arguments:
        extra_args -- Argumentos extra a serem utilizados no método (default: {False})
        allow_short {bool} -- [description] (default: {False})
        row_name {str} -- Nome do index do datafame retornado (default: {''})
    
    Returns:
        [type] -- [description]
    """

    noa = len(rets.columns)
    eweights = np.array(noa * [1. / noa]) 

    bnds = tuple((min_w, max_w) for x in range(noa)) 

    cons = ({'type': 'eq', 'fun': lambda x:  np.sum(x) - 1})

    if (opt_method == 'max_sharpe'):
        opt_method =  lambda w, r:  - obj.sharpe(w, r) 
        arguments = (rets)

    elif (opt_method == 'min_vol'):
        opt_method =  obj.vol
        arguments = (rets)
        cons = (cons,{'type': 'ineq', 'fun': lambda x: obj.ret(x, rets) - extra_args})
    
    elif (opt_method == 'min_vol_master'):
        opt_method =  obj.vol
        arguments = (rets)

    elif (opt_method == 'min_cvar'):
        opt_method = lambda w, r, v_l: 0 - obj.cvar(w, r, v_l)   
        arguments = (rets, extra_args)

    elif (opt_method == 'max_return1'):
        market = extra_args.loc[date_from:date_to]
        var_list = [1,5,25,50,75,95,99]
        arguments = (rets)
        opt_method =  lambda x, r: - obj.ret(x, r)
        cons = [{'type': 'eq', 'fun': lambda x:  np.sum(x) - 1}]
        for _, var1 in enumerate(var_list):
            for _, var2 in enumerate(var_list):
                if (var2 > var1 ):
                    cons.append({'type': 'ineq', 'fun': lambda x: (obj.cvar(x, rets, var2) - obj.cvar(x, rets, var1))  - (calc.cvar(market, var2) - calc.cvar(market, var1)) }) 
        cons = tuple(cons)

    elif (opt_method == 'sthocastic_dominance1'):
        market = extra_args.loc[date_from:date_to]
        cons = ({'type': 'eq', 'fun': lambda x:  np.sum(x) - 1})
        cons = (cons,{'type': 'ineq', 'fun': lambda x: obj.cvar(x, rets, 1) - calc.cvar(market, 1)}) 
        opt_method =  lambda x, r: -min(calc.cvar(market, 1) - obj.cvar(x, r, 1),
                                    calc.cvar(market, 5) - obj.cvar(x, r, 5),
                                    calc.cvar(market, 10) - obj.cvar(x, r, 10),
                                    calc.cvar(market, 25) - obj.cvar(x, r, 25),
                                    calc.cvar(market, 50) - obj.cvar(x, r, 50),
                                    calc.cvar(market, 75) - obj.cvar(x, r, 75),
                                    calc.cvar(market, 90) - obj.cvar(x, r, 90),
                                    calc.cvar(market, 95) - obj.cvar(x, r, 95),
                                    calc.cvar(market, 100) - obj.cvar(x, r, 100))
        arguments = (rets)
    
        
    else:
        Warning("No valid opt_method inserted")

    opts = sco.minimize(fun = opt_method, 
                        x0 = eweights, 
                        args = arguments,
                        method='SLSQP', 
                        bounds=bnds,
                        constraints=cons,
                        tol = minimization_tolerance) 

    if opts['success'] == True:
        weights = opts['x']
        df = pd.DataFrame(weights, columns=[row_name], index=rets.columns)
        return df.transpose()
    else:
        log("Error ocurred in calculation between {} and {}". format(date_from, date_to,))
        Warning("Error ocurred in calculation between {} and {}". format(date_from, date_to,))
        return None