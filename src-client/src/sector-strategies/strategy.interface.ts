// Define o "contrato" para todas as estratégias de setor
export interface ISectorStrategy {
  machineNoun: string;
  machineNounPlural: string;
  journeyNoun: string;
  journeyNounPlural: string;
  distanceUnit: string;
  plateOrIdentifierLabel: string;
  startJourneyButtonLabel: string;
  machinePageTitle: string;
  addMachineButtonLabel: string;
  editButtonLabel: string;
  newButtonLabel: string;
  journeyPageTitle: string;
  journeyHistoryTitle: string;
    journeyStartSuccessMessage: string;
      journeyEndSuccessMessage: string;
      odometerLabel: string;


}