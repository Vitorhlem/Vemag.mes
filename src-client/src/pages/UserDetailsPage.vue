<template>
  <q-page class="q-pa-md bg-grey-2">
    
    <div v-if="isLoading" class="column flex-center q-pa-xl" style="height: 80vh">
        <q-spinner-dots color="primary" size="4em" />
        <div class="text-grey-6 q-mt-sm">Carregando dossiê do colaborador...</div>
    </div>

    <div v-else class="animation-fade-in">
        
        <q-card class="q-mb-lg shadow-3 overflow-hidden relative-position bg-white" style="border-radius: 20px;">
            <div class="absolute-right bg-gradient-primary" style="width: 45%; height: 100%; transform: skewX(-20deg) translateX(80px);"></div>
            
            <q-card-section class="row items-center q-pa-lg relative-position z-top">
                <q-btn flat round icon="arrow_back" color="grey-8" class="q-mr-md" @click="goBack">
                    <q-tooltip>Voltar</q-tooltip>
                </q-btn>

                <div class="relative-position q-mr-lg">
                    <q-avatar size="100px" font-size="44px" class="shadow-5" style="background: linear-gradient(135deg, #263238 0%, #37474F 100%); color: white;">
                        {{ user?.full_name?.charAt(0).toUpperCase() }}
                    </q-avatar>
                    <q-badge floating :color="user?.is_active ? 'green-5' : 'red'" rounded style="border: 2px solid white; width: 16px; height: 16px; bottom: 5px; right: 5px; top: auto;" />
                </div>

                <div class="col">
                    <div class="text-h4 text-weight-bolder text-blue-grey-10">{{ user?.full_name }}</div>
                    <div class="text-subtitle1 text-grey-7 row items-center q-mt-xs">
                        <q-icon name="badge" size="18px" class="q-mr-xs text-primary" /> 
                        <span class="text-weight-medium">ID: #{{ user?.employee_id || user?.id }}</span>
                        <span class="q-mx-md text-grey-4">|</span>
                        <q-icon name="email" size="18px" class="q-mr-xs text-primary" /> 
                        {{ user?.email }}
                    </div>
                    
                    <div class="row q-gutter-x-md q-mt-md">
                        <q-badge color="blue-grey-1" text-color="blue-grey-9" class="q-py-sm q-px-md text-subtitle2 text-weight-bold shadow-1">
                            <q-icon name="engineering" class="q-mr-sm" />
                            {{ user?.role || 'OPERADOR' }}
                        </q-badge>
                        <q-badge :color="getEfficiencyColor(globalStats.efficiency)" class="q-py-sm q-px-md text-subtitle2 text-weight-bold shadow-1">
                            <q-icon name="trending_up" class="q-mr-sm" />
                            Eficiência Histórica: {{ globalStats.efficiency }}%
                        </q-badge>
                    </div>
                </div>

                <div class="col-auto row q-gutter-x-xl text-right mobile-hide q-mr-md">
                    <div class="column items-end">
                        <div class="text-caption text-grey-6 text-weight-bold text-uppercase letter-spacing-1">Sessões Totais</div>
                        <div class="text-h3 text-weight-bolder text-blue-grey-9 lh-small">{{ globalStats.sessions }}</div>
                    </div>
                    <div class="column items-end">
                        <div class="text-caption text-grey-6 text-weight-bold text-uppercase letter-spacing-1">Horas Totais</div>
                        <div class="text-h3 text-weight-bolder text-primary lh-small">{{ globalStats.hours }}h</div>
                    </div>
                </div>
            </q-card-section>
        </q-card>

        <div class="row q-col-gutter-lg">
            
            <div class="col-12 col-md-2">
                <div style="position: sticky; top: 100px;">
                    <div class="text-subtitle2 text-grey-6 q-mb-sm text-uppercase text-weight-bold q-pl-xs">Exercício</div>
                    <q-card class="shadow-1 overflow-hidden" style="border-radius: 16px;">
                        <q-tabs
                            v-model="selectedYear"
                            vertical
                            class="text-grey-7 bg-white"
                            active-color="white"
                            active-bg-color="primary"
                            indicator-color="transparent"
                            content-class="q-py-sm"
                        >
                            <q-tab 
                                v-for="year in availableYears" 
                                :key="year" 
                                :name="year" 
                                class="q-my-xs q-mx-sm transition-tab"
                                style="border-radius: 10px; min-height: 50px;"
                            >
                                <div class="row items-center justify-between full-width">
                                    <span class="text-h6 text-weight-bold">{{ year }}</span>
                                    <q-icon name="chevron_right" size="xs" :class="selectedYear === year ? 'text-white' : 'transparent'" />
                                </div>
                            </q-tab>
                        </q-tabs>
                    </q-card>
                </div>
            </div>

            <div class="col-12 col-md-10">
                
                <q-card class="bg-white q-mb-lg shadow-1" style="border-radius: 16px;">
                    <q-card-section class="q-pa-lg">
                        <div class="row items-center justify-between">
                            <div>
                                <div class="text-h5 text-weight-bold text-blue-grey-9 row items-center">
                                    <q-icon name="analytics" class="q-mr-md text-primary" size="32px" /> 
                                    Performance {{ selectedYear }}
                                </div>
                                <div class="text-subtitle2 text-grey-7 q-mt-xs">Visão consolidada do período</div>
                            </div>
                            
                            <div class="row q-gutter-x-xl">
                                <div class="row items-center">
                                    <q-circular-progress
                                        show-value
                                        font-size="12px"
                                        :value="currentYearStats.efficiency"
                                        size="50px"
                                        :thickness="0.25"
                                        :color="getEfficiencyColorName(currentYearStats.efficiency)"
                                        track-color="grey-3"
                                        class="q-mr-md text-weight-bold"
                                    >
                                        {{ currentYearStats.efficiency }}%
                                    </q-circular-progress>
                                    <div class="column">
                                        <span class="text-caption text-grey-6 text-uppercase">Média Eficiência</span>
                                        <span class="text-h6 text-weight-bold text-dark">
                                            {{ getEfficiencyLabel(currentYearStats.efficiency) }}
                                        </span>
                                    </div>
                                </div>

                                <div class="row items-center">
                                    <q-avatar color="blue-grey-1" text-color="blue-grey-8" icon="schedule" size="50px" class="q-mr-md" />
                                    <div class="column">
                                        <span class="text-caption text-grey-6 text-uppercase">Horas no Ano</span>
                                        <span class="text-h5 text-weight-bold text-dark">{{ currentYearStats.hours }}h</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>

                <div class="column q-gutter-y-md">
                    <q-card 
                        v-for="(monthData, index) in currentYearData" 
                        :key="index" 
                        class="shadow-1 overflow-hidden transition-hover" 
                        style="border-radius: 12px; border: 1px solid #f0f0f0;"
                    >
                        <q-expansion-item
                            group="months"
                            header-class="bg-white text-blue-grey-9 q-py-md"
                            expand-icon-class="text-primary"
                        >
                            <template v-slot:header>
                                <div class="row full-width items-center">
                                    <div class="col-3 row items-center relative-position">
                                        <div class="absolute-left bg-primary" style="width: 4px; height: 30px; border-radius: 4px;" v-if="monthData.sessions.length"></div>
                                        <div class="q-ml-md row items-center">
                                            <q-avatar 
                                                :color="monthData.sessions.length ? 'blue-grey-1' : 'grey-2'" 
                                                :text-color="monthData.sessions.length ? 'blue-grey-8' : 'grey-5'" 
                                                :icon="monthData.sessions.length ? 'folder_open' : 'folder_off'" 
                                                size="44px" 
                                                class="q-mr-md font-weight-bold" 
                                            />
                                            <div>
                                                <div class="text-h6 text-weight-bold line-height-1">{{ monthNames[index] }}</div>
                                                <div class="text-caption text-grey-6" v-if="monthData.sessions.length">{{ monthData.sessions.length }} registros</div>
                                                <div class="text-caption text-grey-5" v-else>Sem atividade</div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="col-9 row items-center justify-end q-gutter-x-xl q-pr-md" v-if="monthData.sessions.length > 0">
                                        <div class="column items-end" style="min-width: 100px;">
                                            <span class="text-caption text-grey-6 text-uppercase text-weight-bold" style="font-size: 0.65rem;">Horas Prod.</span>
                                            <div class="row items-baseline">
                                                <span class="text-h6 text-weight-bolder text-dark">{{ monthData.totalHours }}</span>
                                                <span class="text-caption text-grey-6 q-ml-xs">h</span>
                                            </div>
                                        </div>

                                        <div class="column items-end" style="width: 150px;">
                                            <span class="text-caption text-grey-6 text-uppercase text-weight-bold" style="font-size: 0.65rem;">Eficiência</span>
                                            <div class="row items-center full-width justify-end q-mt-xs">
                                                <q-linear-progress :value="monthData.avgEfficiency / 100" 
                                                    :color="getEfficiencyColorName(monthData.avgEfficiency)" 
                                                    size="8px" rounded class="col q-mr-md" track-color="grey-3"
                                                />
                                                <span class="text-body1 text-weight-bolder" :class="getEfficiencyColorClass(monthData.avgEfficiency)">{{ monthData.avgEfficiency }}%</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </template>

                            <q-card-section class="bg-grey-1 q-pa-lg border-top-light">
                                <div v-if="monthData.sessions.length > 0">
                                    <div class="row q-col-gutter-lg">
                                        
                                        <div class="col-12 col-md-4">
                                            <q-card flat bordered class="full-height bg-white">
                                                <q-card-section>
                                                    <div class="text-subtitle2 text-uppercase text-grey-7 q-mb-lg row items-center">
                                                        <q-icon name="pie_chart" class="q-mr-sm" /> Máquinas Utilizadas
                                                    </div>
                                                    <div v-for="(usage, mName) in monthData.machineStats" :key="mName" class="q-mb-md">
                                                        <div class="row justify-between text-caption q-mb-xs">
                                                            <div class="row items-center">
                                                                <q-icon name="precision_manufacturing" size="14px" class="q-mr-xs text-grey-6" />
                                                                <span class="text-weight-bold text-dark">{{ mName }}</span>
                                                            </div>
                                                            <span class="text-weight-bold">{{ usage.count }}x</span>
                                                        </div>
                                                        <q-linear-progress :value="usage.percent" color="secondary" size="10px" rounded track-color="grey-2" />
                                                    </div>
                                                </q-card-section>
                                            </q-card>
                                        </div>

                                        <div class="col-12 col-md-8">
                                            <q-table
                                                title="Diário de Bordo"
                                                :rows="monthData.sessions"
                                                :columns="sessionColumns"
                                                row-key="id"
                                                flat bordered
                                                class="bg-white my-sticky-header-table"
                                                :pagination="{ rowsPerPage: 10 }"
                                                dense
                                            >
                                                <template v-slot:body-cell-efficiency="props">
                                                    <q-td :props="props">
                                                        <q-badge :color="getEfficiencyColorName(props.value)" class="q-px-sm text-weight-bold shadow-1">
                                                            {{ props.value }}%
                                                        </q-badge>
                                                    </q-td>
                                                </template>
                                                
                                                <template v-slot:body-cell-start_time="props">
                                                    <q-td :props="props">
                                                        <div class="row items-center">
                                                            <div class="bg-blue-grey-1 text-blue-grey-9 q-pa-xs rounded-borders q-mr-sm text-weight-bold" style="font-size: 0.75rem;">
                                                                {{ new Date(props.value).getDate().toString().padStart(2, '0') }}
                                                            </div>
                                                            {{ new Date(props.value).toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit'}) }}
                                                        </div>
                                                    </q-td>
                                                </template>

                                                <template v-slot:body-cell-order_code="props">
    <q-td :props="props">
        <div class="row items-center justify-center">
            <q-badge outline color="blue-grey" :label="props.row.order_code" class="text-weight-bold q-mr-xs" />
            <q-badge v-if="props.row.step" color="grey-3" text-color="grey-9" :label="'ET: ' + props.row.step" class="text-caption" />
        </div>
    </q-td>
</template>
                                            </q-table>
                                        </div>
                                    </div>
                                </div>
                                
                                <div v-else class="column flex-center q-pa-xl text-grey-5">
                                    <q-icon name="folder_off" size="60px" class="q-mb-md opacity-50" />
                                    <div class="text-h6">Nenhuma atividade registrada.</div>
                                </div>
                            </q-card-section>
                        </q-expansion-item>
                    </q-card>
                </div>

            </div>
        </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from 'stores/user-store'; // ✅ STORE DE USUÁRIOS
import { api } from 'boot/axios'; // ✅ AXIOS
import { Notify } from 'quasar';
import type { QTableColumn } from 'quasar';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const userId = Number(route.params.id);

// --- TIPOS ---
interface UserProfile {
    id: number;
    full_name: string;
    email: string;
    employee_id?: string;
    role: string;
    is_active: boolean;
}

interface SessionData {
    id: number;
    machine_name: string;
    order_code: string;
    step?: string; // <--- CAMPO NOVO
    start_time: string;
    end_time?: string;
    duration_minutes: number;
    efficiency: number; // 0-100
}

// --- ESTADOS ---
const user = ref<UserProfile | null>(null);
const userSessions = ref<SessionData[]>([]);
const isLoading = ref(true);

const currentSysYear = new Date().getFullYear();
const selectedYear = ref(currentSysYear);

const monthNames = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
];

const sessionColumns: QTableColumn[] = [
  { name: 'start_time', label: 'Dia / Hora', field: 'start_time', align: 'left', sortable: true },
  { name: 'machine_name', label: 'Equipamento', field: 'machine_name', align: 'left' },
  { name: 'order_code', label: 'O.P. / Etapa', field: 'order_code', align: 'center' }, // Label alterado
  { 
    name: 'duration', 
    label: 'Duração', 
    field: (row: SessionData) => formatDuration(row.duration_minutes), 
    align: 'center' 
  },
  { name: 'efficiency', label: 'Eficiência', field: 'efficiency', align: 'center', sortable: true }
];

function goBack() {
    router.go(-1);
}

function formatDuration(minutes: number) {
    if (minutes === 0) return '< 1m'; // Mostra que foi rápido, mas existiu
    if (!minutes) return '--';
    
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    
    if (h === 0) return `${m}m`; // Ex: "45m"
    return `${h}h ${m}m`;        // Ex: "1h 30m"
}

// --- CARREGAMENTO DE DADOS REAIS ---
async function loadUserData() {
    try {
        isLoading.value = true;
        
        // 1. Busca perfil do usuário
        const foundUser = userStore.users.find(u => u.id === userId);
        if (foundUser) {
            user.value = foundUser;
        } else {
            const { data } = await api.get(`/users/${userId}`);
            user.value = data;
        }

        // 2. Busca histórico de sessões do usuário
        // Rota que criamos no backend: /production/history/user/{id}
        const historyRes = await api.get(`/production/history/user/${userId}`);
        
        // Mapeia para o formato local
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        userSessions.value = historyRes.data.map((item: any) => ({
            id: item.id,
            machine_name: item.machine_name || `Máquina #${item.machine_id}`,
            order_code: item.op_number || 'N/A',
            step: item.step, // <--- MAPEANDO ETAPA
            start_time: item.start_time,
            end_time: item.end_time,
            duration_minutes: item.duration_minutes || 0,
            efficiency: item.efficiency || 100
        }));

        console.log("Dados carregados:", userSessions.value.length, "sessões");

    } catch (error) {
        console.error('Erro ao carregar dados do usuário:', error);
        Notify.create({ type: 'negative', message: 'Falha ao carregar histórico do colaborador.' });
    } finally {
        isLoading.value = false;
    }
}

// --- LÓGICA COMPUTADA (MANTIDA MAS ADAPTADA PARA userSessions REF) ---

const availableYears = computed(() => {
    if (!userSessions.value.length) return [currentSysYear];
    const years = new Set<number>();
    userSessions.value.forEach(s => {
        if(s.start_time) years.add(new Date(s.start_time).getFullYear());
    });
    return Array.from(years).sort((a, b) => b - a); 
});

const currentYearData = computed(() => {
    const year = selectedYear.value;
    
    // Inicializa 12 meses vazios
    const months = Array.from({ length: 12 }, () => ({
        sessions: [] as SessionData[],
        totalHours: 0,
        avgEfficiency: 0,
        machineStats: {} as Record<string, { count: number, percent: number }>
    }));

    // Filtra pelo ano selecionado
    const yearSessions = userSessions.value.filter(s => 
        s.start_time && new Date(s.start_time).getFullYear() === year
    );

    // Distribui nos meses
    yearSessions.forEach(session => {
        const date = new Date(session.start_time);
        const targetMonth = months[date.getMonth()];
        if (targetMonth) {
            targetMonth.sessions.push(session);
        }
    });

    // Calcula estatísticas mensais
    months.forEach(m => {
        if (m.sessions.length === 0) return;
        
        m.sessions.sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());

        const totalEff = m.sessions.reduce((sum, s) => sum + s.efficiency, 0);
        m.avgEfficiency = Math.round(totalEff / m.sessions.length);

        const totalMinutes = m.sessions.reduce((sum, s) => sum + (s.duration_minutes || 0), 0);
        m.totalHours = Math.round(totalMinutes / 60);

        const machineCounts: Record<string, number> = {};
        m.sessions.forEach(s => {
            const name = s.machine_name || 'Outro';
            machineCounts[name] = (machineCounts[name] || 0) + 1;
        });
        
        const totalSess = m.sessions.length;
        Object.keys(machineCounts).forEach(key => {
            const count = machineCounts[key] || 0;
            m.machineStats[key] = {
                count: count,
                percent: totalSess > 0 ? count / totalSess : 0
            };
        });
    });

    return months;
});

const currentYearStats = computed(() => {
    const data = currentYearData.value;
    const totalHours = data.reduce((acc, m) => acc + m.totalHours, 0);
    const activeMonths = data.filter(m => m.sessions.length > 0);
    const avgEff = activeMonths.length 
        ? Math.round(activeMonths.reduce((acc, m) => acc + m.avgEfficiency, 0) / activeMonths.length)
        : 0;
    return { hours: totalHours, efficiency: avgEff };
});

const globalStats = computed(() => {
    const all = userSessions.value;
    const count = all.length;
    const eff = count ? Math.round(all.reduce((acc, s) => acc + s.efficiency, 0) / count) : 0;
    const totalMinutes = all.reduce((acc, s) => acc + (s.duration_minutes || 0), 0);
    const hours = Math.round(totalMinutes / 60);
    return { hours, efficiency: eff, sessions: count };
});

// --- HELPERS VISUAIS ---
function getEfficiencyColorName(val: number) {
    if (val >= 90) return 'positive';
    if (val >= 70) return 'warning';
    return 'negative';
}
function getEfficiencyColor(val: number) {
    if (val >= 90) return '#21BA45'; 
    if (val >= 70) return '#F2C037'; 
    return '#C10015'; 
}
function getEfficiencyColorClass(val: number) {
    if (val >= 90) return 'text-positive';
    if (val >= 70) return 'text-warning';
    return 'text-negative';
}
function getEfficiencyLabel(val: number) {
    if (val >= 90) return 'Excelente';
    if (val >= 70) return 'Regular';
    return 'Abaixo da Meta';
}

// --- INIT ---
onMounted(async () => {
    await loadUserData();
});
</script>

<style scoped>
.bg-gradient-primary {
    background: linear-gradient(135deg, rgba(0,140,122,0) 0%, rgba(0,140,122,0.15) 100%);
}
.border-top-light {
    border-top: 1px solid #e0e0e0;
}
.transition-tab {
    transition: all 0.3s ease;
}
.transition-hover:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    transform: translateY(-2px);
    transition: all 0.3s ease;
}
.z-top {
    z-index: 10;
}
.letter-spacing-1 {
    letter-spacing: 1px;
}
.line-height-1 {
    line-height: 1.1;
}
.lh-small {
    line-height: 1;
}
</style>