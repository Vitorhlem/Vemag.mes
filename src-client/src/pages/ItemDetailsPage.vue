<template>
  <q-page padding>
    <div v-if="!isItemDetailsLoading && item">
      
      <div class="row items-center justify-between q-mb-md">
          <div>
              <div class="text-caption text-grey text-uppercase flex items-center">
                  <q-icon name="qr_code" class="q-mr-xs" /> Serial / ID Único
              </div>
              <h1 class="text-h3 text-weight-bold q-my-none text-primary font-monospace">
                #{{ item.item_identifier }}
              </h1>
              <div class="text-h6 text-grey-8">{{ item.part.name }}</div>
          </div>
          <div>
              <q-btn flat color="secondary" label="Ver Ficha Técnica" @click="openPartHistory" icon="description" />
          </div>
      </div>

      <div class="row q-col-gutter-md q-mb-lg">
        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered class="bg-grey-1">
            <q-card-section>
              <div class="text-caption text-grey">Situação</div>
              <div class="text-h6 text-weight-bold">
                <q-chip :color="statusColor(item.status)" text-color="white" square>
                  {{ translateStatus(item.status) }}
                </q-chip>
              </div>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-caption text-grey">Custo de Aquisição</div>
              <div class="text-h6 text-weight-bold">
                {{ formatCurrency(item.part.value) }}
              </div>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-caption text-grey">Data Entrada</div>
              <div class="text-h6 text-weight-bold">
                {{ formatDate(item.created_at) }}
              </div>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-sm-6 col-md-3">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-caption text-grey">Localização Atual</div>
              <div class="text-h6 text-weight-bold">
                <router-link v-if="item.status === 'Em Uso' && item.installed_on_vehicle_id" 
                    :to="{ name: 'vehicle-details', params: { id: item.installed_on_vehicle_id } }"
                    class="text-primary" style="text-decoration: none"
                >
                  <q-icon name="precision_manufacturing" class="q-mr-xs" /> Ver Máquina
                </router-link>
                <span v-else-if="item.status === 'Disponível'" class="text-positive">
                    <q-icon name="warehouse" class="q-mr-xs" /> Almoxarifado
                </span>
                <span v-else class="text-grey-7">Descartado</span>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <q-card flat bordered>
        <q-card-section>
          <div class="text-h6 flex items-center">
              <q-icon name="history" class="q-mr-sm text-primary" /> 
              Histórico de Movimentação (Kardex Individual)
          </div>
        </q-card-section>
        <q-separator />
        <q-card-section>
          <q-timeline color="secondary" v-if="sortedTransactions.length > 0" class="q-pa-md">
            
            <q-timeline-entry
              v-for="tx in sortedTransactions"
              :key="tx.id"
              :title="translateTransactionType(tx.transaction_type)"
              :subtitle="`${formatDate(tx.timestamp, true)} • Resp: ${tx.user?.full_name || 'Sistema'}`"
              :icon="getIconForType(tx.transaction_type)"
              :color="getColorForType(tx.transaction_type)"
            >
              <div>
                <p v-if="tx.notes" class="q-my-none bg-grey-1 q-pa-sm rounded-borders text-body2">
                    "{{ tx.notes }}"
                </p>
                <div v-if="tx.related_vehicle" class="q-mt-sm">
                  <strong>Destino:</strong> 
                  <router-link :to="{ name: 'vehicle-details', params: { id: tx.related_vehicle.id } }" class="text-weight-bold text-primary">
                    {{ tx.related_vehicle.brand }} {{ tx.related_vehicle.model }} (Tag: {{ tx.related_vehicle.license_plate }})
                  </router-link>
                </div>
              </div>
            </q-timeline-entry>

          </q-timeline>
          <div v-else class="text-center text-grey q-pa-xl">
            <q-icon name="hourglass_empty" size="3em" />
            <div class="q-mt-sm">Nenhum histórico registrado para este item.</div>
          </div>
        </q-card-section>
      </q-card>
    </div>
    
    <div v-else>
      <div class="row q-col-gutter-md q-my-md">
        <q-skeleton v-for="n in 4" :key="n" height="100px" class="col-12 col-sm-6 col-md-3" />
      </div>
      <q-skeleton type="rect" height="400px" />
    </div>

    <PartHistoryDialog v-model="isPartHistoryDialogOpen" :part="item ? item.part : null" />

  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { usePartStore } from 'stores/part-store';
import { storeToRefs } from 'pinia';
import { format } from 'date-fns';
import type { TransactionType } from 'src/models/inventory-transaction-models';
import { InventoryItemStatus } from 'src/models/inventory-item-models';
import PartHistoryDialog from 'components/PartHistoryDialog.vue';

const route = useRoute();
const partStore = usePartStore();
const { selectedItemDetails: item, isItemDetailsLoading } = storeToRefs(partStore);

const itemId = Number(route.params.id);
const isPartHistoryDialogOpen = ref(false);

onMounted(async () => {
  await partStore.fetchItemDetails(itemId);
});

const sortedTransactions = computed(() => {
  if (!item.value?.transactions) return [];
  return [...item.value.transactions].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
});

function openPartHistory() {
  if (!item.value) return;
  void partStore.fetchHistory(item.value.part_id);
  isPartHistoryDialogOpen.value = true;
}

function formatDate(dateStr: string, withTime = false): string {
  try {
    return format(new Date(dateStr), withTime ? 'dd/MM/yyyy HH:mm' : 'dd/MM/yyyy');
  } catch { return '--'; }
}

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A';
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function statusColor(status: InventoryItemStatus): string {
  // CORREÇÃO: Record completo
  const map: Record<InventoryItemStatus, string> = {
    [InventoryItemStatus.DISPONIVEL]: 'positive',
    [InventoryItemStatus.EM_USO]: 'info',
    [InventoryItemStatus.FIM_DE_VIDA]: 'grey',
    [InventoryItemStatus.EM_MANUTENCAO]: 'warning'
  };
  return map[status] || 'grey';
}

function translateStatus(status: InventoryItemStatus): string {
    if (status === InventoryItemStatus.DISPONIVEL) return 'EM ESTOQUE';
    if (status === InventoryItemStatus.EM_USO) return 'INSTALADO';
    if (status === InventoryItemStatus.FIM_DE_VIDA) return 'DESCARTADO';
    if (status === InventoryItemStatus.EM_MANUTENCAO) return 'EM REPARO';
    return status;
}

function getIconForType(type: TransactionType): string {
  const iconMap: Record<string, string> = {
    'Entrada': 'login',
    'Instalação': 'build_circle',
    'Saída para Uso': 'output',
    'Fim de Vida': 'delete',
    'Retorno': 'replay',
  };
  return iconMap[type] || 'history';
}

function getColorForType(type: TransactionType): string {
  const colorMap: Record<string, string> = {
    'Entrada': 'positive',
    'Instalação': 'primary',
    'Saída para Uso': 'primary',
    'Fim de Vida': 'negative',
    'Retorno': 'warning',
  };
  return colorMap[type] || 'grey';
}

function translateTransactionType(type: TransactionType): string {
    if (type === 'Saída para Uso') return 'Instalação / Consumo';
    if (type === 'Fim de Vida') return 'Baixa / Descarte';
    return type;
}
</script>

<style scoped>
.font-monospace { font-family: 'Roboto Mono', monospace; letter-spacing: -1px; }
</style>