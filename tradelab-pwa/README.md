# TradeLab PWA — Pesquisa B3

Painel instalável para computador e celular. Lê os JSONs do motor Python e apresenta
o resumo documentado da pesquisa. Não executa estratégias nem envia ordens.

## Usar no telefone

1. Abra o endereço publicado do TradeLab no Chrome do Android, com sua conta autorizada.
2. Use **Instalar** no cabeçalho. Se a opção nativa ainda não aparecer, abra o menu do
   Chrome → **Adicionar à tela inicial**. Em outros navegadores o nome pode variar.
3. Navegue por **Resumo**, **Testes**, **Diário** e **Dados**.
4. Toque em **Importar JSON** para trazer os relatórios completos da pasta `resultados/`
   do motor. Os arquivos ficam neste navegador; não são enviados ao servidor do painel.

No primeiro acesso já aparece o resumo real da rodada 5R, transcrito do
[`HIPOTESES.md`](../tradelab-motor/HIPOTESES.md), commit de origem
`b1200c4daa4c10d6f4ea8760e896b9019c2e8b41`. São valores arredondados do registro, com
fonte na tela. Os oito resultados continuam reprovados. Não são saldos de conta real,
e o capital de R$ 100 mil identifica uma medição com 1 contrato.

## Arquivos aceitos

| Gerador no motor | Arquivo | O que aparece |
|---|---|---|
| `python -m motor validar ...` | `validacao-*.json` | Métricas fora da amostra, capital, curva após operações encerradas e critérios |
| `python -m motor diario-b3 ...` | `diario.json` | Previsto × executado, taxas, preços, stop, alvo, motivos e origem |
| `python -m motor conferir-b3 ...` | `conferencia-*.json` | SHA-256, origem declarada, cobertura, duplicatas, pausas e bloqueios |

Até 25 MB por arquivo. O exportador antigo de candles para o PWA não é um relatório de
validação e é recusado com uma mensagem explicativa. NaN, Infinity, números ausentes,
inconsistências de totais e vereditos contraditórios também são recusados.

O painel não soma capital nem resultados de medições diferentes. BRL e USDT são
identificados separadamente, sem conversão. A curva usa operações encerradas e é
identificada assim; o drawdown intradiário vem do campo original do relatório. O diário
começa o acumulado em zero, não em um saldo de conta inventado. Taxas e slippage não
são descontados novamente dos preços executados.

## Reserva e privacidade

- A importação bloqueia operações e coberturas a partir de `2026-07`. Uma reserva
  anterior declarada no arquivo também é respeitada; uma posterior não afrouxa a regra.
- Nenhuma hipótese nova foi testada e `criterios.toml` não foi alterado.
- O resumo inicial é um retrato do registro no commit indicado; não se atualiza
  automaticamente ao editar o GitHub. Atualize `dist/project.json` e publique novamente.
- IndexedDB guarda os relatórios por dispositivo. Não há sincronização automática
  entre telefone e computador. Exporte/importe o JSON para transferir uma cópia.
- **Remover** na tela Dados apaga a cópia deste navegador após confirmação. O arquivo
  original não é alterado. Limpar os dados do navegador também remove os registros.
- O service worker prepara os arquivos do aplicativo para uso offline após uma
  primeira abertura bem-sucedida. Não armazena credenciais nem respostas de corretora,
  não intercepta outros domínios e não substitui uma rejeição online de autenticação.

## Desenvolvimento

HTML, CSS e módulos JavaScript, sem dependências de runtime ou build obrigatório.
Node.js 20+ para as verificações; hospedagem HTTPS para instalar e preparar o modo offline.

```sh
cd tradelab-pwa
npm run check
npm test
```

Publique o conteúdo de `dist/` em uma hospedagem estática com HTTPS, preservando os
caminhos relativos. O projeto também contém `.openai/hosting.json` para a publicação
privada feita nesta entrega. Esse arquivo não contém credenciais. O código do GitHub
e a publicação são etapas distintas: alterar o branch não publica sozinho a nova versão.

## Verificação da entrega

- 39 testes passaram: formatos reais do motor, moedas, contas, números ausentes,
  comparações, reserva, arquivos instaláveis e comportamento do cache offline.
- No navegador: importação de três formatos, rejeição da reserva, ficha do diário,
  escape de texto e persistência após recarregar.
- Visual conferido no desktop e em quadros responsivos de 390 e 320 px (área útil
  de 375 e 305 px com a barra de rolagem), sem transbordamento horizontal da página.
- As fixtures de teste são artificiais, identificadas como testes de software e
  ficam em `tests/`, fora dos arquivos publicados de `dist/`.
- Instalação física em um Android não foi executada neste ambiente. Manifesto,
  ícones e service worker foram verificados; a oferta de instalação depende do navegador.

Referência de instalação: [documentação MDN](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable).
