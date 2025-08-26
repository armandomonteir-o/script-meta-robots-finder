# 🤖 Meta Robots Finder

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Um script Python de alto desempenho para automatizar o processo de encontrar a tag meta robots numa grande lista de URLs.**

---

_[Leia em Inglês / Read in English](README.md)_

---

## O Problema

No mundo do SEO técnico, garantir que centenas de páginas de um cliente sejam corretamente indexadas pelos motores de busca é uma tarefa crítica, mas muitas vezes tediosa. Encontrei exatamente este desafio: um grande número de URLs não possuía a tag essencial `<meta name="robots">`, o que colocava em risco a sua visibilidade no Google.

A solução manual era desanimadora. Envolvia um ciclo repetitivo para cada URL:

1.  Abrir a página num navegador.
2.  Pressionar `Ctrl+U` para ver o código-fonte.
3.  Procurar no HTML por uma única linha de código em falta.

O que começou como um simples script para automatizar uma tarefa chata rapidamente evoluiu para um projeto completo, uma oportunidade não só para resolver um problema do mundo real, mas para o fazer de forma eficiente e elegante, aplicando conceitos avançados de programação.

## A Solução

O **Meta Robots Finder** é uma ferramenta de linha de comando que automatiza a tarefa tediosa de verificar a presença da tag `<meta name="robots">` em centenas ou milhares de URLs.

O script lê uma lista de URLs de um arquivo Excel, verifica cada um de forma concorrente em busca da tag e gera uma planilha profissionalmente formatada e limpa com os resultados, indicando `TRUE`, `FALSE` ou `Erro` para cada URL.

## Principais Funcionalidades

A arquitetura desta ferramenta utiliza um conjunto de bibliotecas poderosas para alcançar um alto grau de desempenho e robustez.

- **Arquitetura Orientada a Objetos:** Toda a aplicação é construída usando uma estrutura POO, separando as responsabilidades em classes como `SpreadsheetManager` e `Crawler`.
- **Concorrência de Alto Desempenho:** Utiliza um `ThreadPoolExecutor` para verificar múltiplos URLs em paralelo, reduzindo drasticamente o tempo de execução.
- **Relatórios Profissionais e Elegantes:** Usa o `XlsxWriter` para gerar relatórios Excel limpos e profissionais com formatação condicional e larguras de coluna personalizadas.
- **Interface de Linha de Comando (CLI) Intuitiva:** Oferece uma interface amigável com uma barra de progresso em tempo real do `tqdm`.
- **Tratamento de Erros Robusto:** Implementa um sistema de logging abrangente e blocos `try...except` para gerir erros de rede de forma elegante.
- **Rede Eficiente:** Utiliza um objeto `requests.Session` para reutilizar conexões TCP, melhorando o desempenho da rede.

## Demonstração

Aqui está um exemplo do relatório final gerado pelo script:

![Meta Robots Finder Demo](https://imgur.com/a/5V4FsFB)
_(Nota: Você precisará carregar sua captura de tela para um site como o Imgur e substituir o URL acima)_

## Instalação e Uso

Siga estes passos para executar o script na sua máquina local.

1.  **Clone o repositório:**

    ```bash
    git clone [https://github.com/armandomonteir-o/script-meta-robots-finder](https://github.com/armandomonteir-o/script-meta-robots-finder)
    cd script-meta-robots-finder
    ```

2.  **Crie um ambiente virtual (Recomendado):**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # No Windows, use: .venv\Scripts\activate
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o script:**
    Forneça o caminho para a sua planilha e o nome da coluna que contém os URLs.
    ```bash
    python src/main.py <caminho_para_sua_planilha.xlsx> "<nome_da_coluna>"
    ```
    _Exemplo:_
    ```bash
    python src/main.py minhas_urls.xlsx "URLs do Site"
    ```

## Tecnologias Utilizadas

- **Python:** A linguagem principal para toda a aplicação.
- **Requests:** Para realizar requisições HTTP robustas e eficientes.
- **Beautiful Soup:** Para fazer o parsing do HTML e encontrar a meta tag alvo.
- **Pandas:** Para estruturar os dados e criar o DataFrame.
- **XlsxWriter:** Responsável pela criação de relatórios Excel profissionais.
- **Tqdm:** Para fornecer uma barra de progresso em tempo real na CLI.

## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Contribuidor

Um projeto idealizado e desenvolvido por Armando Monteiro.

<a href="https://github.com/armandomonteir-o">
  <img src="https://avatars.githubusercontent.com/u/141039211?v=4" width="75" height="75">
</a>

---
