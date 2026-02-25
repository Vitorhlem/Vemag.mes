export interface SapOperationMap {
  code: string;           // Código da Operação (Ex: 701)
  description: string;    // Descrição da Operação (Ex: PPCP)
  resourceCode: string;   // Código do Recurso (Ex: 7.01.01)
  resourceName: string;   // Descrição do Recurso (Ex: Analista de PPCP)
}

/**
 * Mapa Global de Operações e seus respectivos Recursos vinculados
 */
export const SAP_OPERATIONS_MAP: Record<string, SapOperationMap> = {
  '101': { code: '101', description: 'ENGENHARIA INDUSTRIAL', resourceCode: '1.01.01', resourceName: 'Técnico de Processos' },
  '201': { code: '201', description: 'DOCUMENTACAO TECNICA DA QUALIDADE', resourceCode: '2.01.01', resourceName: 'Técnico de Solda' },
  '202': { code: '202', description: 'INSPECAO DIMENSIONAL', resourceCode: '2.02.01', resourceName: 'Inspetor Dimensional' },
  '203': { code: '203', description: 'INSPECAO DE SOLDA', resourceCode: '2.03.01', resourceName: 'Inspetor de Solda' },
  '204': { code: '204', description: 'INSPECAO EVS', resourceCode: '2.04.01', resourceName: 'Inspetor EVS' },
  '205': { code: '205', description: 'INSPECAO LP', resourceCode: '2.05.01', resourceName: 'Inspetor LP' },
  '206': { code: '206', description: 'INSPECAO PM', resourceCode: '2.06.01', resourceName: 'Inspetor PM' },
  '207': { code: '207', description: 'INSPECAO RX', resourceCode: '2.07.01', resourceName: 'Inspetor RX' },
  '208': { code: '208', description: 'INSPECAO US', resourceCode: '2.08.01', resourceName: 'Inspetor US' },
  '209': { code: '209', description: 'INSPECAO TESTE DE ESTANQUEIDADE', resourceCode: '2.09.01', resourceName: 'Inspetor de Qualidade' },
  '210': { code: '210', description: 'INSPECAO TESTE HIDROSTATICO', resourceCode: '2.10.01', resourceName: 'Inspetor de Qualidade' },
  '211': { code: '211', description: 'INSPECAO TESTE ESPECIAL', resourceCode: '2.11.01', resourceName: 'Inspetor de Qualidade' },
  '212': { code: '212', description: 'INSPECAO DE PINTURA', resourceCode: '2.12.01', resourceName: 'Inspetor de Pintura' },
  '213': { code: '213', description: 'SUPORTE TECNICO DA QUALIDADE', resourceCode: '2.13.01', resourceName: 'Inspetor de Qualidade' },
  '301': { code: '301', description: 'OXICORTE', resourceCode: '3.01.01', resourceName: 'Operador de Banco de Corte CNC' },
  '302': { code: '302', description: 'PREPARACAO/CONFORMACAO', resourceCode: '3.02.01', resourceName: 'Caldeireiro' },
  '303': { code: '303', description: 'MONTAGEM DE CALDEIRARIA', resourceCode: '3.03.01', resourceName: 'Caldeireiro' },
  '304': { code: '304', description: 'SOLDAGEM', resourceCode: '3.04.01', resourceName: 'Soldador' },
  '305': { code: '305', description: 'REBARBACAO DE CALDEIRARIA', resourceCode: '3.05.01', resourceName: 'Ajudante Geral de Caldeiraria' },
  '401': { code: '401', description: 'FRESADORA', resourceCode: '4.01.01', resourceName: 'Fresador' },
  '402': { code: '402', description: 'FRESADORA PORTAL CNC I', resourceCode: '4.02.01', resourceName: 'Fresador CNC' },
  '403': { code: '403', description: 'MANDRILHADORA', resourceCode: '4.03.01', resourceName: 'Mandrilhador' },
  '404': { code: '404', description: 'MANDRILHADORA CNC', resourceCode: '4.04.01', resourceName: 'Mandrilhador CNC' },
  '405': { code: '405', description: 'MANDRILHADORA FLOOR TYPE CNC', resourceCode: '4.05.01', resourceName: 'Mandrilhador CNC' },
  '406': { code: '406', description: 'RADIAL P', resourceCode: '4.06.01', resourceName: 'Operador de Radial P' },
  '407': { code: '407', description: 'RADIAL M', resourceCode: '4.07.01', resourceName: 'Operador de Radial M' },
  '408': { code: '408', description: 'RADIAL G', resourceCode: '4.08.01', resourceName: 'Furadeira Radial RFH100 - CESPEL' },
  '409': { code: '409', description: 'SERRA DE FITA', resourceCode: '4.09.01', resourceName: 'Ajudante Geral de Usinagem' },
  '410': { code: '410', description: 'TRACAGEM', resourceCode: '4.10.01', resourceName: 'Traçador' },
  '411': { code: '411', description: 'TORNO HORIZONTAL P', resourceCode: '4.11.01', resourceName: 'Torneiro P' },
  '412': { code: '412', description: 'TORNO HORIZONTAL M', resourceCode: '4.12.01', resourceName: 'Torneiro M' },
  '413': { code: '413', description: 'TORNO HORIZONTAL G', resourceCode: '4.13.01', resourceName: 'Torno Horizontal CNC Centur 80A - ROMI' },
  '414': { code: '414', description: 'TORNO HORIZONTAL CNC P', resourceCode: '4.14.01', resourceName: 'Torneiro CNC P' },
  '415': { code: '415', description: 'TORNO HORIZONTAL CNC M', resourceCode: '4.15.01', resourceName: 'Torneiro CNC M' },
  '416': { code: '416', description: 'TORNO HORIZONTAL CNC G', resourceCode: '4.16.01', resourceName: 'Torneiro CNC G' },
  '417': { code: '417', description: 'TORNO VERTICAL P', resourceCode: '4.17.01', resourceName: 'Torneiro P' },
  '418': { code: '418', description: 'TORNO VERTICAL M', resourceCode: '4.18.01', resourceName: 'Torneiro M' },
  '419': { code: '419', description: 'TORNO VERTICAL G', resourceCode: '4.19.01', resourceName: 'Torno Vertical - STANKPORT' },
  '420': { code: '420', description: 'TORNO VERTICAL CNC P', resourceCode: '4.20.01', resourceName: 'Torno Vertical SC14 - TITAN' },
  '421': { code: '421', description: 'TORNO VERTICAL CNC M', resourceCode: '4.21.01', resourceName: 'Torneiro CNC M' },
  '422': { code: '422', description: 'TORNO VERTICAL CNC G', resourceCode: '4.22.01', resourceName: 'Torno Vertical CNC SC33 - TITAN' },
  '423': { code: '423', description: 'REBARBACAO DE USINAGEM', resourceCode: '4.23.01', resourceName: 'Ajudante Geral de Usinagem' },
  '424': { code: '424', description: 'FERRAMENTARIA', resourceCode: '4.24.01', resourceName: 'Técnico de Ferramentas' },
  '425': { code: '425', description: 'FRESADORA PORTAL CNC II', resourceCode: '4.25.01', resourceName: 'Fresador CNC' },
  '501': { code: '501', description: 'JATEAMENTO', resourceCode: '5.01.01', resourceName: 'Jatista' },
  '502': { code: '502', description: 'PINTURA', resourceCode: '5.02.01', resourceName: 'Pintor Industrial' },
  '503': { code: '503', description: 'LIMPEZA/LAVAGEM', resourceCode: '5.03.01', resourceName: 'Ajudante Geral de Pintura' },
  '601': { code: '601', description: 'MONTAGEM MECANICA', resourceCode: '6.01.01', resourceName: 'Montador Mecânico' },
  '701': { code: '701', description: 'PPCP', resourceCode: '7.01.01', resourceName: 'Analista de PPCP' },
  '702': { code: '702', description: 'EXPEDICAO', resourceCode: '7.02.01', resourceName: 'Analista de Expedição' },
  '703': { code: '703', description: 'TERCEIRIZACAO SERVICOS E ATIVIDADES', resourceCode: '7.03.01', resourceName: 'Tercerização Serviços e Atividades' },
};

/**
 * Busca a configuração da Operação pelo Código recebido do SAP (ex: '423')
 */
export function getSapOperationByCode(opCode: string): SapOperationMap | null {
  if (opCode && SAP_OPERATIONS_MAP[opCode]) {
    return SAP_OPERATIONS_MAP[opCode];
  }
  return null;
}

/**
 * Busca qual é a operação dona do recurso logado no tablet
 */
export function findGlobalOpByResource(machineResource: string): SapOperationMap | null {
  if (!machineResource) return null;
  const found = Object.values(SAP_OPERATIONS_MAP).find(op => op.resourceCode === machineResource.trim());
  return found || null;
}

/**
 * FUNÇÃO INTELIGENTE DE ROTEAMENTO
 * Varre as etapas que vieram do SAP e retorna o índice da etapa cuja
 * operação exigida corresponda à máquina que o operador está logado.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function findBestStepIndex(machineResourceCode: string, steps: any[]): number {
  if (!machineResourceCode || !steps || steps.length === 0) return -1;
  const myResource = machineResourceCode.trim();

  const index = steps.findIndex(step => {
    // step.resource agora contém o U_Operacao que veio do SAP (ex: '423')
    const opCode = String(step.resource || '').trim();
    const config = SAP_OPERATIONS_MAP[opCode];

    if (config) {
      // Confirma se o Recurso exigido pelo SAP (ex: 4.23.01) bate com o do Tablet
      const match = myResource.startsWith(config.resourceCode) || config.resourceCode.startsWith(myResource);
      return match && step.status !== 'COMPLETED';
    }
    return false;
  });

  return index;
}