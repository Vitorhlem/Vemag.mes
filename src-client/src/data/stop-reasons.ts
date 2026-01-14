export interface StopReason {
  category: string;
  label: string;
  requiresMaintenance: boolean; // Nova propriedade controladora
}

export const STOP_REASONS: StopReason[] = [
  // --- MECÂNICA (Geralmente requer manutenção) ---
  { category: 'Mecânica', label: 'Quebra de Ferramenta', requiresMaintenance: true },
  { category: 'Mecânica', label: 'Vazamento de Óleo Hidráulico', requiresMaintenance: true },
  { category: 'Mecânica', label: 'Aquecimento do Eixo/Mancal', requiresMaintenance: true },
  { category: 'Mecânica', label: 'Correia Estourada', requiresMaintenance: true },
  { category: 'Mecânica', label: 'Falha no Sistema Hidráulico', requiresMaintenance: true },
  { category: 'Mecânica', label: 'Vibração/Ruído Excessivo', requiresMaintenance: true },
  { category: 'Mecânica', label: 'Problema na Fixação da Peça', requiresMaintenance: true },
  { category: 'Mecânica', label: 'Desalinhamento de Eixos', requiresMaintenance: true },
  { category: 'Mecânica', label: 'Travamento de Guias', requiresMaintenance: true },
  { category: 'Mecânica', label: 'Proteção/Porta Travada', requiresMaintenance: true },
  { category: 'Mecânica', label: 'Falha na Lubrificação Automática', requiresMaintenance: true },

  // --- ELÉTRICA / ELETRÔNICA (Geralmente requer manutenção) ---
  { category: 'Elétrica', label: 'Queda de Energia Geral', requiresMaintenance: false }, // Isso é externo, não quebra da máquina
  { category: 'Elétrica', label: 'Erro/Falha no Inversor', requiresMaintenance: true },
  { category: 'Elétrica', label: 'Sensor Sujo ou Com Defeito', requiresMaintenance: true },
  { category: 'Elétrica', label: 'Curto Circuito Identificado', requiresMaintenance: true },
  { category: 'Elétrica', label: 'Motor Queimado/Travado', requiresMaintenance: true },
  { category: 'Elétrica', label: 'Painel/HMI Apagou', requiresMaintenance: true },
  { category: 'Elétrica', label: 'Fusível Queimado', requiresMaintenance: true },
  { category: 'Elétrica', label: 'Cabo Rompido/Desconectado', requiresMaintenance: true },
  { category: 'Elétrica', label: 'Falha de Comunicação PLC', requiresMaintenance: true },
  { category: 'Elétrica', label: 'Botão de Emergência Acionado', requiresMaintenance: false }, // Pode ser operacional
  { category: 'Elétrica', label: 'Barreira de Luz Atuada (Erro)', requiresMaintenance: true },

  // --- OPERACIONAL (Apenas Pausa) ---
  { category: 'Operacional', label: 'Troca de Turno', requiresMaintenance: false },
  { category: 'Operacional', label: 'Refeição / Intervalo', requiresMaintenance: false },
  { category: 'Operacional', label: 'Reunião Diária (DDS)', requiresMaintenance: false },
  { category: 'Operacional', label: 'Ginástica Laboral', requiresMaintenance: false },
  { category: 'Operacional', label: 'Treinamento Operacional', requiresMaintenance: false },
  { category: 'Operacional', label: 'Ausência do Operador', requiresMaintenance: false },
  { category: 'Operacional', label: 'Erro Operacional / Ajuste', requiresMaintenance: false },
  { category: 'Operacional', label: 'Limpeza do Posto (5S)', requiresMaintenance: false },
  { category: 'Operacional', label: 'Preenchimento de Documentos', requiresMaintenance: false },
  { category: 'Operacional', label: 'Necessidades Pessoais (Banheiro)', requiresMaintenance: false },

  // --- LOGÍSTICA (Apenas Pausa) ---
  { category: 'Logística', label: 'Falta de Matéria Prima', requiresMaintenance: false },
  { category: 'Logística', label: 'Falta de Embalagem/Caixa', requiresMaintenance: false },
  { category: 'Logística', label: 'Aguardando Empilhadeira', requiresMaintenance: false },
  { category: 'Logística', label: 'Expedição/Pulmão Lotado', requiresMaintenance: false },
  { category: 'Logística', label: 'Peça não chegou do processo anterior', requiresMaintenance: false },
  { category: 'Logística', label: 'Parada para Retirada de Cavacos', requiresMaintenance: false },
  { category: 'Logística', label: 'Falta de Pallet', requiresMaintenance: false },
  
  // --- QUALIDADE (Apenas Pausa ou Bloqueio, mas não Manutenção de Maquina) ---
  { category: 'Qualidade', label: 'Aguardando Aprovação (Setup)', requiresMaintenance: false },
  { category: 'Qualidade', label: 'Medição de Peça (Controle)', requiresMaintenance: false },
  { category: 'Qualidade', label: 'Segregação de Peça Refugada', requiresMaintenance: false },
  { category: 'Qualidade', label: 'Ajuste Dimensional', requiresMaintenance: false },
  { category: 'Qualidade', label: 'Aguardando Teste de Laboratório', requiresMaintenance: false },
  { category: 'Qualidade', label: 'Instrumento de Medição Quebrado', requiresMaintenance: false }, // Requer troca do instrumento, não da máquina

  // --- SETUP (Estado Específico) ---
  { category: 'Setup', label: 'Troca de Modelo (Setup)', requiresMaintenance: false },
  { category: 'Setup', label: 'Ajuste Fino de Máquina', requiresMaintenance: false },
  { category: 'Setup', label: 'Troca de Ferramental', requiresMaintenance: false },
  { category: 'Setup', label: 'Aquecimento da Máquina (Warm-up)', requiresMaintenance: false },
  { category: 'Setup', label: 'Carregamento de Programa CNC', requiresMaintenance: false },
  
  // --- OUTROS ---
  { category: 'Outros', label: 'Teste de Engenharia / Processo', requiresMaintenance: false },
  { category: 'Outros', label: 'Falta de Ar Comprimido (Rede)', requiresMaintenance: false }, // Problema externo
  { category: 'Outros', label: 'Goteira / Infraestrutura Predial', requiresMaintenance: false }
];