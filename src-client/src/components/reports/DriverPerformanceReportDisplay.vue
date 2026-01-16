<template>
  <q-card flat bordered>
    <q-card-section class="bg-primary text-white">
      <div class="flex items-center justify-between">
        <div>
          <div class="text-h6">Relatório de Desempenho de Operadores</div>
          <div class="text-subtitle2">Análise comparativa de produtividade e eficiência</div>
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
      <q-table
        :rows="report.drivers_performance"
        :columns="columns"
        row-key="driver_id"
        flat
        bordered
        :pagination="{ rowsPerPage: 10 }"
      >
        <template v-slot:body-cell-driver_name="props">
          <q-td :props="props">
            <q-item dense class="q-pa-none">
              <q-item-section avatar>
                <q-avatar icon="person" color="grey-3" text-color="primary" size="sm" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold">{{ props.value }}</q-item-label>
                <q-item-label caption>ID: {{ props.row.driver_id }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-td>
        </template>
      </q-table>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { type PropType } from 'vue';
import type { QTableColumn } from 'quasar';
import { format } from 'date-fns';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';
import type { DriverPerformanceReport } from 'src/models/report-models';

const props = defineProps({
  report: {
    type: Object as PropType<DriverPerformanceReport>,
    required: true,
  },
});

const formatDate = (dateString: string) => format(new Date(dateString.replace(/-/g, '/')), 'dd/MM/yyyy');
const formatCurrency = (value: number) => value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

// Adaptando colunas para contexto industrial
const columns: QTableColumn[] = [
  { name: 'driver_name', label: 'Operador', field: 'driver_name', align: 'left', sortable: true },
  { name: 'total_distance_km', label: 'Atividade Total (h/km)', field: 'total_distance_km', format: val => val.toFixed(2), align: 'right', sortable: true },
  { name: 'average_consumption', label: 'Eficiência (Média)', field: 'average_consumption', format: val => val.toFixed(2), align: 'right', sortable: true },
  { name: 'total_fuel_cost', label: 'Custo Operacional (R$)', field: 'total_fuel_cost', format: val => formatCurrency(val), align: 'right', sortable: true },
  { name: 'cost_per_km', label: 'Custo Unitário', field: 'cost_per_km', format: val => val.toFixed(2), align: 'right', sortable: true },
  { name: 'total_journeys', label: 'Turnos Realizados', field: 'total_journeys', align: 'center', sortable: true },
];

function exportToPDF() {
  const doc = new jsPDF('landscape');
  const report = props.report;

  doc.setFontSize(18);
  doc.text('Relatório de Desempenho de Operadores', 14, 22);
  doc.setFontSize(11);
  doc.setTextColor(100);
  doc.text(`Período: ${formatDate(report.report_period_start)} a ${formatDate(report.report_period_end)}`, 14, 30);

  autoTable(doc, {
    startY: 40,
    head: [columns.map(col => col.label)],
    body: report.drivers_performance.map(driver => [
      driver.driver_name,
      driver.total_distance_km.toFixed(2),
      driver.average_consumption.toFixed(2),
      formatCurrency(driver.total_fuel_cost),
      `R$ ${driver.cost_per_km.toFixed(2)}`,
      driver.total_journeys,
    ]),
    headStyles: { fillColor: [41, 128, 185] }, // Azul padrão
  });

  doc.save('desempenho_operadores.pdf');
}

function exportToXLSX() {
    const report = props.report;
    const data = report.drivers_performance.map(driver => ({
        'Operador': driver.driver_name,
        'Atividade Total': driver.total_distance_km,
        'Eficiência Média': driver.average_consumption,
        'Custo Operacional (R$)': driver.total_fuel_cost,
        'Custo Unitário': driver.cost_per_km,
        'Turnos': driver.total_journeys,
    }));
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Desempenho");
    XLSX.writeFile(wb, "desempenho_operadores.xlsx");
}
</script>