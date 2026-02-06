import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Importar módulo de renda fixa brasileira
try:
    from renda_fixa_br import obter_ativo_renda_fixa
    RENDA_FIXA_DISPONIVEL = True
except ImportError:
    RENDA_FIXA_DISPONIVEL = False
    print("⚠️  Módulo de renda fixa não disponível")

def obter_dados_ativo(ticker, data_inicio, data_fim):
    """
    Obtém dados históricos de um ativo financeiro
    
    Args:
        ticker: Símbolo do ativo (ex: 'AAPL', 'PETR4.SA', 'RF-CDI')
        data_inicio: Data inicial (datetime)
        data_fim: Data final (datetime)
    
    Returns:
        DataFrame com os dados históricos
    """
    # Verificar se é ativo de renda fixa brasileira
    if ticker.startswith('RF-'):
        if not RENDA_FIXA_DISPONIVEL:
            raise ValueError(
                "Módulo de renda fixa não está disponível. "
                "Certifique-se de que o arquivo renda_fixa_br.py está no mesmo diretório."
            )
        
        print(f"\n💰 Detectado ativo de Renda Fixa Brasileira: {ticker}")
        return obter_ativo_renda_fixa(ticker, data_inicio, data_fim)
    
    # Caso contrário, buscar do Yahoo Finance
    try:
        # Download direto dos dados com múltiplas tentativas
        print(f"  Tentando baixar dados de {ticker}...")
        
        tentativas = 3
        ultimo_erro = None
        
        for tentativa in range(tentativas):
            try:
                dados = yf.download(
                    ticker, 
                    start=data_inicio, 
                    end=data_fim, 
                    progress=False,
                    timeout=30
                )
                
                if not dados.empty:
                    print(f"  ✓ Dados obtidos com sucesso!")
                    print(f"    Período: {dados.index[0].strftime('%d/%m/%Y')} a {dados.index[-1].strftime('%d/%m/%Y')}")
                    print(f"    Total de {len(dados)} dias de dados")
                    return dados
                    
            except Exception as e:
                ultimo_erro = str(e)
                if tentativa < tentativas - 1:
                    print(f"  ⚠️  Tentativa {tentativa + 1} falhou, tentando novamente...")
                    import time
                    time.sleep(2)  # Espera 2 segundos antes de tentar novamente
                    continue
                else:
                    break
        
        # Se chegou aqui, não conseguiu dados
        raise ValueError(f"Ticker '{ticker}' não encontrado ou sem dados disponíveis")
        
    except Exception as e:
        erro_msg = str(e)
        
        # Mensagens de erro mais específicas
        if "404" in erro_msg or "Not Found" in erro_msg or "delisted" in erro_msg:
            raise ValueError(
                f"❌ Ticker '{ticker}' não encontrado no Yahoo Finance.\n"
                f"   Possíveis causas:\n"
                f"   • O ticker foi removido ou renomeado\n"
                f"   • Use '^BVSP' (com acento circunflexo) para Ibovespa\n"
                f"   • Para ações BR, adicione .SA (ex: PETR4.SA)\n"
                f"   • Tente novamente em alguns minutos (pode ser instabilidade temporária)"
            )
        elif "ConnectionError" in erro_msg or "Failed to connect" in erro_msg or "timeout" in erro_msg.lower():
            raise ValueError(
                f"❌ Erro de conexão ao buscar '{ticker}'.\n"
                f"   • Verifique sua conexão com a internet\n"
                f"   • O Yahoo Finance pode estar temporariamente indisponível\n"
                f"   • Tente novamente em alguns minutos"
            )
        else:
            raise ValueError(f"❌ Erro ao obter dados para '{ticker}': {erro_msg}")

def converter_usd_para_brl(dados_usd, data_inicio, data_fim):
    """
    Converte dados de USD para BRL usando taxa de câmbio histórica
    
    Args:
        dados_usd: DataFrame com dados em USD
        data_inicio: Data inicial (datetime)
        data_fim: Data final (datetime)
    
    Returns:
        DataFrame com dados convertidos para BRL
    """
    try:
        print("  Obtendo taxas de câmbio USD/BRL...")
        
        # BRL=X é o par USD/BRL no Yahoo Finance
        cambio = yf.download('BRL=X', start=data_inicio, end=data_fim, progress=False, timeout=30)
        
        if cambio.empty:
            print("  ⚠️  Não foi possível obter taxas de câmbio, usando última taxa conhecida")
            # Tentar obter apenas a última taxa
            cambio_atual = yf.download('BRL=X', period='1d', progress=False, timeout=30)
            if not cambio_atual.empty:
                taxa_fixa = float(cambio_atual['Close'].iloc[-1])
                print(f"  Usando taxa fixa: R$ {taxa_fixa:.2f} por USD")
                dados_brl = dados_usd.copy()
                # Multiplicar coluna por coluna para evitar erros de indexação
                for col in dados_brl.columns:
                    if col in ['Open', 'High', 'Low', 'Close', 'Adj Close']:
                        dados_brl[col] = dados_brl[col] * taxa_fixa
                return dados_brl
            else:
                raise ValueError("Não foi possível obter taxas de câmbio")
        
        print("  ✓ Taxas de câmbio obtidas!")
        
        # Criar cópia dos dados
        dados_brl = dados_usd.copy()
        
        # Extrair a série de taxas de câmbio
        if isinstance(cambio['Close'], pd.DataFrame):
            # Se for DataFrame com múltiplas colunas, pega a primeira
            taxa_cambio = cambio['Close'].iloc[:, 0]
        else:
            # Se for Series, usa diretamente
            taxa_cambio = cambio['Close']
        
        # Criar Series com índice correto para evitar warnings
        taxa_cambio = pd.Series(taxa_cambio.values, index=taxa_cambio.index)
        
        # Reindexar para as datas dos dados USD usando forward fill
        taxa_cambio_alinhada = taxa_cambio.reindex(dados_usd.index)
        taxa_cambio_alinhada = taxa_cambio_alinhada.ffill()  # forward fill
        
        # Se ainda houver NaNs no início, fazer backward fill
        taxa_cambio_alinhada = taxa_cambio_alinhada.bfill()
        
        # Converter cada coluna de preço
        colunas_preco = ['Open', 'High', 'Low', 'Close', 'Adj Close']
        for col in colunas_preco:
            if col in dados_brl.columns:
                # Verificar se a coluna é DataFrame ou Series
                if isinstance(dados_brl[col], pd.DataFrame):
                    dados_brl[col] = dados_brl[col].iloc[:, 0] * taxa_cambio_alinhada
                else:
                    dados_brl[col] = dados_brl[col] * taxa_cambio_alinhada
        
        taxa_media = float(taxa_cambio_alinhada.mean())
        print(f"  ✓ Conversão concluída! Taxa média: R$ {taxa_media:.2f}")
        
        return dados_brl
        
    except Exception as e:
        print(f"  ⚠️  Erro na conversão: {str(e)}")
        import traceback
        traceback.print_exc()
        print("  Continuando com dados em USD...")
        return dados_usd

def calcular_variacao_percentual(dados):
    """
    Calcula a variação percentual em relação ao primeiro valor
    
    Args:
        dados: DataFrame com coluna 'Close'
    
    Returns:
        Series com variações percentuais
    """
    # Extrair a coluna Close corretamente
    if 'Close' in dados.columns:
        coluna_close = dados['Close']
        
        # Se for DataFrame (multi-nível), pegar primeira coluna
        if isinstance(coluna_close, pd.DataFrame):
            coluna_close = coluna_close.iloc[:, 0]
        
        # Garantir que é uma Series
        if not isinstance(coluna_close, pd.Series):
            coluna_close = pd.Series(coluna_close)
        
        preco_inicial = float(coluna_close.iloc[0])
        variacao = ((coluna_close - preco_inicial) / preco_inicial) * 100
        
        return variacao
    else:
        raise ValueError("DataFrame não contém coluna 'Close'")

def calcular_retorno_janela(dados, janela_meses):
    """
    Calcula o retorno percentual para janelas móveis de X meses
    
    Args:
        dados: DataFrame com coluna 'Close'
        janela_meses: Tamanho da janela em meses
    
    Returns:
        Series com retornos de cada janela
    """
    # Extrair a coluna Close
    if 'Close' in dados.columns:
        coluna_close = dados['Close']
        
        if isinstance(coluna_close, pd.DataFrame):
            coluna_close = coluna_close.iloc[:, 0]
        
        if not isinstance(coluna_close, pd.Series):
            coluna_close = pd.Series(coluna_close)
        
        # Calcular retornos para janela móvel
        # Aproximadamente 21 dias úteis por mês
        dias_janela = janela_meses * 21
        
        retornos = []
        datas = []
        
        for i in range(len(coluna_close) - dias_janela):
            preco_inicial = float(coluna_close.iloc[i])
            preco_final = float(coluna_close.iloc[i + dias_janela])
            retorno = ((preco_final - preco_inicial) / preco_inicial) * 100
            retornos.append(retorno)
            datas.append(coluna_close.index[i + dias_janela])
        
        return pd.Series(retornos, index=datas)
    else:
        raise ValueError("DataFrame não contém coluna 'Close'")

def encontrar_janelas_superacao(retornos1, retornos2, janela_meses):
    """
    Identifica janelas onde ativo2 superou ativo1
    
    Args:
        retornos1: Series com retornos do ativo 1
        retornos2: Series com retornos do ativo 2
        janela_meses: Tamanho da janela em meses
    
    Returns:
        Lista de tuplas (data_inicio, data_fim, retorno_ativo1, retorno_ativo2)
    """
    # Alinhar os índices
    retornos_alinhados = pd.DataFrame({
        'ativo1': retornos1,
        'ativo2': retornos2
    }).dropna()
    
    if retornos_alinhados.empty:
        return []
    
    # Encontrar onde ativo2 > ativo1
    superacao = retornos_alinhados['ativo2'] > retornos_alinhados['ativo1']
    
    janelas = []
    em_superacao = False
    inicio_idx = None
    
    dias_janela = janela_meses * 21
    
    for i, (data, valor) in enumerate(superacao.items()):
        if valor and not em_superacao:
            # Início de período de superação
            em_superacao = True
            inicio_idx = i
        elif not valor and em_superacao:
            # Fim de período de superação
            em_superacao = False
            if inicio_idx is not None:
                # A data de início da janela é aproximadamente janela_meses antes da data de fim do retorno
                data_inicio = retornos_alinhados.index[inicio_idx]
                data_fim = data  # data atual (fim da superação)
                ret1 = retornos_alinhados.iloc[i-1]['ativo1']
                ret2 = retornos_alinhados.iloc[i-1]['ativo2']
                janelas.append((data_inicio, data_fim, ret1, ret2))
            inicio_idx = None
    
    # Se terminou ainda em superação
    if em_superacao and inicio_idx is not None:
        data_inicio = retornos_alinhados.index[inicio_idx]
        data_fim = retornos_alinhados.index[-1]
        ret1 = retornos_alinhados.iloc[-1]['ativo1']
        ret2 = retornos_alinhados.iloc[-1]['ativo2']
        janelas.append((data_inicio, data_fim, ret1, ret2))
    
    return janelas

def encontrar_periodos_superacao(var_ativo1, var_ativo2):
    """
    Identifica períodos onde ativo2 supera ativo1
    
    Args:
        var_ativo1: Series com variações do ativo 1
        var_ativo2: Series com variações do ativo 2
    
    Returns:
        Lista de tuplas (data_inicio, data_fim, dias)
    """
    # Alinha os dados por índice (datas)
    df_comparacao = pd.DataFrame({
        'ativo1': var_ativo1,
        'ativo2': var_ativo2
    }).dropna()
    
    # Identifica onde ativo2 está melhor
    ativo2_melhor = df_comparacao['ativo2'] > df_comparacao['ativo1']
    
    periodos = []
    inicio = None
    
    for i, (data, valor) in enumerate(ativo2_melhor.items()):
        if valor and inicio is None:
            # Início de um período de superação
            inicio = data
        elif not valor and inicio is not None:
            # Fim de um período de superação
            fim = df_comparacao.index[i-1]
            dias = (fim - inicio).days + 1
            periodos.append((inicio, fim, dias))
            inicio = None
    
    # Se terminou ainda em superação
    if inicio is not None:
        fim = df_comparacao.index[-1]
        dias = (fim - inicio).days + 1
        periodos.append((inicio, fim, dias))
    
    return periodos

def plotar_comparacao(ticker1, ticker2, data_inicio, data_fim, autoria=""):
    """
    Plota gráfico comparativo de dois ativos
    
    Args:
        ticker1: Ticker do primeiro ativo
        ticker2: Ticker do segundo ativo
        data_inicio: Data inicial (datetime)
        data_fim: Data final (datetime)
        autoria: Nome do autor do gráfico (opcional)
    """
    print(f"Obtendo dados para {ticker1}...")
    dados1 = obter_dados_ativo(ticker1, data_inicio, data_fim)
    
    # Verificar se precisa converter para BRL
    if ticker1.endswith('-USD'):
        print(f"  💱 Detectado ativo em USD, convertendo para BRL...")
        dados1 = converter_usd_para_brl(dados1, data_inicio, data_fim)
        ticker1_display = ticker1.replace('-USD', '-BRL*')
    else:
        ticker1_display = ticker1
    
    print(f"\nObtendo dados para {ticker2}...")
    dados2 = obter_dados_ativo(ticker2, data_inicio, data_fim)
    
    # Verificar se precisa converter para BRL
    if ticker2.endswith('-USD'):
        print(f"  💱 Detectado ativo em USD, convertendo para BRL...")
        dados2 = converter_usd_para_brl(dados2, data_inicio, data_fim)
        ticker2_display = ticker2.replace('-USD', '-BRL*')
    else:
        ticker2_display = ticker2
    
    print("\nCalculando variações...")
    var1 = calcular_variacao_percentual(dados1)
    var2 = calcular_variacao_percentual(dados2)
    
    print("Identificando períodos de superação...")
    periodos = encontrar_periodos_superacao(var1, var2)
    
    # Calcular total de dias
    total_dias = sum(p[2] for p in periodos)
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plotar linhas
    ax.plot(var1.index, var1.values, label=ticker1_display, linewidth=2, color='#1f77b4')
    ax.plot(var2.index, var2.values, label=ticker2_display, linewidth=2, color='#ff7f0e')
    
    # Adicionar sombreamento e anotações
    for inicio, fim, dias in periodos:
        ax.axvspan(inicio, fim, alpha=0.2, color='green', zorder=0)
        
        # Calcular posição para o texto
        meio = inicio + (fim - inicio) / 2
        y_max = max(var1.max(), var2.max())
        y_pos = y_max * 0.95
        
        # Adicionar texto com número de dias
        ax.text(meio, y_pos, f'{dias}d', 
                horizontalalignment='center',
                verticalalignment='top',
                fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                         edgecolor='green', alpha=0.7))
    
    # Adicionar caixa de texto com total de dias
    textstr = f'Total de dias em que {ticker2_display}\nsuperou {ticker1_display}: {total_dias} dias'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)
    
    # Adicionar nota sobre conversão se aplicável
    nota_conversao = []
    if ticker1.endswith('-USD'):
        nota_conversao.append(f'{ticker1_display}: Convertido de USD para BRL usando taxas históricas')
    if ticker2.endswith('-USD'):
        nota_conversao.append(f'{ticker2_display}: Convertido de USD para BRL usando taxas históricas')
    
    if nota_conversao:
        nota_texto = '\n'.join(nota_conversao)
        ax.text(0.98, 0.02, nota_texto, transform=ax.transAxes, fontsize=8,
                verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.6),
                style='italic')
    
    # Adicionar autoria se fornecida
    if autoria:
        ax.text(0.02, 0.02, f'Elaborado por: {autoria}', 
                transform=ax.transAxes, fontsize=9,
                verticalalignment='bottom', horizontalalignment='left',
                style='italic', color='gray')
    
    # Configurações do gráfico
    ax.set_xlabel('Data', fontsize=12)
    ax.set_ylabel('Variação (%)', fontsize=12)
    
    # Formatar período para o título
    periodo_str = f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
    
    titulo = f'Comparação de Desempenho: {ticker1_display} vs {ticker2_display}\nPeríodo: {periodo_str}'
    if nota_conversao:
        titulo += ' (valores em BRL)'
    
    ax.set_title(titulo, fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    
    plt.tight_layout()
    
    # Salvar gráfico
    nome_arquivo = f'comparacao_{ticker1_display.replace("*", "")}_vs_{ticker2_display.replace("*", "")}.png'
    nome_arquivo = nome_arquivo.replace('^', '').replace('=', '').replace('/', '_')
    
    # Tentar salvar em diferentes locais
    caminhos_salvar = [
        '/mnt/user-data/outputs/',  # Para servidor Claude
        './',  # Diretório atual (local)
    ]
    
    salvo = False
    for caminho in caminhos_salvar:
        try:
            import os
            # Criar diretório se não existir
            if not os.path.exists(caminho):
                try:
                    os.makedirs(caminho, exist_ok=True)
                except:
                    continue
            
            caminho_completo = os.path.join(caminho, nome_arquivo)
            plt.savefig(caminho_completo, dpi=300, bbox_inches='tight')
            print(f"\n✓ Gráfico salvo como: {caminho_completo}")
            salvo = True
            break
        except Exception as e:
            continue
    
    if not salvo:
        print(f"\n⚠️  Não foi possível salvar o gráfico em arquivo")
        print(f"   O gráfico será exibido na tela apenas")
    
    plt.show()
    
    # Calcular duração do período
    dias_totais = (data_fim - data_inicio).days
    
    # Imprimir estatísticas
    print(f"\n{'='*70}")
    print(f"✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
    print(f"{'='*70}")
    print(f"\n📊 RESUMO DA ANÁLISE")
    print(f"{'-'*70}")
    print(f"Período analisado: {periodo_str} ({dias_totais} dias)")
    print(f"\nAtivo 1: {ticker1_display}")
    print(f"  • Variação total: {var1.iloc[-1]:+.2f}%")
    if ticker1.endswith('-USD'):
        print(f"  • Convertido de USD para BRL usando taxas históricas")
    
    print(f"\nAtivo 2: {ticker2_display}")
    print(f"  • Variação total: {var2.iloc[-1]:+.2f}%")
    if ticker2.endswith('-USD'):
        print(f"  • Convertido de USD para BRL usando taxas históricas")
    
    print(f"\n🏆 COMPARAÇÃO DE DESEMPENHO")
    print(f"{'-'*70}")
    print(f"Períodos em que {ticker2_display} superou {ticker1_display}: {len(periodos)}")
    print(f"Total de dias de superação: {total_dias} dias")
    
    # Calcular qual ativo teve melhor desempenho geral
    if var1.iloc[-1] > var2.iloc[-1]:
        vencedor = ticker1_display
        diferenca = var1.iloc[-1] - var2.iloc[-1]
    else:
        vencedor = ticker2_display
        diferenca = var2.iloc[-1] - var1.iloc[-1]
    
    print(f"\n🥇 Melhor desempenho geral: {vencedor}")
    print(f"   Diferença: {diferenca:.2f} pontos percentuais")
    print(f"{'='*70}\n")

def plotar_analise_janelas(ticker1, ticker2, periodo_anos, janela_meses, autoria=""):
    """
    Plota análise de janelas móveis comparando dois ativos
    
    Args:
        ticker1: Ticker do primeiro ativo
        ticker2: Ticker do segundo ativo
        periodo_anos: Período total de análise em anos
        janela_meses: Tamanho da janela em meses
        autoria: Nome do autor do gráfico (opcional)
    """
    # Calcular datas - adicionar margem extra para compensar a janela móvel
    # Se queremos analisar 10 anos com janela de 24 meses, precisamos de dados de ~12 anos
    margem_extra_anos = (janela_meses / 12)  # Converter meses em anos
    
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=int((periodo_anos + margem_extra_anos) * 365))
    
    # Datas que queremos mostrar no gráfico (período solicitado pelo usuário)
    data_inicio_display = data_fim - timedelta(days=periodo_anos * 365)
    
    print(f"\n{'='*70}")
    print(f"🔍 ANÁLISE DE JANELAS MÓVEIS")
    print(f"{'='*70}")
    print(f"Período solicitado: {periodo_anos} anos")
    print(f"Tamanho da janela: {janela_meses} meses")
    print(f"Buscando dados extras para cálculo das janelas...")
    print(f"{'='*70}\n")
    
    print(f"Obtendo dados para {ticker1}...")
    dados1 = obter_dados_ativo(ticker1, data_inicio, data_fim)
    
    # Verificar se precisa converter para BRL
    if ticker1.endswith('-USD'):
        print(f"  💱 Detectado ativo em USD, convertendo para BRL...")
        dados1 = converter_usd_para_brl(dados1, data_inicio, data_fim)
        ticker1_display = ticker1.replace('-USD', '-BRL*')
    else:
        ticker1_display = ticker1
    
    print(f"\nObtendo dados para {ticker2}...")
    dados2 = obter_dados_ativo(ticker2, data_inicio, data_fim)
    
    # Verificar se precisa converter para BRL
    if ticker2.endswith('-USD'):
        print(f"  💱 Detectado ativo em USD, convertendo para BRL...")
        dados2 = converter_usd_para_brl(dados2, data_inicio, data_fim)
        ticker2_display = ticker2.replace('-USD', '-BRL*')
    else:
        ticker2_display = ticker2
    
    print("\nCalculando retornos de janelas móveis...")
    retornos1 = calcular_retorno_janela(dados1, janela_meses)
    retornos2 = calcular_retorno_janela(dados2, janela_meses)
    
    print(f"  ✓ {len(retornos1)} janelas calculadas para {ticker1_display}")
    print(f"  ✓ {len(retornos2)} janelas calculadas para {ticker2_display}")
    
    # Verificar se há dados suficientes
    if len(retornos1) == 0 or len(retornos2) == 0:
        print("\n❌ Erro: Não há dados suficientes para calcular janelas móveis")
        print(f"   Tente usar um período maior ou uma janela menor")
        return
    
    # Filtrar retornos para mostrar apenas o período solicitado
    retornos1_filtrado = retornos1[retornos1.index >= data_inicio_display]
    retornos2_filtrado = retornos2[retornos2.index >= data_inicio_display]
    
    print(f"  ✓ Filtrando para período solicitado: {len(retornos1_filtrado)} janelas exibidas")
    
    print("Identificando janelas de superação...")
    janelas = encontrar_janelas_superacao(retornos1_filtrado, retornos2_filtrado, janela_meses)
    
    # Alinhar retornos para plotagem - usar os retornos filtrados
    retornos_alinhados = pd.DataFrame({
        'ret1': retornos1_filtrado,
        'ret2': retornos2_filtrado
    }).dropna()
    
    # Criar figura com 3 subplots
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 1, height_ratios=[2, 1.5, 0.8], hspace=0.3)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    
    # Subplot 1: Retornos das janelas móveis
    # Plotar apenas os dados alinhados
    ax1.plot(retornos_alinhados.index, retornos_alinhados['ret1'], 
             label=f'{ticker1_display}', 
             linewidth=2.5, color='#1f77b4', alpha=0.8)
    ax1.plot(retornos_alinhados.index, retornos_alinhados['ret2'], 
             label=f'{ticker2_display}', 
             linewidth=2.5, color='#ff7f0e', alpha=0.8)
    
    # Preencher área entre as linhas usando dados alinhados
    if not retornos_alinhados.empty:
        ax1.fill_between(retornos_alinhados.index, 
                         retornos_alinhados['ret1'], 
                         retornos_alinhados['ret2'], 
                         where=(retornos_alinhados['ret2'] > retornos_alinhados['ret1']),
                         alpha=0.2, color='green', 
                         label=f'{ticker2_display} > {ticker1_display}',
                         interpolate=True)
        ax1.fill_between(retornos_alinhados.index, 
                         retornos_alinhados['ret1'], 
                         retornos_alinhados['ret2'], 
                         where=(retornos_alinhados['ret1'] >= retornos_alinhados['ret2']),
                         alpha=0.2, color='red', 
                         label=f'{ticker1_display} > {ticker2_display}',
                         interpolate=True)
    
    ax1.set_ylabel(f'Retorno em {janela_meses} meses (%)', fontsize=13, fontweight='bold')
    ax1.set_title(f'Análise de Janelas Móveis: {ticker1_display} vs {ticker2_display}\n'
                  f'Retornos em janelas de {janela_meses} meses ao longo de {periodo_anos} anos',
                  fontsize=15, fontweight='bold', pad=20)
    ax1.legend(loc='best', fontsize=11, framealpha=0.9)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    
    # Adicionar estatísticas no gráfico - usando dados filtrados
    ret1_media = retornos_alinhados['ret1'].mean()
    ret2_media = retornos_alinhados['ret2'].mean()
    stats_text = f'Retorno médio (janela {janela_meses}m):\n{ticker1_display}: {ret1_media:.1f}%  |  {ticker2_display}: {ret2_media:.1f}%'
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Subplot 2: Diferença de retornos
    # Usar os mesmos dados alinhados
    diferenca = retornos_alinhados['ret2'] - retornos_alinhados['ret1']
    cores_diff = ['green' if d > 0 else 'red' for d in diferenca]
    ax2.bar(retornos_alinhados.index, diferenca, width=10, color=cores_diff, alpha=0.6, 
            edgecolor='none', linewidth=0)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.set_ylabel(f'Diferença de retorno\n{ticker2_display} - {ticker1_display} (pp)', 
                   fontsize=12, fontweight='bold')
    ax2.set_title(f'Vantagem Relativa (positivo = {ticker2_display} ganha)', 
                  fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Destacar janelas de superação contínuas
    for inicio, fim, ret1, ret2 in janelas:
        # Filtrar apenas as datas dentro desta janela
        mascara = (retornos_alinhados.index >= inicio) & (retornos_alinhados.index <= fim)
        if mascara.any():
            ax2.axvspan(inicio, fim, alpha=0.15, color='green', zorder=0)
    
    # Subplot 3: Timeline simplificada
    ax3.set_ylim(-0.2, 1.2)
    ax3.set_yticks([])
    
    # Background
    ax3.axhspan(-0.1, 1.1, color='lightgray', alpha=0.2)
    
    # Linha base
    ax3.plot([retornos1.index.min(), retornos1.index.max()], [0.5, 0.5], 
            color='gray', linewidth=8, alpha=0.3, solid_capstyle='round')
    
    # Destacar períodos de superação
    if janelas:
        for inicio, fim, ret1, ret2 in janelas:
            ax3.plot([inicio, fim], [0.5, 0.5], color='green', linewidth=12, 
                    alpha=0.7, solid_capstyle='round')
            
            # Adicionar marcador no meio
            meio = inicio + (fim - inicio) / 2
            duracao_meses = (fim - inicio).days / 30
            
            ax3.plot(meio, 0.5, 'o', color='darkgreen', markersize=10, zorder=5)
            ax3.text(meio, 0.85, f'{duracao_meses:.0f}m', 
                    horizontalalignment='center', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', 
                             edgecolor='darkgreen', alpha=0.9))
        
        # Legenda - movida para cima para não sobrepor o eixo
        ax3.text(0.5, 0.1, f'● = Janela onde {ticker2_display} superou {ticker1_display}', 
                transform=ax3.transAxes, horizontalalignment='center',
                fontsize=10, style='italic')
    else:
        ax3.text(0.5, 0.5, f'Nenhuma janela de superação encontrada', 
                transform=ax3.transAxes, horizontalalignment='center',
                fontsize=11, style='italic', color='red')
    
    ax3.set_xlabel('Período de Análise', fontsize=12, fontweight='bold')
    ax3.set_title('Timeline de Superações', fontsize=11, fontweight='bold')
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['left'].set_visible(False)
    
    # Adicionar autoria se fornecida (no canto inferior esquerdo da figura)
    if autoria:
        fig.text(0.02, 0.01, f'Elaborado por: {autoria}', 
                fontsize=9, style='italic', color='gray',
                verticalalignment='bottom', horizontalalignment='left')
    
    plt.tight_layout()
    
    # Salvar gráfico
    nome_arquivo = f'analise_janelas_{ticker1_display.replace("*", "")}_vs_{ticker2_display.replace("*", "")}_{janela_meses}m.png'
    nome_arquivo = nome_arquivo.replace('^', '').replace('=', '').replace('/', '_')
    
    # Tentar salvar em diferentes locais
    caminhos_salvar = [
        '/mnt/user-data/outputs/',
        './',
    ]
    
    salvo = False
    for caminho in caminhos_salvar:
        try:
            import os
            if not os.path.exists(caminho):
                try:
                    os.makedirs(caminho, exist_ok=True)
                except:
                    continue
            
            caminho_completo = os.path.join(caminho, nome_arquivo)
            plt.savefig(caminho_completo, dpi=300, bbox_inches='tight')
            print(f"\n✓ Gráfico salvo como: {caminho_completo}")
            salvo = True
            break
        except Exception as e:
            continue
    
    if not salvo:
        print(f"\n⚠️  Não foi possível salvar o gráfico em arquivo")
    
    plt.show()
    
    # Imprimir estatísticas
    print(f"\n{'='*70}")
    print(f"✅ ANÁLISE DE JANELAS CONCLUÍDA!")
    print(f"{'='*70}")
    print(f"\n📊 RESUMO DA ANÁLISE")
    print(f"{'-'*70}")
    print(f"Período analisado: {periodo_anos} anos ({data_inicio_display.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')})")
    print(f"Tamanho da janela: {janela_meses} meses")
    print(f"\nTotal de janelas analisadas: {len(retornos_alinhados)}")
    print(f"\n🏆 JANELAS DE SUPERAÇÃO")
    print(f"{'-'*70}")
    
    if janelas:
        print(f"\n{ticker2_display} superou {ticker1_display} em {len(janelas)} janelas:\n")
        
        for i, (inicio, fim, ret1, ret2) in enumerate(janelas, 1):
            duracao_dias = (fim - inicio).days
            duracao_meses = duracao_dias / 30
            diferenca = ret2 - ret1
            
            print(f"  {i}. {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}")
            print(f"     Duração: {duracao_meses:.1f} meses ({duracao_dias} dias)")
            print(f"     {ticker1_display}: {ret1:+.2f}% | {ticker2_display}: {ret2:+.2f}%")
            print(f"     {ticker2_display} superou por: {diferenca:+.2f} pontos percentuais")
            print()
        
        # Estatísticas gerais
        total_meses = sum((fim - inicio).days / 30 for inicio, fim, _, _ in janelas)
        media_duracao = total_meses / len(janelas)
        media_diferenca = sum(ret2 - ret1 for _, _, ret1, ret2 in janelas) / len(janelas)
        
        print(f"📈 ESTATÍSTICAS DAS JANELAS DE SUPERAÇÃO")
        print(f"{'-'*70}")
        print(f"Total de tempo em superação: {total_meses:.1f} meses")
        print(f"Duração média por janela: {media_duracao:.1f} meses")
        print(f"Diferença média de retorno: {media_diferenca:+.2f} pontos percentuais")
    else:
        print(f"\n{ticker2_display} NÃO superou {ticker1_display} em nenhuma janela de {janela_meses} meses")
        print(f"no período analisado.")
    
    print(f"{'='*70}\n")

def main():
    """
    Função principal do programa
    """
    print("="*70)
    print("           COMPARADOR DE ATIVOS FINANCEIROS")
    print("="*70)
    
    # Solicitar autoria (opcional)
    print("\n📝 Informações do gráfico (opcional):")
    autoria = input("Gráfico elaborado por (Enter para pular): ").strip()
    if autoria:
        print(f"   ✓ Autoria: {autoria}")
    
    # Menu principal
    print("\n📊 ESCOLHA O TIPO DE ANÁLISE:")
    print("\n  1️⃣  Análise Simples - Comparação de período específico")
    print("      (Compara variação entre duas datas específicas)")
    print("\n  2️⃣  Análise de Janelas Móveis - Identificar períodos de superação")
    print("      (Identifica em quais janelas de X meses um ativo superou o outro)")
    print()
    
    while True:
        escolha = input("Digite sua escolha (1 ou 2): ").strip()
        if escolha in ['1', '2']:
            break
        print("❌ Opção inválida! Digite 1 ou 2.")
    
    print("\n" + "="*70)
    
    # Informações sobre tickers
    print("\n📊 Exemplos de tickers válidos:")
    print("\n  🇧🇷 Ações brasileiras:")
    print("     PETR4.SA, VALE3.SA, ITUB4.SA, BBDC4.SA, MGLU3.SA")
    print("\n  🇺🇸 Ações americanas:")
    print("     AAPL, GOOGL, MSFT, TSLA, NVDA, AMZN")
    print("\n  📈 ETFs:")
    print("     SPY, QQQ, IVV, BOVA11.SA (Ibovespa)")
    print("\n  ₿ Criptomoedas:")
    print("     BTC-USD (Bitcoin), ETH-USD (Ethereum)")
    print("     ⚠️  Use BTC-USD, não BTC-BRL!")
    print("\n  💱 Índices:")
    print("     ^BVSP (Ibovespa), ^GSPC (S&P 500), ^DJI (Dow Jones)")
    
    if RENDA_FIXA_DISPONIVEL:
        print("\n  💰 Renda Fixa Brasileira (via Banco Central):")
        print("     RF-CDI (CDI acumulado)")
        print("     RF-POUPANCA (Poupança)")
    
    print()
    
    # Solicitar tickers
    ticker1 = input("Digite o ticker do ATIVO 1: ").strip().upper()
    ticker2 = input("Digite o ticker do ATIVO 2: ").strip().upper()
    
    # Validação básica
    if not ticker1 or not ticker2:
        print("\n❌ Erro: Os tickers não podem estar vazios!")
        return
    
    if ticker1 == ticker2:
        print("\n❌ Erro: Os tickers devem ser diferentes!")
        return
    
    # Sugestões para tickers comuns incorretos
    sugestoes = {
        'BTC-BRL': 'BTC-USD',
        'ETH-BRL': 'ETH-USD',
        'BITCOIN': 'BTC-USD',
        'ETHEREUM': 'ETH-USD',
        'IBOV': '^BVSP',
        'IBOVESPA': '^BVSP',
        'BOVESPA': '^BVSP',
        'BVSP': '^BVSP',
        'SP500': '^GSPC',
        'S&P500': '^GSPC',
        'S&P 500': '^GSPC',
        'DOW': '^DJI',
        'NASDAQ': '^IXIC'
    }
    
    # Alternativas para o Ibovespa caso ^BVSP não funcione
    ibov_alternativas = ['BOVA11.SA', '^BVSP', 'IBOV11.SA']
    
    if ticker1 in sugestoes:
        print(f"\n💡 Sugestão: Use '{sugestoes[ticker1]}' ao invés de '{ticker1}'")
        ticker1 = sugestoes[ticker1]
    if ticker2 in sugestoes:
        print(f"\n💡 Sugestão: Use '{sugestoes[ticker2]}' ao invés de '{ticker2}'")
        ticker2 = sugestoes[ticker2]
    
    # Executar análise escolhida
    if escolha == '1':
        # ANÁLISE SIMPLES - PERÍODO ESPECÍFICO
        executar_analise_simples(ticker1, ticker2, autoria)
    else:
        # ANÁLISE DE JANELAS MÓVEIS
        executar_analise_janelas(ticker1, ticker2, autoria)

def executar_analise_simples(ticker1, ticker2, autoria=""):
    """
    Executa análise simples de período específico
    """
    print("\n" + "="*70)
    print("           ANÁLISE SIMPLES - PERÍODO ESPECÍFICO")
    print("="*70)
    
    # Solicitar datas
    print("\n📅 Digite o período de análise (formato: DD/MM/YYYY)")
    print("   Exemplos de períodos interessantes:")
    print("   • Últimos 2 anos: 29/01/2023 até hoje")
    print("   • Ciclo do Bitcoin: 01/01/2020 até 31/12/2021")
    print("   • Pandemia: 01/01/2020 até 31/12/2020")
    print()
    
    # Loop para obter data inicial válida
    while True:
        data_inicio_str = input("Data inicial (DD/MM/YYYY): ").strip()
        try:
            data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y")
            break
        except ValueError:
            print("❌ Formato inválido! Use DD/MM/YYYY (ex: 01/01/2023)")
    
    # Loop para obter data final válida
    while True:
        data_final_str = input("Data final (DD/MM/YYYY) [Enter para hoje]: ").strip()
        
        if not data_final_str:
            data_fim = datetime.now()
            print(f"   Usando data de hoje: {data_fim.strftime('%d/%m/%Y')}")
            break
        
        try:
            data_fim = datetime.strptime(data_final_str, "%d/%m/%Y")
            
            if data_fim <= data_inicio:
                print("❌ A data final deve ser posterior à data inicial!")
                continue
            
            break
        except ValueError:
            print("❌ Formato inválido! Use DD/MM/YYYY (ex: 31/12/2023)")
    
    # Validar período mínimo
    dias_periodo = (data_fim - data_inicio).days
    if dias_periodo < 7:
        print("\n⚠️  Atenção: Período muito curto (menos de 7 dias)")
        continuar = input("Deseja continuar mesmo assim? (s/n): ").strip().lower()
        if continuar != 's':
            print("Análise cancelada.")
            return
    
    print(f"\n{'='*70}")
    print(f"🚀 Iniciando análise comparativa...")
    print(f"{'='*70}")
    print(f"Ativos: {ticker1} vs {ticker2}")
    print(f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    print(f"Duração: {dias_periodo} dias\n")
    
    try:
        plotar_comparacao(ticker1, ticker2, data_inicio, data_fim, autoria)
    except Exception as e:
        print(f"\n❌ Erro ao processar dados: {str(e)}")
        print("\n💡 Dicas:")
        print("   • Verifique se os tickers estão corretos")
        print("   • Para criptomoedas, use: BTC-USD, ETH-USD")
        print("   • Para ações brasileiras, use: PETR4.SA, VALE3.SA")
        print("   • Verifique sua conexão com a internet")
        print("   • Alguns ativos podem ter dados limitados")
        print("   • Verifique se há dados disponíveis para o período escolhido")

def executar_analise_janelas(ticker1, ticker2, autoria=""):
    """
    Executa análise de janelas móveis
    """
    print("\n" + "="*70)
    print("        ANÁLISE DE JANELAS MÓVEIS - PERÍODOS DE SUPERAÇÃO")
    print("="*70)
    
    print("\n📅 Configure os parâmetros da análise:")
    print("\n   Esta análise identifica em quais janelas de X meses,")
    print("   ao longo de Y anos, um ativo superou o outro.")
    print()
    print("   Exemplo: 'Nos últimos 10 anos, em quais janelas de 24 meses")
    print("            o Bitcoin superou o Ibovespa?'")
    print()
    
    # Solicitar período total
    while True:
        try:
            periodo_anos = int(input("Período total de análise (em ANOS): ").strip())
            if periodo_anos < 1 or periodo_anos > 30:
                print("❌ Digite um valor entre 1 e 30 anos")
                continue
            break
        except ValueError:
            print("❌ Digite um número válido")
    
    # Solicitar tamanho da janela
    while True:
        try:
            janela_meses = int(input("Tamanho da janela (em MESES): ").strip())
            if janela_meses < 1 or janela_meses > (periodo_anos * 12):
                print(f"❌ Digite um valor entre 1 e {periodo_anos * 12} meses")
                continue
            break
        except ValueError:
            print("❌ Digite um número válido")
    
    # Validação
    if janela_meses >= (periodo_anos * 12):
        print("\n⚠️  A janela é muito grande para o período escolhido!")
        print(f"   Sugestão: Use janela menor que {periodo_anos * 12} meses")
        continuar = input("Deseja continuar mesmo assim? (s/n): ").strip().lower()
        if continuar != 's':
            print("Análise cancelada.")
            return
    
    print(f"\n{'='*70}")
    print(f"🚀 Iniciando análise de janelas móveis...")
    print(f"{'='*70}")
    print(f"Ativos: {ticker1} vs {ticker2}")
    print(f"Período: {periodo_anos} anos")
    print(f"Janela: {janela_meses} meses\n")
    
    try:
        plotar_analise_janelas(ticker1, ticker2, periodo_anos, janela_meses, autoria)
    except Exception as e:
        print(f"\n❌ Erro ao processar dados: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n💡 Dicas:")
        print("   • Verifique se os tickers estão corretos")
        print("   • Para criptomoedas, use: BTC-USD, ETH-USD")
        print("   • Para ações brasileiras, use: PETR4.SA, VALE3.SA")
        print("   • Verifique sua conexão com a internet")
        print("   • Tente usar um período ou janela diferentes")
        print("   • Alguns ativos podem não ter dados suficientes")

if __name__ == "__main__":
    main()