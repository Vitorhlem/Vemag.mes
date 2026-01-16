<template>
  <q-card flat bordered>
    <q-card-section class="bg-primary text-white">
      <div class="flex items-center justify-between">
        <div>
          <div class="text-h6">Relatório Gerencial de Produção</div>
          <div class="text-subtitle2">Visão macro de custos e eficiência do parque fabril</div>
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
      <div class="row q-col-gutter-md q-mb-lg">
        <div class="col-12 col-md-4">
          <q-card flat bordered class="bg-grey-1">
            <q-card-section>
                <div class="text-caption text-grey-8 text-uppercase">Custo Total da Fábrica</div>
                <div class="text-h5 text-weight-bold text-primary">{{ formatCurrency(report.summary.total_cost) }}</div>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-4">
          <q-card flat bordered class="bg-grey-1">
            <q-card-section>
                <div class="text-caption text-grey-8 text-uppercase">Atividade Total (Horas/Km)</div>
                <div class="text-h5 text-weight-bold text-primary">{{ report.summary.total_distance_km.toFixed(2) }}</div>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-4">
          <q-card flat bordered class="bg-grey-1">
            <q-card-section>
                <div class="text-caption text-grey-8 text-uppercase">Custo Médio Unitário</div>
                <div class="text-h5 text-weight-bold text-primary">{{ report.summary.overall_cost_per_km.toFixed(2) }}</div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <div class="row q-col-gutter-lg">
        <div class="col-12 col-md-5">
          <q-card flat bordered class="full-height">
            <q-card-section>
              <div class="text-h6">Distribuição de Custos</div>
            </q-card-section>
            <q-separator />
            <q-card-section>
              <CostsPieChart v-if="hasCostData" :costs="costsForChart" style="height: 350px;" />
              <div v-else class="text-center text-grey q-pa-md">Sem dados de custo no período.</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12 col-md-7">
          <q-card flat bordered class="full-height">
            <q-card-section>
              <div class="text-h6">Rankings de Máquinas</div>
            </q-card-section>
            <q-separator />
            <q-list separator>
              <q-expansion-item icon="trending_down" label="Top 5 Maiores Custos" header-class="text-negative text-weight-bold" default-opened>
                <RankingTable :data="report.top_5_most_expensive_vehicles" />
              </q-expansion-item>
              
              <q-expansion-item icon="precision_manufacturing" label="Top 5 Mais Eficientes" header-class="text-positive text-weight-bold">
                <RankingTable :data="report.top_5_most_efficient_vehicles" />
              </q-expansion-item>
              
               <q-expansion-item icon="warning" label="Top 5 Maior Custo Unitário" header-class="text-orange text-weight-bold">
                <RankingTable :data="report.top_5_highest_cost_per_km_vehicles" />
              </q-expansion-item>
            </q-list>
          </q-card>
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { type PropType, computed } from 'vue';
import { format } from 'date-fns';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';
import type { FleetManagementReport, VehicleRankingEntry } from 'src/models/report-models';
import CostsPieChart from 'components/CostsPieChart.vue';
import RankingTable from 'components/reports/RankingTable.vue';

// Interface para TypeScript reconhecer plugin
interface jsPDFWithPlugin extends jsPDF {
  lastAutoTable: { finalY: number };
}

const props = defineProps({
  report: {
    type: Object as PropType<FleetManagementReport>,
    required: true,
  },
});

const formatDate = (dateString: string) => format(new Date(dateString.replace(/-/g, '/')), 'dd/MM/yyyy');
const formatCurrency = (value: number) => value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const hasCostData = computed(() => Object.keys(props.report.costs_by_category).length > 0);

const costsForChart = computed(() => {
  return Object.entries(props.report.costs_by_category).map(([type, amount]) => ({
    cost_type: type,
    amount: amount,
  }));
});

function exportToPDF() {
  const doc = new jsPDF() as jsPDFWithPlugin;
  const report = props.report;
  
  doc.setFontSize(18);
  doc.text('Relatório Gerencial de Produção', 14, 22);
  doc.setFontSize(11);
  doc.setTextColor(100);
  doc.text(`Período: ${formatDate(report.report_period_start)} a ${formatDate(report.report_period_end)}`, 14, 30);

  const summaryBody = [
    ['Custo Total da Fábrica', formatCurrency(report.summary.total_cost)],
    ['Atividade Total (h/km)', `${report.summary.total_distance_km.toFixed(2)}`],
    ['Custo Médio Unitário', `${formatCurrency(report.summary.overall_cost_per_km)}`],
  ];
  autoTable(doc, { startY: 40, head: [['Métrica', 'Valor']], body: summaryBody });

  const createRankingBody = (data: VehicleRankingEntry[]) => data.map(item => [item.vehicle_identifier, `${item.value.toFixed(2)} ${item.unit}`]);

  // Tabela 1
  autoTable(doc, {
    startY: doc.lastAutoTable.finalY + 10,
    head: [['Top 5 - Maiores Custos (R$)']],
    body: createRankingBody(report.top_5_most_expensive_vehicles),
    theme: 'grid', headStyles: { fillColor: '#c0392b' }
  });

  // Tabela 2
  autoTable(doc, {
    startY: doc.lastAutoTable.finalY + 5,
    head: [['Top 5 - Maior Custo Unitário']],
    body: createRankingBody(report.top_5_highest_cost_per_km_vehicles),
    theme: 'grid', headStyles: { fillColor: '#f39c12' }
  });

  // Tabela 3
  autoTable(doc, {
    startY: doc.lastAutoTable.finalY + 5,
    head: [['Top 5 - Mais Eficientes']],
    body: createRankingBody(report.top_5_most_efficient_vehicles),
    theme: 'grid', headStyles: { fillColor: '#27ae60' }
  });

  doc.save('relatorio_gerencial_producao.pdf');
}

function exportToXLSX() {
  const report = props.report;
  const wb = XLSX.utils.book_new();

  const summaryData = [
    ["Relatório Gerencial de Produção"], [],
    ["Período", `${formatDate(report.report_period_start)} a ${formatDate(report.report_period_end)}`], [],
    ["Resumo Geral"],
    ["Custo Total (R$)", report.summary.total_cost],
    ["Atividade Total", report.summary.total_distance_km],
    ["Custo Médio Unitário", report.summary.overall_cost_per_km],
  ];
  const wsSummary = XLSX.utils.aoa_to_sheet(summaryData);
  XLSX.utils.book_append_sheet(wb, wsSummary, "Resumo");
  
  const rankingsData = [
    ...report.top_5_most_expensive_vehicles.map(v => ({ Ranking: "Maiores Custos (R$)", Máquina: v.vehicle_identifier, Valor: v.value })),
    ...report.top_5_highest_cost_per_km_vehicles.map(v => ({ Ranking: "Maior Custo Unitário", Máquina: v.vehicle_identifier, Valor: v.value })),
    ...report.top_5_most_efficient_vehicles.map(v => ({ Ranking: "Mais Eficientes", Máquina: v.vehicle_identifier, Valor: v.value })),
  ];
  const wsRankings = XLSX.utils.json_to_sheet(rankingsData);
  XLSX.utils.book_append_sheet(wb, wsRankings, "Rankings");

  XLSX.writeFile(wb, "relatorio_gerencial_producao.xlsx");
}
</script>