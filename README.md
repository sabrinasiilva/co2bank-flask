# CO2Bank

Carteira inteligente com limite ecológico.

## O problema

Os apps de carbono atuais dependem de digitação manual e só mostram o dano
*depois* da compra. O CO2Bank resolve isso automatizando o cálculo via Open
Finance e agindo *antes* do gasto acontecer.

## O que o CO2Bank faz

- Calcula o CO2 de cada compra no cartão de crédito automaticamente, via dados
  de Open Finance (sem digitação manual).
- Cria um limite ecológico mensal por usuário.
- Usa IA para avisar o usuário *antes* de ele ultrapassar o limite (agir antes
  do dano, não depois).
- Converte CO2 economizado em tokens de desconto com marcas parceiras.

## ODS atendidos

- **ODS 12 — Consumo responsável:** o app dá visibilidade e feedback contínuo
  sobre o impacto de cada compra.
- **ODS 13 — Ação climática:** o alerta preventivo por IA muda o comportamento
  antes da emissão acontecer, não só depois.
- **ODS 17 — Parcerias:** CO2 economizado vira token de desconto em marcas
  parceiras, criando um incentivo econômico compartilhado.

## Referência de produto: Doconomy

O diferencial do Doconomy é calcular o CO2 de cada compra direto na fatura e
bloquear o cartão se o limite ecológico do mês for atingido. O CO2Bank usa essa
mesma lógica de "agir no momento da compra" como norte do produto.

## Metodologia de trabalho

Híbrida: **tradicional** para as regras de negócio sensíveis e dados
financeiros (garante que cálculo de CO2, limite e regras de segurança fiquem
corretos e sem ambiguidade) + **ágil** para prototipagem de telas, testes
rápidos e coleta de feedback em ciclos curtos, sem quebrar as regras já
validadas no núcleo do sistema. A arquitetura em camadas (abaixo) existe
justamente para permitir essa combinação.

## Arquitetura

Camadas / DDD-lite, em vez de MVC — separa a regra de negócio sensível da
camada de interface, para poder iterar rápido na interface sem arriscar o
núcleo:

```
app/
├── domain/          # Entidades e regras de negócio puras (User, Transaction,
│                    # CarbonLimit, Reward, cálculo de CO2, política de limite).
│                    # Não depende de Flask, banco ou API externa.
├── application/      # Casos de uso que orquestram domain + infrastructure
│                    # (processar transação, gerar resumo mensal).
├── infrastructure/   # Integrações externas: Open Finance, persistência
│                    # (SQLAlchemy), IA de alerta.
└── interface/        # Camada HTTP: blueprints Flask, schemas/DTOs.
```

Regra geral: `interface` chama `application`, que chama `domain` e
`infrastructure`. `domain` nunca depende de `infrastructure` nem de `interface`.

## Cálculo de CO2 por categoria — mapeamento de referência (v0)

Não existe uma tabela pública e auditada de fatores de emissão por transação —
a Doconomy licencia o Índice Åland via Mastercard Developer, com dados do S&P
Global/Trucost. O mapeamento abaixo é uma **estimativa ilustrativa para
prototipagem**, construída a partir da metodologia deles (agrupar por MCC —
Merchant Category Code) e de fatores spend-based conhecidos (EEIO/EXIOBASE/
DEFRA). **Não deve ser tratado como dado auditado.**

| Categoria (grupo de MCC) | Exemplos de MCC | Intensidade | kg CO2e / R$100 (ilustrativo) |
|---|---|---|---|
| Combustível/posto | 5541, 5542 | Muito alta | ~25–35 |
| Passagens aéreas | 3000–3350 | Muito alta | ~30–45 |
| Hospedagem/hotel | 7011 | Alta | ~10–15 |
| Restaurante/fast-food | 5812, 5814 | Alta | ~8–12 |
| Supermercado | 5411 | Média-alta | ~6–9 |
| Transporte por app/táxi | 4121 | Média-alta | ~7–10 |
| Moda/vestuário | 5651, 5699 | Média | ~5–8 |
| Eletrônicos | 5732, 5722 | Média | ~4–7 |
| Farmácia/saúde | 5912 | Baixa-média | ~2–4 |
| Assinaturas digitais/streaming | 5815, 5817 | Baixa | ~0.5–1.5 |
| Educação | 8211, 8220 | Baixa | ~1–2 |
| Serviços financeiros/Pix/transferência | 6011 | Muito baixa | ~0.2–0.5 |

**Achado específico do Brasil:** a matriz elétrica brasileira é majoritariamente
hidrelétrica (muito mais limpa que EUA/UE), então categorias "elétrico-
intensivas" (eletrônicos, serviços digitais) devem pesar *menos* que em modelos
americanos/europeus. Em compensação, o perfil de emissões do Brasil é dominado
por agropecuária e uso da terra — então categorias como carne/açougue e
supermercado (proteína animal) devem pesar *mais* do que sugerem os fatores
genéricos internacionais. **Não dá para importar direto uma tabela EEIO
americana/europeia sem recalibrar esses dois pontos.**

**Para produção** (fora do escopo do protótipo): licenciar o Índice Åland via
Mastercard Developer Program, ou construir sobre EPA USEEIO / EXIOBASE / DEFRA
recalibrado — como já fazem o C6 Bank ("Extrato de Carbono") e o Mastercard
Carbon Calculator no Brasil.

Fontes: [Doconomy — Sustainable Consumption Index](https://www.doconomy.com/the-sustainable-consumption-index),
[Doconomy Åland Index — Mastercard Developers](https://developer.mastercard.com/product/doconomy-aland-index),
[C6 Bank — Extrato de Carbono](https://c6bank.com.br/blog/o-que-sao-creditos-de-carbono),
[Mastercard Carbon Calculator](https://www.mastercard.com/br/pt/for-the-world/planet/priceless-planet/carbon-calculator.html),
[Climatiq — Spend-based emissions](https://www.climatiq.io/blog/introduction-spend-based-emissions-calculations),
[Merchant Category Code — Wikipedia](https://en.wikipedia.org/wiki/Merchant_category_code).

## Como rodar localmente

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # Windows (cp no Unix)
python run.py
```

Confirmar que subiu: `GET http://127.0.0.1:5000/health` deve responder
`{"status": "ok"}`.

Rodar os testes:

```bash
pytest
```

## App cliente

O app (Flutter) que consome esta API vive no repositório `Co2Bank-dart`.
