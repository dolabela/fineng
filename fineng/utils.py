from datetime import datetime
import os 
import dateutil.relativedelta
from copy import deepcopy

import pandas as pd 


def log( type = '', text = '',num = 0, log_path = 'log.csv', init = False):
    
    if init == True:
        log_file = open(log_path, "w") 
        log_file.write("date;type;id;text\n")
        log_file.close()
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = now + ";" + str(type) + ";" + str(num)+ ";" + text 
        log_file = open(log_path, "a") 
        log_file.write(log + '\n')
        log_file.close()

        if (type == 'start'):
            type = 'Starting'
        elif (type == 'finish'):
            type = 'Finished'

        print("[" + now + "] " + type + ' ' + text) 



# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """Imprime uma barra de progresso
    
    Arguments:
        iteration {[type]} -- current iteration 
        total {[type]} -- total iterations
        prefix {str} -- prefix string (default: {''})
        suffix {str} -- suffix string (default: {''})
        decimals {int} -- ositive number of decimals in percent complete (default: {1})
        length {int} -- character length of bar (default: {100})
        fill {str} -- bar fill character (default: {'█'})
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * (iteration) // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')


def gen_dates(time_is, time_os, date_from = '2013-01-01', date_to = '2017-12-31'):
    """ Gera DataFrame com datas dos períodos in-sample e out-of-sample
    
    Arguments:
        time_is {int} -- Quantidade de meses a serem utilizados para treinar o modelo
        time_os {int} -- Quantidade de meses a serem utilizados na simulação do modelo treinado
        date_from {str} -- Data de início da análise (default: {'2013-01-01'})
        date_to {str} -- Data de término da análise (default: {'2017-12-31'})
    
    Returns:
        [type] -- [description]
    """
    
    list_of_dates = []
    date_to = datetime.strptime(date_to , "%Y-%m-%d")     
    date_from = datetime.strptime(date_from , "%Y-%m-%d")
    date_from_is = date_from
        
    while (True):
        date_from_os = date_from_is + dateutil.relativedelta.relativedelta(months = time_is )
        date_to_is = date_from_os - dateutil.relativedelta.relativedelta(days = 1 )
        date_to_os = date_from_os + dateutil.relativedelta.relativedelta(months = time_os )
        
        if(date_from_os > date_to):
            break        
        elif (date_to_os > date_to):
            date_to_os = date_to
            list_of_dates.append([date_from_is.strftime("%Y-%m-%d"), date_to_is.strftime("%Y-%m-%d"), date_from_os.strftime("%Y-%m-%d"), date_to_os.strftime("%Y-%m-%d")])
            break

        list_of_dates.append([date_from_is.strftime("%Y-%m-%d"), date_to_is.strftime("%Y-%m-%d"), date_from_os.strftime("%Y-%m-%d"), date_to_os.strftime("%Y-%m-%d")])
    
        date_from_is = date_from_is + dateutil.relativedelta.relativedelta(months = time_os )
    return list_of_dates

def same_index(rets1, rets2):
    """Garante que 2 dataframes tenham os mesmos índices
    
    Arguments:
        rets1 {dataframe} -- Retorno
        rets2 {dataframe} -- Retorno
    
    Returns:
        dataframe -- Retorno
        dataframe -- Retorno
    """
    rets1.index = pd.to_datetime( rets1.index )
    rets2.index = pd.to_datetime( rets2.index )

    from_date = max(rets1.index[0], rets2.index[0])
    to_date = min(rets1.index[-1], rets2.index[-1])

    rets1 = rets1.loc[from_date:to_date]
    rets2 = rets2.loc[from_date:to_date]
    return rets1, rets2 