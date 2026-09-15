# CO2Bank

Carteira inteligente com limite ecológico.

## O problema

Os apps de carbono hoje dependem de digitação manual e só mostram o impacto depois da compra. O CO2Bank automatiza o cálculo via Open Finance e avisa o usuário antes do limite ser ultrapassado.

## O que o CO2Bank faz

- Calcula o CO2 de cada compra no cartão automaticamente, usando dados do Open Finance
- Cria um limite ecológico mensal por usuário
- Usa IA para avisar antes de ultrapassar o limite
- Converte CO2 economizado em tokens de desconto com marcas parceiras

## ODS atendidos

- **ODS 12 - Consumo responsável:** dá visibilidade sobre o impacto de cada compra
- **ODS 13 - Ação climática:** o alerta preventivo por IA muda o comportamento antes da emissão acontecer
- **ODS 17 - Parcerias:** CO2 economizado vira desconto em marcas parceiras

## Referência de produto

O Doconomy calcula o CO2 de cada compra direto na fatura e bloqueia o cartão quando o limite ecológico do mês é atingido. O CO2Bank segue essa mesma lógica de agir no momento da compra.

## Metodologia

A metodologia é híbrida: usamos o modelo **tradicional** para as regras de negócio e dados financeiros, garantindo que o cálculo de CO2 e as regras de segurança fiquem corretos. E **ágil** para prototipagem de telas e coleta de feedback rápido, sem mexer no núcleo já validado.

## Arquitetura

Usamos uma arquitetura em camadas (DDD-lite), separando a regra de negócio da interface para poder iterar rápido sem arriscar o núcleo:

```
app/
├── domain/          # Entidades e regras de negócio puras (User, Transaction,
│                    # CarbonLimit, Reward, cálculo de CO2, política de limite).
│                    # Não depende de Flask, banco ou API externa.
├── application/     # Casos de uso que orquestram domain + infrastructure
│                    # (processar transação, gerar resumo mensal).
├── infrastructure/  # Integrações externas: Open Finance, persistência
│                    # (SQLAlchemy), IA de alerta.
└── interface/       # Camada HTTP: blueprints Flask, schemas/DTOs.
```

A regra geral é: `interface` chama `application`, que chama `domain` e `infrastructure`. O `domain` nunca depende de `infrastructure` nem de `interface`.

## Cálculo de CO2 por categoria

Não existe uma tabela pública e auditada de fatores de emissão por transação. A Doconomy licencia o Índice Åland via Mastercard Developer, com dados do S&P Global/Trucost. O mapeamento abaixo é uma estimativa ilustrativa para prototipagem, baseada na metodologia deles (agrupamento por MCC) e fatores spend-based conhecidos (EEIO/EXIOBASE/DEFRA). Não deve ser tratado como dado auditado.

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

O Brasil tem uma matriz elétrica majoritariamente hidrelétrica, muito mais limpa que EUA e UE. Por isso, categorias como eletrônicos e serviços digitais pesam menos aqui do que em modelos internacionais. Por outro lado, o perfil de emissões brasileiro é dominado por agropecuária, então categorias como carne e supermercado (proteína animal) pesam mais do que os fatores genéricos sugerem.

Para produção (fora do escopo do protótipo): licenciar o Índice Åland via Mastercard Developer Program, ou usar EPA USEEIO / EXIOBASE / DEFRA recalibrado, como fazem o C6 Bank e o Mastercard Carbon Calculator no Brasil.

Fontes: [Doconomy - Sustainable Consumption Index](https://www.doconomy.com/the-sustainable-consumption-index),
[Doconomy Åland Index - Mastercard Developers](https://developer.mastercard.com/product/doconomy-aland-index),
[C6 Bank - Extrato de Carbono](https://c6bank.com.br/blog/o-que-sao-creditos-de-carbono),
[Mastercard Carbon Calculator](https://www.mastercard.com/br/pt/for-the-world/planet/priceless-planet/carbon-calculator.html),
[Climatiq - Spend-based emissions](https://www.climatiq.io/blog/introduction-spend-based-emissions-calculations),
[Merchant Category Code - Wikipedia](https://en.wikipedia.org/wiki/Merchant_category_code).

## Como rodar localmente

### Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- Python 3.10 ou superior ([baixar aqui](https://www.python.org/downloads/))
- pip (já vem junto com o Python)
- Git

Para checar se o Python já está instalado:

```bash
python --version
```

### Instalação

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
copy .env.example .env          # Windows
# cp .env.example .env          # Linux/macOS
```

Depois de copiar o `.env`, você pode editar o arquivo para trocar a `SECRET_KEY` ou o caminho do banco, se quiser.

### Subir o servidor

```bash
python run.py
```

Para confirmar que subiu certinho, acesse `http://127.0.0.1:5000/health` no navegador ou pelo terminal. A resposta deve ser `{"status": "ok"}`.

### Rodar os testes

```bash
pytest
```

## Acessar o backend pelo celular (Android)

Para testar o app no celular enquanto o backend roda no PC, você pode usar o `adb reverse`. Ele mapeia a porta do servidor para o celular via cabo USB, sem precisar de IP fixo ou colocar os dois na mesma rede Wi-Fi.

Antes de começar:
- Ative a Depuração USB no celular (Configurações > Opções do desenvolvedor > Depuração USB)
- Conecte o celular por USB e autorize quando aparecer a pergunta no celular

Com o backend rodando, execute no terminal do PC:

```bash
adb reverse tcp:5000 tcp:5000
```

Pronto. A partir daí, `http://localhost:5000` dentro do celular vai apontar direto para o servidor na sua máquina. Para confirmar:

```bash
adb shell curl http://localhost:5000/health
# deve retornar: {"status": "ok"}
```

Se o celular não aparecer quando você rodar `adb devices`, tente desconectar e reconectar o cabo. Use um cabo que suporte dados, não apenas carga.

## App cliente

O app mobile que consome esta API vive no repositório `Co2Bank-dart`.
