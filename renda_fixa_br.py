"""
Módulo de Renda Fixa Brasileira
Integração com APIs do Banco Central do Brasil e outras fontes oficiais
"""

import pandas as pd
import numpy as np
import requests
import os
import json
from datetime import datetime, timedelta
from pathlib import Path


class RendaFixaBR:
    """
    Classe para obter dados de investimentos de renda fixa brasileiros
    """
    
    def __init__(self, cache_dir='./dados_renda_fixa'):
        """
        Inicializa o gerenciador de renda fixa
        
        Args:
            cache_dir: Diretório para armazenar cache de dados
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # URLs da API do Banco Central
        self.bcb_base_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
        
        # Códigos de séries do BCB
        self.series = {
            'CDI': 12,           # Taxa CDI diária
            'SELIC': 432,        # Taxa SELIC diária
            'TR': 226,           # Taxa Referencial
            'IPCA': 433,         # IPCA acumulado
        }
        
        self.ultima_atualizacao_file = self.cache_dir / 'ultima_atualizacao.json'
        
    def _formatar_data_bcb(self, data):
        """Converte datetime para formato do BCB (DD/MM/YYYY)"""
        return data.strftime('%d/%m/%Y')
    
    def _buscar_serie_bcb(self, serie_codigo, data_inicio, data_fim):
        """
        Busca série temporal do Banco Central (Versão com Paginação de Datas)
        Resolve o erro de limite de 10 anos do BCB.
        """
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Lista para armazenar os pedaços dos dados
        todos_dados = []
        
        # Define um tamanho seguro de janela (ex: 5 anos para não bater no limite de 10)
        janela_anos = 5
        
        data_atual = data_inicio
        
        print(f"  📡 Iniciando busca da série {serie_codigo} (fatiada em blocos de {janela_anos} anos)...")

        while data_atual < data_fim:
            # Calcula o fim desta fatia
            fim_fatia = min(data_atual + timedelta(days=365 * janela_anos), data_fim)
            
            # Formata datas para log
            d_ini_str = data_atual.strftime('%d/%m/%Y')
            d_fim_str = fim_fatia.strftime('%d/%m/%Y')
            
            # HEADERS COMPLETOS
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Connection": "keep-alive",
                "Referer": "https://www.bcb.gov.br/"
            }
            
            params = {
                'formato': 'json',
                'dataInicial': self._formatar_data_bcb(data_atual),
                'dataFinal': self._formatar_data_bcb(fim_fatia)
            }
            
            try:
                url = self.bcb_base_url.format(serie=serie_codigo)
                
                # Tenta requisição normal
                try:
                    response = requests.get(url, params=params, headers=headers, timeout=30)
                    response.raise_for_status()
                except requests.exceptions.RequestException:
                    print(f"    ⚠️ Falha SSL no bloco {d_ini_str}. Tentando modo inseguro...")
                    response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
                    response.raise_for_status()
                
                # Tenta ler o JSON
                try:
                    dados = response.json()
                except json.JSONDecodeError:
                    print(f"    ❌ Resposta inválida (não JSON) para o período {d_ini_str}-{d_fim_str}")
                    dados = []

                # Verifica se o JSON é uma lista ou um dicionário de erro
                if isinstance(dados, dict) and "error" in dados:
                    print(f"    ❌ Erro da API do BCB: {dados['error']}")
                elif isinstance(dados, list) and len(dados) > 0:
                    todos_dados.extend(dados) # Adiciona à lista geral
                    print(f"    ✓ Bloco {d_ini_str} a {d_fim_str}: {len(dados)} registros.")
                else:
                    print(f"    ⚠️ Sem dados para o bloco {d_ini_str} a {d_fim_str}.")
                    
            except Exception as e:
                print(f"    ❌ Erro ao buscar bloco {d_ini_str}: {str(e)}")
            
            # Avança para o dia seguinte ao fim desta fatia
            data_atual = fim_fatia + timedelta(days=1)
        
        # Processar o resultado acumulado
        if not todos_dados:
            print(f"  ⚠️  Nenhum dado retornado em nenhuma das tentativas.")
            return pd.DataFrame()
            
        try:
            df = pd.DataFrame(todos_dados)
            # Garantir que as colunas existem antes de processar
            if 'data' in df.columns and 'valor' in df.columns:
                df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
                df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
                df = df.dropna()
                df = df.set_index('data')
                df = df.sort_index()
                # Remove duplicatas que podem ocorrer na junção das fatias
                df = df[~df.index.duplicated(keep='first')]
                print(f"  ✅ Total consolidado: {len(df)} registros obtidos.")
                return df
            else:
                print("  ❌ Formato de dados inesperado após consolidação.")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"  ❌ Erro ao processar DataFrame final: {str(e)}")
            return pd.DataFrame()
    
    def _salvar_cache(self, nome, df):
        """Salva DataFrame em cache"""
        cache_file = self.cache_dir / f'{nome}.csv'
        df.to_csv(cache_file)
        
        # Atualizar timestamp
        timestamps = {}
        if self.ultima_atualizacao_file.exists():
            with open(self.ultima_atualizacao_file, 'r') as f:
                timestamps = json.load(f)
        
        timestamps[nome] = datetime.now().isoformat()
        
        with open(self.ultima_atualizacao_file, 'w') as f:
            json.dump(timestamps, f, indent=2)
    
    def _carregar_cache(self, nome):
        """Carrega DataFrame do cache"""
        cache_file = self.cache_dir / f'{nome}.csv'
        if cache_file.exists():
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            return df
        return None
    
    def _cache_valido(self, nome, max_dias=7):
        """Verifica se o cache é válido (menos de X dias)"""
        if not self.ultima_atualizacao_file.exists():
            return False
        
        with open(self.ultima_atualizacao_file, 'r') as f:
            timestamps = json.load(f)
        
        if nome not in timestamps:
            return False
        
        ultima_atualizacao = datetime.fromisoformat(timestamps[nome])
        idade = (datetime.now() - ultima_atualizacao).days
        
        return idade < max_dias
    
    def obter_cdi(self, data_inicio, data_fim):
        """
        Obtém dados do CDI e retorna em formato compatível com yfinance
        
        Args:
            data_inicio: Data inicial
            data_fim: Data final
            
        Returns:
            DataFrame no formato yfinance (com Close, Open, High, Low, Volume)
        """
        print("\n💰 Obtendo dados do CDI (Certificado de Depósito Interbancário)")
        
        # Verificar cache
        cache_valido = self._cache_valido('cdi')
        dados_cache = self._carregar_cache('cdi') if cache_valido else None
        
        if dados_cache is not None and cache_valido:
            print("  ✓ Cache local encontrado e válido")
            
            # Verificar se precisa atualizar dados mais recentes
            if dados_cache.index[-1].date() < data_fim.date():
                print("  📥 Atualizando dados mais recentes...")
                novos_dados = self._buscar_serie_bcb(
                    self.series['CDI'],
                    dados_cache.index[-1] + timedelta(days=1),
                    data_fim
                )
                if not novos_dados.empty:
                    dados_cache = pd.concat([dados_cache, novos_dados])
                    self._salvar_cache('cdi', dados_cache)
        else:
            print("  📥 Buscando dados do Banco Central do Brasil...")
            dados_cache = self._buscar_serie_bcb(
                self.series['CDI'],
                data_inicio,
                data_fim
            )
            if not dados_cache.empty:
                self._salvar_cache('cdi', dados_cache)
        
        if dados_cache.empty:
            raise ValueError("Não foi possível obter dados do CDI")
        
        # Filtrar período solicitado
        mask = (dados_cache.index >= data_inicio) & (dados_cache.index <= data_fim)
        df_filtrado = dados_cache[mask].copy()
        
        # Calcular valor acumulado do investimento
        # Assumindo investimento inicial de R$ 100.000
        valor_inicial = 100000
        
        # CDI é taxa anual, converter para diária
        df_filtrado['taxa_diaria'] = (1 + df_filtrado['valor'] / 100) ** (1/252) - 1
        df_filtrado['fator_acumulado'] = (1 + df_filtrado['taxa_diaria']).cumprod()
        df_filtrado['valor_investimento'] = valor_inicial * df_filtrado['fator_acumulado']
        
        # Criar DataFrame compatível com yfinance
        df_yf = pd.DataFrame(index=df_filtrado.index)
        df_yf['Open'] = df_filtrado['valor_investimento']
        df_yf['High'] = df_filtrado['valor_investimento']
        df_yf['Low'] = df_filtrado['valor_investimento']
        df_yf['Close'] = df_filtrado['valor_investimento']
        df_yf['Volume'] = 0
        df_yf['Adj Close'] = df_filtrado['valor_investimento']
        
        # Estatísticas
        taxa_media = df_filtrado['valor'].mean()
        taxa_periodo = ((df_filtrado['fator_acumulado'].iloc[-1] - 1) * 100)
        
        print(f"\n  📊 Estatísticas do CDI no período:")
        print(f"     • Taxa média: {taxa_media:.2f}% a.a.")
        print(f"     • Rentabilidade acumulada: {taxa_periodo:.2f}%")
        print(f"     • Dias úteis: {len(df_filtrado)}")
        print(f"     • Valor final (R$ 100k investidos): R$ {df_filtrado['valor_investimento'].iloc[-1]:,.2f}")
        
        return df_yf
    
    def obter_poupanca(self, data_inicio, data_fim):
        """
        Calcula rendimento da poupança baseado nas regras vigentes
        
        Args:
            data_inicio: Data inicial
            data_fim: Data final
            
        Returns:
            DataFrame no formato yfinance
        """
        print("\n🏦 Calculando rendimento da Poupança")
        print("  📋 Regra: Se SELIC > 8,5% → 0,5% a.m. + TR")
        print("            Se SELIC ≤ 8,5% → 70% SELIC + TR")
        
        try:
            # Obter SELIC
            print("  📥 Buscando dados da SELIC...")
            selic = self._buscar_serie_bcb(self.series['SELIC'], data_inicio, data_fim)
            if selic.empty:
                raise ValueError("Não foi possível obter dados da SELIC")
            
            # Obter TR (Taxa Referencial)
            print("  📥 Buscando dados da TR...")
            tr = self._buscar_serie_bcb(self.series['TR'], data_inicio, data_fim)
            if tr.empty:
                print("  ⚠️  TR não disponível, assumindo 0%")
                tr = pd.DataFrame({'valor': 0}, index=selic.index)
            
            # Alinhar dados usando merge para evitar problemas
            df = selic.rename(columns={'valor': 'selic'})
            if not tr.empty and 'valor' in tr.columns:
                tr_renamed = tr.rename(columns={'valor': 'tr'})
                df = df.merge(tr_renamed, left_index=True, right_index=True, how='left')
            else:
                df['tr'] = 0
            
            # Preencher valores faltantes
            df = df.fillna(0)
            
            # Filtrar período solicitado
            mask = (df.index >= data_inicio) & (df.index <= data_fim)
            df = df[mask].copy()
            
            if df.empty:
                raise ValueError("Nenhum dado disponível para o período solicitado")
            
            # Calcular rendimento da poupança
            # Poupança rende mensalmente, mas vamos aproximar diariamente
            valor_inicial = 100000
            
            # Aplicar regra da poupança
            df['rendimento_mensal'] = df['selic'].apply(
                lambda x: 0.5 if x > 8.5 else (x * 0.7 / 12)
            )
            
            # Adicionar TR (converter para mensal)
            df['rendimento_total'] = df['rendimento_mensal'] + (df['tr'] / 12)
            
            # Calcular acumulado (aproximação diária)
            df['taxa_diaria'] = df['rendimento_total'] / 30
            df['fator_acumulado'] = (1 + df['taxa_diaria'] / 100).cumprod()
            df['valor_investimento'] = valor_inicial * df['fator_acumulado']
            
            # Criar DataFrame compatível com yfinance
            df_yf = pd.DataFrame(index=df.index)
            df_yf['Open'] = df['valor_investimento']
            df_yf['High'] = df['valor_investimento']
            df_yf['Low'] = df['valor_investimento']
            df_yf['Close'] = df['valor_investimento']
            df_yf['Volume'] = 0
            df_yf['Adj Close'] = df['valor_investimento']
            
            # Estatísticas
            taxa_periodo = ((df['fator_acumulado'].iloc[-1] - 1) * 100)
            selic_media = df['selic'].mean()
            
            print(f"\n  📊 Estatísticas da Poupança no período:")
            print(f"     • SELIC média: {selic_media:.2f}% a.a.")
            print(f"     • Rentabilidade acumulada: {taxa_periodo:.2f}%")
            print(f"     • Dias com dados: {len(df)}")
            print(f"     • Valor final (R$ 100k investidos): R$ {df['valor_investimento'].iloc[-1]:,.2f}")
            
            return df_yf
            
        except Exception as e:
            print(f"\n  ❌ Erro ao calcular poupança: {str(e)}")
            print(f"  💡 Dica: A poupança requer dados da SELIC")
            print(f"          Tente usar RF-CDI como alternativa")
            raise ValueError(f"Não foi possível calcular rendimento da poupança: {str(e)}")


# Função auxiliar para integração fácil
def obter_ativo_renda_fixa(ticker, data_inicio, data_fim):
    """
    Função auxiliar para obter dados de renda fixa
    
    Args:
        ticker: Código do ativo (RF-CDI, RF-POUPANCA, etc.)
        data_inicio: Data inicial
        data_fim: Data final
        
    Returns:
        DataFrame no formato yfinance
    """
    rf = RendaFixaBR()
    
    if ticker == 'RF-CDI':
        return rf.obter_cdi(data_inicio, data_fim)
    elif ticker == 'RF-POUPANCA':
        return rf.obter_poupanca(data_inicio, data_fim)
    else:
        raise ValueError(f"Ticker de renda fixa '{ticker}' não reconhecido")