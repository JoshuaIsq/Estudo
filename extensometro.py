import datetime as dt
import os
import time

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import nptdms
import numpy as np
import pandas as pd
import rainflow as rf
from scipy import signal
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler


#Realizar a conversão do arquivo tdms para dataframe

def _convert_tdms_to_df(tdms_file):
        return tdms_file.groups()[0].as_dataframe()

#Criar vetor de tempo a partir dos metadados do arquivo tdms

def _create_timestamp(tdms_file, data):
    start_time = tdms_file.properties["Title"][0:18]
    start_time = dt.datetime.strptime(start_time, "%d/%m/%Y %H:%M:%S")
    time = tdms_file.properties["log-dt"] * pd.Series(range(len(data)))
    time = time.round(4)
    time = pd.to_timedelta(time, unit="s") + start_time

    return time   

#Converter milissegundos em timestamp para arquivos txt/csv
      
def _convert_milis_to_timestamp(txt_file, str_start_time):
    time_column = txt_file.iloc[:,0]
    aquisition_duration = pd.to_timedelta(time_column , unit='ms')
    str_start_time = dt.datetime.strptime(str_start_time, "%d/%m/%Y %H:%M:%S")
    time = str_start_time + aquisition_duration
    return time

def load_data(filename, str_start_time):
        """Abre arquivo de medição para análise experimental de tensões

        O método abre o arquivo de medição podendo esse ser no formato
        .tdms ou .csv/.txt. É criado o Dataframe da medição e o
        vetor contendo os registros temporais de todas as entradas.

        Argumentos:
        - filename: Nome do arquivo a ser lido pelo método"""

        if filename.endswith(".tdms"):
            tdms_file = nptdms.TdmsFile(filename)
            data = _convert_tdms_to_df(tdms_file)
            raw_data = data.copy()
            timestamp = _create_timestamp(tdms_file, data)
            del tdms_file
        elif filename.endswith(".txt"):
            txt_file = pd.read_csv(filename, sep=';')
            data = txt_file.iloc[:,1:-1]
            raw_data = data.copy()
            timestamp = _convert_milis_to_timestamp(txt_file, str_start_time)

            del txt_file
        else:
            data = pd.DataFrame()
            raw_data = pd.DataFrame()
            timestamp = pd.Series()
        return data, raw_data, timestamp

def rename_channels(data, raw_data, channel_list):      
        """Renomeia o nome das colunas do Dataframe de medição

        Argumentos:
        - channel_list: Lista com o nome dos canais na ordem das colunas
        do Dataframe
        """

        data.columns = channel_list
        raw_data.columns = channel_list
        return data, raw_data

def delete_channel(data, raw_data, channel_names):
        """Deleta canal dos dados de medição
        
        Método utilizado para deletar canais de medição que foram descartados.
        
        Argumentos:
        - channel_name: lista de nomes dos canais a serem deletados.
        """

        NovaData = data.drop(labels=channel_names, axis=1)
        NovaRawData = raw_data.drop(labels=channel_names, axis=1)
        return NovaData, NovaRawData
    
def drop_nans(data, raw_data, timestamp):
        """Deleta todas as linhas que contém a entrada NaN
        
        Método utilizado para limpar a medição de entradas do tipo NaN
        """

        NovaData = data.dropna()

        Novotimestamp = timestamp.loc[NovaData.index]
        Novoraw_data = raw_data.loc[NovaData.index]

        NovaData = NovaData.reset_index(drop=True)
        Novoraw_data = Novoraw_data.reset_index(drop=True)
        Novotimestamp = Novotimestamp.reset_index(drop=True)
        return NovaData, Novoraw_data, Novotimestamp

def concatenate_databases(data, raw_data, timestamp, filename, channel_names):
        """Concatena outras medições à medição já aberta pela classe
        
        Método que abre outros arquivos de medição e concatena eles abaixo
        da medição já aberta pela classe de extensometria
        
        Argumentos:
        - filename: Nome do arquivo a ser concatenado na medição a ser tratada
        - channel_names: Nome dos canais a serem adicionados
        """
        
        if filename.endswith(".tdms"):
            tdms_file = nptdms.TdmsFile(filename)
            new_data = _convert_tdms_to_df(tdms_file)
            new_data.columns = channel_names
            new_timestamp = _create_timestamp(tdms_file, new_data)
            data = pd.concat([data, new_data], ignore_index=True)
            raw_data = pd.concat([raw_data, new_data], ignore_index=True)
            timestamp = pd.concat([timestamp, new_timestamp], ignore_index=True)
            return data, raw_data, timestamp
        elif filename.endswith(".txt"):
            txt_file = pd.read_csv(filename, sep=';')
            new_data = txt_file.iloc[:,1:-1]
            new_data.columns = channel_names
            new_timestamp = _convert_milis_to_timestamp(txt_file, str_start_time)
            data = pd.concat([data, new_data], ignore_index=True)
            raw_data = pd.concat([raw_data, new_data], ignore_index=True)
            timestamp = pd.concat([timestamp, new_timestamp], ignore_index=True)
            return data, raw_data, timestamp
        
def convert_data_to_stress(data, channel_calibration):
        """Converte os dados lidos em valores de tensão mecânica [MPa]

        Argumentos:
        - channel_calibration: Vetor contendo a constante de calibração
        individual de cada canal ou constante de calibração para todos
        os canais de medição
        """

        data = data * channel_calibration
        return data

def adjust_offset(data, raw_data, interval_size):
        """Ajusta o offset de medição de cada canal

        Método tira a média das primeiras N entradas da medição e subtrai de
        todos os dados, forçando seu início em 0

        Argumentos:
        - interval_size: Número de entradas utilizado para cálculo de offset
        """

        data = data - data[:interval_size].mean()
        raw_data = raw_data - raw_data[:interval_size].mean()
        return data, raw_data

def filter_moving_average(data, filter_window):
        """Trata os dados da classe usando um filtro de média móvel

        Método tira uma média de N vetores de forma iterativa ao longo do
        banco de dados. A varredura do filtro reduz a influência de sinais
        de alta frequência

        Argumentos:
        - filter_window: Janela de N valores a serem utilizados na varredura
        do filtro
        """

        for column in data.columns:
            data[column] = data[column].rolling(window=filter_window).mean()

        data = data.round(4)
        return data

def filter_low_pass(data, cut_freq=2000, sample_rate=25000, order=2):
        """Trata os dados da classe usando um filtro passa-baixas

        Método aplica um filtro passa-baixas nos dados de medição, objetivando
        atenuar os sinais de frequência mais alta que a frequência de corte

        Argumentos:
        - cut_freq: Frequência de corte em Hz
        - signal_freq: Frequência de amostragem da medição
        - order: Ordem do filtro passa-baixas
        """

        nyquist_freq = 0.5 * sample_rate
        low_pass_ratio = cut_freq / nyquist_freq
        b, a = signal.butter(order, low_pass_ratio, btype="low")
        for column in data.columns:
            data[column] = signal.filtfilt(b, a, data[column])
        data = data.round(4)
        return data

def identify_outliers(data, window=2000, thresh=3, verbose=False):
        """
        Identifica outliers por coluna individualmente usando zscore local 
        (móvel - calculado a partir de um janelamento de dados).

        Parâmetros:
        - self: DataFrame com os dados dos sensores por coluna
        - window: janelamento de dados móvel para o cálculo do zscore local
        - thresh: threshold limite inferior ou superior do zscore a partir
        dos quais um dado é considerado outlier em comparação
        o valor mais tradicional é 3 e isso vem da distribuição normal: 
        cerca de 99,7% dos dados estão dentro de 3 desvios padrão da média.
        - verbose: se True, exibe resumo

        Retorna:
        - outlier_mask: DataFrame com apenas o booleano da posição dos outliers
        no dataframe original
        """

        outlier_mask = pd.DataFrame(False, index=data.index, columns=data.columns)

        for column in data.columns:
            series = data[column]
            rolling_mean = series.rolling(window=window, min_periods=1).mean()
            rolling_std = series.rolling(window=window, min_periods=1).std()
            z_score = (series - rolling_mean) / rolling_std
            outliers = np.abs(z_score) > thresh
            outlier_mask[column] = outliers

            if verbose:
                print(f"[INFO] Coluna: {column}")
                print(f"       Média: {series.mean():.2f}, Desvio padrão: {series.std():.2f}")
                print(f"       Outliers detectados: {outliers.sum()} de {len(series)}\n")