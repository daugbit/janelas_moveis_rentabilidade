# 💰 Guia de Renda Fixa Brasileira

## 🎯 Como Funciona

O módulo de renda fixa integra dados oficiais do **Banco Central do Brasil** para permitir comparações diretas entre investimentos de renda variável e renda fixa.

## 📊 Ativos Disponíveis

### RF-CDI (Certificado de Depósito Interbancário)
- **Fonte**: Banco Central do Brasil (Série 12 - SGS)
- **Descrição**: Principal taxa de referência do mercado financeiro brasileiro
- **Uso típico**: Base para fundos DI, CDBs que rendem % do CDI
- **Exemplo**: "100% do CDI"

### RF-POUPANCA (Caderneta de Poupança)
- **Fonte**: Calculado com base na SELIC e TR (BCB)
- **Descrição**: Investimento mais popular do Brasil
- **Regras aplicadas**:
  - SELIC > 8,5%: Rendimento = 0,5% a.m. + TR
  - SELIC ≤ 8,5%: Rendimento = 70% da SELIC + TR

## 🔄 Sistema de Cache

### Como Funciona:
1. **Primeira execução**: Baixa dados do BCB e salva localmente
2. **Execuções seguintes**: Usa cache se tiver menos de 7 dias
3. **Atualizações**: Busca apenas dados faltantes (incremental)

### Localização do Cache:
```
./dados_renda_fixa/
  ├── cdi.csv                 # Dados históricos do CDI
  ├── selic_historica.csv     # Taxa SELIC
  ├── tr_historica.csv        # Taxa Referencial
  └── ultima_atualizacao.json # Timestamps
```

## 💡 Exemplos de Uso

### 1. Bitcoin vs CDI
**Pergunta**: "O Bitcoin rendeu mais que o CDI nos últimos 2 anos?"

```
Ativo 1: BTC-USD
Ativo 2: RF-CDI
Período: 2 anos
```

**Resultado esperado**: Gráfico mostrando que BTC tem muito mais volatilidade mas rendimento superior.

### 2. Ação vs Poupança
**Pergunta**: "Investir em Petrobras foi melhor que deixar na poupança?"

```
Ativo 1: PETR4.SA
Ativo 2: RF-POUPANCA
Período: 5 anos
```

**Resultado esperado**: Comparação clara entre renda variável e o investimento mais conservador.

### 3. Ibovespa vs CDI
**Pergunta**: "O índice da bolsa brasileira superou a renda fixa?"

```
Ativo 1: BOVA11.SA
Ativo 2: RF-CDI
Período: 10 anos
```

**Resultado esperado**: Períodos onde bolsa supera renda fixa e vice-versa.

### 4. Análise de Janelas - CDI vs Poupança
**Pergunta**: "Em quais janelas de 12 meses o CDI foi melhor que a poupança?"

```
Tipo: Análise de Janelas Móveis
Ativo 1: RF-POUPANCA
Ativo 2: RF-CDI
Período: 10 anos
Janela: 12 meses
```

## 📈 Interpretação dos Resultados

### Valor Base dos Investimentos:
Todos os cálculos assumem um investimento inicial de **R$ 100.000,00**

**Exemplo de saída:**
```
Valor final (R$ 100k investidos): R$ 128,450.00
Rentabilidade acumulada: 28.45%
```

**Isso significa**: 
- Investindo R$ 100.000 no início do período
- Você teria R$ 128.450 no final
- Ganho de R$ 28.450 (28,45%)

### Comparação Justa:
Como todos os ativos começam com R$ 100k, a comparação é direta:
- Se Ativo A terminou em R$ 150k e Ativo B em R$ 130k
- Ativo A rendeu 50% vs 30% do Ativo B
- Diferença de 20 pontos percentuais

## 🔧 Detalhes Técnicos

### Cálculo do CDI:
```python
# CDI fornece taxa anual
# Converter para taxa diária (252 dias úteis)
taxa_diaria = (1 + taxa_anual/100)^(1/252) - 1

# Acumular ao longo do tempo
valor_final = valor_inicial × ∏(1 + taxa_diária)
```

### Cálculo da Poupança:
```python
# Regra atual (desde maio/2012)
if SELIC > 8.5%:
    rendimento_mensal = 0.5% + TR
else:
    rendimento_mensal = (0.70 × SELIC/12) + TR
```

## ⚠️ Limitações e Considerações

### 1. Impostos NÃO estão incluídos
- **CDI/CDB**: IR de 22,5% a 15% (conforme prazo)
- **Ações**: IR de 15% sobre ganho de capital
- **Poupança**: Isenta de IR

### 2. Taxas de Administração
- Fundos DI têm taxa de administração (não incluída)
- Corretagem de ações não está no cálculo
- Use como comparação de ÍNDICES, não de investimentos líquidos

### 3. Liquidez
- CDI assume liquidez diária (nem todos CDBs têm)
- Poupança tem aniversário mensal
- Ações podem ter dias sem liquidez

### 4. Risco
- Renda fixa (até R$ 250k): Protegida pelo FGC
- Ações: Risco de perda total
- Comparação mostra apenas RETORNO, não RISCO

## 🚀 Próximas Implementações

### Em desenvolvimento:
- ⏳ Tesouro SELIC (LFT)
- ⏳ Tesouro IPCA+ (NTN-B)
- ⏳ Tesouro Prefixado (LTN)
- ⏳ IPCA (para comparação com inflação)

### Planejado:
- 📅 Fundos DI (via índices ANBIMA)
- 📅 CDB com percentuais do CDI (ex: 120% CDI)
- 📅 LCI/LCA estimados

## 📞 Troubleshooting

### Erro: "Módulo de renda fixa não disponível"
**Solução**: Certifique-se que `renda_fixa_br.py` está no mesmo diretório que `comparacao_ativos.py`

### Erro: "Não foi possível obter dados do CDI"
**Causas possíveis**:
1. Sem conexão com internet
2. API do Banco Central fora do ar
3. Período muito antigo (dados limitados)

**Solução**: 
- Verifique conexão
- Tente novamente em alguns minutos
- Use período a partir de 2000

### Cache desatualizado
**Solução**: Delete a pasta `dados_renda_fixa` para forçar atualização completa

### Dados inconsistentes
**Solução**: 
```bash
rm -rf dados_renda_fixa/
python comparacao_ativos.py
```

## 📚 Fontes Oficiais

- **Banco Central do Brasil**: https://www.bcb.gov.br
- **SGS - Sistema Gerenciador de Séries**: https://www3.bcb.gov.br/sgspub
- **API BCB**: https://api.bcb.gov.br
- **Tesouro Direto**: https://www.tesourodireto.com.br

## 💼 Exemplos Práticos de Análise

### Para Investidor Conservador:
```
"Quanto eu perderia deixando na poupança vs CDI?"
→ RF-POUPANCA vs RF-CDI (últimos 5 anos)
```

### Para Investidor Moderado:
```
"Vale a pena arriscar em ações vs segurança do CDI?"
→ BOVA11.SA vs RF-CDI (últimos 10 anos)
```

### Para Investidor Arrojado:
```
"Bitcoin compensa o risco vs renda fixa?"
→ BTC-USD vs RF-CDI (últimos 5 anos)
```

### Para Day Trader:
```
"Em quais janelas de 3 meses a bolsa superou o CDI?"
→ Análise de Janelas: ^BVSP vs RF-CDI (janela 3m, 5 anos)
```