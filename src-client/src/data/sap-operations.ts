// Arquivo: src-client/src/data/sap-operations.ts

export interface SapOperationMap {
  code: string;        // Operação (Ex: 701)
  description: string; // Descrição (Ex: PPCP)
}

// Alterado para Record<string, ...> para suportar chaves "010"
export const SAP_OPERATIONS: Record<string, SapOperationMap> = {
  // --- ROTEIRO PADRÃO ---
  '010': { code: '701', description: 'PPCP' },
  '020': { code: '414', description: 'TORNO HORIZONTAL CNC P' },
  '030': { code: '410', description: 'TRACAGEM' },
  '040': { code: '406', description: 'RADIAL P' },
  '050': { code: '703', description: 'TERCEIRIZACAO SERVICOS E ATIVIDADES' },
  '060': { code: '414', description: 'TORNO HORIZONTAL CNC P' },
  '070': { code: '202', description: 'INSPECAO DIMENSIONAL' },
  '080': { code: '701', description: 'PPCP' },

  // --- POSIÇÃO 999 (LISTA COMPLETA) ---
  '999': { code: '416', description: 'TORNO HORIZONTAL CNC G' },
  '999': { code: '411', description: 'TORNO HORIZONTAL P' },
  '999': { code: '417', description: 'TORNO VERTICAL P' },
  '999': { code: '409', description: 'SERRA DE FITA' },
  '999': { code: '408', description: 'RADIAL G' },
  '999': { code: '407', description: 'RADIAL M' },
  '999': { code: '419', description: 'TORNO VERTICAL G' },
  '999': { code: '423', description: 'REBARBACAO DE USINAGEM' },
  '999': { code: '403', description: 'MANDRILHADORA' },
  '999': { code: '412', description: 'TORNO HORIZONTAL M' },
  '999': { code: '418', description: 'TORNO VERTICAL M' },
  '999': { code: '401', description: 'FRESADORA' },
  '999': { code: '302', description: 'PREPARACAO/CONFORMACAO' },
  '999': { code: '301', description: 'OXICORTE' },
  '999': { code: '503', description: 'LIMPEZA/LAVAGEM' },
  '999': { code: '213', description: 'SUPORTE TECNICO DA QUALIDADE' },
  '999': { code: '212', description: 'INSPECAO DE PINTURA' },
  '999': { code: '303', description: 'MONTAGEM DE CALDEIRARIA' },
  '999': { code: '211', description: 'INSPECAO TESTE ESPECIAL' },
  '999': { code: '502', description: 'PINTURA' },
  '999': { code: '210', description: 'INSPECAO TESTE HIDROSTATICO' },
  '999': { code: '304', description: 'SOLDAGEM' },
  '999': { code: '402', description: 'FRESADORA PORTAL CNC I' },
  '999': { code: '207', description: 'INSPECAO RX' },
  '999': { code: '404', description: 'MANDRILHADORA CNC' },
  '999': { code: '413', description: 'TORNO HORIZONTAL G' },
  '999': { code: '601', description: 'MONTAGEM MECANICA' },
  '999': { code: '305', description: 'REBARBACAO DE CALDEIRARIA' },
  '999': { code: '206', description: 'INSPECAO PM' },
  '999': { code: '425', description: 'FRESADORA PORTAL CNC II' },
  '999': { code: '205', description: 'INSPECAO LP' },
  '999': { code: '204', description: 'INSPECAO EVS' },
  '999': { code: '702', description: 'EXPEDICAO' },
  '999': { code: '203', description: 'INSPECAO DE SOLDA' },
  '999': { code: '201', description: 'DOCUMENTACAO TECNICA DA QUALIDADE' },
  '999': { code: '101', description: 'ENGENHARIA INDUSTRIAL' },
  '999': { code: '208', description: 'INSPECAO US' },
  '999': { code: '424', description: 'FERRAMENTARIA' },
  '999': { code: '501', description: 'JATEAMENTO' },
  '999': { code: '209', description: 'INSPECAO TESTE DE ESTANQUEIDADE' },
  '999': { code: '405', description: 'MANDRILHADORA FLOOR TYPE CNC' },
  '999': { code: '415', description: 'TORNO HORIZONTAL CNC M' },
  '999': { code: '422', description: 'TORNO VERTICAL CNC G' },
  '999': { code: '421', description: 'TORNO VERTICAL CNC M' },
  '999': { code: '420', description: 'TORNO VERTICAL CNC P' }
};

export function getSapOperation(stageSeq: number | string): SapOperationMap {
  // 1. Converte qualquer entrada (10, "10", "010") para o padrão "010"
  const num = parseInt(String(stageSeq), 10);
  
  if (isNaN(num)) return { code: '', description: '' };

  // Arredonda para dezena (Ex: 15 -> 10)
  const cleanSeq = Math.floor(num / 10) * 10;
  
  // Formata com 3 dígitos (Ex: 10 -> "010", 100 -> "100")
  const lookupKey = cleanSeq.toString().padStart(3, '0');

  // Busca pela chave exata "010"
  if (SAP_OPERATIONS[lookupKey]) {
    return SAP_OPERATIONS[lookupKey];
  }

  return { code: '', description: '' };
}