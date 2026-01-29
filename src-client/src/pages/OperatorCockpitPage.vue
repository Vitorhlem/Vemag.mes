<template>
  <q-layout view="hHh lpR fFf" class="bg-grey-2 text-dark font-inter window-height overflow-hidden">
    
    <q-header bordered class="q-py-xs shadow-3 text-white" style="height: 65px; background-color: #008C7A;">
      <q-toolbar class="full-height q-px-lg"> 
        <div class="row items-center no-wrap">
          <img :src="logoPath" alt="Logo" style="height: 40px; max-width: 180px; object-fit: contain; filter: brightness(0) invert(1);" />
          
          <q-separator vertical inset class="q-mx-md mobile-hide bg-white opacity-50" /> 
          
          <div class="column justify-center">
            <div class="text-caption text-uppercase text-grey-3 letter-spacing-1" style="line-height: 1;">
              {{ productionStore.machineSector }}
            </div>
            <div class="row items-center q-mt-xs">
              <div class="text-h6 text-weight-bolder lh-small text-white q-mr-sm">
                {{ productionStore.machineName }}
              </div>
              <q-badge rounded :class="statusBgClass" class="shadow-2 text-white q-py-xs q-px-sm text-caption">
                <q-icon :name="statusIcon" color="white" class="q-mr-xs" size="14px" />
                {{ displayStatus }}
              </q-badge>
            </div>
          </div>
        </div>
        
        <q-space />
        
        <div class="row items-center q-gutter-x-md">
          <div class="row items-center bg-white text-dark q-py-xs q-px-sm rounded-borders shadow-2" style="height: 42px; border-radius: 10px;">
            <q-avatar size="28px" class="shadow-1 vemag-bg-primary text-white" icon="person" font-size="18px" />
            
            <div class="column items-start justify-center q-ml-sm mobile-hide" style="line-height: 1.1;">
              <div class="text-caption text-weight-bold vemag-text-primary text-uppercase" style="font-size: 0.6rem;">OP</div>
              <div class="text-caption text-grey-9 text-weight-bold">
                {{ productionStore.currentOperator?.full_name || productionStore.currentOperatorBadge || '---' }}
              </div>
            </div>
            
            <q-separator vertical inset class="q-mx-sm bg-grey-4" />
            
            <div class="text-h6 font-monospace vemag-text-primary text-weight-bold" style="margin-top: 1px;">
              {{ timeDisplay }}
            </div>
          </div>
          
          <q-btn flat round icon="logout" class="text-white" size="md" padding="xs" @click="handleLogout" />
        </div>

      </q-toolbar>
      <q-linear-progress :value="1" color="green" class="q-mt-none" size="4px" />
    </q-header>

    <q-page-container class="full-height">
      <q-page class="q-pa-sm full-height column no-wrap">
        
        <div v-if="!productionStore.activeOrder" class="col flex flex-center column">
          <q-card class="q-pa-lg text-center shadow-10 bg-white" style="border-radius: 20px; max-width: 500px; width: 90%;">
            <div class="vemag-bg-light q-pa-md rounded-borders inline-block q-mb-md">
               <q-icon name="qr_code_scanner" size="60px" class="vemag-text-primary" />
            </div>
            <div class="text-h4 text-weight-bolder vemag-text-primary q-mb-sm">Aguardando O.P.</div>
            <div class="text-subtitle1 text-grey-7 q-mb-lg">A máquina está parada.<br>Selecione uma opção:</div>
            
            <div class="column q-gutter-y-md">
                <q-btn 
                    push rounded 
                    color="blue-grey-9" text-color="white"
                    class="full-width shadow-3" 
                    size="18px" 
                    padding="md"
                    icon="list_alt" 
                    label="SELECIONAR DA LISTA" 
                    @click="openOpListDialog" 
                />

                <div class="text-caption text-grey-5">- OU -</div>

                <q-btn 
                    push rounded 
                    class="vemag-bg-primary text-white full-width shadow-4" 
                    size="18px" 
                    padding="md"
                    icon="photo_camera" 
                    label="LER QR CODE" 
                    @click="simulateOpScan" 
                />
            </div>
          </q-card>
        </div>

        <div v-else class="col row q-col-gutter-md items-stretch content-stretch">
  
  <div class="col-12 col-md-8 column no-wrap full-height q-gutter-y-md">
    
    <q-card class="col column relative-position overflow-hidden shadow-6 bg-white" style="border-radius: 20px; border-left: 10px solid #008C7A;">
      
      <div class="col-auto relative-position bg-vemag-gradient text-white q-pa-lg shadow-3">
          <q-img :src="customOsBackgroundImage" class="absolute-full opacity-10" fit="cover" />
          
          <div class="row items-center justify-between relative-position z-top">
              <div class="col-grow">
                  <div class="row items-center q-gutter-x-sm q-mb-xs">
                      <q-badge color="orange-10" class="text-bold shadow-2 q-px-sm" label="PRODUÇÃO" />
                    <q-badge outline color="white" class="text-bold" :label="`OP #${productionStore.activeOrder?.code || '---'}`" />
                    <q-chip v-if="productionStore.activeOrder?.drawing" dense square color="blue-grey-9" text-color="white" icon="architecture" size="sm">
                      DESENHO: {{ productionStore.activeOrder.drawing }}
                    </q-chip>
                  </div>
                  <div class="text-h4 text-weight-bolder ellipsis q-mt-sm">{{ productionStore.activeOrder.part_name }}</div>
                  <div class="text-subtitle2 text-grey-3 q-mt-xs">Cód. Item: <span class="text-white text-bold">{{ productionStore.activeOrder.part_code }}</span></div>
              </div>

                      <div class="column items-end q-gutter-y-xs">
                          <div class="row items-center bg-black-transparent q-px-md q-py-sm rounded-borders shadow-1">
                  <div class="column items-end q-mr-md">
                      <div class="text-overline text-grey-4" style="line-height: 1;">META TOTAL</div>
                      <div class="text-h5 text-weight-bolder">
                        {{ productionStore.activeOrder.produced_quantity }} 
                        <span class="text-subtitle1 text-grey-5">/ {{ productionStore.activeOrder.target_quantity }} {{ productionStore.activeOrder.uom }}</span>
                      </div>
                  </div>
                              <q-circular-progress
                      show-value font-size="12px"
                      :value="((productionStore.activeOrder.produced_quantity || 0) / (productionStore.activeOrder.target_quantity || 1)) * 100"
                      size="55px" :thickness="0.25" color="orange-5" track-color="grey-9" class="text-white text-bold shadow-2"
                  >
                      {{ Math.round(((productionStore.activeOrder.produced_quantity || 0) / (productionStore.activeOrder.target_quantity || 1)) * 100) }}%
                  </q-circular-progress>
                          </div>
                          <q-btn 
                              push color="blue-grey-9" text-color="white" 
                              icon="image" label="DESENHO" 
                              size="sm" padding="xs sm"
                              @click="openDrawing" 
                          />
                      </div>
                  </div>
              </div>

              <div class="col-auto bg-grey-2 q-px-md q-py-sm border-bottom-light row items-center justify-between" v-if="productionStore.currentActiveStep">
    <div class="row items-center">
        <div class="text-subtitle1 text-grey-7 q-mr-sm text-weight-bold">#{{ productionStore.currentActiveStep.seq }}</div>
        <div class="text-h6 text-weight-bold ellipsis" style="line-height: 1.1;">{{ productionStore.currentActiveStep.name }}</div>
    </div>
    <q-chip square dense color="blue-grey-9" text-color="white" icon="precision_manufacturing" :label="productionStore.currentActiveStep.resource" class="text-caption text-weight-bold" />
</div>

<div class="text-dark bg-grey-1 q-pa-md rounded-borders" 
    style="white-space: pre-wrap; font-size: 1.3rem; line-height: 1.6; border: 2px dashed #008C7A; min-height: 250px; font-family: monospace;">   
   <div class="text-weight-bold text-primary q-mb-sm">
      <q-icon name="menu_book" size="sm" /> INSTRUÇÕES DE TRABALHO:
   </div>

   {{ productionStore.currentActiveStep?.description || 'Carregando instruções técnicas do SAP...' }}
</div>

<div class="row justify-between items-center q-mt-auto q-pt-md">
   <div class="text-caption text-grey-7">
      <q-icon name="info" /> 
      <strong class="text-dark">{{}}</strong>
   </div>
   
   <q-chip outline color="primary" icon="timer">
      Tempo Est: <strong>{{ productionStore.currentActiveStep?.timeEst || 0 }}h</strong>
   </q-chip>
</div>

              <q-separator />
              
              <q-card-actions align="between" class="col-auto q-pa-sm bg-grey-1">
                  <div class="row q-gutter-x-sm col-8">
                    <q-btn 
                       push color="white" text-color="primary" 
                       icon="arrow_back" label="ANTERIOR" 
                       size="md" class="col-grow shadow-1"
                       @click="prevStepView" 
                       :disable="viewedStepIndex === 0" 
                    />
                    <q-btn 
                       push color="primary" text-color="white" 
                       icon-right="arrow_forward" label="PRÓXIMO" 
                       size="md" class="col-grow shadow-2"
                       @click="nextStepView" 
                       :disable="!productionStore.activeOrder.steps || viewedStepIndex === productionStore.activeOrder.steps.length - 1" 
                    />
                  </div>

                  <q-btn 
                    flat color="negative" icon="delete_outline" 
                    label="Refugo" 
                    size="md"
                    class="bg-red-1"
                    @click="productionStore.addProduction(1, true)"
                  />
              </q-card-actions>
            </q-card>
          </div>

          <div class="col-12 col-md-4 column no-wrap full-height justify-between">
            
            <q-card class="col-auto bg-white text-center q-py-sm relative-position shadow-3" style="border-radius: 16px;">
               <div class="row items-center justify-center q-gutter-x-sm">
                  <q-icon name="timer" class="vemag-text-secondary" size="24px" />
                  <div class="text-subtitle1 vemag-text-primary text-uppercase font-weight-bold">
                    Tempo no Estado
                  </div>
               </div>
               <div class="text-h4 text-weight-bolder font-monospace q-my-xs text-dark">{{ elapsedTime }}</div>
               <q-linear-progress stripe query :class="statusTextClass" size="6px" class="q-mt-xs absolute-bottom" />
            </q-card>

            <div class="col relative-position q-mb-sm q-mt-sm">
               <q-btn 
                  class="fit shadow-6 hover-scale-producing" 
                  :class="getButtonClass" 
                  push :loading="isLoadingAction"
                  style="border-radius: 20px;"
                  @click="handleMainButtonClick"
               >
                  <div class="column items-center justify-center full-height">
                    <q-icon size="60px" :name="isPaused ? 'play_arrow' : (normalizedStatus === 'EM OPERAÇÃO' ? 'pause_circle' : 'play_circle_filled')" />
                    
                    <div class="text-h4 text-weight-bolder q-mt-sm">
                        {{ isPaused ? 'RETOMAR' : (normalizedStatus === 'EM OPERAÇÃO' ? 'PAUSAR' : 'INICIAR') }}
                    </div>
                    
                    <div class="text-subtitle2 text-uppercase letter-spacing-1 opacity-80 q-mt-xs">
                        {{ isPaused ? 'VOLTAR A PRODUZIR' : (normalizedStatus === 'EM OPERAÇÃO' ? 'REGISTRAR PARADA' : 'INICIAR OPERAÇÃO') }}
                    </div>
                  </div>
               </q-btn>
            </div>

            <div class="col-auto row q-gutter-x-sm q-mb-sm" style="height: 80px;">
               <q-btn 
  class="col shadow-3 hover-scale"
  :class="productionStore.isInSetup ? 'bg-purple-9 text-white' : 'bg-blue-grey-2 text-blue-grey-9'"
  push style="border-radius: 16px;" 
  :loading="isLoadingAction"
  @click="handleSetupClick"
>
  <div class="column items-center justify-center">
      <q-icon :name="productionStore.isInSetup ? 'check_circle' : 'build'" size="28px" class="q-mb-xs" />
      
      <div class="text-subtitle1 text-weight-bold">
          {{ productionStore.isInSetup ? 'FIM SETUP' : 'SETUP' }}
      </div>

      <div v-if="productionStore.isInSetup" class="text-caption text-weight-bold bg-black-transparent q-px-sm rounded-borders q-mt-xs">
          {{ elapsedTime }}
      </div>
  </div>
</q-btn>
               <q-btn 
                  class="col shadow-3 hover-scale vemag-bg-secondary text-white"
                  push style="border-radius: 16px;"
                  @click="isAndonDialogOpen = true"
               >
                  <div class="column items-center justify-center">
                     <q-icon name="notifications_active" size="28px" class="q-mb-xs" />
                     <div class="text-subtitle1 text-weight-bold">AJUDA</div>
                  </div>
               </q-btn>
            </div>

            <div class="col-auto">
               <q-btn 
                  class="full-width shadow-4" color="red-10" text-color="white"
                  push size="18px" icon="stop_circle" label="FINALIZAR O.P."
                  style="border-radius: 16px; min-height: 60px;"
                  @click="confirmFinishOp"
               />
            </div>
          </div>
        </div>
      </q-page>
    </q-page-container>

    <q-dialog v-model="showOpList" maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card>
        <q-bar class="vemag-bg-primary text-white">
          <q-icon name="list" />
          <div class="text-h6 q-ml-sm">Ordens de Produção Liberadas (SAP)</div>
          <q-space />
          <q-btn dense flat icon="close" v-close-popup />
        </q-bar>

        <q-card-section class="q-pa-none">
          <q-table
            :rows="openOps"
            :columns="opColumns"
            row-key="op_number"
            :loading="loadingOps"
            flat
            bordered
            separator="cell"
          >
            <template v-slot:body="props">
              <q-tr @click="selectOp(props.row)" class="cursor-pointer hover-bg-grey-3">
                <q-td key="op_number" :props="props">
                  <div class="text-weight-bold text-subtitle1">{{ props.row.op_number }}</div>
                  <div class="text-caption text-grey-7" v-if="props.row.custom_ref">Ref: {{ props.row.custom_ref }}</div>
                </q-td>
                <q-td key="part_name" :props="props">
                  <div class="text-weight-medium">{{ props.row.part_name }}</div>
                  <div class="text-caption text-blue-grey">{{ props.row.item_code }}</div>
                </q-td>
                <q-td key="planned_qty" :props="props" class="text-center text-weight-bold">
                  {{ props.row.planned_qty }} {{ props.row.uom }}
                </q-td>
                <q-td key="action" :props="props" class="text-center">
                  <q-btn round color="secondary" icon="arrow_forward" size="sm" />
                </q-td>
              </q-tr>
            </template>
            <template v-slot:no-data>
                <div class="full-width row flex-center q-pa-md text-grey">
                    <q-icon name="warning" size="sm" class="q-mr-sm" />
                    Nenhuma O.P. liberada encontrada no SAP.
                </div>
            </template>
          </q-table>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isDrawingDialogOpen" maximized transition-show="slide-up" transition-hide="slide-down">
        <q-card class="bg-grey-10 text-white column">
            <q-bar class="bg-grey-9 q-pa-sm z-top" style="height: 60px;">
                <q-icon name="picture_as_pdf" size="24px" />
                <div class="text-h6 q-ml-md">
                    Desenho: {{ productionStore.activeOrder?.part_code }}
                </div>
                <q-space />
                <q-btn flat icon="refresh" label="Recarregar" @click="openDrawing" class="q-mr-sm" />
                <q-btn dense flat icon="close" size="20px" v-close-popup />
            </q-bar>

            <q-card-section class="col q-pa-none relative-position bg-grey-3">
                <iframe 
                    v-if="drawingUrl"
                    :src="drawingUrl" 
                    class="fit" 
                    style="border: none;"
                ></iframe>
                <div v-else class="absolute-full flex flex-center text-grey-8">
                    Carregando visualizador...
                </div>
            </q-card-section>
        </q-card>
    </q-dialog>

    <q-dialog v-model="isStopDialogOpen" persistent maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card class="bg-grey-2 column">
        <q-toolbar class="bg-white text-dark q-py-md shadow-2 z-top">
          <q-toolbar-title class="text-weight-bold text-h6 row items-center">
            <q-icon name="warning" color="warning" size="30px" class="q-mr-md"/> 
            SELECIONE O MOTIVO
          </q-toolbar-title>
          <q-btn flat round icon="close" size="lg" v-close-popup />
        </q-toolbar>
        
        <q-card-section class="col column q-pa-none">
            <div class="q-pa-md">
               <q-input v-model="stopSearch" outlined bg-color="white" placeholder="Pesquisar..." class="text-subtitle1" dense autofocus clearable>
                  <template v-slot:prepend><q-icon name="search" /></template>
               </q-input>
            </div>
            <div class="col scroll q-px-md q-pb-md">
               <div class="row q-col-gutter-md">
                  <div v-for="(reason, idx) in filteredStopReasons" :key="idx" class="col-12 col-sm-6 col-md-4">
    <q-btn 
      flat 
      bordered
      class="full-width reason-card" 
      :class="{ 'special-active': reason.isSpecial }"
      @click="handleSapPause(reason)"
    >
      <div class="row items-center no-wrap full-width q-pa-sm">
        <q-avatar 
          size="48px"
          :color="reason.code === '111' ? 'blue-8' : (reason.requiresMaintenance ? 'red-8' : 'grey-3')" 
          :text-color="reason.requiresMaintenance || reason.code === '111' ? 'white' : 'grey-9'"
          :class="{ 'pulse-animation': reason.isSpecial }"
        >
          <q-icon :name="reason.code === '111' ? 'sync_alt' : (reason.requiresMaintenance ? 'engineering' : 'pause')" size="28px" />
        </q-avatar>

        <div class="column q-ml-md text-left">
          <div class="text-subtitle1 text-weight-bold lh-tight" :class="reason.isSpecial ? 'text-dark' : 'text-grey-9'">
            {{ reason.label }}
          </div>
          <div class="text-caption text-grey-6">Cód: {{ reason.code }}</div>
        </div>
      </div>
    </q-btn>
  </div>
               </div>
            </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isMaintenanceConfirmOpen" persistent transition-show="slide-up" transition-hide="slide-down">
  <q-card class="maintenance-card shadow-24">
    <q-card-section class="bg-red-10 text-white row items-center q-py-lg">
      <q-avatar icon="engineering" color="white" text-color="red-10" size="50px" class="q-mr-md shadow-3" />
      <div class="column">
        <div class="text-h5 text-weight-bolder uppercase letter-spacing-1">Registrar Quebra</div>
        <div class="text-caption opacity-80">A máquina será bloqueada e uma O.M. será aberta.</div>
      </div>
      <q-space />
      <q-btn icon="close" flat round dense v-close-popup @click="cancelMaintenanceSelection" />
    </q-card-section>

    <q-card-section class="q-pa-lg">
      <div class="text-overline text-grey-7 q-mb-sm">Onde está o problema?</div>
      <div class="row q-col-gutter-sm q-mb-lg">
        <div v-for="opt in subReasonOptions" :key="opt.value" class="col-6 col-sm-4">
          <q-btn 
            flat 
            bordered 
            class="full-width sub-reason-btn" 
            :class="{ 'sub-reason-active': maintenanceSubReason === opt.value }"
            @click="maintenanceSubReason = opt.value"
          >
            <div class="column items-center">
              <q-icon :name="opt.icon" size="24px" class="q-mb-xs" />
              <div class="text-caption text-weight-bold">{{ opt.label }}</div>
            </div>
          </q-btn>
        </div>
      </div>

      <div class="text-overline text-grey-7 q-mb-sm">Descreva o que aconteceu:</div>
      <q-input
        v-model="maintenanceNote"
        filled
        type="textarea"
        placeholder="Ex: Mangueira de óleo estourou no eixo X..."
        bg-color="grey-2"
        rows="3"
        class="text-subtitle1"
      />
    </q-card-section>

    <q-card-actions align="between" class="q-px-lg q-pb-lg">
      <q-btn 
        flat 
        label="CANCELAR" 
        color="grey-7" 
        size="lg" 
        @click="cancelMaintenanceSelection" 
      />
      <q-btn 
        push 
        rounded
        label="ABRIR O.M. AGORA" 
        color="red-10" 
        icon-right="send"
        size="lg" 
        class="q-px-xl text-weight-bolder" 
        @click="triggerCriticalBreakdown" 
      />
    </q-card-actions>
  </q-card>
</q-dialog>

    <q-dialog v-model="isShiftChangeDialogOpen" persistent>
      <q-card class="q-pa-md text-center" style="width: 400px; border-radius: 16px;">
        <q-icon name="groups" size="60px" color="primary" class="q-mb-sm" />
        <div class="text-h5 text-weight-bold">Troca de Turno</div>
        <div class="text-subtitle1 text-grey-8 q-my-md">A máquina vai parar ou o próximo operador assume imediatamente?</div>
        
        <div class="column q-gutter-y-md">
           <q-btn 
              push color="positive" size="lg" icon="autorenew" 
              label="CONTINUA RODANDO" 
              @click="executeShiftChange(true)" 
           />
           <div class="text-caption text-grey">O apontamento atual será fechado e a OP ficará aguardando o próximo login.</div>
           
           <q-separator />
           
           <q-btn 
              flat color="negative" icon="pause" 
              label="VAI PARAR A MÁQUINA" 
              @click="executeShiftChange(false)" 
           />
        </div>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isAndonDialogOpen" transition-show="scale" transition-hide="scale">
      <q-card style="width: 700px; max-width: 95vw; border-radius: 20px;">
        <q-card-section class="vemag-bg-primary text-white row items-center justify-between q-pa-md">
          <div class="text-h6 text-weight-bold row items-center">
              <q-icon name="campaign" size="30px" class="q-mr-sm" />
              Central de Ajuda (Andon)
          </div>
          <q-btn icon="close" flat round size="md" v-close-popup />
        </q-card-section>
        
        <q-card-section class="q-pa-lg">
          <div class="text-subtitle1 q-mb-md vemag-text-primary text-weight-bold">Qual setor você precisa chamar?</div>
          
          <div class="row q-col-gutter-md">
            <div v-for="opt in andonOptions" :key="opt.label" class="col-6 col-md-4">
              <q-btn 
                push 
                class="full-width full-height column flex-center q-pa-md shadow-3 hover-scale" 
                :class="`bg-${opt.color} text-white`" 
                style="border-radius: 16px; min-height: 100px;" 
                @click="confirmAndonCall(opt.label)"
              >
                <q-icon :name="opt.icon" size="36px" class="q-mb-sm" />
                <div class="text-subtitle1 text-weight-bold">{{ opt.label }}</div>
              </q-btn>
            </div>
          </div>

          <div class="q-mt-lg">
            <q-input 
                v-model="andonNote" 
                outlined 
                label="Observação (Opcional)" 
                placeholder="Ex: Falta parafuso M5"
                dense 
                class="text-subtitle1" 
                bg-color="grey-1" 
            />
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useProductionStore } from 'stores/production-store';
import { storeToRefs } from 'pinia';
import { ProductionService } from 'src/services/production-service';
import { useAuthStore } from 'stores/auth-store';
import { api } from 'boot/axios'; // IMPORTADO PARA USAR NA URL DO DESENHO

// --- IMPORTAÇÕES DE DADOS ---
import { findBestStepIndex } from 'src/data/sap-operations';
import { getOperatorName } from 'src/data/operators'; 
import { getSapOperation, SAP_OPERATIONS_MAP } from 'src/data/sap-operations'; 
import { SAP_STOP_REASONS } from 'src/data/sap-stops';
import type { SapStopReason } from 'src/data/sap-stops';
import { ANDON_OPTIONS } from 'src/data/andon-options';

const router = useRouter();
const $q = useQuasar();
const productionStore = useProductionStore();
const authStore = useAuthStore();
const { activeOrder } = storeToRefs(productionStore); 
const isShiftChangeDialogOpen = ref(false); // NOVO
const logoPath = ref('/Logo-Oficial.png');
const isLoadingAction = ref(false);
const maintenanceSubReason = ref('Mecânica'); // Padrão
const maintenanceNote = ref('');
const subReasonOptions = [
  { label: 'Falha Mecânica', value: 'Mecânica', icon: 'settings' },
  { label: 'Falha Elétrica', value: 'Elétrica', icon: 'bolt' },
  { label: 'Hidráulica / Vazamento', value: 'Hidráulica', icon: 'water_drop' },
  { label: 'Pneumática / Ar', value: 'Pneumática', icon: 'air' },
  { label: 'Erro de Software / CNC', value: 'Software', icon: 'terminal' }
];
const customOsBackgroundImage = ref('/a.jpg');
const opNumberToSend = computed(() => {
  if (!productionStore.activeOrder) return '';
  
  const order = productionStore.activeOrder;

  // CENÁRIO 1: Ordem de Serviço (O.S.)
  // Enviamos o código completo (ex: OS-4595-1). 
  // O backend Python já está programado para extrair apenas o "4595"
  if (order.is_service) {
    return String(order.code); 
  }

  // CENÁRIO 2: Ordem de Produção (O.P.)
  // Enviamos o custom_ref que contém o formato esperado pelo SAP (ex: 4152/0)
  // Se por acaso estiver vazio, usamos o code como fallback.
  return order.custom_ref || order.code;
});
// --- Estados ---
const isPaused = ref(false);
const currentPauseObj = ref<{
  startTime: Date;
  reasonCode: string;
  reasonLabel: string;
} | null>(null);

const isStopDialogOpen = ref(false);
const isAndonDialogOpen = ref(false);
const isMaintenanceConfirmOpen = ref(false); // NOVO DIALOGO
const isDrawingDialogOpen = ref(false);
const drawingUrl = ref(''); // NOVA URL DINÂMICA
const showOpList = ref(false);
const loadingOps = ref(false);

const stopSearch = ref('');
const statusStartTime = ref(new Date());
const currentTime = ref(new Date());
let timerInterval: ReturnType<typeof setInterval>;
const andonNote = ref('');

// Importando opções do Andon
const andonOptions = ANDON_OPTIONS; 

// --- Tabela ---
const openOps = ref([]);
const opColumns = [
  { name: 'op_number', label: 'OP / Ref', align: 'left', field: 'op_number', sortable: true },
  { name: 'part_name', label: 'Produto / Item', align: 'left', field: 'part_name', sortable: true },
  { name: 'planned_qty', label: 'Qtd', align: 'center', field: 'planned_qty' },
  { name: 'action', label: 'Selecionar', align: 'center' }
];

// --- Navigation ---
const viewedStepIndex = ref(0);

const currentViewedStep = computed(() => {
    // Se a OP ativa tem passos carregados do SAP
    if (activeOrder.value?.steps && activeOrder.value.steps.length > 0) {
        return activeOrder.value.steps[viewedStepIndex.value];
    }
    // Caso contrário, mostra um estado de "Carregando" ou "Vazio"
    return { 
        seq: '---', 
        name: 'Aguardando Roteiro', 
        description: 'Buscando operações no SAP...', 
        resource: '---', 
        timeEst: 0 
    };
});

function nextStepView() {
    if (activeOrder.value?.steps && viewedStepIndex.value < activeOrder.value.steps.length - 1) {
        viewedStepIndex.value++;
    }
}

function cancelMaintenanceSelection() {
  isMaintenanceConfirmOpen.value = false;
  maintenanceNote.value = '';
  maintenanceSubReason.value = 'Mecânica';
  currentPauseObj.value = null;
  isStopDialogOpen.value = true; // Reabre a lista principal
}

function prevStepView() {
    if (viewedStepIndex.value > 0) {
        viewedStepIndex.value--;
    }
}

// --- Computeds Visuais ---
const elapsedTime = computed(() => {
   const diff = Math.max(0, Math.floor((currentTime.value.getTime() - statusStartTime.value.getTime()) / 1000));
   const h = Math.floor(diff / 3600).toString().padStart(2, '0');
   const m = Math.floor((diff % 3600) / 60).toString().padStart(2, '0');
   const s = (diff % 60).toString().padStart(2, '0');
   return `${h}:${m}:${s}`;
});
const timeDisplay = computed(() => currentTime.value.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }));

const normalizedStatus = computed(() => {
    // 1. Prioridade para a flag de Setup da Store
    if (productionStore.isInSetup) return 'MANUTENÇÃO';

    const raw = activeOrder.value?.status || '';
    const s = String(raw).trim().toUpperCase();
    
    // Status da Máquina (para pegar Maintenance do banco)
    const m = String(productionStore.currentMachine?.status || '').toUpperCase();

    if (['RUNNING', 'EM USO', 'EM OPERAÇÃO', 'IN_USE'].includes(s)) return 'EM OPERAÇÃO';
    
    // Agora reconhece SETUP e MANUTENÇÃO
    if (['SETUP', 'MAINTENANCE', 'EM MANUTENÇÃO', 'MANUTENÇÃO'].includes(s) || 
        ['MAINTENANCE', 'EM MANUTENÇÃO', 'MANUTENÇÃO'].includes(m)) {
        return 'MANUTENÇÃO';
    }

    if (['PAUSED', 'PARADA', 'STOPPED', 'AVAILABLE', 'DISPONÍVEL'].includes(s)) return 'PARADA'; 
    
    return 'PARADA'; 
});
const displayStatus = computed(() => {
  if (productionStore.isInSetup) return 'EM PREPARAÇÃO (SETUP)';
  
  // --- MUDANÇA: Texto explícito "EM PAUSA" quando pausado manualmente ---
  if (isPaused.value) return 'EM PAUSA - ' + (currentPauseObj.value?.reasonLabel || '');
  
  const rawStatus = activeOrder.value?.status?.toUpperCase() || '';
  if (['AVAILABLE', 'DISPONÍVEL', 'PENDING'].includes(rawStatus)) {
      return 'AGUARDANDO INÍCIO'; // Sem tolerância, apenas status neutro
  }
  
  return normalizedStatus.value;
});

const statusBgClass = computed(() => {
  if (productionStore.isInSetup) return 'bg-purple-9 text-white';
  
  // --- MUDANÇA: Cor Laranja (Warning) para Pausa ---
  if (isPaused.value) return 'bg-orange-9 text-white'; 
  
  if (normalizedStatus.value === 'EM OPERAÇÃO') return 'bg-positive text-white';
  
  // Cor neutra para Aguardando
  return 'bg-blue-grey-9 text-white';
});

const statusTextClass = computed(() => {
    if (isPaused.value) return 'text-warning';
    if (normalizedStatus.value === 'EM OPERAÇÃO') return 'vemag-text-primary';
    return 'text-negative';
});

const statusIcon = computed(() => {
    if (productionStore.isInSetup) return 'build_circle';
    if (isPaused.value) return 'pause_circle_filled'; // Ícone de pausa preenchido
    if (normalizedStatus.value === 'EM OPERAÇÃO') return 'autorenew';
    return 'hourglass_empty';
});
const getButtonClass = computed(() => {
  if (isPaused.value) return 'bg-orange-9 text-white'; 
  if (normalizedStatus.value === 'EM OPERAÇÃO') return 'vemag-bg-primary text-white';
  return 'bg-blue-grey-10 text-white';
});

const filteredStopReasons = computed(() => {
   if (!stopSearch.value) return SAP_STOP_REASONS;
   const needle = stopSearch.value.toLowerCase();
   return SAP_STOP_REASONS.filter(r => r.label.toLowerCase().includes(needle));
});

function getCategoryColor(cat: string) { return 'blue-grey'; }
function resetTimer() { statusStartTime.value = new Date(); }

// --- Actions ---

async function openOpListDialog() {
  showOpList.value = true;
  loadingOps.value = true;
  try {
    openOps.value = await ProductionService.getOpenOrders();
  } catch (error) {
    console.error(error);
    $q.notify({ type: 'negative', message: 'Erro ao carregar OPs' });
  } finally {
    loadingOps.value = false;
  }
}

async function selectOp(op: any) {
  console.log(`🎯 [MES] Selecionando OP: ${op.op_number} - ${op.part_name}`);

  // 1. Configura o objeto inicial
  productionStore.activeOrder = {
    code: String(op.op_number),
    part_name: op.part_name,
    part_code: op.item_code,
    target_quantity: Number(op.planned_qty),
    uom: op.uom || 'pç',
    produced_quantity: 0,
    scrap_quantity: 0,
    status: 'PENDING',
    custom_ref: op.custom_ref || '',
    drawing: op.drawing || '',
    
    // ✅ ADIÇÃO RECOMENDADA: Flag explícita para o Frontend
    is_service: String(op.op_number).startsWith('OS-'),
    
    steps: op.steps || [] 
  };

  try {
    $q.loading.show({ 
      message: `Buscando roteiro técnico para ${op.op_number}...`,
      backgroundColor: 'teal-10'
    });

    // 2. Carrega detalhes do Backend (Garante que U_Instrucoes venha atualizado)
    await productionStore.loadOrderFromQr(String(op.op_number));
    
    // 3. Roteamento Inteligente (Mantido igual)
    if (productionStore.activeOrder?.steps && productionStore.activeOrder.steps.length > 0) {
      const myRes = productionStore.machineResource;
      const idx = findBestStepIndex(myRes, productionStore.activeOrder.steps);
      
      if (idx !== -1) {
        productionStore.currentStepIndex = idx;
        if (typeof viewedStepIndex !== 'undefined') {
          viewedStepIndex.value = idx;
        }
        console.log(`✅ [MES] Máquina identificada na etapa: ${productionStore.activeOrder.steps[idx].name}`);
      } else {
        productionStore.currentStepIndex = 0;
        console.warn("⚠️ [MES] Máquina não encontrada no roteiro. Iniciando na etapa 010.");
      }
    }

  } catch (error) {
    console.error("❌ [MES] Falha ao carregar roteiro:", error);
    $q.notify({ type: 'negative', message: 'Erro de comunicação com o SAP.' });
  } finally {
    showOpList.value = false;
    $q.loading.hide();
    if (typeof resetTimer === 'function') resetTimer();
  }
}
// --- FUNÇÃO PARA ABRIR O DESENHO (CORRIGIDA) ---
function openDrawing() {
  if (!productionStore.activeOrder?.part_code) {
      $q.notify({ type: 'warning', message: 'O.P. sem código de item definido.' });
      return;
  }

  const itemCode = productionStore.activeOrder.part_code;
  
  // URL dinâmica apontando para o backend Python (porta 8000 geralmente)
  // Ajuste a porta se necessário. Se estiver rodando tudo na mesma origem, use /api/v1/drawings
  const baseUrl = 'http://localhost:8000'; // ou api.defaults.baseURL
  drawingUrl.value = `${baseUrl}/drawings/${encodeURIComponent(itemCode)}?t=${new Date().getTime()}`;
  
  isDrawingDialogOpen.value = true;
}
async function handleMainButtonClick() {
  // CENÁRIO 1: RETOMAR (Pausa manual)
  if (isPaused.value) {
    await finishPauseAndResume();
    return;
  }

  // CENÁRIO 2: PAUSAR (Se já estiver produzindo)
  if (normalizedStatus.value === 'EM OPERAÇÃO') {
      isStopDialogOpen.value = true;
      return;
  }

  // --- CORREÇÃO: TRANSITANDO DE SETUP PARA PRODUÇÃO ---
  if (productionStore.isInSetup) {
    $q.loading.show({ message: 'Encerrando Setup e iniciando produção...' });
    
    try {
      const now = new Date();
      const startSetup = statusStartTime.value;
      
      let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
      if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
      
      const operatorName = getOperatorName(String(badge).trim());
      const machineRes = productionStore.machineResource || '4.02.01';
      
      // 1. Envia o fechamento do SETUP para o SAP (Motivo 52)
      const setupPayload = {
          op_number: '', 
          position: '', operation: '', operation_desc: '',    
          resource_code: machineRes,
          resource_name: productionStore.machineName,
          operator_name: operatorName,
          operator_id: String(badge),
          vehicle_id: productionStore.machineId || 0,
          start_time: startSetup.toISOString(),
          end_time: now.toISOString(),
          stop_reason: '52', 
          stop_description: 'Setup' 
      };
      
      await ProductionService.sendAppointment(setupPayload);
      
      // 2. Desativa a flag de Setup na Store
      // IMPORTANTE: toggleSetup sem enviar evento, pois enviaremos o RUNNING logo abaixo
      productionStore.activeOrder.status = 'PENDING'; 
      
    } catch (error) {
      console.error("Erro ao finalizar setup:", error);
      $q.notify({ type: 'negative', message: 'Falha ao encerrar setup no SAP.' });
      $q.loading.hide();
      return;
    }
  }
  
  // --- INICIAR PRODUÇÃO (Para novos inícios ou após Setup) ---
  isLoadingAction.value = true;
  try {
    // 1. Chama a ação da Store que envia o evento 'RUNNING'
    // Isso fecha a fatia de Setup/Idle e abre a de Produção no Banco Local
    await productionStore.startProduction();
    
    // 2. Atualiza os cronômetros visuais
    statusStartTime.value = new Date();
    isPaused.value = false;
    
    $q.notify({ type: 'positive', message: 'Produção Iniciada!', icon: 'play_arrow' });
  } catch (e) {
    console.error("Erro ao iniciar produção:", e);
    $q.notify({ type: 'negative', message: 'Erro ao registrar início de produção.' });
  } finally {
    isLoadingAction.value = false;
    $q.loading.hide();
  }
}

// --- LÓGICA DE SELEÇÃO DE MOTIVO (CRÍTICO) ---
function handleSapPause(stopReason: SapStopReason) {
  const now = new Date();
  
  currentPauseObj.value = {
    startTime: now,
    reasonCode: stopReason.code,
    reasonLabel: stopReason.label
  };

  // 1. DETECÇÃO DE TROCA DE TURNO
  if (stopReason.label.toLowerCase().includes('troca de turno') || stopReason.code === '111') {
      isStopDialogOpen.value = false;
      isShiftChangeDialogOpen.value = true; // Abre Dialog Pergunta
      return;
  }

  // 2. VERIFICAÇÃO CRÍTICA (QUEBRA)
  if (stopReason.requiresMaintenance) {
      isStopDialogOpen.value = false;
      isMaintenanceConfirmOpen.value = true; 
  } else {
      applyNormalPause();
  }
}
async function applyNormalPause() {
    isStopDialogOpen.value = false;
    isMaintenanceConfirmOpen.value = false;
    
    $q.loading.show({ message: 'Enviando produção e registrando parada...' });

    try {
        const now = new Date();
        const prodStart = statusStartTime.value;
        const reason = currentPauseObj.value;

        let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
        const machineRes = productionStore.machineResource || '4.02.01';

        // 1. FECHA PRODUÇÃO
        if (activeOrder.value?.code) {
            const prodPayload = {
                op_number: String(opNumberToSend.value),
                service_code: activeOrder.value.is_service ? activeOrder.value.part_code : '',
                position: currentViewedStep.value?.seq?.toString().padStart(3, '0') || '010',
                operation: '', // opcional aqui
                operation_desc: '',
                resource_code: machineRes,
                operator_id: String(badge),
                start_time: prodStart.toISOString(),
                end_time: now.toISOString(),
                stop_reason: '', 
                stop_description: ''
            };
            await ProductionService.sendAppointment(prodPayload);
        }

        // 2. REGISTRA PARADA
        const stopPayload = {
            op_number: '',
            resource_code: machineRes,
            operator_id: String(badge),
            start_time: now.toISOString(),
            end_time: now.toISOString(),
            stop_reason: reason?.reasonCode || '100',
            stop_description: reason?.reasonLabel || 'Pausa'
        };
        await ProductionService.sendAppointment(stopPayload);

        // Estado local
        isPaused.value = true;
        if (activeOrder.value) activeOrder.value.status = 'PAUSED';
        await productionStore.setMachineStatus('STOPPED'); 
        statusStartTime.value = new Date(); // Reinicia cronômetro para contar tempo da PAUSA

        $q.notify({ type: 'warning', message: 'Produção salva. Máquina em Pausa.' });
    } catch (error) {
        console.error("Erro ao pausar:", error);
    } finally {
        $q.loading.hide();
    }
}

function confirmPauseOnly() {
    applyNormalPause();
}


async function executeShiftChange(keepRunning: boolean) {
    isShiftChangeDialogOpen.value = false;
    const now = new Date();
    
    // Se o operador escolheu parar a máquina, tratamos como uma pausa normal
    if (!keepRunning) {
        // Configuramos o motivo manualmente para Troca de Turno
        currentPauseObj.value = {
            startTime: now,
            reasonCode: '111',
            reasonLabel: 'Troca de Turno'
        };
        void applyNormalPause();
        return;
    }

    $q.loading.show({ message: 'Processando Troca de Turno no SAP...' });

    try {
        let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
        if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
        
        const operatorName = getOperatorName(String(badge).trim());
        const machineRes = productionStore.machineResource || '4.02.01';
        
        // --- Cálculo de Etapa ---
        const rawSeq = currentViewedStep.value?.seq || (viewedStepIndex.value + 1) * 10;
        const stageStr = Math.floor(rawSeq / 10 * 10).toString().padStart(3, '0');
        const sapData = getSapOperation(stageStr);

        // 1. PRIMEIRO PASSO: FECHAR A O.P. (APONTAMENTO DE PRODUÇÃO)
        if (activeOrder.value?.code) {
            const prodPayload = {
                op_number: String(opNumberToSend.value), // Envia formatado (ex: 4152/0)
                service_code: activeOrder.value.is_service ? activeOrder.value.part_code : '',
                position: stageStr,
                operation: sapData.code || '',
                operation_desc: sapData.description || '',
                resource_code: machineRes,
                resource_name: productionStore.machineName,
                part_description: activeOrder.value.part_name || '',
                item_code: activeOrder.value.part_code || '',
                operator_name: operatorName,
                operator_id: String(badge),
                start_time: statusStartTime.value.toISOString(),
                end_time: now.toISOString(),
                stop_reason: '', // Sem motivo = Produção
                stop_description: ''
            };
            console.log("📤 [1/2] Fechando Produção (Troca Turno):", prodPayload);
            await ProductionService.sendAppointment(prodPayload);
        }

        // 2. SEGUNDO PASSO: CRIAR A ORDEM DE PARADA (APONTAMENTO DE RECURSO)
        const stopPayload = {
            op_number: '', // Parada de recurso não vincula O.P.
            service_code: '',
            position: '',
            operation: '',
            operation_desc: '',
            resource_code: machineRes,
            resource_name: productionStore.machineName,
            operator_name: operatorName,
            operator_id: String(badge),
            start_time: now.toISOString(),
            end_time: now.toISOString(), // Início e fim iguais registram o evento de parada
            stop_reason: '111', // Código SAP para Troca de Turno
            stop_description: 'Troca de Turno'
        };
        console.log("📤 [2/2] Registrando Parada (Troca Turno):", stopPayload);
        await ProductionService.sendAppointment(stopPayload);

        // Finalização local
        await productionStore.logoutOperator(undefined, true); // Mantém O.P. no cache
        await router.push({ name: 'machine-kiosk' });
        $q.notify({ type: 'positive', message: 'Turno encerrado e parada registrada.' });

    } catch (error) {
        console.error("Erro na Troca de Turno:", error);
        $q.notify({ type: 'negative', message: 'Erro ao sincronizar troca de turno com SAP.' });
    } finally {
        $q.loading.hide();
    }
}

// --- FUNÇÃO DE QUEBRA DE MÁQUINA (ABRIR O.M.) ---
async function triggerCriticalBreakdown() {
    if (!currentPauseObj.value) return;
    const finalDesc = `[${maintenanceSubReason.value}] ${maintenanceNote.value}`.trim();
    isMaintenanceConfirmOpen.value = false;
    $q.loading.show({ 
        message: '🚨 Processando Quebra e Finalizando O.P...', 
        backgroundColor: 'red-10'
    });

    try {
        const now = new Date();
        const productionStart = statusStartTime.value;
        const eventTime = now.toISOString();
        
        // --- DADOS COMUNS ---
        let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
        if (!badge && authStore.user?.employee_id && authStore.user.role !== 'admin') {
             badge = authStore.user.employee_id;
        }
        const operatorName = getOperatorName(String(badge).trim());
        const machineRes = productionStore.machineResource || '4.02.01';
        
        let resourceDescription = '';
        const foundEntry = Object.values(SAP_OPERATIONS_MAP).find(op => op.resourceCode === machineRes);
        if (foundEntry) resourceDescription = foundEntry.description;

        // =================================================================
        // PASSO 1: ENVIAR APONTAMENTO DE PRODUÇÃO (FINALIZAR A O.P.)
        // =================================================================
        
        if (activeOrder.value?.code) {
            // Recalcula dados da etapa atual para garantir precisão
            const rawSeq = currentViewedStep.value?.seq || (viewedStepIndex.value + 1) * 10;
            const cleanSeq = Math.floor(rawSeq / 10) * 10;
            const stageStr = cleanSeq.toString().padStart(3, '0'); 
            const sapData = getSapOperation(stageStr);


            const productionPayload = {
                op_number: String(opNumberToSend.value),
                position: stageStr,
                operation: sapData.code || '',
                operation_desc: sapData.description || '',
                part_description: activeOrder.value.part_name || '',
                item_code: activeOrder.value.part_code || '',
                service_code: '',
                
                resource_code: machineRes,
                resource_name: resourceDescription,
                operator_name: operatorName || '',
                operator_id: String(badge),
                vehicle_id: productionStore.machineId || 0,

                start_time: productionStart.toISOString(),
                end_time: eventTime,

                stop_reason: '', 
                stop_description: '' 
            };

            console.log("📤 [1/2] Enviando Produção Final (Pré-Quebra):", productionPayload);
            // MANTIDO: Envio manual para garantir o fechamento antes da quebra
            await ProductionService.sendAppointment(productionPayload);
        }

        // =================================================================
        // PASSO 2: ENVIAR APONTAMENTO DE PARADA (REGISTRAR A QUEBRA)
        // =================================================================
        
        const stopPayload = {
            op_number: '',
            position: '',
            operation: '',
            operation_desc: '',
            part_description: '',
            item_code: '',
            service_code: '',

            resource_code: machineRes,
            resource_name: resourceDescription,
            operator_name: operatorName || '',
            operator_id: String(badge),
            vehicle_id: productionStore.machineId || 0,

            start_time: eventTime,
            end_time: eventTime, // No SAP, início e fim iguais marcam o evento

            stop_reason: currentPauseObj.value.reasonCode,
            stop_description: currentPauseObj.value.reasonLabel
        };

        console.log("📤 [2/2] Enviando Registro de Quebra:", stopPayload);
        await ProductionService.sendAppointment(stopPayload);

        // =================================================================
        // PASSO 3: BLOQUEIO E LOGOUT
        // =================================================================

        // Atualiza status visual e banco local
        await productionStore.setMachineStatus('MAINTENANCE');
        
        // Finaliza sessão localmente
        await productionStore.finishSession();
        
        // Logout forçado com status de manutenção
        await productionStore.logoutOperator('MAINTENANCE');

        await router.push({ 
            name: 'machine-kiosk', 
            query: { state: 'maintenance' } 
        });
        
        $q.notify({ type: 'negative', icon: 'build', message: 'Máquina parada. O.M. solicitada.', timeout: 5000 });

    } catch (error) {
        console.error("Erro fatal:", error);
        $q.notify({ type: 'negative', message: 'Erro ao registrar quebra.' });
    } finally {
        $q.loading.hide();
    }
}

// --- FUNÇÃO DE FINALIZAR PAUSA NORMAL ---
async function finishPauseAndResume() {
  if (!currentPauseObj.value) return;
  
  $q.loading.show({ message: 'Enviando parada e retomando...' });
  
  try {
    const endTime = new Date(); // Hora da retomada
    const pauseStart = currentPauseObj.value.startTime; // Hora que a pausa começou
    
    // --- 1. DADOS PARA O APONTAMENTO DE PARADA ---
    let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
    if (!badge && authStore.user?.employee_id && authStore.user.role !== 'admin') badge = authStore.user.employee_id;
    const operatorName = getOperatorName(String(badge).trim());
    const machineRes = productionStore.machineResource || '4.02.01'; 
    let resourceDescription = '';
    const foundEntry = Object.values(SAP_OPERATIONS_MAP).find(op => op.resourceCode === machineRes);
    if (foundEntry) resourceDescription = foundEntry.description; 

    const stopPayload = {
      op_number: '', // Parada não tem OP no apontamento de Recurso (geralmente)
      position: '', operation: '', operation_desc: '', 
      part_description: '', item_code: '', service_code: '',
      
      resource_code: machineRes, 
      resource_name: resourceDescription, 
      operator_name: operatorName || '', 
      operator_id: String(badge),
      vehicle_id: productionStore.machineId || 0,
      
      start_time: pauseStart.toISOString(), 
      end_time: endTime.toISOString(),
      
      stop_reason: currentPauseObj.value.reasonCode, 
      stop_description: currentPauseObj.value.reasonLabel
    };

    // --- 2. ENVIA O APONTAMENTO DE PARADA PRO SAP ---
    console.log("📤 [RETOMADA] Enviando apontamento de parada:", stopPayload);
    await ProductionService.sendAppointment(stopPayload);

    // --- 3. REABRE A PRODUÇÃO (LOCAL E BACKEND) ---
    // Envia evento para o backend saber que voltou a rodar
    await productionStore.sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' });
    await productionStore.setMachineStatus('RUNNING'); 

    // Reseta visual
    isPaused.value = false;
    currentPauseObj.value = null;
    if (productionStore.activeOrder) {
        productionStore.activeOrder.status = 'RUNNING';
    }
    
    // Zera o relógio. O tempo começa a contar a partir de AGORA para a nova fatia de produção.
    statusStartTime.value = new Date(); 
    
    $q.notify({ type: 'positive', message: 'Parada registrada. Produção Iniciada!', icon: 'play_circle' });

  } catch (error) {
    console.error("Erro ao retomar:", error);
    $q.notify({ type: 'negative', message: 'Erro ao enviar parada para o SAP.' });
    // Destrava visualmente
    isPaused.value = false;
    statusStartTime.value = new Date();
  } finally { 
    $q.loading.hide(); 
  }
}



function confirmFinishOp() {
  let badge = productionStore.currentOperatorBadge;

  // Lógica de verificação de crachá (Mantida)
  if (!badge && authStore.user?.employee_id) {
      const role = authStore.user.role || '';
      if (role !== 'admin' && role !== 'manager') badge = authStore.user.employee_id;
  }

  if (!badge || badge.includes('@')) {
      $q.dialog({
        title: 'Identificação Obrigatória',
        message: 'Bipe seu crachá:',
        prompt: { model: '', type: 'text', isValid: val => val.length > 0 },
        cancel: true, persistent: true
      }).onOk(data => {
        productionStore.currentOperatorBadge = data;
        confirmFinishOp(); 
      });
      return; 
  }

  const operatorName = getOperatorName(String(badge).trim());

  $q.dialog({
    title: 'Finalizar O.P.',
    message: `Encerrar O.P. e liberar a máquina?`,
    cancel: true, persistent: true,
    ok: { label: 'Finalizar e Sair', color: 'negative', push: true }
  }).onOk(async () => {
     $q.loading.show({ message: 'Enviando ao SAP e Finalizando...' });
     
     try {
       const endTime = new Date();
       
       // --- 1. ENVIA O APONTAMENTO FINAL PARA O SAP (IGUAL AO PAUSAR) ---
       // Recalcula dados da etapa
       const rawSeq = currentViewedStep.value?.seq || (viewedStepIndex.value + 1) * 10;
       const cleanSeq = Math.floor(rawSeq / 10) * 10;
       const stageStr = cleanSeq.toString().padStart(3, '0'); 
       const sapData = getSapOperation(stageStr);


       // Dados da máquina/operador
       const machineRes = productionStore.machineResource || sapData.resourceCode || '4.02.01';
       let resourceDescription = sapData.resourceName || '';
       const foundEntry = Object.values(SAP_OPERATIONS_MAP).find(op => op.resourceCode === machineRes);
       if (foundEntry) resourceDescription = foundEntry.description;

       const payload = {
         op_number: String(opNumberToSend.value),
         service_code: '', 
         position: stageStr, 
         operation: sapData.code || '', 
         operation_desc: sapData.description || '',
         resource_code: machineRes, 
         resource_name: resourceDescription,
         part_description: activeOrder.value?.part_name || '', 
         operator_name: operatorName || '', 
         operator_id: String(badge),
         start_time: statusStartTime.value.toISOString(),
         end_time: endTime.toISOString(),
         item_code: activeOrder.value?.part_code || '', 
         stop_reason: '', 
         vehicle_id: productionStore.machineId || 0
       };

       console.log("📤 [FINALIZAR] Enviando O.P. final:", payload);
       await ProductionService.sendAppointment(payload);

       // --- 2. ATUALIZAÇÕES DO SISTEMA (O QUE FALTAVA) ---
       
       // a) Encerra a sessão no banco de dados
       await productionStore.finishSession();
       
       // b) Define status explicitamente como DISPONÍVEL (AVAILABLE)
       await productionStore.setMachineStatus('AVAILABLE');

       // c) Faz Logout do Operador
       await productionStore.logoutOperator();

       // d) Redireciona para a tela de Kiosk (Descanso de Tela)
       await router.push({ name: 'machine-kiosk' });

       $q.notify({ type: 'positive', message: 'O.P. Finalizada. Máquina Disponível!' });

     } catch (error) {
       console.error("Erro SAP:", error);
       $q.notify({ type: 'negative', message: 'Erro ao registrar no SAP.' });
     } finally {
       $q.loading.hide();
     }
  });
}

function handleLogout() {
  $q.dialog({ title: 'Sair', message: 'Fazer logoff?', cancel: true }).onOk(() => {
    void (async () => {
        await productionStore.logoutOperator();
        await router.push({ name: 'machine-kiosk' });
    })();
  });
}

async function simulateOpScan() {
  await productionStore.loadOrderFromQr('OP-TESTE-4500');
  resetTimer();
}

async function confirmAndonCall(sector: string) {
    isAndonDialogOpen.value = false;
    await productionStore.triggerAndon(sector, andonNote.value);
    andonNote.value = '';
}



async function handleSetupClick() {
  // --- CENÁRIO 1: FINALIZAR SETUP E REABRIR A O.P. AUTOMATICAMENTE ---
  if (productionStore.isInSetup) {
      $q.dialog({
          title: 'Finalizar Setup',
          message: 'Deseja encerrar a preparação e VOLTAR A PRODUZIR agora?',
          cancel: true,
          persistent: true,
          ok: { label: 'Finalizar e Iniciar O.P.', color: 'positive', push: true }
      }).onOk(async () => {
          $q.loading.show({ message: 'Enviando Setup e reiniciando produção...' });
          isLoadingAction.value = true;
          
          try {
              const now = new Date();
              const startSetup = statusStartTime.value; 

              // 1. Prepara dados comuns
              let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
              if (!badge && authStore.user?.employee_id && authStore.user.role !== 'admin') badge = authStore.user.employee_id;
              const operatorName = getOperatorName(String(badge).trim());
              const machineRes = productionStore.machineResource || '4.02.01';
              
              let resourceDescription = '';
              const foundEntry = Object.values(SAP_OPERATIONS_MAP).find(op => op.resourceCode === machineRes);
              if (foundEntry) resourceDescription = foundEntry.description;

              // 2. Envia o Apontamento de SETUP finalizado para o SAP (Motivo 52)
              const setupPayload = {
                  op_number: '', // Setup não vincula OP no recurso
                  position: '', operation: '', operation_desc: '',    
                  part_description: '', item_code: '', service_code: '',
                  resource_code: machineRes,
                  resource_name: resourceDescription,
                  operator_name: operatorName || '',
                  operator_id: String(badge),
                  vehicle_id: productionStore.machineId || 0,
                  start_time: startSetup.toISOString(),
                  end_time: now.toISOString(),
                  stop_reason: '52', // Código de Setup configurado no seu SAP
                  stop_description: 'Setup' 
              };
              await ProductionService.sendAppointment(setupPayload);

              // 3. Desativa o modo Setup na Store
              await productionStore.toggleSetup();

              // 4. AUTOMAÇÃO: Abre novamente o apontamento da O.P. no Servidor
              const step = currentViewedStep.value; 
              const startPayload = {
                op_number: String(productionStore.activeOrder.code),
                step_seq: String(step.seq || ''),
                machine_id: Number(productionStore.machineId),
                operator_badge: String(badge)
              };

              const response = await api.post('/production/session/start', startPayload);
              
              if (response.data.status === 'success') {
                statusStartTime.value = new Date();
                if (activeOrder.value) activeOrder.value.status = 'RUNNING';
                await productionStore.setMachineStatus('RUNNING');
                $q.notify({ type: 'positive', message: 'Setup registrado. Produção retomada!', icon: 'play_arrow' });
              }

          } catch (error) {
              console.error("Erro na transição de Setup:", error);
              $q.notify({ type: 'negative', message: 'Erro ao processar fim de Setup.' });
          } finally {
              $q.loading.hide();
              isLoadingAction.value = false;
          }
      });
  } 
  
  // --- CENÁRIO 2: INICIAR SETUP (FECHA A O.P. SE ESTIVER RODANDO) ---
  else {
      isLoadingAction.value = true;
      try {
          const now = new Date();
          
          // Se a máquina estiver EM OPERAÇÃO, finalizamos a fatia de produção antes do setup
          if (normalizedStatus.value === 'EM OPERAÇÃO' && activeOrder.value?.code) {
              $q.loading.show({ message: 'Encerrando produção para iniciar Setup...' });
              
              const productionStart = statusStartTime.value;
              let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
              if (!badge && authStore.user?.employee_id && authStore.user.role !== 'admin') badge = authStore.user.employee_id;
              
              const operatorName = getOperatorName(String(badge).trim());
              const machineRes = productionStore.machineResource || '4.02.01';
              const rawSeq = currentViewedStep.value?.seq || (viewedStepIndex.value + 1) * 10;
              const stageStr = Math.floor(rawSeq / 10 * 10).toString().padStart(3, '0');
              const sapData = getSapOperation(stageStr);

              const productionPayload = {
                  op_number: String(opNumberToSend.value), // Usa o número formatado 4152/0
                  position: stageStr,
                  operation: sapData.code || '',
                  operation_desc: sapData.description || '',
                  part_description: activeOrder.value.part_name || '',
                  item_code: activeOrder.value.part_code || '',
                  service_code: '',
                  resource_code: machineRes,
                  resource_name: sapData.description || '',
                  operator_name: operatorName || '',
                  operator_id: String(badge),
                  vehicle_id: productionStore.machineId || 0,
                  start_time: productionStart.toISOString(),
                  end_time: now.toISOString(),
                  stop_reason: '', 
                  stop_description: '' 
              };
              
              await ProductionService.sendAppointment(productionPayload);
          }

          // Ativa o modo Setup e altera status visual
          await productionStore.toggleSetup();
          await productionStore.setMachineStatus('MAINTENANCE'); 
          statusStartTime.value = new Date(); // Inicia cronômetro do Setup
          
          $q.notify({ type: 'info', message: 'Produção salva. Modo Setup Iniciado.', icon: 'build' });
      } catch (e) {
          console.error("Erro ao iniciar setup:", e);
          $q.notify({ type: 'negative', message: 'Erro ao iniciar Setup.' });
      } finally {
          $q.loading.hide();
          isLoadingAction.value = false;
      }
  }
}
let scanBuffer = '';
let scanTimeout: any = null;

async function handleGlobalKeydown(event: KeyboardEvent) {
  if ((event.target as HTMLElement).tagName === 'INPUT') return;

  if (event.key === 'Enter') {
      if (scanBuffer.length > 2) {
          const scannedBadge = scanBuffer.trim();
          $q.loading.show({ message: `Autenticando...` });
          try {
              await authStore.loginByBadge(scannedBadge);
              if (authStore.user?.employee_id) {
                  productionStore.currentOperatorBadge = authStore.user.employee_id;
                  $q.notify({ type: 'positive', message: `Olá, ${authStore.user.full_name}` });
              } else {
                  productionStore.currentOperatorBadge = scannedBadge;
              }
          } catch (e) {
              $q.notify({ type: 'negative', message: 'Crachá inválido.' });
          } finally {
              $q.loading.hide();
              scanBuffer = '';
          }
      }
      scanBuffer = ''; 
  } else {
      if (event.key.length === 1) {
          scanBuffer += event.key;
          clearTimeout(scanTimeout);
          scanTimeout = setTimeout(() => { scanBuffer = ''; }, 2000);
      }
  }
}

onMounted(() => {
  if (productionStore.currentStepIndex !== -1) viewedStepIndex.value = productionStore.currentStepIndex;
  timerInterval = setInterval(() => { currentTime.value = new Date(); }, 1000);
  resetTimer();
  window.addEventListener('keydown', handleGlobalKeydown);

  if (!productionStore.currentOperatorBadge && authStore.user?.employee_id && authStore.user.role !== 'admin') {
      productionStore.currentOperatorBadge = authStore.user.employee_id;
  }
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleGlobalKeydown);
    clearInterval(timerInterval);
});
</script>

<style>
.vemag-bg-primary { background-color: #008C7A !important; }
.vemag-text-primary { color: #008C7A !important; }
.vemag-bg-secondary { background-color: #66B8B0 !important; }
.vemag-text-secondary { color: #66B8B0 !important; }
.vemag-bg-light { background-color: #E0F2F1 !important; }
.bg-vemag-gradient { background: linear-gradient(135deg, #008C7A 0%, #00695C 100%); }
.bg-black-transparent { background-color: rgba(0,0,0,0.15); }
.hover-bg-grey-3:hover { background-color: #eeeeee; }
</style>

<style scoped>
.reason-card {
  border-radius: 12px;
  background: white;
  transition: all 0.3s ease;
  border: 1px solid #e0e0e0;
  min-height: 85px;
}

.reason-card:hover {
  background: #f5f5f5;
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

/* Destaque para os itens Especiais (Troca de Turno e Manutenção) */
.special-active {
  border: 2px solid #008C7A !important; /* Borda cor da marca */
  background: #f0fdfa !important;
}

/* Animação de pulsação discreta no ícone sinalizado */
.pulse-animation {
  animation: pulse-shadow 2s infinite;
}

@keyframes pulse-shadow {
  0% { box-shadow: 0 0 0 0 rgba(0, 140, 122, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(0, 140, 122, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 140, 122, 0); }
}

.lh-tight {
  line-height: 1.2;
}
.font-inter { font-family: 'Roboto', sans-serif; }
.maintenance-dialog {
  width: 550px; 
  max-width: 95vw; 
  border-radius: 24px; 
  overflow: hidden;
  background: #ffffff;
}

/* Pulsação do ícone de aviso para atrair atenção */
.pulse-animation {
  animation: pulse-red 2s infinite;
  box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7);
  border-radius: 50%;
}

@keyframes pulse-red {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 15px rgba(255, 255, 255, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
}

/* Botão de confirmação com destaque */
.q-btn--push.text-weight-bolder {
  border: 1px solid rgba(255, 255, 255, 0.3);
}
.maintenance-card {
  width: 600px;
  max-width: 95vw;
  border-radius: 20px;
}

.sub-reason-btn {
  border-radius: 12px;
  height: 80px;
  border: 1px solid #e0e0e0;
  color: #616161;
  background: #fafafa;
  transition: all 0.2s ease;
}

.sub-reason-active {
  background: #ffebee !important;
  border: 2px solid #b71c1c !important;
  color: #b71c1c !important;
  transform: scale(1.03);
}

.letter-spacing-1 {
  letter-spacing: 1px;
}
.font-monospace { font-family: 'Courier New', monospace; letter-spacing: -1px; }
.lh-small { line-height: 1.1; }
.col-grow { flex-grow: 1; }
.opacity-60 { opacity: 0.6; }
.opacity-50 { opacity: 0.5; }
.opacity-20 { opacity: 0.2; }
.opacity-80 { opacity: 0.8; }
.hover-scale-producing { transition: all 0.2s ease-in-out; }
.hover-scale-producing:active { transform: scale(0.98); }
.border-bottom-light { border-bottom: 2px solid #e0e0e0; }
</style>