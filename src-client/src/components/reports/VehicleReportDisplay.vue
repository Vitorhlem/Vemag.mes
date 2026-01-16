<template>
  <q-card flat bordered>
    <q-card-section class="bg-primary text-white">
      <div class="flex items-center justify-between">
        <div>
          <div class="text-h6">Dossiê Técnico da Máquina</div>
          <div class="text-subtitle2">{{ report.vehicle_model }} ({{ report.vehicle_identifier }})</div>
        </div>
        <div class="q-gutter-sm">
          <q-btn @click="exportToPDF" icon="picture_as_pdf" label="PDF" dense unelevated color="white" text-color="primary" />
          <q-btn @click="exportToXLSX" icon="description" label="Excel" dense unelevated color="white" text-color="primary" />
        </div>
      </div>
      <div class="text-caption q-mt-sm">
        Período de Análise: {{ formatDate(report.report_period_start) }} a {{ formatDate(report.report_period_end) }}
      </div>
    </q-card-section>

    <q-card-section>
      <div class="row q-col-gutter-md">
        
        <div v-if="report.financial_summary" class="col-12 col-md-6">
          <q-card flat bordered>
            <q-card-section><div class="text-subtitle1 text-weight-bold text-grey-8">Resumo de Custos</div></q-card-section>
            <q-list separator dense>
              <q-item>
                <q-item-section>Custo Total no Período:</q-item-section>
                <q-item-section side class="text-weight-bold">{{ formatCurrency(report.financial_summary.total_costs) }}</q-item-section>
              </q-item>
              <q-item v-if="report.financial_summary.cost_per_metric > 0">
                <q-item-section>
                  {{ report.financial_summary.metric_unit === 'km' ? 'Custo por KM:' : 'Custo por Hora:' }}
                </q-item-section>
                <q-item-section side class="text-weight-bold">
                  {{ formatCurrency(report.financial_summary.cost_per_metric) }} / {{ report.financial_summary.metric_unit }}
                </q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>
        
        <div v-if="report.performance_summary" class="col-12 col-md-6">
          <q-card flat bordered>
            <q-card-section><div class="text-subtitle1 text-weight-bold text-grey-8">Resumo de Performance</div></q-card-section>
            <q-list separator dense>
              <q-item>
                <q-item-section>
                  {{ report.performance_summary.activity_unit === 'km' ? 'Horímetro Atual:' : 'Horímetro Atual:' }}
                </q-item-section>
                <q-item-section side class="text-weight-bold">
                  {{ report.performance_summary.vehicle_total_activity.toFixed(2) }} {{ report.performance_summary.activity_unit }}
                </q-item-section>
              </q-item>

              <q-item v-if="report.performance_summary.period_total_activity > 0">
                <q-item-section>
                  {{ report.performance_summary.activity_unit === 'km' ? 'Produção (Distância):' : 'Produção (Horas):' }}
                </q-item-section>
                <q-item-section side class="text-weight-bold">
                  {{ report.performance_summary.period_total_activity.toFixed(2) }} {{ report.performance_summary.activity_unit }}
                </q-item-section>
              </q-item>
              
              <q-item v-if="report.performance_summary.period_total_fuel > 0">
                <q-item-section>
                  Consumo Total:
                </q-item-section>
                <q-item-section side class="text-weight-bold">
                  {{ report.performance_summary.period_total_fuel.toFixed(2) }} 
                  {{ report.performance_summary.activity_unit === 'km' ? 'L' : 'Unid.' }}
                </q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>
      </div>

      <div v-if="report.costs_detailed && report.costs_detailed.length > 0" class="q-mt-lg">
        <q-table title="Detalhamento de Custos" :rows="report.costs_detailed" :columns="costColumns" row-key="id" flat dense bordered />
      </div>

      <div v-if="report.maintenance_detailed && report.maintenance_detailed.length > 0" class="q-mt-lg">
        <q-table title="Histórico de Manutenções" :rows="report.maintenance_detailed" :columns="maintenanceColumns" row-key="id" flat dense bordered />
      </div>

      <div v-if="report.journeys_detailed && report.journeys_detailed.length > 0" class="q-mt-lg">
        <q-table title="Histórico de Turnos" :rows="report.journeys_detailed" :columns="journeysColumns" row-key="id" flat dense bordered />
      </div>
      
      <div v-if="report.fuel_logs_detailed && report.fuel_logs_detailed.length > 0" class="q-mt-lg">
        <q-table title="Histórico de Abastecimento / Energia" :rows="report.fuel_logs_detailed" :columns="fuelColumns" row-key="id" flat dense bordered />
      </div>

      <div v-if="report.documents_detailed && report.documents_detailed.length > 0" class="q-mt-lg">
        <q-table title="Documentação Técnica" :rows="report.documents_detailed" :columns="documentsColumns" row-key="id" flat dense bordered />
      </div>

    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { type PropType } from 'vue';
import type { QTableColumn } from 'quasar';
import { format } from 'date-fns';
import { jsPDF } from 'jspdf';
import autoTable, { type UserOptions } from 'jspdf-autotable';
import * as XLSX from 'xlsx';
import type { VehicleConsolidatedReport } from 'src/models/report-models';
import type { Journey } from 'src/models/journey-models';
import type { DocumentPublic } from 'src/models/document-models';
import type { MaintenanceRequest } from 'src/models/maintenance-models';
import type { FuelLog } from 'src/models/fuel-log-models';
import type { VehicleCost } from 'src/models/vehicle-cost-models';

interface AutoTableOptions extends UserOptions { startY?: number; }
interface jsPDFWithLastTable extends jsPDF { lastAutoTable: { finalY: number }; }

const props = defineProps({
  report: {
    type: Object as PropType<VehicleConsolidatedReport>,
    required: true,
  },
});

const formatDate = (dateString: string | Date | null | undefined) => {
  if (!dateString) return 'N/A';
  const date = typeof dateString === 'string' ? new Date(dateString.replace(/-/g, '/')) : dateString;
  try { return format(date, 'dd/MM/yyyy'); } catch  { return 'Data Inválida'; }
};
const formatDateTime = (dateString: string | Date | null | undefined) => {
  if (!dateString) return 'N/A';
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
   try { return format(date, 'dd/MM/yyyy HH:mm'); } catch { return 'Data Inválida'; }
};
const formatCurrency = (value: number | null | undefined) => {
  if (value === null || value === undefined) return 'R$ 0,00';
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
};

// COLUNAS
const costColumns: QTableColumn<VehicleCost>[] = [
  { name: 'date', label: 'Data', field: 'date', format: val => formatDate(val), align: 'left', sortable: true },
  { name: 'cost_type', label: 'Tipo', field: 'cost_type', align: 'left', sortable: true },
  { name: 'description', label: 'Descrição', field: 'description', align: 'left' },
  { name: 'amount', label: 'Valor', field: 'amount', format: val => formatCurrency(val), align: 'right', sortable: true },
];

const fuelColumns: QTableColumn<FuelLog>[] = [
  { name: 'timestamp', label: 'Data', field: 'timestamp', format: val => formatDateTime(val), align: 'left', sortable: true },
  { name: 'odometer', label: 'Horímetro/Km', field: 'odometer', align: 'center', sortable: true },
  { name: 'liters', label: 'Qtd', field: 'liters', align: 'right', sortable: true },
  { name: 'total_cost', label: 'Custo', field: 'total_cost', format: val => formatCurrency(val), align: 'right', sortable: true },
];

const maintenanceColumns: QTableColumn<MaintenanceRequest>[] = [
  { name: 'created_at', label: 'Data', field: 'created_at', format: val => formatDate(val), align: 'left', sortable: true },
  { name: 'category', label: 'Categoria', field: 'category', align: 'left', sortable: true },
  { name: 'status', label: 'Status', field: 'status', align: 'center', sortable: true },
  { name: 'problem_description', label: 'Descrição', field: 'problem_description', align: 'left', style: 'white-space: normal; min-width: 200px;' },
];

const journeysColumns: QTableColumn<Journey>[] = [
  { name: 'start_time', label: 'Início', field: 'start_time', format: val => formatDateTime(val), align: 'left', sortable: true },
  { name: 'end_time', label: 'Término', field: 'end_time', format: val => formatDateTime(val), align: 'left', sortable: true },
  { name: 'start_engine_hours', label: 'Início (h/km)', field: 'start_engine_hours', align: 'center' },
  { name: 'end_engine_hours', label: 'Fim (h/km)', field: 'end_engine_hours', align: 'center' },
  { name: 'is_active', label: 'Status', field: 'is_active', format: val => (val ? 'Em Andamento' : 'Finalizado'), align: 'center', sortable: true },
];

const documentsColumns: QTableColumn<DocumentPublic>[] = [
  { name: 'document_type', label: 'Tipo', field: 'document_type', align: 'left', sortable: true },
  { name: 'expiry_date', label: 'Vencimento', field: 'expiry_date', format: val => formatDate(val), align: 'center', sortable: true },
];

function exportToPDF() {
  const doc = new jsPDF() as jsPDFWithLastTable;
  const report = props.report;

  doc.setFontSize(18);
  doc.text(`Dossiê Técnico: ${report.vehicle_model} (${report.vehicle_identifier})`, 14, 22);
  doc.setFontSize(11);
  doc.setTextColor(100);
  doc.text(`Período: ${formatDate(report.report_period_start)} a ${formatDate(report.report_period_end)}`, 14, 30);
  
  let startY = 40;
  const summaryBody: (string | number)[][] = [];
  
  if (report.performance_summary) {
     const unit = report.performance_summary.activity_unit;
     const totalLabel = unit === 'km' ? 'Odômetro Atual' : 'Horímetro Atual';
     const totalValue = `${report.performance_summary.vehicle_total_activity.toFixed(2)} ${unit}`;
     summaryBody.push([totalLabel, totalValue]);
     
     if (report.performance_summary.period_total_activity > 0) {
        const periodLabel = unit === 'km' ? 'Produção (Distância)' : 'Produção (Horas)';
        const periodValue = `${report.performance_summary.period_total_activity.toFixed(2)} ${unit}`;
        summaryBody.push([periodLabel, periodValue]);
     }
  }

  if (report.financial_summary) {
    summaryBody.push(['Custo Total (Período)', formatCurrency(report.financial_summary.total_costs)]);
  }

  if (summaryBody.length > 0) {
    autoTable(doc, {
      startY: startY,
      head: [['Métrica', 'Valor']],
      body: summaryBody,
    } as AutoTableOptions);
    startY = doc.lastAutoTable.finalY + 10;
  }
  
  const addTableToPdf = (title: string, head: string[][], body: (string | number | undefined | null)[][]) => {
    if (!body || body.length === 0) return;
    doc.setFontSize(14);
    doc.text(title, 14, startY);
    startY += 8;
    autoTable(doc, { startY: startY, head: head, body: body, headStyles: { fillColor: [41, 128, 185] } } as AutoTableOptions);
    startY = doc.lastAutoTable.finalY + 10;
  };

  addTableToPdf('Custos',
    [['Data', 'Tipo', 'Descrição', 'Valor']],
    report.costs_detailed?.map(c => [formatDate(c.date), c.cost_type, c.description, formatCurrency(c.amount)]) || []
  );
  addTableToPdf('Manutenções',
    [['Data', 'Categoria', 'Status', 'Descrição']],
    report.maintenance_detailed?.map(m => [formatDate(m.created_at), m.category, m.status, m.problem_description]) || []
  );
  addTableToPdf('Turnos',
    [['Início', 'Término', 'Horím. Início', 'Horím. Fim', 'Status']],
    report.journeys_detailed?.map(j => [
      formatDateTime(j.start_time), 
      formatDateTime(j.end_time || ''), 
      j.start_engine_hours ?? 'N/A', 
      j.end_engine_hours ?? 'N/A', 
      j.is_active ? 'Ativa' : 'Finalizada'
    ]) || []
  );
  
  doc.save(`dossie_${report.vehicle_identifier}.pdf`);
}

function exportToXLSX() {
  const report = props.report;
  const wb = XLSX.utils.book_new();
  
  const summaryData: (string | number)[][] = [
    ["Dossiê Técnico da Máquina"],
    [`${report.vehicle_model} (${report.vehicle_identifier})`],
    [`Período: ${formatDate(report.report_period_start)} a ${formatDate(report.report_period_end)}`],
    [],
    ["Métrica", "Valor"],
  ];
  
  if (report.performance_summary) {
    summaryData.push(['Atividade Total', report.performance_summary.vehicle_total_activity]);
  }
  if (report.financial_summary) {
    summaryData.push(['Custo Total', report.financial_summary.total_costs]);
  }
  
  const wsSummary = XLSX.utils.aoa_to_sheet(summaryData);
  XLSX.utils.book_append_sheet(wb, wsSummary, "Resumo");

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const addSheet = (sheetName: string, data: Record<string, any>[] | undefined) => {
    if (data && data.length > 0) {
      const ws = XLSX.utils.json_to_sheet(data);
      XLSX.utils.book_append_sheet(wb, ws, sheetName);
    }
  };

  addSheet("Custos", report.costs_detailed?.map(c => ({
    Data: formatDate(c.date), Tipo: c.cost_type, Descrição: c.description, Valor: c.amount
  })));
  addSheet("Manutenções", report.maintenance_detailed?.map(m => ({
    Data: formatDate(m.created_at), Categoria: m.category, Status: m.status, Descrição: m.problem_description
  })));
  addSheet("Turnos", report.journeys_detailed?.map(j => ({
    Início: formatDateTime(j.start_time), 
    Término: formatDateTime(j.end_time || ''), 
    'Horím. Inicial': j.start_engine_hours,
    'Horím. Final': j.end_engine_hours,
    Status: j.is_active ? 'Ativa' : 'Finalizada'
  })));

  XLSX.writeFile(wb, `dossie_${report.vehicle_identifier}.xlsx`);
}
</script>