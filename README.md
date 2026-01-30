# Comparador de Ativos Financeiros

## 📊 Descrição

Este programa Python permite comparar o desempenho de dois ativos financeiros ao longo do tempo, destacando visualmente os períodos em que um ativo supera o outro.

## 🚀 Funcionalidades

### 📊 Dois tipos de análise disponíveis:

#### 1️⃣ **Análise Simples - Período Específico**
- Compara dois ativos entre duas datas específicas
- **Conversão automática USD→BRL**: Ativos em USD são automaticamente convertidos para BRL
- **Normalização em 0%**: Ambos os ativos começam em 0% de variação
- **Destaque visual**: Períodos em que o ativo 2 supera o ativo 1 são marcados
- **Contagem de dias**: Cada período destacado mostra quantos dias durou
- **Estatísticas resumidas**: Total de dias de superação exibido no gráfico

#### 2️⃣ **Análise de Janelas Móveis - Períodos de Superação** ✨ NOVO!
- Identifica **em quais janelas de X meses** um ativo superou o outro
- Analisa um **período total de Y anos**
- Mostra **retornos de janelas móveis** ao longo do tempo
- Exibe **timeline visual** dos períodos de superação
- Calcula **estatísticas detalhadas** (duração média, diferença de retorno, etc.)

**Exemplo de uso**: "Nos últimos 10 anos, o Ibovespa teve melhor desempenho que o S&P 500 em janelas de 24 meses nos períodos X, Y e Z"

## 📦 Instalação

### Opção 1: Usando requirements.txt
```bash
pip install -r requirements.txt
```

### Opção 2: Usando o script de instalação (Recomendado)

**Linux/Mac:**
```bash
chmod +x instalar.sh
./instalar.sh
```

**Windows:**
```cmd
instalar.bat
```

### Opção 3: Instalação manual
```bash
pip install --upgrade pip
pip install --upgrade yfinance
pip install matplotlib pandas numpy
```

## ⚠️ Solução de Problemas

### Erro de importação do yfinance
Se você receber erros relacionados a `typing.NamedTuple` ou conflitos de dependências:

1. **Atualize o pip primeiro:**
   ```bash
   pip install --upgrade pip
   ```

2. **Instale yfinance separadamente:**
   ```bash
   pip install --upgrade yfinance
   ```

3. **Se o problema persistir, use um ambiente virtual:**
   ```bash
   # Criar ambiente virtual
   python -m venv venv
   
   # Ativar (Linux/Mac)
   source venv/bin/activate
   
   # Ativar (Windows)
   venv\Scripts\activate
   
   # Instalar dependências
   pip install yfinance matplotlib pandas numpy
   ```

### Erro de conexão
- Verifique sua conexão com a internet
- Se estiver atrás de um firewall corporativo, pode haver bloqueio
- Tente usar uma VPN se o Yahoo Finance estiver bloqueado
- Alguns tickers podem estar indisponíveis no Yahoo Finance
- Tente usar tickers alternativos

### Ticker não encontrado
**Problema comum:** `BTC-BRL` não existe!
- ✅ Use `BTC-USD` para Bitcoin
- ✅ Use `ETH-USD` para Ethereum
- O Yahoo Finance não suporta pares com BRL para criptomoedas

### Versão do Python
- Certifique-se de estar usando Python 3.8 ou superior
- Verifique com: `python --version`

## 💻 Como Usar

### Modo Interativo

Execute o programa:
```bash
python comparacao_ativos.py
```

O programa solicitará:
1. Ticker do primeiro ativo
2. Ticker do segundo ativo
3. Período em anos (padrão: 2 anos)

### Exemplos de Tickers

**Ações Brasileiras:**
- `PETR4.SA` - Petrobras
- `VALE3.SA` - Vale
- `ITUB4.SA` - Itaú
- `BBDC4.SA` - Bradesco
- `MGLU3.SA` - Magazine Luiza

**Ações Americanas:**
- `AAPL` - Apple
- `GOOGL` - Google
- `MSFT` - Microsoft
- `TSLA` - Tesla
- `NVDA` - NVIDIA

**ETFs:**
- `SPY` - S&P 500
- `QQQ` - Nasdaq 100
- `IVV` - S&P 500 iShares
- `BOVA11.SA` - ETF Ibovespa

**Criptomoedas:**
- `BTC-USD` - Bitcoin (✨ convertido automaticamente para BRL)
- `ETH-USD` - Ethereum (✨ convertido automaticamente para BRL)

**Índices:**
- `^BVSP` - Ibovespa
- `^GSPC` - S&P 500
- `^DJI` - Dow Jones

### ⚠️ IMPORTANTE: Tickers de Criptomoedas

O Yahoo Finance **NÃO** suporta pares BTC-BRL ou ETH-BRL diretamente. 

**✨ NOVIDADE**: O programa agora **converte automaticamente** ativos em USD para BRL!

- ✅ Use `BTC-USD` → será **automaticamente convertido para BRL** usando taxas históricas
- ✅ Use `ETH-USD` → será **automaticamente convertido para BRL** usando taxas históricas
- ❌ ~~`BTC-BRL`~~ (não existe no Yahoo Finance)
- ❌ ~~`ETH-BRL`~~ (não existe no Yahoo Finance)

**Exemplo perfeito para Bitcoin vs Ibovespa:**
```
Ativo 1: BTC-USD  (será convertido para BRL automaticamente)
Ativo 2: ^BVSP    (Ibovespa já está em BRL)
```

### Exemplo de Uso - Análise Simples

```
========================================================
COMPARADOR DE ATIVOS FINANCEIROS
========================================================

📊 ESCOLHA O TIPO DE ANÁLISE:

  1️⃣  Análise Simples - Comparação de período específico
  2️⃣  Análise de Janelas Móveis - Identificar períodos de superação

Digite sua escolha (1 ou 2): 1

Digite o ticker do ATIVO 1: BTC-USD
Digite o ticker do ATIVO 2: ^BVSP

📅 Digite o período de análise (formato: DD/MM/YYYY)
Data inicial (DD/MM/YYYY): 01/01/2023
Data final (DD/MM/YYYY) [Enter para hoje]: ↵
```

### Exemplo de Uso - Análise de Janelas Móveis ✨

```
Digite sua escolha (1 ou 2): 2

Digite o ticker do ATIVO 1: ^BVSP
Digite o ticker do ATIVO 2: ^GSPC

📅 Configure os parâmetros da análise:
Período total de análise (em ANOS): 10
Tamanho da janela (em MESES): 24

🔍 Resultado: "Nos últimos 10 anos, em quais janelas de 24 meses
             o Ibovespa superou o S&P 500?"
```

## 📈 Interpretação dos Gráficos

### Análise Simples:
- **Linhas coloridas**: Representam a variação percentual de cada ativo
- **Áreas sombreadas em verde**: Períodos em que o ATIVO 2 teve melhor desempenho
- **Números sobre as áreas**: Duração em dias de cada período de superação
- **Caixa amarela**: Total acumulado de dias em que o ativo 2 superou o ativo 1

### Análise de Janelas Móveis: ✨
- **Gráfico superior**: Mostra os retornos de cada ativo em janelas móveis de X meses
- **Áreas sombreadas**: Indicam janelas onde o ativo 2 superou o ativo 1
- **Gráfico inferior (Timeline)**: Visualização temporal dos períodos de superação
- **Anotações**: Mostram duração (em meses) e diferença de retorno (pp = pontos percentuais)

## 🎯 Saídas

O programa gera:

### Para Análise Simples:
1. **Gráfico interativo** na tela
2. **Arquivo PNG** salvo com alta resolução (300 dpi)
3. **Estatísticas no console** com resumo da análise
4. **Nome do arquivo**: `comparacao_[ATIVO1]_vs_[ATIVO2].png`

### Para Análise de Janelas Móveis: ✨
1. **Gráfico duplo interativo** (retornos + timeline)
2. **Arquivo PNG** salvo com alta resolução (300 dpi)
3. **Relatório detalhado** com cada janela de superação
4. **Estatísticas** de duração e diferença de retorno
5. **Nome do arquivo**: `analise_janelas_[ATIVO1]_vs_[ATIVO2]_[X]m.png`

## 📝 Observações

- Os dados são obtidos do Yahoo Finance via biblioteca `yfinance`
- A variação percentual é calculada em relação ao primeiro dia do período
- Períodos de superação são identificados quando ativo 2 > ativo 1
- O gráfico é salvo automaticamente na pasta de saída

## 🛠️ Personalização

Você pode modificar o código para:
- Alterar cores das linhas e sombreamento
- Ajustar o estilo do gráfico
- Adicionar mais métricas (volatilidade, Sharpe ratio, etc.)
- Comparar mais de 2 ativos simultaneamente

## ⚠️ Requisitos

- Python 3.7 ou superior
- Conexão com internet para baixar dados
- Tickers válidos no Yahoo Finance
