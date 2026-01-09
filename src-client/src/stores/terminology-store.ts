import { defineStore } from 'pinia';
import type { UserSector } from 'src/models/auth-models';
import type { ISectorStrategy } from 'src/sector-strategies/strategy.interface';

// --- ESTRATÉGIA INDUSTRIAL (NOVA) ---
const IndustrialStrategy: ISectorStrategy = {
  vehicleNoun: 'Máquina',
  vehicleNounPlural: 'Máquinas',
  journeyNoun: 'Ordem de Produção',
  journeyNounPlural: 'Ordens de Produção',
  distanceUnit: 'Horas',
  plateOrIdentifierLabel: 'Patrimônio / TAG',
  startJourneyButtonLabel: 'Iniciar Turno/Ordem',
  vehiclePageTitle: 'Parque de Máquinas',
  addVehicleButtonLabel: 'Adicionar Máquina',
  editButtonLabel: 'Editar Máquina',
  newButtonLabel: 'Nova Máquina',
  journeyPageTitle: 'Ordens de Produção',
  journeyHistoryTitle: 'Histórico de Produção',
  journeyStartSuccessMessage: 'Ordem iniciada com sucesso',
  journeyEndSuccessMessage: 'Ordem finalizada',
  odometerLabel: 'Horímetro Total',
};
// ------------------------------------

interface TerminologyState {
  currentSector: UserSector;
}

export const useTerminologyStore = defineStore('terminology', {
  state: (): TerminologyState => ({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    currentSector: 'industria' as any, 
  }),

  getters: {
    activeStrategy(): ISectorStrategy {
      // Retorna SEMPRE a estratégia industrial, independente do setor do usuário
      return IndustrialStrategy;
    },
    
    vehicleNoun(): string { return this.activeStrategy.vehicleNoun; },
    vehicleNounPlural(): string { return this.activeStrategy.vehicleNounPlural; },
    journeyNoun(): string { return this.activeStrategy.journeyNoun; },
    journeyNounPlural(): string { return this.activeStrategy.journeyNounPlural; },
    distanceUnit(): string { return this.activeStrategy.distanceUnit; },
    
    fuelUnit(): string {
      // Na indústria, medimos consumo por hora (ex: kWh ou Litros/Hora)
      return 'un/h'; 
    },

    plateOrIdentifierLabel(): string { return this.activeStrategy.plateOrIdentifierLabel; },
    startJourneyButtonLabel(): string { return this.activeStrategy.startJourneyButtonLabel; },
    vehiclePageTitle(): string { return this.activeStrategy.vehiclePageTitle; },
    addVehicleButtonLabel(): string { return this.activeStrategy.addVehicleButtonLabel; },
    editButtonLabel(): string { return this.activeStrategy.editButtonLabel; },
    newButtonLabel(): string { return this.activeStrategy.newButtonLabel; },
    journeyPageTitle(): string { return this.activeStrategy.journeyPageTitle; },
    journeyHistoryTitle(): string { return this.activeStrategy.journeyHistoryTitle; },
    journeyStartSuccessMessage(): string { return this.activeStrategy.journeyStartSuccessMessage; },
    journeyEndSuccessMessage(): string { return this.activeStrategy.journeyEndSuccessMessage; },
    odometerLabel(): string { return this.activeStrategy.odometerLabel; },
  },

  actions: {
    setSector(sector: UserSector) {
      this.currentSector = sector;
    },
  },
});