import { api } from 'boot/axios';

// Interface atualizada para incluir os campos que o SAP exige
export interface ProductionAppointmentPayload {
  op_number: string;      // U_NumeroDocumento (DocNum)
  service_code: string;   // U_Servico (Agora recebe o ItemCode, ex: "PA-10020")
  position: string;       // U_Posicao
  operation: string;      // U_Operacao
  operator_id: string;    // U_Operador
  vehicle_id: number;     // ID interno da máquina
  start_time: string;     // ISO Date
  end_time: string;       // ISO Date
  item_code: string;      // ItemCode (Backup/Log)
  stop_reason?: string;   // U_MotivoParada
}

export const ProductionService = {
  /**
   * Busca a lista de OPs liberadas (boposReleased)
   * Rota Backend: GET /api/v1/production/orders/open
   */
  async getOpenOrders() {
    // Atenção: Verifique se o prefixo '/production' está correto na sua configuração do Axios
    const response = await api.get('/production/orders/open');
    return response.data;
  },

  /**
   * Envia o apontamento de produção
   * Rota Backend: POST /api/v1/production/appoint
   */
  async sendAppointment(payload: ProductionAppointmentPayload) {
    // Atenção: Verifique se o prefixo '/production' está correto na sua configuração do Axios
    const response = await api.post('/production/appoint', payload);
    return response.data;
  }
};