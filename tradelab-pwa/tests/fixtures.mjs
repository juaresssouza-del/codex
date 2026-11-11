// Artificial software fixtures. These are not market tests or trading results.
const ts=t=>Date.parse(`2025-01-06T${t}:00-03:00`);
export function validation(){return {
  versao_motor:'0.3.0',estrategia:'TESTE_SOFTWARE',simbolo:'WIN',intervalo:'5m',moeda:'R$',
  risco:{capital:1000},criterios:{reserva_inicio:'2026-07'},
  metricas_fora_da_amostra:{operacoes:2,resultado_liquido:10,custos_totais:4,resultado_bruto:14,retorno_pct:1,taxa_acerto_pct:50,fator_lucro:2,expectativa:5,drawdown_minimo_pct:2,drawdown_fechamento_pct:1},
  veredito:{aprovado:false,itens:[{texto:'Operações fora da amostra',valor:2,limite:200,passou:false},{texto:'Fator de lucro',valor:2,limite:1.3,passou:true}]},
  operacoes:[{ts_entrada:ts('09:30'),ts_saida:ts('09:40'),pnl:20},{ts_entrada:ts('09:45'),ts_saida:ts('09:55'),pnl:-10}]
};}
export function diary(){return {
  tipo:'diario_simulador_b3',versao_motor:'0.3.0',ambiente:'simulador',moeda:'BRL',reserva_inicio:'2026-07-01T00:00:00-03:00',
  resumo:{operacoes:2,resultado_previsto:4.6,resultado_bruto_executado:6,resultado_liquido:.6,taxas_executadas:5.4,impacto_execucao_brl:4,diferenca_liquido:-4,acerto_liquido_pct:50,fator_lucro:15.3/14.7},
  operacoes:[{id:'TESTE-SOFTWARE-01',contrato:'WIN',lado:'comprado',quantidade:1,entrada:'2025-01-06T09:30:00-03:00',saida:'2025-01-06T09:45:00-03:00',preco_entrada_previsto:100000,preco_saida_previsto:100100,preco_entrada_executado:100005,preco_saida_executado:100095,taxas_previstas:2.7,taxas_executadas:2.7,resultado_previsto:17.3,resultado_bruto_executado:18,resultado_liquido:15.3,diferenca_liquido:-2,impacto_execucao_brl:2,desvio_entrada_ticks:1,desvio_saida_ticks:1,stop:99950,alvo:100100,hipotese:'EXEMPLO ARTIFICIAL',motivo_entrada:'Teste de software',motivo_saida:'Encerramento artificial',origem:'Fixture de software, não é histórico real'},
  {id:'TESTE-SOFTWARE-02',contrato:'WIN',lado:'vendido',quantidade:1,entrada:'2025-01-06T10:00:00-03:00',saida:'2025-01-06T10:10:00-03:00',preco_entrada_previsto:100000,preco_saida_previsto:100050,preco_entrada_executado:99995,preco_saida_executado:100055,taxas_previstas:2.7,taxas_executadas:2.7,resultado_previsto:-12.7,resultado_bruto_executado:-12,resultado_liquido:-14.7,diferenca_liquido:-2,impacto_execucao_brl:2,desvio_entrada_ticks:1,desvio_saida_ticks:1,stop:100100,alvo:null,hipotese:'EXEMPLO ARTIFICIAL',motivo_entrada:'<script>Teste de escape</script>',motivo_saida:'Encerramento artificial',origem:'Fixture de software, não é histórico real'}]
};}
export function quality(){return {
  tipo:'conferencia_dados_b3',versao_motor:'0.3.0',arquivo:'TESTE_ARTIFICIAL.csv',origem_declarada:'Fixture de software',contrato_declarado:'WIN',sha256_arquivo:'a'.repeat(64),reserva_inicio:'2026-07-01T00:00:00-03:00',
  cobertura_observada:{inicio:'2025-01-06T09:00:00-03:00',fim:'2025-01-06T09:10:00-03:00'},qualidade:{candles:3,pregoes:1,duplicatas_removidas:0,pausas:[]},linhas_excluidas_por_data:0,liberado_para_teste_dos_dados:true,erros:[],pausas_conferidas:[]
};}
