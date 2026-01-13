import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { Notify } from 'quasar';

const PART_IMAGE_URL = '/a.jpg';

export interface OperationStep {
  opCode: string;      
  title: string;       
  description: string; 
  tools: string[];     
  params: string;      
}

export interface ProductionOrder {
  id: string;
  code: string;
  partName: string;
  partImage: string;
  targetQuantity: number;
  producedQuantity: number;
  scrapQuantity: number;
  status: 'PENDING' | 'SETUP' | 'RUNNING' | 'PAUSED' | 'COMPLETED';
  operations: OperationStep[];
  documents: { title: string; type: string; url: string }[];
}

export const useProductionStore = defineStore('production', () => {
  const currentOperator = ref<{ name: string; id: number; avatar: string } | null>(null);
  const activeOrder = ref<ProductionOrder | null>(null);

  const isShiftActive = computed(() => !!currentOperator.value);

  // CORREÇÃO: Removemos o underscore e USAMOS a variável na lógica
  function loginOperator(badgeCode: string) {
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        // Uso da variável para satisfazer o Linter
        const mockId = badgeCode === 'BADGE-123' ? 592 : 888;
        
        currentOperator.value = {
          name: 'Carlos Oliveira',
          id: mockId,
          avatar: ''
        };
        Notify.create({ type: 'positive', message: `Operador Autenticado: ${currentOperator.value.name}` });
        resolve();
      }, 800);
    });
  }

  function logoutOperator() {
    currentOperator.value = null;
    activeOrder.value = null;
  }

  // CORREÇÃO: Removemos o underscore e USAMOS a variável na lógica
  function loadOrderFromQr(qrCode: string) {
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        activeOrder.value = {
          id: '4599',
          // Uso da variável aqui:
          code: qrCode || 'OS-4599/24',
          partName: 'Eixo Pinhão Z18 - Aço SAE 4340 (Temperado)',
          partImage: PART_IMAGE_URL, 
          targetQuantity: 150,
          producedQuantity: 32,
          scrapQuantity: 1,
          status: 'RUNNING',
          
          operations: [
            { opCode: 'OP 10', title: 'PREPARAÇÃO E SETUP', description: 'Fixar peça bruta na castanha dura. Ajustar pressão para 30 Bar. Zerar ferramenta T01 na face da peça (Z0).', tools: ['Chave de Castanha', 'Relógio Comparador'], params: 'N/A' },
            { opCode: 'OP 20', title: 'FACEAMENTO E CENTRO', description: 'Facear a peça para limpar a face (tirar 1.0mm). Fazer furo de centro para contra-ponta.', tools: ['T01 - Faceadora WNMG', 'T08 - Broca de Centro A4'], params: 'S: 1200 RPM | F: 0.15 mm/rev' },
            { opCode: 'OP 30', title: 'DESBASTE EXTERNO (Roughing)', description: 'Usinar perfil externo deixando 0.5mm de sobremetal para acabamento. Atenção à vibração no diâmetro menor.', tools: ['T02 - Desbaste CNMG 1204'], params: 'S: 1800 RPM | F: 0.25 mm/rev | Ap: 2.0mm' },
            { opCode: 'OP 40', title: 'ACABAMENTO (Finishing)', description: 'Dar passe de acabamento em todo o perfil. Garantir tolerância H7 no colo do rolamento (Ø35.00 +0.025/-0).', tools: ['T03 - Acabamento VCMT 1604 (Raio 0.4)'], params: 'S: 2500 RPM | F: 0.08 mm/rev' },
            { opCode: 'OP 50', title: 'CANAIS E ALÍVIOS', description: 'Abrir canal de anel elástico (Largura 1.85mm). Quebrar cantos vivos 0.5x45º.', tools: ['T04 - Bedame 2mm'], params: 'S: 800 RPM | F: 0.05 mm/rev' },
            { opCode: 'OP 60', title: 'ROSCAMENTO M30x1.5', description: 'Executar rosca métrica na ponta do eixo. Verificar com anel PASSA/NÃO-PASSA a cada 10 peças.', tools: ['T05 - Insert Full Profile 1.5ISO', 'Calibrador Anel M30'], params: 'S: 600 RPM | Passes: 8' },
            { opCode: 'OP 70', title: 'INSPEÇÃO FINAL', description: 'Medir rugosidade (Ra < 0.8) e dimensional crítico. Preencher carta de CEP.', tools: ['Rugosímetro', 'Micrômetro Externo 25-50mm'], params: 'Manual' }
          ],
          documents: []
        };
        Notify.create({ type: 'info', icon: 'description', message: `Roteiro ${qrCode} carregado com sucesso.` });
        resolve();
      }, 1500);
    });
  }

  function startProduction() { if (activeOrder.value) activeOrder.value.status = 'RUNNING'; }
  
  function pauseProduction(reason: string) { 
      if (activeOrder.value) {
          activeOrder.value.status = 'PAUSED'; 
          // Uso simples para evitar erro de não usado
          console.log('Parada registrada:', reason); 
      }
  }
  
  function addProduction(qty: number, isScrap = false) {
    if (!activeOrder.value) return;
    if (isScrap) {
        activeOrder.value.scrapQuantity += qty;
    } else {
        activeOrder.value.producedQuantity += qty;
    }
  }

  return {
    currentOperator, activeOrder, isShiftActive,
    loginOperator, logoutOperator, loadOrderFromQr,
    startProduction, pauseProduction, addProduction
  };
});